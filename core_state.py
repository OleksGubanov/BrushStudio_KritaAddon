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

    def get_safe_ratio(self):
        w = max(0.1, self.aspect_w)
        h = max(0.1, self.aspect_h)
        return max(0.1, min(w / h, 10.0))

    def get_effective_layout(self):
        if self.mode == "auto":
            if self.is_floating:
                return self.manual_layout
            elif self.current_dock_area in (Qt.TopDockWidgetArea, Qt.BottomDockWidgetArea):
                return "horizontal"
            else:
                return "vertical"
        return self.manual_layout