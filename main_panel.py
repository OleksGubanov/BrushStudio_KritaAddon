import krita
from PyQt5.QtWidgets import (QDockWidget, QWidget, QBoxLayout, QHBoxLayout, 
                             QPushButton, QComboBox, QLabel, QSpinBox, 
                             QMenu, QWidgetAction, QListWidgetItem, 
                             QFormLayout, QGridLayout, QApplication)
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
        
        # --- Settings Bar ---
        self.top_bar = QWidget()
        self.top_bar.setStyleSheet("background-color: #202020;") 
        self.bar_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.bar_layout.setContentsMargins(2, 2, 2, 2)
        self.bar_layout.setSpacing(0)
        
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedSize(20, 20)
        self.btn_settings.setStyleSheet("QPushButton { background: transparent; color: #888; border: none; font-size: 14px; } QPushButton:hover { color: white; }")
        self.btn_settings.clicked.connect(self.show_popup_settings)
        
        self.bar_layout.addStretch()
        self.bar_layout.addWidget(self.btn_settings)
        self.top_bar.setLayout(self.bar_layout)
        
        # --- Anchor Grid Container ---
        self.anchor_widget = QWidget()
        self.anchor_layout = QGridLayout()
        self.anchor_layout.setContentsMargins(0,0,0,0)
        self.anchor_layout.setSpacing(0)
        self.anchor_widget.setLayout(self.anchor_layout)
        
        self.grid = AdaptiveListWidget(self.state)
        self.grid.itemClicked.connect(self.on_brush_clicked)
        
        self.main_widget.setLayout(self.main_layout)
        self.setWidget(self.main_widget)
        
        self.build_popup_menu()
        self.apply_architecture()

    def apply_architecture(self):
        """Rebuilds the entire layout based on independent Bar and Anchor properties"""
        # 1. Update Settings Bar Position
        self.main_layout.removeWidget(self.top_bar)
        self.main_layout.removeWidget(self.anchor_widget)
        
        bp = self.state.bar_position
        if bp == "Top":
            self.main_layout.setDirection(QBoxLayout.TopToBottom)
            self.bar_layout.setDirection(QBoxLayout.LeftToRight)
        elif bp == "Bottom":
            self.main_layout.setDirection(QBoxLayout.BottomToTop)
            self.bar_layout.setDirection(QBoxLayout.LeftToRight)
        elif bp == "Left":
            self.main_layout.setDirection(QBoxLayout.LeftToRight)
            self.bar_layout.setDirection(QBoxLayout.TopToBottom)
        elif bp == "Right":
            self.main_layout.setDirection(QBoxLayout.RightToLeft)
            self.bar_layout.setDirection(QBoxLayout.TopToBottom)
            
        self.main_layout.addWidget(self.top_bar)
        self.main_layout.addWidget(self.anchor_widget)

        # 2. Update Grid Anchor Position (Pushes the grid into a specific corner)
        self.anchor_layout.removeWidget(self.grid)
        
        # Reset stretches
        self.anchor_layout.setRowStretch(0, 0)
        self.anchor_layout.setRowStretch(1, 0)
        self.anchor_layout.setColumnStretch(0, 0)
        self.anchor_layout.setColumnStretch(1, 0)
        
        ac = self.state.anchor_corner
        if ac == "Top-Left":
            self.anchor_layout.addWidget(self.grid, 0, 0)
            self.anchor_layout.setRowStretch(1, 1); self.anchor_layout.setColumnStretch(1, 1)
        elif ac == "Top-Right":
            self.anchor_layout.addWidget(self.grid, 0, 1)
            self.anchor_layout.setRowStretch(1, 1); self.anchor_layout.setColumnStretch(0, 1)
        elif ac == "Bottom-Left":
            self.anchor_layout.addWidget(self.grid, 1, 0)
            self.anchor_layout.setRowStretch(0, 1); self.anchor_layout.setColumnStretch(1, 1)
        elif ac == "Bottom-Right":
            self.anchor_layout.addWidget(self.grid, 1, 1)
            self.anchor_layout.setRowStretch(0, 1); self.anchor_layout.setColumnStretch(0, 1)

        self.load_real_brushes()
        self.grid.recalculate_math()

    def build_popup_menu(self):
        self.settings_menu = QMenu(self)
        self.settings_menu.setStyleSheet("QMenu { background-color: #2D2D2D; border: 1px solid #555; border-radius: 6px; color: #EEE; }")
        
        settings_widget = QWidget()
        settings_widget.setMinimumWidth(260)
        form_layout = QFormLayout()
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(8)
        
        # Base Size Rule (8px to 256px, step 2)
        self.spin_base = QSpinBox()
        self.spin_base.setRange(8, 256)
        self.spin_base.setSingleStep(2)
        self.spin_base.setValue(self.state.base_icon_size)
        
        # Placement Rules
        self.cmb_anchor = QComboBox()
        self.cmb_anchor.addItems(["Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right"])
        self.cmb_anchor.setCurrentText(self.state.anchor_corner)
        
        self.cmb_bar = QComboBox()
        self.cmb_bar.addItems(["Top", "Bottom", "Left", "Right"])
        self.cmb_bar.setCurrentText(self.state.bar_position)
        
        self.cmb_layout = QComboBox()
        self.cmb_layout.addItems(["vertical", "horizontal"])
        self.cmb_layout.setCurrentText(self.state.manual_layout)
        
        self.spin_divider = QSpinBox()
        self.spin_divider.setRange(1, 20)
        self.spin_divider.setValue(self.state.main_divider)
        
        self.spin_padding = QSpinBox()
        self.spin_padding.setRange(0, 10)
        self.spin_padding.setValue(self.state.slot_padding)
        
        aspect_layout = QHBoxLayout()
        aspect_layout.setContentsMargins(0,0,0,0)
        self.spin_asp_w = QSpinBox(); self.spin_asp_w.setRange(1, 100); self.spin_asp_w.setValue(int(self.state.aspect_w))
        self.spin_asp_h = QSpinBox(); self.spin_asp_h.setRange(1, 100); self.spin_asp_h.setValue(int(self.state.aspect_h))
        aspect_layout.addWidget(self.spin_asp_w); aspect_layout.addWidget(QLabel(":")); aspect_layout.addWidget(self.spin_asp_h)
        
        form_layout.addRow("Base Icon Size (px):", self.spin_base)
        form_layout.addRow("Anchor Corner:", self.cmb_anchor)
        form_layout.addRow("Settings Bar:", self.cmb_bar)
        form_layout.addRow("Layout Direction:", self.cmb_layout)
        form_layout.addRow("Target Cols/Rows:", self.spin_divider)
        form_layout.addRow("Slot Padding (px):", self.spin_padding)
        form_layout.addRow("Proportions (W : H):", aspect_layout)
        
        settings_widget.setLayout(form_layout)
        action = QWidgetAction(self.settings_menu)
        action.setDefaultWidget(settings_widget)
        self.settings_menu.addAction(action)
        
        self.spin_base.valueChanged.connect(self.on_settings_changed)
        self.cmb_anchor.currentTextChanged.connect(self.on_settings_changed)
        self.cmb_bar.currentTextChanged.connect(self.on_settings_changed)
        self.cmb_layout.currentTextChanged.connect(self.on_settings_changed)
        self.spin_divider.valueChanged.connect(self.on_settings_changed)
        self.spin_padding.valueChanged.connect(self.on_settings_changed)
        self.spin_asp_w.valueChanged.connect(self.on_settings_changed)
        self.spin_asp_h.valueChanged.connect(self.on_settings_changed)

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

    def on_settings_changed(self):
        self.state.base_icon_size = self.spin_base.value()
        self.state.anchor_corner = self.cmb_anchor.currentText()
        self.state.bar_position = self.cmb_bar.currentText()
        self.state.manual_layout = self.cmb_layout.currentText()
        self.state.main_divider = self.spin_divider.value()
        self.state.slot_padding = self.spin_padding.value()
        self.state.aspect_w = float(self.spin_asp_w.value())
        self.state.aspect_h = float(self.spin_asp_h.value())
        
        self.state.save()
        self.apply_architecture()

    def load_real_brushes(self):
        self.grid.clear()
        app = krita.Krita.instance()
        all_presets = list(app.resources("preset").items())[:40]
        
        # If user anchors to bottom, reverse the list so brushes build upwards from the anchor
        if "Bottom" in self.state.anchor_corner:
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