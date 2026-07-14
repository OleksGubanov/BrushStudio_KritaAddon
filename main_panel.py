import krita
from PyQt5.QtWidgets import (QDockWidget, QWidget, QBoxLayout, QHBoxLayout, QVBoxLayout,
                             QPushButton, QComboBox, QLabel, QSpinBox, 
                             QMenu, QAction, QWidgetAction, QListWidgetItem, 
                             QFormLayout, QApplication)
from PyQt5.QtCore import Qt, QPoint, QEvent
from PyQt5.QtGui import QIcon, QPixmap, QPalette

from .core_state import PanelState
from .ui_grid import AdaptiveListWidget

class SmartPanelDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brush Studio")
        self.state = PanelState()
        
        self._last_width = 0
        self._last_height = 0
        self._updating = False  # Флаг для предотвращения рекурсии в resizeEvent
        
        self.main_widget = QWidget()
        self.main_layout = QBoxLayout(QBoxLayout.TopToBottom)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # --- Settings Bar ---
        self.top_bar = QWidget()
        self.bar_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.bar_layout.setContentsMargins(2, 2, 2, 2)
        self.bar_layout.setSpacing(0)
        
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedSize(20, 20)
        self.btn_settings.clicked.connect(self.show_popup_settings)
        
        self.bar_layout.addStretch()
        self.bar_layout.addWidget(self.btn_settings)
        self.top_bar.setLayout(self.bar_layout)
        
        # --- Anchor Grid Container ---
        self.anchor_widget = QWidget()
        self.anchor_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.anchor_layout.setContentsMargins(0,0,0,0)
        self.anchor_layout.setSpacing(0)
        self.anchor_widget.setLayout(self.anchor_layout)
        
        self.grid = AdaptiveListWidget(self.state)
        self.grid.itemClicked.connect(self.on_slot_clicked)
        
        self.grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self.on_context_menu)
        
        self.anchor_layout.addWidget(self.grid)
        self.anchor_layout.addStretch()
        
        self.main_layout.addWidget(self.top_bar)
        self.main_layout.addWidget(self.anchor_widget)
        self.main_widget.setLayout(self.main_layout)
        self.setWidget(self.main_widget)
        
        self.build_popup_menu()
        self.dockLocationChanged.connect(self.on_dock_changed)
        self.topLevelChanged.connect(self.on_float_changed)
        
        self.update_theme()
        # apply_architecture будет вызван при первом resizeEvent

    def update_theme(self):
        palette = QApplication.palette()
        bg_color = palette.color(QPalette.Window).name()
        text_color = palette.color(QPalette.WindowText).name()
        hover_color = palette.color(QPalette.Highlight).name()
        
        self.top_bar.setStyleSheet(f"background-color: {bg_color}; color: {text_color};")
        
        self.btn_settings.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {text_color};
                border: none;
                font-size: 14px;
            }}
            QPushButton:hover {{
                color: {hover_color};
            }}
        """)
        
        menu_bg = palette.color(QPalette.Window).name()
        menu_text = palette.color(QPalette.WindowText).name()
        menu_highlight = palette.color(QPalette.Highlight).name()
        self.settings_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {menu_bg};
                border: 1px solid {palette.color(QPalette.Dark).name()};
                border-radius: 6px;
                color: {menu_text};
            }}
            QMenu::item:selected {{
                background-color: {menu_highlight};
            }}
        """)
        
        self.grid.viewport().update()

    def changeEvent(self, event):
        if event.type() == QEvent.PaletteChange:
            self.update_theme()
        super().changeEvent(event)

    def resizeEvent(self, event):
        if self._updating:
            super().resizeEvent(event)
            return
        
        self._last_width = event.size().width()
        self._last_height = event.size().height()
        
        # Вызываем apply_architecture с защитой от рекурсии
        self._updating = True
        self.apply_architecture()
        self._updating = False
        
        super().resizeEvent(event)

    def apply_architecture(self):
        w = self._last_width if self._last_width > 0 else self.main_widget.width()
        h = self._last_height if self._last_height > 0 else self.main_widget.height()
        is_wide = w > h
        
        eff_layout, eff_anchor, eff_bar = self.state.get_effective_state(is_wide)
        
        if eff_layout == "vertical":
            if eff_anchor == "Left":
                self.anchor_layout.setDirection(QBoxLayout.LeftToRight)
            else:
                self.anchor_layout.setDirection(QBoxLayout.RightToLeft)
        else:
            if eff_anchor == "Top":
                self.anchor_layout.setDirection(QBoxLayout.TopToBottom)
            else:
                self.anchor_layout.setDirection(QBoxLayout.BottomToTop)

        if eff_bar == "Top":
            self.main_layout.setDirection(QBoxLayout.TopToBottom)
            self.bar_layout.setDirection(QBoxLayout.LeftToRight)
        elif eff_bar == "Bottom":
            self.main_layout.setDirection(QBoxLayout.BottomToTop)
            self.bar_layout.setDirection(QBoxLayout.LeftToRight)
        elif eff_bar == "Left":
            self.main_layout.setDirection(QBoxLayout.LeftToRight)
            self.bar_layout.setDirection(QBoxLayout.TopToBottom)
        elif eff_bar == "Right":
            self.main_layout.setDirection(QBoxLayout.RightToLeft)
            self.bar_layout.setDirection(QBoxLayout.TopToBottom)
            
        self.grid.recalculate_math(eff_layout)
        self.load_slots()

    def load_slots(self):
        self.grid.clear()
        app = krita.Krita.instance()
        resources = app.resources("preset")
        
        grid_size = self.grid.gridSize() 
        
        for i in range(self.state.total_slots):
            item = QListWidgetItem()
            item.setData(Qt.UserRole + 1, i)
            item.setSizeHint(grid_size) 
            
            brush_name = self.state.slot_data.get(str(i))
            if brush_name and brush_name in resources:
                preset = resources.get(brush_name)
                icon = QIcon(QPixmap.fromImage(preset.image()))
                item.setData(Qt.DecorationRole, icon)
                item.setData(Qt.UserRole, brush_name)
                item.setToolTip(f"{brush_name}\nRight-click to clear")
            else:
                item.setData(Qt.DecorationRole, QIcon())
                item.setData(Qt.UserRole, "")
                item.setToolTip("Empty Slot\nLeft-click: Assign active brush")
                
            self.grid.addItem(item)

    def on_slot_clicked(self, item):
        idx = item.data(Qt.UserRole + 1)
        brush_name = item.data(Qt.UserRole)
        app = krita.Krita.instance()
        window = app.activeWindow()
        if not window or not window.activeView(): return
        
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
        settings_widget.setMinimumWidth(280)
        form_layout = QFormLayout()
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(8)
        
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
        
        self.lbl_auto_v = QLabel("Auto Anchor (Vert Docks):"); self.lbl_auto_h = QLabel("Auto Anchor (Horiz Docks):")
        self.lbl_man_l = QLabel("Manual Layout:"); self.lbl_man_a = QLabel("Manual Cross-Anchor:"); self.lbl_man_b = QLabel("Manual Settings Bar:")
        
        form_layout.addRow("Mode:", self.cmb_mode)
        form_layout.addRow(self.lbl_auto_v, self.cmb_auto_vert)
        form_layout.addRow(self.lbl_auto_h, self.cmb_auto_horiz)
        form_layout.addRow(self.lbl_man_l, self.cmb_layout)
        form_layout.addRow(self.lbl_man_a, self.cmb_anchor)
        form_layout.addRow(self.lbl_man_b, self.cmb_bar)
        form_layout.addRow("Total Grid Slots:", self.spin_slots)
        form_layout.addRow("Target Cols/Rows:", self.spin_divider)
        form_layout.addRow("Base Icon Size (px):", self.spin_base)
        form_layout.addRow("Slot Padding (px):", self.spin_padding)
        form_layout.addRow("Proportions (W : H):", aspect_layout)
        
        settings_widget.setLayout(form_layout)
        action = QWidgetAction(self.settings_menu)
        action.setDefaultWidget(settings_widget)
        self.settings_menu.addAction(action)
        
        self.update_settings_visibility()
        
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

    def update_settings_visibility(self):
        is_auto = (self.cmb_mode.currentText() == "auto")
        self.lbl_auto_v.setVisible(is_auto); self.cmb_auto_vert.setVisible(is_auto)
        self.lbl_auto_h.setVisible(is_auto); self.cmb_auto_horiz.setVisible(is_auto)
        
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

    def on_settings_changed(self):
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
        
        self.update_settings_visibility()
        self.state.save()
        self.apply_architecture()

    def on_dock_changed(self, area):
        self.state.current_dock_area = area
        self.apply_architecture()

    def on_float_changed(self, is_floating):
        self.state.is_floating = is_floating
        self.apply_architecture()