from PyQt5.QtCore import QSettings, Qt

class PanelState:
    def __init__(self):
        self.settings = QSettings("BrushStudio", "CompactPalette")
        self.load()
        
        # Transient actuals (not saved to settings, calculated on the fly)
        self.actual_divider = 1
        self.actual_w = 32
        self.actual_h = 32

    def load(self):
        self.mode = self.settings.value("mode", "auto")
        self.manual_layout = self.settings.value("manual_layout", "vertical")
        
        # Base settings
        self.scale_factor = float(self.settings.value("scale_factor", 1.0))
        self.main_divider = int(self.settings.value("main_divider", 3))
        self.aspect_w = float(self.settings.value("aspect_w", 3.0))
        self.aspect_h = float(self.settings.value("aspect_h", 1.0))
        
        self.start_dir_vert = self.settings.value("start_dir_vert", "left")
        self.start_dir_horiz = self.settings.value("start_dir_horiz", "top")
        self.auto_invert = self.settings.value("auto_invert", False, type=bool)
        
        self.current_dock_area = Qt.RightDockWidgetArea
        self.is_floating = False

    def save(self):
        self.settings.setValue("mode", self.mode)
        self.settings.setValue("manual_layout", self.manual_layout)
        self.settings.setValue("scale_factor", self.scale_factor)
        self.settings.setValue("main_divider", self.main_divider)
        self.settings.setValue("aspect_w", self.aspect_w)
        self.settings.setValue("aspect_h", self.aspect_h)
        self.settings.setValue("start_dir_vert", self.start_dir_vert)
        self.settings.setValue("start_dir_horiz", self.start_dir_horiz)
        self.settings.setValue("auto_invert", self.auto_invert)

    def get_safe_ratio(self):
        w = max(0.1, self.aspect_w)
        h = max(0.1, self.aspect_h)
        return max(0.1, min(w / h, 10.0))

    def get_effective_layout(self, is_wide=False):
        if self.mode == "auto":
            if self.is_floating:
                return "horizontal" if is_wide else "vertical"
            elif self.current_dock_area in (Qt.TopDockWidgetArea, Qt.BottomDockWidgetArea):
                return "horizontal"
            else:
                return "vertical"
        return self.manual_layout

    def get_effective_direction(self, is_wide=False):
        layout = self.get_effective_layout(is_wide)
        if self.mode == "auto":
            if layout == "vertical":
                base_dir = "left" if self.current_dock_area == Qt.LeftDockWidgetArea else "right"
                return "right" if (self.auto_invert and base_dir == "left") else ("left" if self.auto_invert else base_dir)
            else:
                base_dir = "bottom" if self.current_dock_area == Qt.BottomDockWidgetArea else "top"
                return "bottom" if (self.auto_invert and base_dir == "top") else ("top" if self.auto_invert else base_dir)
        else:
            return self.start_dir_horiz if layout == "horizontal" else self.start_dir_vert