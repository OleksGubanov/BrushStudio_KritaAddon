import krita
from PyQt5.QtWidgets import (QDockWidget, QWidget, QBoxLayout, QHBoxLayout, 
                             QPushButton, QComboBox, QLabel, QSpinBox, 
                             QMenu, QWidgetAction, QListWidgetItem, QCheckBox, 
                             QFormLayout, QDoubleSpinBox, QApplication)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon, QPixmap

from .core_state import PanelState
from .ui_grid import AdaptiveListWidget

class SmartPanelDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brush Studio")
        self.state = PanelState()
        
        self.main_widget = QWidget()
        self.main_layout = QBoxLayout(QBoxLayout.TopToBottom)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.top_bar = QWidget()
        self.top_bar.setStyleSheet("background-color: #202020;") 
        self.bar_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.bar_layout.setContentsMargins(2, 2, 2, 2)
        self.bar_layout.setSpacing(0)
        
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedSize(20, 20)
        self.btn_settings.setStyleSheet("QPushButton { background: transparent; color: #888; border: none; font-size: 14px; } QPushButton:hover { color: white; }")
        
        self.bar_layout.addStretch()
        self.bar_layout.addWidget(self.btn_settings)
        self.top_bar.setLayout(self.bar_layout)
        
        self.grid = AdaptiveListWidget(self.state, self)
        
        self.main_layout.addWidget(self.top_bar)
        self.main_layout.addWidget(self.grid)
        self.main_widget.setLayout(self.main_layout)
        self.setWidget(self.main_widget)
        
        self.build_popup_menu()
        
        self.btn_settings.clicked.connect(self.show_popup_settings)
        self.grid.itemClicked.connect(self.on_brush_clicked)
        self.dockLocationChanged.connect(self.on_dock_changed)
        self.topLevelChanged.connect(self.on_float_changed)
        
        self.grid.recalculate_math(force=True)

    def update_bar_orientation(self, layout_type, direction):
        if layout_type == "vertical":
            self.bar_layout.setDirection(QBoxLayout.LeftToRight) 
            if direction == "right":
                self.main_layout.setDirection(QBoxLayout.BottomToTop) 
            else:
                self.main_layout.setDirection(QBoxLayout.TopToBottom) 
        else:
            self.bar_layout.setDirection(QBoxLayout.TopToBottom) 
            if direction == "bottom":
                self.main_layout.setDirection(QBoxLayout.RightToLeft) 
            else:
                self.main_layout.setDirection(QBoxLayout.LeftToRight) 

    def build_popup_menu(self):
        self.settings_menu = QMenu(self)
        self.settings_menu.setStyleSheet("QMenu { background-color: #2D2D2D; border: 1px solid #555; border-radius: 6px; color: #EEE; }")
        
        settings_widget = QWidget()
        settings_widget.setMinimumWidth(240)
        
        form_layout = QFormLayout()
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(8)
        
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["auto", "manual"])
        self.cmb_mode.setCurrentText(self.state.mode)
        
        self.chk_auto_invert = QCheckBox("Invert Direction")
        self.chk_auto_invert.setChecked(self.state.auto_invert)
        
        self.cmb_layout = QComboBox()
        self.cmb_layout.addItems(["vertical", "horizontal"])
        self.cmb_layout.setCurrentText(self.state.manual_layout)
        
        # New Scale Factor
        self.spin_scale = QDoubleSpinBox()
        self.spin_scale.setRange(0.5, 10.0)
        self.spin_scale.setSingleStep(0.1)
        self.spin_scale.setValue(self.state.scale_factor)
        
        self.spin_divider = QSpinBox()
        self.spin_divider.setRange(1, 10)
        self.spin_divider.setValue(self.state.main_divider)
        
        aspect_layout = QHBoxLayout()
        aspect_layout.setContentsMargins(0,0,0,0)
        self.spin_asp_w = QSpinBox()
        self.spin_asp_w.setRange(1, 100)
        self.spin_asp_w.setValue(int(self.state.aspect_w))
        self.spin_asp_h = QSpinBox()
        self.spin_asp_h.setRange(1, 100)
        self.spin_asp_h.setValue(int(self.state.aspect_h))
        aspect_layout.addWidget(self.spin_asp_w)
        aspect_layout.addWidget(QLabel(":"))
        aspect_layout.addWidget(self.spin_asp_h)
        
        self.cmb_dir = QComboBox()
        
        # Technical actuals readout
        self.lbl_actuals = QLabel("Actual: -")
        self.lbl_actuals.setStyleSheet("color: #E2E8F0; font-size: 11px; background: #1A202C; padding: 4px; border-radius: 4px;")
        self.lbl_actuals.setAlignment(Qt.AlignCenter)
        
        self.lbl_layout = QLabel("Manual Layout:")
        
        form_layout.addRow("Mode:", self.cmb_mode)
        form_layout.addRow("", self.chk_auto_invert)
        form_layout.addRow(self.lbl_layout, self.cmb_layout)
        form_layout.addRow("Scale (Base 32px):", self.spin_scale)
        form_layout.addRow("Target Cols/Rows:", self.spin_divider)
        form_layout.addRow("Proportions (W : H):", aspect_layout)
        
        self.lbl_dir = QLabel("Start Direction:")
        form_layout.addRow(self.lbl_dir, self.cmb_dir)
        form_layout.addRow(self.lbl_actuals)
        
        settings_widget.setLayout(form_layout)
        action = QWidgetAction(self.settings_menu)
        action.setDefaultWidget(settings_widget)
        self.settings_menu.addAction(action)
        
        self.update_settings_visibility()

        self.cmb_mode.currentTextChanged.connect(self.on_settings_changed)
        self.chk_auto_invert.stateChanged.connect(self.on_settings_changed)
        self.cmb_layout.currentTextChanged.connect(self.on_settings_changed)
        self.spin_scale.valueChanged.connect(self.on_settings_changed)
        self.spin_divider.valueChanged.connect(self.on_settings_changed)
        self.spin_asp_w.valueChanged.connect(self.on_settings_changed)
        self.spin_asp_h.valueChanged.connect(self.on_settings_changed)
        self.cmb_dir.currentTextChanged.connect(self.on_dir_changed)

    def update_settings_visibility(self):
        is_auto = (self.cmb_mode.currentText() == "auto")
        is_manual = not is_auto
        
        self.chk_auto_invert.setVisible(is_auto)
        self.cmb_layout.setVisible(is_manual)
        self.lbl_layout.setVisible(is_manual)
        self.cmb_dir.setVisible(is_manual)
        self.lbl_dir.setVisible(is_manual)
        
        if is_manual:
            self.cmb_dir.blockSignals(True)
            self.cmb_dir.clear()
            if self.cmb_layout.currentText() == "vertical":
                self.cmb_dir.addItems(["left", "right"])
                self.cmb_dir.setCurrentText(self.state.start_dir_vert)
            else:
                self.cmb_dir.addItems(["top", "bottom"])
                self.cmb_dir.setCurrentText(self.state.start_dir_horiz)
            self.cmb_dir.blockSignals(False)

    def update_actuals_display(self):
        """Updates the technical readout in the settings menu"""
        div = self.state.actual_divider
        w = int(self.state.actual_w)
        h = int(self.state.actual_h)
        self.lbl_actuals.setText(f"Actual Grid: {div} | Slot Size: {w}x{h} px")

    def show_popup_settings(self):
        """Smart diagonal positioning based on screen quadrants"""
        btn_pos = self.btn_settings.mapToGlobal(QPoint(0, 0))
        screen_rect = QApplication.desktop().screenGeometry(self.btn_settings)
        menu_size = self.settings_menu.sizeHint()

        # Default assumes Top-Left origin, opening Bottom-Right
        x = btn_pos.x()
        y = btn_pos.y() + self.btn_settings.height()

        # If button is in the Right half of the screen, open to the Left
        if btn_pos.x() > screen_rect.center().x():
            x = btn_pos.x() - menu_size.width() + self.btn_settings.width()

        # If button is in the Bottom half of the screen, open to the Top
        if btn_pos.y() > screen_rect.center().y():
            y = btn_pos.y() - menu_size.height()

        self.settings_menu.exec_(QPoint(x, y))

    def on_settings_changed(self):
        self.state.mode = self.cmb_mode.currentText()
        self.state.auto_invert = self.chk_auto_invert.isChecked()
        self.state.manual_layout = self.cmb_layout.currentText()
        self.state.scale_factor = float(self.spin_scale.value())
        self.state.main_divider = self.spin_divider.value()
        self.state.aspect_w = float(self.spin_asp_w.value())
        self.state.aspect_h = float(self.spin_asp_h.value())
        
        self.update_settings_visibility()
        self.state.save()
        self.grid.recalculate_math(force=True)
        
    def on_dir_changed(self, val):
        if self.cmb_layout.currentText() == "vertical":
            self.state.start_dir_vert = val
        else:
            self.state.start_dir_horiz = val
        self.state.save()
        self.grid.recalculate_math(force=True)

    def on_dock_changed(self, area):
        self.state.current_dock_area = area
        self.grid.recalculate_math(force=True)

    def on_float_changed(self, is_floating):
        self.state.is_floating = is_floating
        self.grid.recalculate_math(force=True)

    def load_real_brushes(self, effective_layout="vertical", effective_dir="left"):
        self.grid.clear()
        app = krita.Krita.instance()
        all_presets = list(app.resources("preset").items())[:30]
        
        if effective_layout == "horizontal" and effective_dir == "bottom":
            all_presets.reverse()
            
        for name, preset in all_presets:
            icon = QIcon(QPixmap.fromImage(preset.image()))
            item = QListWidgetItem()
            item.setData(Qt.DecorationRole, icon)
            item.setData(Qt.UserRole, name)
            item.setToolTip(name)
            self.grid.addItem(item)

    def on_brush_clicked(self, item):
        preset_name = item.data(Qt.UserRole)
        app = krita.Krita.instance()
        action = app.action('KritaShape/KritaToolFreehand')
        if action: action.trigger()
        window = app.activeWindow()
        if window and window.activeView():
            preset = app.resources("preset").get(preset_name)
            if preset: window.activeView().setCurrentBrushPreset(preset)