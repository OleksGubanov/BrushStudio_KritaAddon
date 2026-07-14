# preview_service.py
import os
import krita
from PyQt5.QtCore import QObject, pyqtSignal, QStandardPaths
from PyQt5.QtGui import QPixmap, QPixmapCache

class BrushEngineParser:
    """Хак для чтения типа движка прямо из файла .kpp"""
    ENGINE_ICONS = {
        "pixelbrush": "🖌",
        "colorsmudge": "💧",
        "hairybrush": "🧹",
        "sketchbrush": "✏",
        "curvebrush": "〰",
        "tangentnormal": "🪨",
        "particlebrush": "✨",
        "hatchingbrush": "///"
    }

    @classmethod
    def get_engine_icon(cls, preset_name):
        res = krita.Krita.instance().resources("preset").get(preset_name)
        if not res:
            return "?"
        
        filepath = res.filename()
        try:
            with open(filepath, 'rb') as f:
                data = f.read(2048)  # Читаем начало файла, XML обычно там
                idx = data.find(b'paintop="')
                if idx != -1:
                    start = idx + 9
                    end = data.find(b'"', start)
                    engine_name = data[start:end].decode('utf-8')
                    return cls.ENGINE_ICONS.get(engine_name, "🖌")
        except Exception:
            return "🖌"
        return "🖌"


class PreviewService(QObject):
    # Сигнал сообщает ui_slot, что мазок готов к отрисовке
    previewReady = pyqtSignal(str, QPixmap)

    def __init__(self, state):
        super().__init__()
        self.state = state
        
        # Автоматически определяем системную папку кэша для плагина
        cache_base = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
        self.cache_dir = os.path.join(cache_base, "smart_brush_panel", "strokes")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def request_stroke(self, preset_name):
        """Входная точка для ячеек. Проверяет кэш и при необходимости создает мазок."""
        if not preset_name:
            return

        # 1. Ищем быстрый кэш в RAM (QPixmapCache)
        pixmap = QPixmapCache.find(preset_name)
        if pixmap and not pixmap.isNull():
            self.previewReady.emit(preset_name, pixmap)
            return

        # 2. Ищем долговременный кэш на диске
        disk_path = os.path.join(self.cache_dir, f"{preset_name}.png")
        if os.path.exists(disk_path):
            pixmap = QPixmap()
            if pixmap.load(disk_path):
                QPixmapCache.insert(preset_name, pixmap)
                self.previewReady.emit(preset_name, pixmap)
                return

        # 3. Если кэш пуст — отправляем на генерацию
        self.generate_stroke_preview(preset_name)

    def generate_stroke_preview(self, preset_name):
        """Метод генерации превью мазка кисти."""
        app = krita.Krita.instance()
        method = getattr(self.state, 'render_method', 'A')
        
        try:
            if method == 'A':
                # ПУТЬ А: Новый документ в фоне
                # ... Твой будущий код для генерации через фоновый документ
                pass
            
            elif method == 'B':
                # ПУТЬ Б: Временный слой в текущем документе
                doc = app.activeDocument()
                if doc:
                    # doc.setBatchmode(True) # Отключаем обновление UI
                    # ... Твой будущий код для работы с активным холстом
                    # doc.setBatchmode(False)
                    pass
            
            # ВАЖНО: Пока векторный рендер не дописан до конца (так как Krita Action 
            # перехватывает фокус), создаем заглушку для кэша, чтобы сервис работал.
            # Мы берем стандартную иконку пресета и сохраняем её как мазок.
            res = app.resources("preset").get(preset_name)
            if res:
                img = res.image()
                pix = QPixmap.fromImage(img)
                disk_path = os.path.join(self.cache_dir, f"{preset_name}.png")
                
                pix.save(disk_path, "PNG")
                QPixmapCache.insert(preset_name, pix)
                self.previewReady.emit(preset_name, pix)
                
        except Exception as e:
            print(f"Brush Studio Render Error: {e}")