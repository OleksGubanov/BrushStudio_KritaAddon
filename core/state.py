import json
from PyQt5.QtCore import QSettings

class AppearanceSettings:
    def __init__(self, settings):
        self.mode = settings.value("app_mode", "auto")
        self.base_icon_size = int(settings.value("base_icon_size", 48))
        self.slot_padding = int(settings.value("slot_padding", 2))

class GridSettings:
    def __init__(self, settings):
        self.total_slots = int(settings.value("total_slots", 16))
        self.main_divider = int(settings.value("main_divider", 4))
        self.aspect_w = float(settings.value("aspect_w", 1.0))
        self.aspect_h = float(settings.value("aspect_h", 1.0))
        self.flip_x = settings.value("grid_flip_x", False, type=bool)
        self.flip_y = settings.value("grid_flip_y", False, type=bool)

class PreviewSettings:
    def __init__(self, settings):
        self.render_method = settings.value("render_method", "fallback") # A, B или fallback
        self.cache_version = "v3"

class UISettings:
    def __init__(self, settings):
        self.show_engine = settings.value("show_engine", True, type=bool)
        self.show_icon = settings.value("show_icon", True, type=bool)
        self.show_stroke = settings.value("show_stroke", True, type=bool)

class PanelState:
    """Инкапсулирует логические группы настроек."""
    def __init__(self):
        self._settings = QSettings("Krita", "SmartBrushPanel")
        self.load()

    def load(self):
        self.appearance = AppearanceSettings(self._settings)
        self.grid = GridSettings(self._settings)
        self.preview = PreviewSettings(self._settings)
        self.ui = UISettings(self._settings)
        
        slots_json = self._settings.value("slot_data", "{}")
        try:
            self.slot_data = json.loads(slots_json)
        except Exception:
            self.slot_data = {}

    def save(self):
        # Сохранение делегируется обратно в self._settings (для краткости опущено)
        self._settings.setValue("slot_data", json.dumps(self.slot_data))