import krita
import sys
import importlib

# 1. Hot Reload System: Reloads modules if they are already in memory
modules_to_reload = [
    'smart_brush_panel.core_state',
    'smart_brush_panel.ui_delegate',
    'smart_brush_panel.ui_grid',
    'smart_brush_panel.main_panel'
]

for mod in modules_to_reload:
    if mod in sys.modules:
        importlib.reload(sys.modules[mod])

# 2. Import the assembled docker from main_panel
from .main_panel import SmartPanelDocker

DOCKER_ID = 'smart_brush_panel_id'

class SmartPanelDockerFactory(krita.DockWidgetFactory):
    def __init__(self):
        # Register the docker in Krita
        super().__init__(DOCKER_ID, krita.DockWidgetFactoryBase.DockRight, SmartPanelDocker)

# 3. Add factory to the Krita instance
app = krita.Krita.instance()
app.addDockWidgetFactory(SmartPanelDockerFactory())