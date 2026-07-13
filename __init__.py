import krita
from .smart_panel import SmartPanelDocker

DOCKER_ID = 'smart_brush_panel_id'

class SmartPanelDockerFactory(krita.DockWidgetFactory):
    def __init__(self):
        # DockRight - прикрепить справа по умолчанию
        super().__init__(DOCKER_ID, krita.DockWidgetFactoryBase.DockRight, SmartPanelDocker)

app = Krita.instance()
app.addDockWidgetFactory(SmartPanelDockerFactory())