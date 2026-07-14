import json
from PyQt5.QtCore import QSettings, Qt

class PanelState:
    def __init__(self):
        self.settings = QSettings("BrushStudio", "SlotPalette")
        self.load()

    def load(self):
        self.mode = self.settings.value("mode", "auto")
        
        # Auto Mode Preferences (Cross-axis anchoring)
        self.auto_vert_docks = self.settings.value("auto_vert_docks", "Left")
        self.auto_horiz_docks = self.settings.value("auto_horiz_docks", "Top")
        
        # Manual Mode Preferences
        self.manual_layout = self.settings.value("manual_layout", "vertical")
        self.manual_anchor = self.settings.value("manual_anchor", "Left")
        self.manual_bar = self.settings.value("manual_bar", "Top")

        # Slot Generation
        self.total_slots = int(self.settings.value("total_slots", 20))
        self.main_divider = int(self.settings.value("main_divider", 3))
        
        # Absolute Sizing
        self.base_icon_size = int(self.settings.value("base_icon_size", 32))
        self.aspect_w = float(self.settings.value("aspect_w", 1.0))
        self.aspect_h = float(self.settings.value("aspect_h", 1.0))
        self.slot_padding = int(self.settings.value("slot_padding", 2))
        
        # Restore saved dock area state to prevent mismatch on first launch
        self.current_dock_area = Qt.DockWidgetArea(int(self.settings.value("current_dock_area", int(Qt.RightDockWidgetArea))))
        self.is_floating = self.settings.value("is_floating", "false") == "true"
        
        # Dictionary storing user assignments
        slots_json = self.settings.value("slot_data", "{}")
        try:
            self.slot_data = json.loads(slots_json)
        except:
            self.slot_data = {}

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
        self.settings.setValue("slot_data", json.dumps(self.slot_data))
        self.settings.setValue("current_dock_area", int(self.current_dock_area))
        self.settings.setValue("is_floating", self.is_floating)

    def get_effective_state(self, is_wide=False):
        """Returns tuple: (Layout Direction, Cross-Axis Anchor, Bar Position)"""
        if self.mode == "manual":
            return self.manual_layout, self.manual_anchor, self.manual_bar
            
        # AUTO MODE INTELLIGENCE
        if self.is_floating:
            if is_wide:
                return "horizontal", self.auto_horiz_docks, "Top"
            else:
                return "vertical", self.auto_vert_docks, "Left"
        
        if self.current_dock_area == Qt.TopDockWidgetArea:
            return "horizontal", self.auto_horiz_docks, "Top"
        elif self.current_dock_area == Qt.BottomDockWidgetArea:
            return "horizontal", self.auto_horiz_docks, "Bottom"
        elif self.current_dock_area == Qt.LeftDockWidgetArea:
            return "vertical", self.auto_vert_docks, "Left"
        else: # Right Dock
            return "vertical", self.auto_vert_docks, "Right"