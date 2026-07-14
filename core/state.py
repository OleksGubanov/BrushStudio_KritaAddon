import json
from dataclasses import dataclass

from PyQt5.QtCore import QSettings, Qt


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


class LayoutSettings:
    def __init__(self, settings):
        self.auto_vertical_anchor = settings.value("auto_vertical_anchor", "Left")
        self.auto_horizontal_anchor = settings.value("auto_horizontal_anchor", "Top")
        self.manual_flow_axis = settings.value("manual_flow_axis", "vertical")
        self.manual_anchor = settings.value("manual_anchor", "Left")
        self.manual_bar_position = settings.value("manual_bar_position", "Top")


class PreviewSettings:
    def __init__(self, settings):
        self.render_method = settings.value("render_method", "disabled")
        self.cache_version = "v4"
        if self.render_method not in ("canvas", "disabled"):
            self.render_method = "disabled"


class UISettings:
    def __init__(self, settings):
        self.show_engine = settings.value("show_engine", True, type=bool)
        self.show_icon = settings.value("show_icon", True, type=bool)
        self.show_stroke = settings.value("show_stroke", True, type=bool)


@dataclass(frozen=True)
class LayoutSpec:
    """The single source of truth for docker geometry."""

    flow_axis: str
    anchor: str
    bar_position: str


class PanelState:
    """Persistent settings and layout policy for the brush panel."""

    SETTINGS_ORGANIZATION = "Krita"
    SETTINGS_APPLICATION = "SmartBrushPanel"
    LEGACY_ORGANIZATION = "BrushStudio"
    LEGACY_APPLICATION = "SlotPalette"
    SCHEMA_VERSION = 2

    def __init__(self):
        self._settings = QSettings(self.SETTINGS_ORGANIZATION, self.SETTINGS_APPLICATION)
        self._migrate_legacy_settings()
        self.load()

    def _migrate_legacy_settings(self):
        try:
            schema_version = int(self._settings.value("schema_version", 0))
        except (TypeError, ValueError):
            schema_version = 0
        if schema_version >= self.SCHEMA_VERSION:
            return

        legacy = QSettings(self.LEGACY_ORGANIZATION, self.LEGACY_APPLICATION)
        if not self._settings.contains("slot_data") and legacy.contains("slot_data"):
            key_mapping = {
                "mode": "app_mode",
                "total_slots": "total_slots",
                "main_divider": "main_divider",
                "base_icon_size": "base_icon_size",
                "aspect_w": "aspect_w",
                "aspect_h": "aspect_h",
                "slot_padding": "slot_padding",
                "slot_data": "slot_data",
                "auto_vert_docks": "auto_vertical_anchor",
                "auto_horiz_docks": "auto_horizontal_anchor",
                "manual_layout": "manual_flow_axis",
                "manual_anchor": "manual_anchor",
                "manual_bar": "manual_bar_position",
            }
            for legacy_key, current_key in key_mapping.items():
                if legacy.contains(legacy_key):
                    val = legacy.value(legacy_key)
                    if legacy_key == "slot_data" and not isinstance(val, str):
                        try:
                            val = json.dumps(val)
                        except Exception:
                            val = str(val)
                    self._settings.setValue(current_key, val)

        self._settings.setValue("schema_version", self.SCHEMA_VERSION)
        self._settings.sync()

    def load(self):
        self.appearance = AppearanceSettings(self._settings)
        self.grid = GridSettings(self._settings)
        self.layout = LayoutSettings(self._settings)
        self.preview = PreviewSettings(self._settings)
        self.ui = UISettings(self._settings)

        self.current_dock_area = int(self._settings.value("current_dock_area", int(Qt.RightDockWidgetArea)))
        self.is_floating = self._settings.value("is_floating", False, type=bool)

        slots_json = self._settings.value("slot_data", "{}")
        try:
            self.slot_data = json.loads(str(slots_json))
        except (TypeError, ValueError):
            self.slot_data = {}

    def save(self):
        self._settings.setValue("schema_version", self.SCHEMA_VERSION)
        self._settings.setValue("app_mode", self.appearance.mode)
        self._settings.setValue("base_icon_size", self.appearance.base_icon_size)
        self._settings.setValue("slot_padding", self.appearance.slot_padding)
        self._settings.setValue("total_slots", self.grid.total_slots)
        self._settings.setValue("main_divider", self.grid.main_divider)
        self._settings.setValue("aspect_w", self.grid.aspect_w)
        self._settings.setValue("aspect_h", self.grid.aspect_h)
        self._settings.setValue("grid_flip_x", self.grid.flip_x)
        self._settings.setValue("grid_flip_y", self.grid.flip_y)
        self._settings.setValue("auto_vertical_anchor", self.layout.auto_vertical_anchor)
        self._settings.setValue("auto_horizontal_anchor", self.layout.auto_horizontal_anchor)
        self._settings.setValue("manual_flow_axis", self.layout.manual_flow_axis)
        self._settings.setValue("manual_anchor", self.layout.manual_anchor)
        self._settings.setValue("manual_bar_position", self.layout.manual_bar_position)
        self._settings.setValue("render_method", self.preview.render_method)
        self._settings.setValue("show_engine", self.ui.show_engine)
        self._settings.setValue("show_icon", self.ui.show_icon)
        self._settings.setValue("show_stroke", self.ui.show_stroke)
        self._settings.setValue("slot_data", json.dumps(self.slot_data))
        self._settings.setValue("current_dock_area", int(self.current_dock_area))
        self._settings.setValue("is_floating", self.is_floating)
        self._settings.sync()

    def get_layout_spec(self, is_wide):
        if self.appearance.mode == "manual":
            return LayoutSpec(
                self.layout.manual_flow_axis,
                self.layout.manual_anchor,
                self.layout.manual_bar_position,
            )

        if self.is_floating:
            if is_wide:
                return LayoutSpec("horizontal", self.layout.auto_horizontal_anchor, "Top")
            return LayoutSpec("vertical", self.layout.auto_vertical_anchor, "Left")

        dock_area = self.current_dock_area
        if dock_area == Qt.TopDockWidgetArea:
            return LayoutSpec("horizontal", self.layout.auto_horizontal_anchor, "Top")
        if dock_area == Qt.BottomDockWidgetArea:
            return LayoutSpec("horizontal", self.layout.auto_horizontal_anchor, "Bottom")
        if dock_area == Qt.LeftDockWidgetArea:
            return LayoutSpec("vertical", self.layout.auto_vertical_anchor, "Left")
        return LayoutSpec("vertical", self.layout.auto_vertical_anchor, "Right")
