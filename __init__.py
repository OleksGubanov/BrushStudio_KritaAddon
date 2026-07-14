import krita
from .ui.main_panel import SmartPanelDocker

# Поддержка отладки: принудительно обновляем все подмодули при перезапуске плагина в Krita
import sys
from importlib import reload

modules_to_reload = [
    "smart_brush_panel.core.models",
    "smart_brush_panel.core.state",
    "smart_brush_panel.core.parser",
    "smart_brush_panel.services.preview.cache",
    "smart_brush_panel.services.preview.renderer",
    "smart_brush_panel.services.preview.queue",
    "smart_brush_panel.services.preview.service",
    "smart_brush_panel.ui.slot",
    "smart_brush_panel.ui.grid",
    "smart_brush_panel.ui.settings_popup",
    "smart_brush_panel.ui.main_panel"
]

for module_name in modules_to_reload:
    if module_name in sys.modules:
        reload(sys.modules[module_name])

class SmartPanelExtension(krita.Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        pass

# Регистрация панели в интерфейсе Krita
Instance = krita.Krita.instance()
dock_factory = krita.DockWidgetFactory(
    "smart_brush_panel", 
    krita.DockWidgetFactoryBase.DockRight, 
    SmartPanelDocker
)
Instance.addDockWidgetFactory(dock_factory)