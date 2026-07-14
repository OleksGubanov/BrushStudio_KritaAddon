import krita
from PyQt5.QtWidgets import QDockWidget, QWidget, QBoxLayout, QHBoxLayout, QPushButton, QApplication
from PyQt5.QtCore import Qt, QPoint, QEvent
from ..core.state import PanelState
from .grid import AdaptiveGridWidget, SlotScrollArea
from .slot import BrushSlot
from .settings_popup import SettingsMenu
from ..services.preview import PreviewService

class SmartPanelDocker(QDockWidget):
    """Главный координатор интерфейса докера в Krita."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brush Studio")
        self.state = PanelState()
        self.preview_service = PreviewService(self.state)
        
        self._last_width = 0
        self._last_height = 0
        self._updating = False  
        
        self.main_widget = QWidget()
        self.main_layout = QBoxLayout(QBoxLayout.TopToBottom)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.grid = AdaptiveGridWidget(self.state)
        self.scroll_area = SlotScrollArea(self.grid)
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
                eff_layout, eff_anchor, eff_bar = self.state.get_effective_state(is_wide)
                self.update_layout_architecture(eff_layout, eff_bar)
                self.grid.update_architecture(eff_layout)
        finally:
            self._updating = False
            
    def update_layout_architecture(self, eff_layout, eff_bar):
        if self.main_layout.direction() != (QBoxLayout.TopToBottom if eff_layout == "vertical" else QBoxLayout.LeftToRight):
            if eff_layout == "vertical":
                self.main_layout.setDirection(QBoxLayout.TopToBottom)
            else:
                self.main_layout.setDirection(QBoxLayout.LeftToRight)
            
        self.main_layout.removeWidget(self.control_bar)
        self.main_layout.removeWidget(self.scroll_area)
        
        if eff_bar in ["Top", "Left"]:
            self.main_layout.addWidget(self.control_bar)
            self.main_layout.addWidget(self.scroll_area)
        else:
            self.main_layout.addWidget(self.scroll_area)
            self.main_layout.addWidget(self.control_bar)
            
    def load_slots(self):
        app = krita.Krita.instance()
        new_slots = []
        for i in range(self.state.total_slots):
            slot = BrushSlot(i, self.state, self.preview_service)
            brush_name = self.state.slot_data.get(str(i), "")
            if brush_name:
                # ИСПРАВЛЕНО: Извлекаем текстуру иконки из ресурсов Krita
                preset = app.resources("preset").get(brush_name)
                preset_image = preset.image() if preset else None
                slot.set_brush(brush_name, preset_image)
                
            slot.clicked.connect(self.on_slot_clicked)
            slot.clear_requested.connect(self.clear_slot)
            new_slots.append(slot)
            
        self.grid.set_slots(new_slots)
        
        # ИСПРАВЛЕНО: Принудительно заставляем сетку мгновенно перерисоваться под новые настройки
        self._last_width = 0
        self._last_height = 0
        self.on_widget_resized()

    def on_slot_clicked(self, idx, brush_name):
        app = krita.Krita.instance()
        window = app.activeWindow()
        if not window or not window.activeView(): return
        
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