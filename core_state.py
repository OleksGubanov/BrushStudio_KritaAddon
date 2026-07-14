from PyQt5.QtCore import QSettings, Qt

class PanelState:
    def __init__(self):
        self.settings = QSettings("BrushStudio", "CompactPalette")
        self.load()

    def load(self):
        # We removed "Auto" mode completely. It's fully manual now.
        self.manual_layout = self.settings.value("manual_layout", "vertical")
        
        # Absolute Size Rules
        self.base_icon_size = int(self.settings.value("base_icon_size", 32))
        self.main_divider = int(self.settings.value("main_divider", 3))
        self.aspect_w = float(self.settings.value("aspect_w", 1.0))
        self.aspect_h = float(self.settings.value("aspect_h", 1.0))
        self.slot_padding = int(self.settings.value("slot_padding", 2))
        
        # Independent Placement Rules
        self.anchor_corner = self.settings.value("anchor_corner", "Top-Left")
        self.bar_position = self.settings.value("bar_position", "Top")

    def save(self):
        self.settings.setValue("manual_layout", self.manual_layout)
        self.settings.setValue("base_icon_size", self.base_icon_size)
        self.settings.setValue("main_divider", self.main_divider)
        self.settings.setValue("aspect_w", self.aspect_w)
        self.settings.setValue("aspect_h", self.aspect_h)
        self.settings.setValue("slot_padding", self.slot_padding)
        self.settings.setValue("anchor_corner", self.anchor_corner)
        self.settings.setValue("bar_position", self.bar_position)

    def get_safe_ratio(self):
        w = max(0.1, self.aspect_w)
        h = max(0.1, self.aspect_h)
        return max(0.1, min(w / h, 10.0))