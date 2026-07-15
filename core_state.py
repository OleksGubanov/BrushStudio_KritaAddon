import json
from PyQt5.QtCore import QSettings

class PanelState:
    def __init__(self):
        self.settings = QSettings("BrushStudio", "SlotPalette")
        self.load()

    def load(self):
        self.mode = self.settings.value("mode", "auto")
        self.auto_vert_docks = self.settings.value("auto_vert_docks", "Left")
        self.auto_horiz_docks = self.settings.value("auto_horiz_docks", "Top")
        self.manual_layout = self.settings.value("manual_layout", "vertical")
        self.manual_anchor = self.settings.value("manual_anchor", "Left")
        self.manual_bar = self.settings.value("manual_bar", "Top")
        self.total_slots = int(self.settings.value("total_slots", 20))
        self.main_divider = int(self.settings.value("main_divider", 3))
        self.base_icon_size = int(self.settings.value("base_icon_size", 32))
        self.aspect_w = float(self.settings.value("aspect_w", 1.0)) or 1.0
        self.aspect_h = float(self.settings.value("aspect_h", 1.0)) or 1.0
        self.slot_padding = int(self.settings.value("slot_padding", 2))
        
        self.show_icon = self.settings.value("show_icon", True, type=bool)
        self.show_stroke = self.settings.value("show_stroke", True, type=bool)
        self.show_tip = self.settings.value("show_tip", True, type=bool)
        self.show_engine = self.settings.value("show_engine", True, type=bool)
        self.recolor_preview = self.settings.value("recolor_preview", False, type=bool)
        
        self.preview_render_w = int(self.settings.value("preview_render_w", 256))
        self.preview_render_h = int(self.settings.value("preview_render_h", 64))
        self.tip_render_size = int(self.settings.value("tip_render_size", 64))
        self.brush_scale_coef = float(self.settings.value("brush_scale_coef", 0.4))
        
        self.canvas_modifier = float(self.settings.value("canvas_modifier", 2.0))
        self.max_iterations = int(self.settings.value("max_iterations", 5))
        self.safe_zone_padding = int(self.settings.value("safe_zone_padding", 50))
        
        raw_data = self.settings.value("slot_data", "{}")
        try:
            self.slot_data = json.loads(raw_data)
        except Exception:
            self.slot_data = {}
            
        self.current_dock_area = self.settings.value("current_dock_area", 1)
        self.is_floating = self.settings.value("is_floating", False, type=bool)

    def save(self):
        self.settings.setValue("mode", self.mode)
        self.settings.setValue("auto_vert_docks", self.auto_vert_docks)
        self.settings.setValue("auto_horiz_docks", self.auto_horiz_docks)
        self.settings.setValue("manual_layout", self.manual_layout)
        self.settings.setValue("manual_anchor", self.manual_anchor)
        self.settings.setValue("manual_bar", self.manual_bar)
        self.settings.setValue("total_slots", self.total_slots)
        self.settings.setValue("main_divider", self.main_divider)
        self.settings.setValue("base_icon_size", self.base_icon_size)
        self.settings.setValue("aspect_w", self.aspect_w)
        self.settings.setValue("aspect_h", self.aspect_h)
        self.settings.setValue("slot_padding", self.slot_padding)
        
        self.settings.setValue("show_icon", self.show_icon)
        self.settings.setValue("show_stroke", self.show_stroke)
        self.settings.setValue("show_tip", self.show_tip)
        self.settings.setValue("show_engine", self.show_engine)
        self.settings.setValue("recolor_preview", self.recolor_preview)
        
        self.settings.setValue("preview_render_w", self.preview_render_w)
        self.settings.setValue("preview_render_h", self.preview_render_h)
        self.settings.setValue("tip_render_size", self.tip_render_size)
        self.settings.setValue("brush_scale_coef", self.brush_scale_coef)
        
        self.settings.setValue("canvas_modifier", self.canvas_modifier)
        self.settings.setValue("max_iterations", self.max_iterations)
        self.settings.setValue("safe_zone_padding", self.safe_zone_padding)
        
        self.settings.setValue("slot_data", json.dumps(self.slot_data))
        self.settings.setValue("current_dock_area", int(self.current_dock_area))
        self.settings.setValue("is_floating", self.is_floating)

    def get_effective_state(self, is_wide):
        if self.mode == "auto":
            layout = "horizontal" if is_wide else "vertical"
            anchor = self.auto_vert_docks if is_wide else self.auto_horiz_docks
            bar = "Top"
        else:
            layout = self.manual_layout
            anchor = self.manual_anchor
            bar = self.manual_bar
        return layout, anchor, bar