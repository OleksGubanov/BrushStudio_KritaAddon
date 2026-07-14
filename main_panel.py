import krita
from PyQt5.QtWidgets import (QDockWidget, QWidget, QBoxLayout, QHBoxLayout, 
                             QPushButton, QComboBox, QLabel, QSpinBox, 
                             QMenu, QAction, QWidgetAction, QFormLayout, QApplication)
from PyQt5.QtCore import Qt, QPoint, QEvent
from PyQt5.QtGui import QPalette

from .core_state import PanelState
from .ui_grid import AdaptiveGridWidget, SlotScrollArea
from .ui_slot import BrushSlot

class SmartPanelDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brush Studio")
        self.state = PanelState()
        self._presets_cache = {}
        
        self.main_widget = QWidget()
        self.main_layout = QBoxLayout(QBoxLayout.TopToBottom)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.top_bar = QWidget()
        self.bar_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.bar_layout.setContentsMargins(2, 2, 2, 2)
        
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedSize(20, 20)
        self.btn_settings.clicked.connect(self.show_popup_settings)
        
        self.bar_layout.addStretch()
        self.bar_layout.addWidget(self.btn_settings)
        self.top_bar.setLayout(self.bar_layout)
        
        # New Pure Architecture
        self.grid = AdaptiveGridWidget(self.state)
        self.scroll_area = SlotScrollArea(self.grid)
        
        self.main_layout.addWidget(self.top_bar)
        self.main_layout.addWidget(self.scroll_area)
        self.main_widget.setLayout(self.main_layout)
        self.setWidget(self.main_widget)
        
        self.build_popup_menu()
        self.dockLocationChanged.connect(self.on_dock_changed)
        self.topLevelChanged.connect(self.on_float_changed)
        
        self.update_theme()
        self.apply_architecture(force_reload=True)

    def get_presets_map(self, force_refresh=False):
        if not self._presets_cache or force_refresh:
            self._presets_cache = krita.Krita.instance().resources("preset")
        return self._presets_cache

    def changeEvent(self, event):
        if event and event.type() == QEvent.PaletteChange:
            self.update_theme()
        super().changeEvent(event)

    def update_theme(self):
        palette = self.palette()
        bg = palette.color(QPalette.Window).name()
        text = palette.color(QPalette.WindowText).name()
        border = palette.color(QPalette.Mid).name()
        hl = palette.color(QPalette.Highlight).name()
        
        self.main_widget.setStyleSheet(f"background-color: {bg};")
        self.top_bar.setStyleSheet(f"background-color: {bg}; border-bottom: 1px solid {border};")
        self.btn_settings.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {text}; border: none; font-size: 14px; }}"
            f"QPushButton:hover {{ color: {hl}; }}"
        )
        self.settings_menu.setStyleSheet(
            f"QMenu {{ background-color: {bg}; border: 1px solid {border}; border-radius: 6px; color: {text}; }}"
            f"QMenu::item:selected {{ background-color: {hl}; color: {palette.color(QPalette.HighlightedText).name()}; }}"
        )
        for slot in self.grid.slots: slot.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_architecture()

    def showEvent(self, event):
        super().showEvent(event)
        self.get_presets_map(force_refresh=True)
        self.load_slots()

    def apply_architecture(self, force_reload=False):
        w, h = self.main_widget.width(), self.main_widget.height()
        eff_layout, eff_anchor, eff_bar = self.state.get_effective_state(w > h)
        
        # 1. Native QScrollArea Alignment! Replaces anchor stretches
        align = Qt.AlignTop
        if eff_anchor == "Left": align |= Qt.AlignLeft
        elif eff_anchor == "Right": align |= Qt.AlignRight
        elif eff_anchor == "Top": align |= Qt.AlignTop
        elif eff_anchor == "Bottom": align |= Qt.AlignBottom
        self.scroll_area.setAlignment(align)

        if eff_layout == "vertical":
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 2. Bar Position
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
            
        self.grid.update_architecture(eff_layout)
        if force_reload: self.load_slots()

    def load_slots(self):
        resources = self.get_presets_map()
        slots_list = []
        
        for i in range(self.state.total_slots):
            slot = BrushSlot(i, self.state)
            brush_name = self.state.slot_data.get(str(i))
            
            if brush_name and brush_name in resources:
                preset = resources.get(brush_name)
                slot.set_brush(brush_name, preset.image())
            else:
                slot.set_brush("")
                
            slot.clicked.connect(self.on_slot_clicked)
            slot.clear_requested.connect(self.clear_slot)
            slots_list.append(slot)
            
        self.grid.set_slots(slots_list)

    def on_slot_clicked(self, idx, brush_name):
        app = krita.Krita.instance()
        window = app.activeWindow()
        if not window or not window.activeView(): return
        
        if brush_name:
            preset = self.get_presets_map().get(brush_name)
            if preset: window.activeView().setCurrentBrushPreset(preset)
        else:
            preset = window.activeView().currentBrushPreset()
            if preset:
                self.state.slot_data[str(idx)] = preset.name()
                self.get_presets_map()[preset.name()] = preset
                self.state.save()
                self.load_slots()
                
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
        
        self.cmb_mode = QComboBox(); self.cmb_mode.addItems(["auto", "manual"]); self.cmb_mode.setCurrentText(self.state.mode)
        self.cmb_auto_vert = QComboBox(); self.cmb_auto_vert.addItems(["Left", "Right"]); self.cmb_auto_vert.setCurrentText(self.state.auto_vert_docks)
        self.cmb_auto_horiz = QComboBox(); self.cmb_auto_horiz.addItems(["Top", "Bottom"]); self.cmb_auto_horiz.setCurrentText(self.state.auto_horiz_docks)
        self.cmb_layout = QComboBox(); self.cmb_layout.addItems(["vertical", "horizontal"]); self.cmb_layout.setCurrentText(self.state.manual_layout)
        self.cmb_anchor = QComboBox(); self.cmb_anchor.addItems(["Left", "Right", "Top", "Bottom"]); self.cmb_anchor.setCurrentText(self.state.manual_anchor)
        self.cmb_bar = QComboBox(); self.cmb_bar.addItems(["Top", "Bottom", "Left", "Right"]); self.cmb_bar.setCurrentText(self.state.manual_bar)
        
        self.spin_slots = QSpinBox(); self.spin_slots.setRange(1, 200); self.spin_slots.setValue(self.state.total_slots)
        self.spin_divider = QSpinBox(); self.spin_divider.setRange(1, 20); self.spin_divider.setValue(self.state.main_divider)
        self.spin_base = QSpinBox(); self.spin_base.setRange(8, 256); self.spin_base.setValue(self.state.base_icon_size)
        self.spin_padding = QSpinBox(); self.spin_padding.setRange(0, 20); self.spin_padding.setValue(self.state.slot_padding)
        
        aspect_layout = QHBoxLayout(); aspect_layout.setContentsMargins(0,0,0,0)
        self.spin_asp_w = QSpinBox(); self.spin_asp_w.setValue(int(self.state.aspect_w))
        self.spin_asp_h = QSpinBox(); self.spin_asp_h.setValue(int(self.state.aspect_h))
        aspect_layout.addWidget(self.spin_asp_w); aspect_layout.addWidget(QLabel(":")); aspect_layout.addWidget(self.spin_asp_h)
        
        self.lbl_auto_v, self.lbl_auto_h = QLabel("Auto (Vert):"), QLabel("Auto (Horiz):")
        self.lbl_man_l, self.lbl_man_a, self.lbl_man_b = QLabel("Layout:"), QLabel("Anchor:"), QLabel("Settings Bar:")
        
        form_layout.addRow("Mode:", self.cmb_mode)
        form_layout.addRow(self.lbl_auto_v, self.cmb_auto_vert)
        form_layout.addRow(self.lbl_auto_h, self.cmb_auto_horiz)
        form_layout.addRow(self.lbl_man_l, self.cmb_layout)
        form_layout.addRow(self.lbl_man_a, self.cmb_anchor)
        form_layout.addRow(self.lbl_man_b, self.cmb_bar)
        form_layout.addRow("Total Slots:", self.spin_slots)
        form_layout.addRow("Target Cols/Rows:", self.spin_divider)
        form_layout.addRow("Base Size (px):", self.spin_base)
        form_layout.addRow("Slot Padding:", self.spin_padding)
        form_layout.addRow("Proportions:", aspect_layout)
        
        settings_widget.setLayout(form_layout)
        action = QWidgetAction(self.settings_menu)
        action.setDefaultWidget(settings_widget)
        self.settings_menu.addAction(action)
        
        self.update_settings_visibility()
        
        for w in [self.cmb_mode, self.cmb_auto_vert, self.cmb_auto_horiz, self.cmb_layout, self.cmb_anchor, self.cmb_bar]:
            w.currentTextChanged.connect(self.on_settings_changed)
        for w in [self.spin_slots, self.spin_divider, self.spin_base, self.spin_padding, self.spin_asp_w, self.spin_asp_h]:
            w.valueChanged.connect(self.on_settings_changed)

    def update_settings_visibility(self):
        is_auto = (self.cmb_mode.currentText() == "auto")
        for lbl, w in [(self.lbl_auto_v, self.cmb_auto_vert), (self.lbl_auto_h, self.cmb_auto_horiz)]:
            lbl.setVisible(is_auto); w.setVisible(is_auto)
        for lbl, w in [(self.lbl_man_l, self.cmb_layout), (self.lbl_man_a, self.cmb_anchor), (self.lbl_man_b, self.cmb_bar)]:
            lbl.setVisible(not is_auto); w.setVisible(not is_auto)
        
        if not is_auto:
            self.cmb_anchor.blockSignals(True)
            self.cmb_anchor.clear()
            self.cmb_anchor.addItems(["Left", "Right"] if self.cmb_layout.currentText() == "vertical" else ["Top", "Bottom"])
            self.cmb_anchor.setCurrentText(self.state.manual_anchor)
            self.cmb_anchor.blockSignals(False)

    def show_popup_settings(self):
        btn_pos = self.btn_settings.mapToGlobal(QPoint(0, 0))
        self.settings_menu.exec_(QPoint(btn_pos.x() - self.settings_menu.sizeHint().width() + 20, btn_pos.y() + 20))

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
        self.state.aspect_w, self.state.aspect_h = float(self.spin_asp_w.value()), float(self.spin_asp_h.value())
        
        self.update_settings_visibility()
        self.state.save()
        self.apply_architecture(force_reload=True)

    def on_dock_changed(self, area):
        self.state.current_dock_area = area
        self.state.save()
        self.apply_architecture()

    def on_float_changed(self, is_floating):
        self.state.is_floating = is_floating
        self.state.save()
        self.apply_architecture()