from PyQt5.QtWidgets import (QMenu, QWidget, QFormLayout, QComboBox, QSpinBox, 
                             QHBoxLayout, QLabel, QGroupBox, QGridLayout, 
                             QToolButton, QButtonGroup, QRadioButton, QCheckBox, QWidgetAction)

class SettingsMenu(QMenu):
    """Изолированный интерфейс изменения конфигурации (всплывающее окно)."""
    def __init__(self, parent, state):
        super().__init__(parent)
        self.state = state
        self.build_ui()

    def build_ui(self):
        widget = QWidget()
        widget.setMinimumWidth(320)
        layout = QFormLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

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
        self.spin_base = QSpinBox(); self.spin_base.setRange(8, 256); self.spin_base.setValue(self.state.base_icon_size)
        self.spin_padding = QSpinBox(); self.spin_padding.setRange(0, 20); self.spin_padding.setValue(self.state.slot_padding)

        aspect_box = QHBoxLayout()
        self.spin_asp_w = QSpinBox(); self.spin_asp_w.setRange(1, 100); self.spin_asp_w.setValue(int(self.state.aspect_w))
        self.spin_asp_h = QSpinBox(); self.spin_asp_h.setRange(1, 100); self.spin_asp_h.setValue(int(self.state.aspect_h))
        aspect_box.addWidget(self.spin_asp_w); aspect_box.addWidget(QLabel(":")); aspect_box.addWidget(self.spin_asp_h)

        # Сетка квадрантов 2х2
        self.corner_group = QGroupBox()
        self.corner_group.setStyleSheet("QGroupBox { border: none; }")
        corner_grid = QGridLayout(self.corner_group)
        corner_grid.setContentsMargins(0,0,0,0)
        self.corner_btns = QButtonGroup(self)
        
        corners = [("LT", "↖", 0, 0), ("RT", "↗", 0, 1), ("LB", "↙", 1, 0), ("RB", "↘", 1, 1)]
        for code, icon, r, c in corners:
            btn = QToolButton()
            btn.setText(icon)
            btn.setCheckable(True)
            btn.setFixedSize(32, 32)
            if self.state.grid_corner == code: btn.setChecked(True)
            self.corner_btns.addButton(btn)
            btn.setProperty("corner_code", code)
            corner_grid.addWidget(btn, r, c)

        # А/Б Тестирование
        self.render_group = QGroupBox()
        self.render_group.setStyleSheet("QGroupBox { border: none; }")
        render_box = QHBoxLayout(self.render_group)
        render_box.setContentsMargins(0,0,0,0)
        self.rb_a = QRadioButton("A (Hidden)")
        self.rb_b = QRadioButton("B (Active)")
        if self.state.render_method == "B": self.rb_b.setChecked(True)
        else: self.rb_a.setChecked(True)
        render_box.addWidget(self.rb_a); render_box.addWidget(self.rb_b)

        # Чекбоксы видимости элементов ячеек
        self.chk_engine = QCheckBox("Show Engine (💧/🖌)")
        self.chk_engine.setChecked(self.state.show_engine)
        self.chk_icon = QCheckBox("Show Preset Icon")
        self.chk_icon.setChecked(self.state.show_icon)
        self.chk_stroke = QCheckBox("Show Brush Stroke")
        self.chk_stroke.setChecked(self.state.show_stroke)

        # Сборка формы настроек
        layout.addRow("Mode:", self.cmb_mode)
        layout.addRow("Auto Vert Anchor:", self.cmb_auto_vert)
        layout.addRow("Auto Horiz Anchor:", self.cmb_auto_horiz)
        layout.addRow("Grid Corner (2x2):", self.corner_group)
        layout.addRow("Manual Layout:", self.cmb_layout)
        layout.addRow("Manual Anchor:", self.cmb_anchor)
        layout.addRow("Manual Bar:", self.cmb_bar)
        layout.addRow("Total Slots:", self.spin_slots)
        layout.addRow("Divider (Cols/Rows):", self.spin_divider)
        layout.addRow("Icon Size (px):", self.spin_base)
        layout.addRow("Padding (px):", self.spin_padding)
        layout.addRow("Proportions (W:H):", aspect_box)
        layout.addRow("Render Engine:", self.render_group)
        layout.addRow("Visibility:", self.chk_engine)
        layout.addRow("", self.chk_icon)
        layout.addRow("", self.chk_stroke)

        action = QWidgetAction(self)
        action.setDefaultWidget(widget)
        self.addAction(action)

        # Привязка сигналов
        self.cmb_mode.currentTextChanged.connect(self.save_settings)
        self.cmb_auto_vert.currentTextChanged.connect(self.save_settings)
        self.cmb_auto_horiz.currentTextChanged.connect(self.save_settings)
        self.cmb_layout.currentTextChanged.connect(self.save_settings)
        self.cmb_anchor.currentTextChanged.connect(self.save_settings)
        self.cmb_bar.currentTextChanged.connect(self.save_settings)
        self.spin_slots.valueChanged.connect(self.save_settings)
        self.spin_divider.valueChanged.connect(self.save_settings)
        self.spin_base.valueChanged.connect(self.save_settings)
        self.spin_padding.valueChanged.connect(self.save_settings)
        self.spin_asp_w.valueChanged.connect(self.save_settings)
        self.spin_asp_h.valueChanged.connect(self.save_settings)
        self.corner_btns.buttonClicked.connect(self.save_settings)
        self.rb_a.toggled.connect(self.save_settings)
        self.chk_engine.stateChanged.connect(self.save_settings)
        self.chk_icon.stateChanged.connect(self.save_settings)
        self.chk_stroke.stateChanged.connect(self.save_settings)

    def save_settings(self):
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
        self.state.aspect_w = float(self.spin_asp_w.value())
        self.state.aspect_h = float(self.spin_asp_h.value())
        
        for btn in self.corner_btns.buttons():
            if btn.isChecked():
                self.state.grid_corner = btn.property("corner_code")
                break
                
        self.state.render_method = "B" if self.rb_b.isChecked() else "A"
        self.state.show_engine = self.chk_engine.isChecked()
        self.state.show_icon = self.chk_icon.isChecked()
        self.state.show_stroke = self.chk_stroke.isChecked()
        
        self.state.save()
        self.parent().load_slots()