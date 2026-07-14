import krita
from .ui.main_panel import SmartPanelDocker

# Поддержка автоматического обновления модулей при разработке
import sys
from importlib import reload
if "smart_brush_panel.core.state" in sys.modules:
    reload(sys.modules["smart_brush_panel.core.state"])
    reload(sys.modules["smart_brush_panel.core.parser"])
    reload(sys.modules["smart_brush_panel.services.preview"])
    reload(sys.modules["smart_brush_panel.ui.slot"])
    reload(sys.modules["smart_brush_panel.ui.grid"])
    reload(sys.modules["smart_brush_panel.ui.settings_popup"])
    reload(sys.modules["smart_brush_panel.ui.main_panel"])

class SmartPanelExtension(krita.Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        pass

# Регистрация панели в интерфейсе Krita
Instance = krita.Krita.instance()
dock_factory = krita.DockWidgetFactory("smart_brush_panel", krita.DockWidgetFactoryBase.DockRight, SmartPanelDocker)
Instance.addDockWidgetFactory(dock_factory)