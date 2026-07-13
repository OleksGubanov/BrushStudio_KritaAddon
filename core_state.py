from PyQt5.QtCore import QSettings, Qt

class PanelState:
    def __init__(self):
        self.settings = QSettings("BrushStudio", "CompactPalette")
        self.load()

    def load(self):
        self.mode = self.settings.value("mode", "auto")
        self.manual_layout = self.settings.value("manual_layout", "vertical")
        self.main_divider = int(self.settings.value("main_divider", 3))
        self.aspect_w = float(self.settings.value("aspect_w", 3.0))
        self.aspect_h = float(self.settings.value("aspect_h", 1.0))
        self.start_dir_vert = self.settings.value("start_dir_vert", "left")
        self.start_dir_horiz = self.settings.value("start_dir_horiz", "top")
        
        # Boolean for Auto Mode inversion
        self.auto_invert = self.settings.value("auto_invert", False, type=bool)
        
        self.current_dock_area = Qt.RightDockWidgetArea
        self.is_floating = False

    def save(self):
        self.settings.setValue("mode", self.mode)
        self.settings.setValue("manual_layout", self.manual_layout)
        self.settings.setValue("main_divider", self.main_divider)
        self.settings.setValue("aspect_w", self.aspect_w)
        self.settings.setValue("aspect_h", self.aspect_h)
        self.settings.setValue("start_dir_vert", self.start_dir_vert)
        self.settings.setValue("start_dir_horiz", self.start_dir_horiz)
        self.settings.setValue("auto_invert", self.auto_invert)

    def get_safe_ratio(self):
        """Returns the aspect ratio with a safety clamp to prevent render crashes."""
        w = max(0.1, self.aspect_w)
        h = max(0.1, self.aspect_h)
        return max(0.1, min(w / h, 10.0))

    def get_effective_layout(self, is_wide=False):
        """Determines layout based on dock area or window aspect ratio if floating."""
        if self.mode == "auto":
            if self.is_floating:
                return "horizontal" if is_wide else "vertical"
            elif self.current_dock_area in (Qt.TopDockWidgetArea, Qt.BottomDockWidgetArea):
                return "horizontal"
            else:
                return "vertical"
        return self.manual_layout

    def get_effective_direction(self, is_wide=False):
        """Calculates natural start direction based on Krita dock location or user inversion."""
        layout = self.get_effective_layout(is_wide)
        
        if self.mode == "auto":
            if layout == "vertical":
                # Natural start for left dock is left, right is right
                base_dir = "left" if self.current_dock_area == Qt.LeftDockWidgetArea else "right"
                if self.auto_invert:
                    return "right" if base_dir == "left" else "left"
                return base_dir
            else:
                # Natural start for top dock is top, bottom is bottom
                base_dir = "bottom" if self.current_dock_area == Qt.BottomDockWidgetArea else "top"
                if self.auto_invert:
                    return "bottom" if base_dir == "top" else "top"
                return base_dir
        else:
            return self.start_dir_horiz if layout == "horizontal" else self.start_dir_vert