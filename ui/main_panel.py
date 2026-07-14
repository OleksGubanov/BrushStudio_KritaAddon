import krita
from PyQt5.QtWidgets import QDockWidget, QWidget, QBoxLayout, QHBoxLayout, QPushButton, QApplication
from PyQt5.QtCore import Qt, QPoint, QEvent
from PyQt5.QtGui import QPixmap

from ..core.state import PanelState
from ..core.models import BrushData
from ..core.parser import PresetMetadataReader
from ..services.preview import PreviewCache, PreviewRenderer, PreviewService
from .grid import AdaptiveGridWidget, SlotScrollArea
from .slot import BrushSlot
from .settings_popup import SettingsMenu

class SmartPanelDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brush Studio")
        self.state = PanelState()

        # Инициализация новой модульной архитектуры Preview
        self.preview_cache = PreviewCache(version=self.state.preview.cache_version)
        self.preview_renderer = PreviewRenderer(self.state)
        self.preview_service = PreviewService(self.preview_cache, self.preview_renderer)
        
        # Подписка на сигнал готового мазка
        self.preview_service.previewReady.connect(self.on_preview_ready)

        self._last_width = 0
        self._last_height = 0
        self._updating = False  

        self.main_widget = QWidget()
        self.main_layout = QBoxLayout(QBoxLayout.TopToBottom)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.grid = AdaptiveGridWidget(self.state)
        self.scroll_area = SlotScrollArea(self.grid)
        
        # Ленивая загрузка мазков при прокрутке
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._check_visible_slots)
        
        self.main_layout.addWidget(self.scroll_area)

        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedSize(24, 24)
        self.btn_settings.clicked.connect(self.show_popup_settings)

        self.control_bar = QWidget()
        self.control_layout = QHBoxLayout(self.control_bar)
        self.control_layout.setContentsMargins(4, 4, 4, 4)
        self.control_layout.addStretch()
        self.control_layout.addWidget(self.btn_settings)

        self.main_layout.addWidget(self.control_bar)
        self.main_widget.setLayout(self.main_layout)
        self.setWidget(self.main_widget)

        self.settings_menu = SettingsMenu(self, self.state)
        self.load_slots()

        self.main_widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.main_widget and event.type() == QEvent.Resize:
            self.on_widget_resized()
        return super().eventFilter(obj, event)

    def on_widget_resized(self):
        if self._updating: return
        self._updating = True
        try:
            w = self.main_widget.width()
            h = self.main_widget.height()
            if w != self._last_width or h != self._last_height:
                self._last_width = w
                self._last_height = h
                
                is_wide = w > h
                eff_layout = "horizontal" if is_wide else "vertical"
                self.update_layout_architecture(eff_layout)
        finally:
            self._updating = False
            self._check_visible_slots()  # Проверяем видимость после ресайза

    def update_layout_architecture(self, eff_layout):
        direction = QBoxLayout.LeftToRight if eff_layout == "horizontal" else QBoxLayout.TopToBottom
        if self.main_layout.direction() != direction:
            self.main_layout.setDirection(direction)

    def load_slots(self):
        self.preview_service.cancel_all() # Отменяем генерацию при обновлении сетки
        app = krita.Krita.instance()
        new_slots = []
        
        for i in range(self.state.grid.total_slots):
            slot = BrushSlot(i)
            brush_name = self.state.slot_data.get(str(i), "")
            brush_data = BrushData(name=brush_name)
            
            if brush_name:
                preset = app.resources("preset").get(brush_name)
                if preset:
                    if self.state.ui.show_icon:
                        brush_data.icon_pixmap = QPixmap.fromImage(preset.image())
                    
                    metadata = PresetMetadataReader.get_metadata(brush_name)
                    if self.state.ui.show_engine:
                        brush_data.engine_icon = metadata.get("engine", "🖌")
                        
            slot.set_data(brush_data)
            slot.clicked.connect(self.on_slot_clicked)
            slot.clear_requested.connect(self.clear_slot)
            new_slots.append(slot)

        self.grid.set_slots(new_slots)
        self._last_width = 0
        self._last_height = 0
        self.on_widget_resized()
        
    def _check_visible_slots(self):
        if not self.state.ui.show_stroke:
            return
            
        vp = self.scroll_area.viewport().rect()
        vp.adjust(0, -50, 0, 50)  # Небольшой буфер для рендера заранее
        
        for slot in self.grid.slots:
            if not slot.data or not slot.data.name: continue
            if slot.data.stroke_pixmap: continue
                
            if slot.geometry().intersects(vp):
                metadata = PresetMetadataReader.get_metadata(slot.data.name)
                self.preview_service.request_stroke(slot.data.name, metadata, high_priority=True)

    def on_preview_ready(self, preset_name, pixmap):
        for slot in self.grid.slots:
            if slot.data and slot.data.name == preset_name:
                slot.data.stroke_pixmap = pixmap
                slot.set_data(slot.data) # Триггерит перерисовку тупого виджета

    def on_slot_clicked(self, idx):
        app = krita.Krita.instance()
        window = app.activeWindow()
        if not window or not window.activeView(): return

        brush_name = self.state.slot_data.get(str(idx), "")
        if brush_name:
            preset = app.resources("preset").get(brush_name)
            if preset: window.activeView().setCurrentBrushPreset(preset)
        else:
            preset = window.activeView().currentBrushPreset()
            if preset:
                self.state.slot_data[str(idx)] = preset.name()
                self.state.save()
                self.load_slots()

    def clear_slot(self, idx):
        if str(idx) in self.state.slot_data:
            del self.state.slot_data[str(idx)]
            self.state.save()
            self.load_slots()

    def show_popup_settings(self):
        btn_pos = self.btn_settings.mapToGlobal(QPoint(0, 0))
        screen_rect = QApplication.desktop().screenGeometry(self.btn_settings)
        menu_size = self.settings_menu.sizeHint()

        x = btn_pos.x()
        y = btn_pos.y() + self.btn_settings.height()

        if btn_pos.x() > screen_rect.center().x(): 
            x = btn_pos.x() - menu_size.width() + self.btn_settings.width()
        if btn_pos.y() > screen_rect.center().y(): 
            y = btn_pos.y() - menu_size.height()

        self.settings_menu.exec_(QPoint(x, y))