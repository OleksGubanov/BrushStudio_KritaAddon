import sys
import importlib
import krita

# 1. СИСТЕМА ГОРЯЧЕЙ ПЕРЕЗАГРУЗКИ (Hot Reload)
# Порядок критически важен! Зависимые модули перезагружаются после базовых.
modules_to_reload = [
    'smart_brush_panel.core_state',      # Хранение настроек (независимый)
    'smart_brush_panel.preview_service', # Новый фоновый сервис рендера мазков
    'smart_brush_panel.ui_slot',         # Слот (зависит от настроек и сервиса)
    'smart_brush_panel.ui_grid',         # Сетка (управляет слотами)
    'smart_brush_panel.main_panel'       # Главный докер (собирает всё воедино)
]

for mod in modules_to_reload:
    if mod in sys.modules:
        try:
            importlib.reload(sys.modules[mod])
        except Exception as e:
            print(f"[Brush Studio] Ошибка горячей перезагрузки модуля {mod}: {e}")

# 2. ИМПОРТ И РЕГИСТРАЦИЯ ДОКЕРА В KRITA
# Импортируем докер только ПОСЛЕ того, как сработал Hot Reload для всех модулей
from .main_panel import SmartPanelDocker

DOCKER_ID = 'smart_brush_panel_id'

class SmartPanelDockerFactory(krita.DockWidgetFactory):
    def __init__(self):
        super().__init__(
            DOCKER_ID, 
            krita.DockWidgetFactoryBase.DockRight, 
            SmartPanelDocker
        )

# Регистрируем фабрику панели в запущенном инстансе Krita
app = krita.Krita.instance()
app.addDockWidgetFactory(SmartPanelDockerFactory())