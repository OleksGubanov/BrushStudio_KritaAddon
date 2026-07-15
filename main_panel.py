import krita
from PyQt5.QtWidgets import (QDockWidget, QWidget, QBoxLayout, QHBoxLayout, 
                             QPushButton, QComboBox, QLabel, QSpinBox, QDoubleSpinBox,
                             QMenu, QAction, QWidgetAction, QFormLayout, QApplication, QCheckBox, QFrame)
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
        
        self.bar_layout.addWidget(self.btn_settings)
        self.bar_layout.addStretch()
        
        self.top_bar.setLayout(self.bar_layout)
        self.main_layout.addWidget(self.top_bar)
        
        self.grid_widget = AdaptiveGridWidget(self.state)
        self.scroll_area = SlotScrollArea(self.grid_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.main_layout.addWidget(self.scroll_area)
        
        self.main_widget.setLayout(self.main_layout)
        self.setWidget(self.main_widget)
        self.topLevelChanged.connect(self.on_top_level_changed)
        
        self.rebuild_slots()
        self.apply_architecture()

    def show_popup_settings(self):
        menu = QMenu(self)
        menu.setMinimumWidth(300)
        
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.cmb_mode = QComboBox(); self.cmb_mode.addItems(["auto", "manual"]); self.cmb_mode.setCurrentText(self.state.mode)
        self.cmb_auto_vert = QComboBox(); self.cmb_auto_vert.addItems(["Left", "Right", "Top", "Bottom"]); self.cmb_auto_vert.setCurrentText(self.state.auto_vert_docks)
        self.cmb_auto_horiz = QComboBox(); self.cmb_auto_horiz.addItems(["Left", "Right", "Top", "Bottom"]); self.cmb_auto_horiz.setCurrentText(self.state.auto_horiz_docks)
        
        self.cmb_layout = QComboBox(); self.cmb_layout.addItems(["vertical", "horizontal"]); self.cmb_layout.setCurrentText(self.state.manual_layout)
        self.cmb_anchor = QComboBox(); self.cmb_anchor.addItems(["Left", "Right", "Top", "Bottom"]); self.cmb_anchor.setCurrentText(self.state.manual_anchor)
        self.cmb_bar = QComboBox(); self.cmb_bar.addItems(["Top", "Bottom", "Left", "Right", "Hidden"]); self.cmb_bar.setCurrentText(self.state.manual_bar)
        
        self.spin_slots = QSpinBox(); self.spin_slots.setRange(1, 100); self.spin_slots.setValue(self.state.total_slots)
        self.spin_divider = QSpinBox(); self.spin_divider.setRange(1, 20); self.spin_divider.setValue(self.state.main_divider)
        self.spin_base = QSpinBox(); self.spin_base.setRange(16, 128); self.spin_base.setValue(self.state.base_icon_size)
        
        self.spin_asp_w = QDoubleSpinBox(); self.spin_asp_w.setRange(0.1, 5.0); self.spin_asp_w.setSingleStep(0.1); self.spin_asp_w.setValue(self.state.aspect_w)
        self.spin_asp_h = QDoubleSpinBox(); self.spin_asp_h.setRange(0.1, 5.0); self.spin_asp_h.setSingleStep(0.1); self.spin_asp_h.setValue(self.state.aspect_h)
        
        self.chk_icon = QCheckBox("Show Icon"); self.chk_icon.setChecked(self.state.show_icon)
        self.chk_stroke = QCheckBox("Show Stroke"); self.chk_stroke.setChecked(self.state.show_stroke)
        self.chk_tip = QCheckBox("Show Tip"); self.chk_tip.setChecked(self.state.show_tip)
        self.chk_engine = QCheckBox("Show Engine Emoji"); self.chk_engine.setChecked(self.state.show_engine)
        self.chk_recolor = QCheckBox("Recolor to UI"); self.chk_recolor.setChecked(self.state.recolor_preview)
        
        self.spin_prev_w = QSpinBox(); self.spin_prev_w.setRange(64, 1024); self.spin_prev_w.setValue(self.state.preview_render_w)
        self.spin_prev_h = QSpinBox(); self.spin_prev_h.setRange(16, 512); self.spin_prev_h.setValue(self.state.preview_render_h)
        self.spin_tip_size = QSpinBox(); self.spin_tip_size.setRange(16, 512); self.spin_tip_size.setValue(self.state.tip_render_size)
        
        self.spin_canvas_mod = QDoubleSpinBox(); self.spin_canvas_mod.setRange(1.1, 10.0); self.spin_canvas_mod.setSingleStep(0.1); self.spin_canvas_mod.setValue(self.state.canvas_modifier)
        self.spin_max_iter = QSpinBox(); self.spin_max_iter.setRange(1, 20); self.spin_max_iter.setValue(self.state.max_iterations)
        self.spin_safe_pad = QSpinBox(); self.spin_safe_pad.setRange(0, 500); self.spin_safe_pad.setValue(self.state.safe_zone_padding)
        
        layout.addRow("Mode:", self.cmb_mode)
        self.lbl_auto_v = QLabel("Wide Panel Anchor:"); layout.addRow(self.lbl_auto_v, self.cmb_auto_vert)
        self.lbl_auto_h = QLabel("Tall Panel Anchor:"); layout.addRow(self.lbl_auto_h, self.cmb_auto_horiz)
        self.lbl_man_l = QLabel("Layout:"); layout.addRow(self.lbl_man_l, self.cmb_layout)
        self.lbl_man_a = QLabel("Anchor:"); layout.addRow(self.lbl_man_a, self.cmb_anchor)
        self.lbl_man_b = QLabel("Bar Pos:"); layout.addRow(self.lbl_man_b, self.cmb_bar)
        
        layout.addRow("Total Slots:", self.spin_slots)
        layout.addRow("Grid Divider:", self.spin_divider)
        layout.addRow("Base Size:", self.spin_base)
        
        asp_layout = QHBoxLayout()
        asp_layout.addWidget(self.spin_asp_w); asp_layout.addWidget(QLabel(":")); asp_layout.addWidget(self.spin_asp_h)
        layout.addRow("Aspect Ratio (W:H):", asp_layout)
        
        layout.addRow(self.chk_icon)
        layout.addRow(self.chk_stroke)
        layout.addRow(self.chk_tip)
        layout.addRow(self.chk_engine)
        layout.addRow(self.chk_recolor)
        
        layout.addRow("Render Width:", self.spin_prev_w)
        layout.addRow("Render Height:", self.spin_prev_h)
        layout.addRow("Tip Render Size:", self.spin_tip_size)
        
        layout.addRow("Canvas Modifier:", self.spin_canvas_mod)
        layout.addRow("Max Iterations:", self.spin_max_iter)
        layout.addRow("Safe Zone Padding:", self.spin_safe_pad)
        
        btn_apply = QPushButton("Apply")
        btn_apply.clicked.connect(lambda: self.save_settings(menu))
        layout.addRow(btn_apply)
        
        self.cmb_mode.currentTextChanged.connect(self.update_settings_visibility)
        self.update_settings_visibility()
        
        wa = QWidgetAction(menu)
        wa.setDefaultWidget(widget)
        menu.addAction(wa)
        
        global_pos = self.btn_settings.mapToGlobal(QPoint(0, self.btn_settings.height()))
        menu.exec_(global_pos)

    def update_settings_visibility(self):
        is_auto = (self.cmb_mode.currentText() == "auto")
        self.lbl_auto_v.setVisible(is_auto); self.cmb_auto_vert.setVisible(is_auto)
        self.lbl_auto_h.setVisible(is_auto); self.cmb_auto_horiz.setVisible(is_auto)
        self.lbl_man_l.setVisible(not is_auto); self.cmb_layout.setVisible(not is_auto)
        self.lbl_man_a.setVisible(not is_auto); self.cmb_anchor.setVisible(not is_auto)
        self.lbl_man_b.setVisible(not is_auto); self.cmb_bar.setVisible(not is_auto)

    def save_settings(self, menu):
        old_slots = self.state.total_slots
        
        self.state.mode = self.cmb_mode.currentText()
        self.state.auto_vert_docks = self.cmb_auto_vert.currentText()
        self.state.auto_horiz_docks = self.cmb_auto_horiz.currentText()
        self.state.manual_layout = self.cmb_layout.currentText()
        self.state.manual_anchor = self.cmb_anchor.currentText()
        self.state.manual_bar = self.cmb_bar.currentText()
        self.state.total_slots = self.spin_slots.value()
        self.state.main_divider = self.spin_divider.value()
        self.state.base_icon_size = self.spin_base.value()
        self.state.aspect_w, self.state.aspect_h = float(self.spin_asp_w.value()), float(self.spin_asp_h.value())
        
        self.state.show_icon = self.chk_icon.isChecked()
        self.state.show_stroke = self.chk_stroke.isChecked()
        self.state.show_tip = self.chk_tip.isChecked()
        self.state.show_engine = self.chk_engine.isChecked()
        self.state.recolor_preview = self.chk_recolor.isChecked()
        
        self.state.preview_render_w = self.spin_prev_w.value()
        self.state.preview_render_h = self.spin_prev_h.value()
        self.state.tip_render_size = self.spin_tip_size.value()
        
        self.state.canvas_modifier = self.spin_canvas_mod.value()
        self.state.max_iterations = self.spin_max_iter.value()
        self.state.safe_zone_padding = self.spin_safe_pad.value()
        
        self.update_settings_visibility()
        self.state.save()
        
        if old_slots != self.state.total_slots:
            self.rebuild_slots()
            
        self.apply_architecture()
        for slot in self.grid_widget.slots:
            slot.update()
            
        menu.close()

    def rebuild_slots(self):
        slots = []
        for i in range(self.state.total_slots):
            slot = BrushSlot(i, self.state)
            slot.clicked.connect(self.on_slot_clicked)
            slot.clear_requested.connect(self.on_slot_clear)
            slots.append(slot)
        self.grid_widget.set_slots(slots)

    def on_slot_clicked(self, index, stored_brush_name):
        app = krita.Krita.instance()
        window = app.activeWindow()
        if not window: return
        view = window.activeView()
        if not view: return
        
        if not stored_brush_name:
            current_preset = app.currentBrushPreset()
            if current_preset:
                self.grid_widget.slots[index].set_brush(current_preset.name())
        else:
            preset = app.resources("preset").get(stored_brush_name)
            if preset:
                view.setCurrentBrushPreset(preset)
        for slot in self.grid_widget.slots:
            slot.update()

    def on_slot_clear(self, index):
        self.grid_widget.slots[index].set_brush("")

    def on_top_level_changed(self, is_floating):
        self.state.is_floating = is_floating
        self.state.save()
        self.apply_architecture()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_architecture()

    def apply_architecture(self):
        w, h = self.width(), self.height()
        is_wide = w > h
        eff_layout, eff_anchor, eff_bar = self.state.get_effective_state(is_wide)
        
        if eff_bar == "Hidden":
            self.top_bar.hide()
        else:
            self.top_bar.show()
            self.main_layout.removeWidget(self.top_bar)
            self.main_layout.removeWidget(self.scroll_area)
            
            self.bar_layout.setDirection(QBoxLayout.LeftToRight)
            if eff_bar in ("Left", "Right"):
                self.main_layout.setDirection(QBoxLayout.LeftToRight if eff_bar == "Left" else QBoxLayout.RightToLeft)
                self.bar_layout.setDirection(QBoxLayout.TopToBottom)
            else:
                self.main_layout.setDirection(QBoxLayout.TopToBottom if eff_bar == "Top" else QBoxLayout.BottomToTop)
                
            self.main_layout.addWidget(self.top_bar)
            self.main_layout.addWidget(self.scroll_area)
            
        self.grid_widget.update_architecture(eff_layout)