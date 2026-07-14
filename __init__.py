# __init__.py
import krita
import sys
import importlib

modules_to_reload = [
    'smart_brush_panel.core_state',
    'smart_brush_panel.ui_slot',   
    'smart_brush_panel.ui_grid',
    'smart_brush_panel.preview_service',
    'smart_brush_panel.main_panel'       # main_panel всегда идет последним
]

for mod in modules_to_reload:
    if mod in sys.modules:
        importlib.reload(sys.modules[mod])

from .main_panel import SmartPanelDocker

DOCKER_ID = 'smart_brush_panel_id'

class SmartPanelDockerFactory(krita.DockWidgetFactory):
    def __init__(self):
        super().__init__(DOCKER_ID, krita.DockWidgetFactoryBase.DockRight, SmartPanelDocker)

app = krita.Krita.instance()
app.addDockWidgetFactory(SmartPanelDockerFactory())