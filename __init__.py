import krita
import sys
import importlib

# 1. Система Hot Reload: Перезагружаем модули, если они уже есть в памяти Криты
modules_to_reload = [
    'smart_brush_panel.core_state',
    'smart_brush_panel.ui_delegate',
    'smart_brush_panel.ui_grid',
    'smart_brush_panel.main_panel'
]

for mod in modules_to_reload:
    if mod in sys.modules:
        importlib.reload(sys.modules[mod])

# 2. Импортируем наш собранный докер из main_panel
from .main_panel import SmartPanelDocker

DOCKER_ID = 'smart_brush_panel_id'

class SmartPanelDockerFactory(krita.DockWidgetFactory):
    def __init__(self):
        # Регистрируем докер в Krita
        super().__init__(DOCKER_ID, krita.DockWidgetFactoryBase.DockRight, SmartPanelDocker)

# 3. Добавляем фабрику в ядро
app = krita.Krita.instance()
app.addDockWidgetFactory(SmartPanelDockerFactory())