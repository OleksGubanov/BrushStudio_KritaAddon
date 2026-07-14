from PyQt5.QtWidgets import (QMenu, QWidget, QFormLayout, QComboBox, QSpinBox, 
                             QHBoxLayout, QLabel, QGroupBox, QRadioButton, QCheckBox, QWidgetAction)

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
        self.cmb_mode.setCurrentText(self.state.appearance.mode)

        self.spin_slots = QSpinBox(); self.spin_slots.setRange(1, 200); self.spin_slots.setValue(self.state.grid.total_slots)
        self.spin_divider = QSpinBox(); self.spin_divider.setRange(1, 20); self.spin_divider.setValue(self.state.grid.main_divider)
        self.spin_base = QSpinBox(); self.spin_base.setRange(8, 256); self.spin_base.setValue(self.state.appearance.base_icon_size)
        self.spin_padding = QSpinBox(); self.spin_padding.setRange(0, 20); self.spin_padding.setValue(self.state.appearance.slot_padding)

        aspect_box = QHBoxLayout()
        self.spin_asp_w = QSpinBox(); self.spin_asp_w.setRange(1, 100); self.spin_asp_w.setValue(int(self.state.grid.aspect_w))
        self.spin_asp_h = QSpinBox(); self.spin_asp_h.setRange(1, 100); self.spin_asp_h.setValue(int(self.state.grid.aspect_h))
        aspect_box.addWidget(self.spin_asp_w); aspect_box.addWidget(QLabel(":")); aspect_box.addWidget(self.spin_asp_h)

        # Отражение сетки
        self.chk_flip_x = QCheckBox("Flip Grid Horizontally")
        self.chk_flip_x.setChecked(self.state.grid.flip_x)
        self.chk_flip_y = QCheckBox("Flip Grid Vertically")
        self.chk_flip_y.setChecked(self.state.grid.flip_y)

        # А/Б Тестирование Рендерера
        self.render_group = QGroupBox()
        self.render_group.setStyleSheet("QGroupBox { border: none; }")
        render_box = QHBoxLayout(self.render_group)
        render_box.setContentsMargins(0,0,0,0)
        
        self.rb_a = QRadioButton("A (Hidden Doc)")
        self.rb_b = QRadioButton("B (Active Doc)")
        self.rb_fallback = QRadioButton("Fallback")
        
        if self.state.preview.render_method == "A": self.rb_a.setChecked(True)
        elif self.state.preview.render_method == "B": self.rb_b.setChecked(True)
        else: self.rb_fallback.setChecked(True)
        
        render_box.addWidget(self.rb_a)
        render_box.addWidget(self.rb_b)
        render_box.addWidget(self.rb_fallback)

        # Чекбоксы видимости
        self.chk_engine = QCheckBox("Show Engine (💧/🖌)")
        self.chk_engine.setChecked(self.state.ui.show_engine)
        self.chk_icon = QCheckBox("Show Preset Icon")
        self.chk_icon.setChecked(self.state.ui.show_icon)
        self.chk_stroke = QCheckBox("Show Brush Stroke")
        self.chk_stroke.setChecked(self.state.ui.show_stroke)

        layout.addRow("Mode:", self.cmb_mode)
        layout.addRow("Total Slots:", self.spin_slots)
        layout.addRow("Divider (Cols/Rows):", self.spin_divider)
        layout.addRow("Icon Size (px):", self.spin_base)
        layout.addRow("Padding (px):", self.spin_padding)
        layout.addRow("Proportions (W:H):", aspect_box)
        layout.addRow("Grid Origin:", self.chk_flip_x)
        layout.addRow("", self.chk_flip_y)
        layout.addRow("Render Engine:", self.render_group)
        layout.addRow("Visibility:", self.chk_engine)
        layout.addRow("", self.chk_icon)
        layout.addRow("", self.chk_stroke)

        action = QWidgetAction(self)
        action.setDefaultWidget(widget)
        self.addAction(action)

        # Привязка сигналов
        self.cmb_mode.currentTextChanged.connect(self.save_settings)
        self.spin_slots.valueChanged.connect(self.save_settings)
        self.spin_divider.valueChanged.connect(self.save_settings)
        self.spin_base.valueChanged.connect(self.save_settings)
        self.spin_padding.valueChanged.connect(self.save_settings)
        self.spin_asp_w.valueChanged.connect(self.save_settings)
        self.spin_asp_h.valueChanged.connect(self.save_settings)
        self.chk_flip_x.stateChanged.connect(self.save_settings)
        self.chk_flip_y.stateChanged.connect(self.save_settings)
        self.rb_a.toggled.connect(self.save_settings)
        self.rb_b.toggled.connect(self.save_settings)
        self.rb_fallback.toggled.connect(self.save_settings)
        self.chk_engine.stateChanged.connect(self.save_settings)
        self.chk_icon.stateChanged.connect(self.save_settings)
        self.chk_stroke.stateChanged.connect(self.save_settings)

    def save_settings(self):
        self.state.appearance.mode = self.cmb_mode.currentText()
        self.state.grid.total_slots = self.spin_slots.value()
        self.state.grid.main_divider = self.spin_divider.value()
        self.state.appearance.base_icon_size = self.spin_base.value()
        self.state.appearance.slot_padding = self.spin_padding.value()
        self.state.grid.aspect_w = float(self.spin_asp_w.value())
        self.state.grid.aspect_h = float(self.spin_asp_h.value())
        
        self.state.grid.flip_x = self.chk_flip_x.isChecked()
        self.state.grid.flip_y = self.chk_flip_y.isChecked()
        
        if self.rb_a.isChecked(): self.state.preview.render_method = "A"
        elif self.rb_b.isChecked(): self.state.preview.render_method = "B"
        else: self.state.preview.render_method = "fallback"
            
        self.state.ui.show_engine = self.chk_engine.isChecked()
        self.state.ui.show_icon = self.chk_icon.isChecked()
        self.state.ui.show_stroke = self.chk_stroke.isChecked()
        
        self.state.save()
        self.parent().load_slots()