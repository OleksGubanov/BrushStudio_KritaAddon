import krita
from .ui.main_panel import SmartPanelDocker

# Принудительно обновляем все подмодули при перезапуске плагина в Krita
import sys
from importlib import reload

modules_to_reload = [
    "brush_studio.core.models",
    "brush_studio.core.state",
    "brush_studio.core.parser",
    "brush_studio.services.preview.cache",
    "brush_studio.services.preview.renderer",
    "brush_studio.services.preview.queue",
    "brush_studio.services.preview.service",
    "brush_studio.ui.slot",
    "brush_studio.ui.grid",
    "brush_studio.ui.settings_popup",
    "brush_studio.ui.main_panel"
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
    "brush_studio", 
    krita.DockWidgetFactoryBase.DockRight, 
    SmartPanelDocker
)
Instance.addDockWidgetFactory(dock_factory)