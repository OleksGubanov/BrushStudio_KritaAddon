# main_panel.py
import krita
from PyQt5.QtWidgets import (QDockWidget, QWidget, QBoxLayout, QHBoxLayout, QVBoxLayout,
                             QPushButton, QComboBox, QLabel, QSpinBox, 
                             QMenu, QAction, QWidgetAction, QListWidgetItem, 
                             QFormLayout, QApplication,
                             QButtonGroup, QToolButton, QGridLayout, QGroupBox, QRadioButton, QCheckBox)
from PyQt5.QtCore import Qt, QPoint, QEvent
from PyQt5.QtGui import QIcon, QPixmap, QPalette

# === ИСПРАВЛЕННЫЕ ИМПОРТЫ ===
from .core_state import PanelState
from .ui_grid import AdaptiveGridWidget, SlotScrollArea # Ошибка была здесь (ListWidget)
from .ui_slot import BrushSlot
from .preview_service import PreviewService
# ============================

class SmartPanelDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brush Studio")
        self.state = PanelState()
        self.preview_service = PreviewService(self.state)
        
        self._last_width = 0
        self._last_height = 0
        self._updating = False  # Prevents recursion in resizeEvent
        
        self.main_widget = QWidget()
        self.main_layout = QBoxLayout(QBoxLayout.TopToBottom)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 1. Initialize grid first
        self.grid = AdaptiveGridWidget(self.state)
        
        # 2. Pass the grid directly as a positional argument
        self.scroll_area = SlotScrollArea(self.grid)
        
        self.main_layout.addWidget(self.scroll_area)
        
        # Settings button (gear)
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedSize(24, 24)
        self.btn_settings.clicked.connect(self.show_popup_settings)
        
        # Control bar container
        self.control_bar = QWidget()
        self.control_layout = QHBoxLayout(self.control_bar)
        self.control_layout.setContentsMargins(4, 4, 4, 4)
        self.control_layout.addStretch()
        self.control_layout.addWidget(self.btn_settings)
        
        self.main_layout.addWidget(self.control_bar)
        self.main_widget.setLayout(self.main_layout)
        self.setWidget(self.main_widget)
        
        self.load_slots()
        self.build_popup_menu()
        
        # Install event filter for tracking resize
        self.main_widget.installEventFilter(self)
        
    def eventFilter(self, obj, event):
        if obj == self.main_widget and event.type() == QEvent.Resize:
            self.on_widget_resized()
        return super().eventFilter(obj, event)
        
    def on_widget_resized(self):
        if self._updating:
            return
        self._updating = True
        try:
            w = self.main_widget.width()
            h = self.main_widget.height()
            if w != self._last_width or h != self._last_height:
                self._last_width = w
                self._last_height = h
                
                # Определяем эффективное расположение
                is_wide = w > h
                eff_layout, eff_anchor, eff_bar = self.state.get_effective_state(is_wide)
                
                # Перестраиваем архитектуру панелей
                self.update_layout_architecture(eff_layout, eff_bar)
                
                # Пересчитываем сетку
                self.grid.update_architecture(eff_layout)
        finally:
            self._updating = False
            
    def update_layout_architecture(self, eff_layout, eff_bar):
        # Меняем направление главного контейнера
        if eff_layout == "vertical":
            self.main_layout.setDirection(QBoxLayout.TopToBottom)
        else:
            self.main_layout.setDirection(QBoxLayout.LeftToRight)
            
        # Позиционируем control_bar (с кнопкой настроек)
        self.main_layout.removeWidget(self.control_bar)
        self.main_layout.removeWidget(self.scroll_area)
        
        if eff_bar in ["Top", "Left"]:
            self.main_layout.addWidget(self.control_bar)
            self.main_layout.addWidget(self.scroll_area)
        else:
            self.main_layout.addWidget(self.scroll_area)
            self.main_layout.addWidget(self.control_bar)
            
    def load_slots(self):
        # Очищаем и создаем заново слоты на основе total_slots
        new_slots = []
        for i in range(self.state.total_slots):
            slot = BrushSlot(i, self.state, self.preview_service)
            
            # Загружаем имя кисти, если оно сохранено для этого слота
            brush_name = self.state.slot_data.get(str(i), "")
            if brush_name:
                slot.set_brush(brush_name)
                
            slot.clicked.connect(self.on_slot_clicked)
            slot.clear_requested.connect(self.clear_slot)
            new_slots.append(slot)
            
        # Передаем созданные слоты в AdaptiveGridWidget
        self.grid.set_slots(new_slots)

    def on_slot_clicked(self, idx, brush_name):
        app = krita.Krita.instance()
        window = app.activeWindow()
        if not window or not window.activeView(): 
            return
        
        if brush_name:
            preset = app.resources("preset").get(brush_name)
            if preset:
                window.activeView().setCurrentBrushPreset(preset)
        else:
            preset = window.activeView().currentBrushPreset()
            if preset:
                self.state.slot_data[str(idx)] = preset.name()
                self.state.save()
                self.load_slots()
                
    def on_context_menu(self, pos):
        item = self.grid.itemAt(pos)
        if not item: return
        idx = item.data(Qt.UserRole + 1)
        brush_name = item.data(Qt.UserRole)
        
        if brush_name:
            menu = QMenu(self)
            menu.setStyleSheet(self.settings_menu.styleSheet())
            clear_action = QAction("Clear Slot", self)
            clear_action.triggered.connect(lambda: self.clear_slot(idx))
            menu.addAction(clear_action)
            menu.exec_(self.grid.viewport().mapToGlobal(pos))
            
    def clear_slot(self, idx):
        if str(idx) in self.state.slot_data:
            del self.state.slot_data[str(idx)]
            self.state.save()
            self.load_slots()

    def build_popup_menu(self):
        self.settings_menu = QMenu(self)
        
        settings_widget = QWidget()
        settings_widget.setMinimumWidth(300) # Сделали чуть шире для новых элементов
        form_layout = QFormLayout()
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(8)
        
        # --- Базовые настройки (Твои текущие) ---
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["auto", "manual"])
        self.cmb_mode.setCurrentText(self.state.mode)
        
        self.cmb_auto_vert = QComboBox(); self.cmb_auto_vert.addItems(["Left", "Right"]); self.cmb_auto_vert.setCurrentText(self.state.auto_vert_docks)
        self.cmb_auto_horiz = QComboBox(); self.cmb_auto_horiz.addItems(["Top", "Bottom"]); self.cmb_auto_horiz.setCurrentText(self.state.auto_horiz_docks)
        
        self.cmb_layout = QComboBox(); self.cmb_layout.addItems(["vertical", "horizontal"]); self.cmb_layout.setCurrentText(self.state.manual_layout)
        self.cmb_anchor = QComboBox(); self.cmb_anchor.addItems(["Left", "Right", "Top", "Bottom"]); self.cmb_anchor.setCurrentText(self.state.manual_anchor)
        self.cmb_bar = QComboBox(); self.cmb_bar.addItems(["Top", "Bottom", "Left", "Right"]); self.cmb_bar.setCurrentText(self.state.manual_bar)
        
        self.spin_slots = QSpinBox(); self.spin_slots.setRange(1, 200); self.spin_slots.setValue(self.state.total_slots)
        self.spin_divider = QSpinBox(); self.spin_divider.setRange(1, 20); self.spin_divider.setValue(self.state.main_divider)
        self.spin_base = QSpinBox(); self.spin_base.setRange(8, 256); self.spin_base.setSingleStep(2); self.spin_base.setValue(self.state.base_icon_size)
        self.spin_padding = QSpinBox(); self.spin_padding.setRange(0, 20); self.spin_padding.setValue(self.state.slot_padding)
        
        aspect_layout = QHBoxLayout()
        aspect_layout.setContentsMargins(0,0,0,0)
        self.spin_asp_w = QSpinBox(); self.spin_asp_w.setRange(1, 100); self.spin_asp_w.setValue(int(self.state.aspect_w))
        self.spin_asp_h = QSpinBox(); self.spin_asp_h.setRange(1, 100); self.spin_asp_h.setValue(int(self.state.aspect_h))
        aspect_layout.addWidget(self.spin_asp_w); aspect_layout.addWidget(QLabel(":")); aspect_layout.addWidget(self.spin_asp_h)
        
        # =========================================================
        # НОВЫЙ БЛОК 1: Углы привязки (Визуальная сетка 2x2)
        # =========================================================
        self.corner_groupbox = QGroupBox()
        self.corner_groupbox.setStyleSheet("QGroupBox { border: none; margin-top: 0px; }")
        corner_layout = QGridLayout()
        corner_layout.setContentsMargins(0, 0, 0, 0)
        corner_layout.setSpacing(4)
        self.corner_btns = QButtonGroup(self)
        
        corners = [("LT", "↖", 0, 0), ("RT", "↗", 0, 1), 
                   ("LB", "↙", 1, 0), ("RB", "↘", 1, 1)]
                   
        for code, icon, row, col in corners:
            btn = QToolButton()
            btn.setText(icon)
            btn.setCheckable(True)
            btn.setFixedSize(30, 30)
            if self.state.grid_corner == code:
                btn.setChecked(True)
            self.corner_btns.addButton(btn)
            btn.setProperty("corner_code", code) # Сохраняем код угла в кнопку
            corner_layout.addWidget(btn, row, col)
            
        self.corner_groupbox.setLayout(corner_layout)

        # =========================================================
        # НОВЫЙ БЛОК 2: А/Б тесты метода рендера
        # =========================================================
        self.render_groupbox = QGroupBox()
        self.render_groupbox.setStyleSheet("QGroupBox { border: none; margin-top: 0px; }")
        render_layout = QHBoxLayout()
        render_layout.setContentsMargins(0, 0, 0, 0)
        
        self.rb_render_a = QRadioButton("A (Hidden)")
        self.rb_render_b = QRadioButton("B (Active)")
        if self.state.render_method == 'B': self.rb_render_b.setChecked(True)
        else: self.rb_render_a.setChecked(True)
        
        render_layout.addWidget(self.rb_render_a)
        render_layout.addWidget(self.rb_render_b)
        self.render_groupbox.setLayout(render_layout)

        # =========================================================
        # НОВЫЙ БЛОК 3: Чекбоксы отображения (Движок, Мазок, Иконка)
        # =========================================================
        self.chk_engine = QCheckBox("Show Engine Icon (💧/🖌)")
        self.chk_engine.setChecked(self.state.show_engine)
        
        self.chk_icon = QCheckBox("Show Brush Icon")
        self.chk_icon.setChecked(getattr(self.state, 'show_icon', True))
        
        self.chk_stroke = QCheckBox("Show Brush Stroke")
        self.chk_stroke.setChecked(getattr(self.state, 'show_stroke', True))

        # --- Лейблы ---
        self.lbl_auto_v = QLabel("Auto Anchor (Vert Docks):"); self.lbl_auto_h = QLabel("Auto Anchor (Horiz Docks):")
        self.lbl_man_l = QLabel("Manual Layout:"); self.lbl_man_a = QLabel("Manual Cross-Anchor:"); self.lbl_man_b = QLabel("Manual Settings Bar:")
        self.lbl_corner = QLabel("Grid Start Corner:") # Новый лейбл для углов
        
        # --- Сборка формы ---
        form_layout.addRow("Mode:", self.cmb_mode)
        form_layout.addRow(self.lbl_auto_v, self.cmb_auto_vert)
        form_layout.addRow(self.lbl_auto_h, self.cmb_auto_horiz)
        form_layout.addRow(self.lbl_corner, self.corner_groupbox) # Вставили Углы
        
        form_layout.addRow(self.lbl_man_l, self.cmb_layout)
        form_layout.addRow(self.lbl_man_a, self.cmb_anchor)
        form_layout.addRow(self.lbl_man_b, self.cmb_bar)
        
        form_layout.addRow("Total Grid Slots:", self.spin_slots)
        form_layout.addRow("Target Cols/Rows:", self.spin_divider)
        form_layout.addRow("Base Icon Size (px):", self.spin_base)
        form_layout.addRow("Slot Padding (px):", self.spin_padding)
        form_layout.addRow("Proportions (W : H):", aspect_layout)
        
        form_layout.addRow("Render Engine:", self.render_groupbox) # Вставили А/Б
        form_layout.addRow("Visibility:", self.chk_engine)         # Вставили чекбоксы
        form_layout.addRow("", self.chk_icon)
        form_layout.addRow("", self.chk_stroke)
        
        settings_widget.setLayout(form_layout)
        action = QWidgetAction(self.settings_menu)
        action.setDefaultWidget(settings_widget)
        self.settings_menu.addAction(action)
        
        self.update_settings_visibility()
        
        # --- Подключение сигналов ---
        self.cmb_mode.currentTextChanged.connect(self.on_settings_changed)
        self.cmb_auto_vert.currentTextChanged.connect(self.on_settings_changed)
        self.cmb_auto_horiz.currentTextChanged.connect(self.on_settings_changed)
        self.cmb_layout.currentTextChanged.connect(self.on_settings_changed)
        self.cmb_anchor.currentTextChanged.connect(self.on_settings_changed)
        self.cmb_bar.currentTextChanged.connect(self.on_settings_changed)
        self.spin_slots.valueChanged.connect(self.on_settings_changed)
        self.spin_divider.valueChanged.connect(self.on_settings_changed)
        self.spin_base.valueChanged.connect(self.on_settings_changed)
        self.spin_padding.valueChanged.connect(self.on_settings_changed)
        self.spin_asp_w.valueChanged.connect(self.on_settings_changed)
        self.spin_asp_h.valueChanged.connect(self.on_settings_changed)
        
        # Сигналы от новых элементов
        self.corner_btns.buttonClicked.connect(self.on_settings_changed)
        self.rb_render_a.toggled.connect(self.on_settings_changed)
        self.chk_engine.stateChanged.connect(self.on_settings_changed)
        self.chk_icon.stateChanged.connect(self.on_settings_changed)
        self.chk_stroke.stateChanged.connect(self.on_settings_changed)

    def update_settings_visibility(self):
        is_auto = (self.cmb_mode.currentText() == "auto")
        
        self.lbl_auto_v.setVisible(is_auto); self.cmb_auto_vert.setVisible(is_auto)
        self.lbl_auto_h.setVisible(is_auto); self.cmb_auto_horiz.setVisible(is_auto)
        
        # Показываем блок настройки углов ТОЛЬКО в режиме Auto
        self.lbl_corner.setVisible(is_auto); self.corner_groupbox.setVisible(is_auto)
        
        self.lbl_man_l.setVisible(not is_auto); self.cmb_layout.setVisible(not is_auto)
        self.lbl_man_a.setVisible(not is_auto); self.cmb_anchor.setVisible(not is_auto)
        self.lbl_man_b.setVisible(not is_auto); self.cmb_bar.setVisible(not is_auto)
        
        if not is_auto:
            self.cmb_anchor.blockSignals(True)
            self.cmb_anchor.clear()
            if self.cmb_layout.currentText() == "vertical":
                self.cmb_anchor.addItems(["Left", "Right"])
            else:
                self.cmb_anchor.addItems(["Top", "Bottom"])
            self.cmb_anchor.setCurrentText(self.state.manual_anchor)
            self.cmb_anchor.blockSignals(False)

    def show_popup_settings(self):
        btn_pos = self.btn_settings.mapToGlobal(QPoint(0, 0))
        screen_rect = QApplication.desktop().screenGeometry(self.btn_settings)
        menu_size = self.settings_menu.sizeHint()

        x = btn_pos.x()
        y = btn_pos.y() + self.btn_settings.height()

        if btn_pos.x() > screen_rect.center().x(): x = btn_pos.x() - menu_size.width() + self.btn_settings.width()
        if btn_pos.y() > screen_rect.center().y(): y = btn_pos.y() - menu_size.height()

        self.settings_menu.exec_(QPoint(x, y))

    def on_settings_changed(self, *args):
        self.state.mode = self.cmb_mode.currentText()
        self.state.auto_vert_docks = self.cmb_auto_vert.currentText()
        self.state.auto_horiz_docks = self.cmb_auto_horiz.currentText()
        self.state.manual_layout = self.cmb_layout.currentText()
        self.state.manual_anchor = self.cmb_anchor.currentText()
        self.state.manual_bar = self.cmb_bar.currentText()
        self.state.total_slots = self.spin_slots.value()
        self.state.main_divider = self.spin_divider.value()
        self.state.base_icon_size = self.spin_base.value()
        self.state.slot_padding = self.spin_padding.value()
        self.state.aspect_w = max(1.0, float(self.spin_asp_w.value()))
        self.state.aspect_h = max(1.0, float(self.spin_asp_h.value()))
        
        # --- Сохранение новых параметров ---
        for btn in self.corner_btns.buttons():
            if btn.isChecked():
                self.state.grid_corner = btn.property("corner_code")
                break
                
        self.state.render_method = 'B' if self.rb_render_b.isChecked() else 'A'
        self.state.show_engine = self.chk_engine.isChecked()
        self.state.show_icon = self.chk_icon.isChecked()
        self.state.show_stroke = self.chk_stroke.isChecked()
        
        self.update_settings_visibility()
        self.state.save()
        

        self.load_slots()

    def on_dock_changed(self, area):
        self.state.current_dock_area = area
        self.apply_architecture()

    def on_float_changed(self, is_floating):
        self.state.is_floating = is_floating
        self.apply_architecture()