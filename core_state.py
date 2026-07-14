# core_state.py
import json
from PyQt5.QtCore import QSettings, Qt

class PanelState:
    def __init__(self):
        self.settings = QSettings("BrushStudio", "SlotPalette")
        self.load()

    def load(self):
        self.mode = self.settings.value("mode", "auto")
        
        self.auto_vert_docks = self.settings.value("auto_vert_docks", "Left")
        self.auto_horiz_docks = self.settings.value("auto_horiz_docks", "Top")
        self.auto_bar_vert = self.settings.value("auto_bar_vert", "Top")
        self.auto_bar_horiz = self.settings.value("auto_bar_horiz", "Left")
        
        self.manual_layout = self.settings.value("manual_layout", "vertical")
        self.manual_anchor = self.settings.value("manual_anchor", "Left")
        self.manual_bar = self.settings.value("manual_bar", "Top")
        
        # НОВАЯ НАСТРОЙКА УГЛА СЕТКИ (Left-Top по умолчанию)
        self.grid_corner = self.settings.value("grid_corner", "LT")
        
        # НОВЫЕ НАСТРОЙКИ ДЛЯ РЕНДЕРА И ДВИЖКА
        self.show_engine = self.settings.value("show_engine", True, type=bool)
        self.render_method = self.settings.value("render_method", "A")

        self.total_slots = int(self.settings.value("total_slots", 44))
        self.main_divider = int(self.settings.value("main_divider", 4))
        self.base_icon_size = int(self.settings.value("base_icon_size", 32))
        self.aspect_w = float(self.settings.value("aspect_w", 1.0))
        self.aspect_h = float(self.settings.value("aspect_h", 1.0))
        self.slot_padding = int(self.settings.value("slot_padding", 2))
        
        self.show_icon = self.settings.value("show_icon", True, type=bool)
        self.show_stroke = self.settings.value("show_stroke", True, type=bool)
        self.show_tip = self.settings.value("show_tip", False, type=bool)
        
        try:
            self.slot_data = json.loads(self.settings.value("slot_data", "{}"))
        except json.JSONDecodeError:
            self.slot_data = {}
            
        self.current_dock_area = self.settings.value("current_dock_area", int(Qt.RightDockWidgetArea))
        self.is_floating = self.settings.value("is_floating", False, type=bool)

    def save(self):
        self.settings.setValue("mode", self.mode)
        self.settings.setValue("auto_vert_docks", self.auto_vert_docks)
        self.settings.setValue("auto_horiz_docks", self.auto_horiz_docks)
        self.settings.setValue("auto_bar_vert", self.auto_bar_vert)
        self.settings.setValue("auto_bar_horiz", self.auto_bar_horiz)
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
        self.settings.setValue("slot_data", json.dumps(self.slot_data))
        self.settings.setValue("current_dock_area", int(self.current_dock_area))
        self.settings.setValue("is_floating", self.is_floating)
        self.settings.setValue("grid_corner", self.grid_corner)
        self.settings.setValue("show_engine", self.show_engine)
        self.settings.setValue("render_method", self.render_method)

    def get_effective_state(self, is_wide=False):
        if self.mode == "manual":
            return self.manual_layout, self.manual_anchor, self.manual_bar
            
        if self.is_floating:
            # Dynamically shifts based on window aspect ratio
            return ("horizontal", self.auto_horiz_docks, self.auto_bar_horiz) if is_wide else ("vertical", self.auto_vert_docks, self.auto_bar_vert)
        
        if self.current_dock_area == Qt.TopDockWidgetArea: return "horizontal", self.auto_horiz_docks, self.auto_bar_horiz
        elif self.current_dock_area == Qt.BottomDockWidgetArea: return "horizontal", self.auto_horiz_docks, self.auto_bar_horiz
        elif self.current_dock_area == Qt.LeftDockWidgetArea: return "vertical", self.auto_vert_docks, self.auto_bar_vert
        else: return "vertical", self.auto_vert_docks, self.auto_bar_vert