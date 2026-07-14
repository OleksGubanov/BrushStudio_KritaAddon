import json
from PyQt5.QtCore import QSettings

class PanelState:
    """Управление персистентным состоянием и конфигурацией плагина."""
    def __init__(self):
        self.settings = QSettings("Krita", "SmartBrushPanel")
        self.load()

    def load(self):
        self.mode = self.settings.value("mode", "auto")
        self.auto_vert_docks = self.settings.value("auto_vert_docks", "Left")
        self.auto_horiz_docks = self.settings.value("auto_horiz_docks", "Top")
        self.manual_layout = self.settings.value("manual_layout", "vertical")
        self.manual_anchor = self.settings.value("manual_anchor", "Left")
        self.manual_bar = self.settings.value("manual_bar", "Top")
        self.total_slots = int(self.settings.value("total_slots", 16))
        self.main_divider = int(self.settings.value("main_divider", 4))
        self.base_icon_size = int(self.settings.value("base_icon_size", 48))
        self.slot_padding = int(self.settings.value("slot_padding", 2))
        self.aspect_w = float(self.settings.value("aspect_w", 1.0))
        self.aspect_h = float(self.settings.value("aspect_h", 1.0))
        
        self.grid_corner = self.settings.value("grid_corner", "LT")
        self.render_method = self.settings.value("render_method", "A")
        self.show_engine = self.parse_bool(self.settings.value("show_engine", True))
        self.show_icon = self.parse_bool(self.settings.value("show_icon", True))
        self.show_stroke = self.parse_bool(self.settings.value("show_stroke", True))
        
        # Загрузка сохраненных данных слотов
        slots_json = self.settings.value("slot_data", "{}")
        try:
            self.slot_data = json.loads(slots_json)
        except Exception:
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
        self.settings.setValue("slot_padding", self.slot_padding)
        self.settings.setValue("aspect_w", self.aspect_w)
        self.settings.setValue("aspect_h", self.aspect_h)
        self.settings.setValue("grid_corner", self.grid_corner)
        self.settings.setValue("render_method", self.render_method)
        self.settings.setValue("show_engine", self.show_engine)
        self.settings.setValue("show_icon", self.show_icon)
        self.settings.setValue("show_stroke", self.show_stroke)
        self.settings.setValue("slot_data", json.dumps(self.slot_data))

    def parse_bool(self, val):
        if isinstance(val, bool): return val
        return str(val).lower() in ['true', '1', 'yes']

    def get_effective_state(self, is_wide):
        """Возвращает актуальный тип раскладки на основе геометрии окна."""
        if self.mode == "auto":
            eff_layout = "horizontal" if is_wide else "vertical"
            eff_anchor = self.auto_vert_docks if eff_layout == "vertical" else self.auto_horiz_docks
            eff_bar = "Top" if eff_layout == "vertical" else "Left"
            return eff_layout, eff_anchor, eff_bar
        else:
            return self.manual_layout, self.manual_anchor, self.manual_bar