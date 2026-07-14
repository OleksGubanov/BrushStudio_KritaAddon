from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from .queue import GenerationQueue

class PreviewService(QObject):
    """Координатор асинхронного рендеринга и кэширования."""
    previewReady = pyqtSignal(str, object)  # (preset_name, QPixmap)

    def __init__(self, cache, renderer):
        super().__init__()
        self.cache = cache
        self.renderer = renderer
        self.queue = GenerationQueue()
        
        # Таймер для разгрузки UI-потока (1 задача в 15 мс)
        self._timer = QTimer(self)
        self._timer.setInterval(15)
        self._timer.timeout.connect(self._process_next)

    def request_stroke(self, preset_name, metadata, high_priority=False):
        if not preset_name:
            return
        if not self.renderer.can_render_automatically():
            return

        # 1. Быстрая проверка кэша (мгновенно возвращаем, если есть)
        pixmap = self.cache.get(preset_name, metadata.get("mtime", 0))
        if pixmap and not pixmap.isNull():
            self.previewReady.emit(preset_name, pixmap)
            return

        # 2. Если в кэше нет, ставим задачу в очередь
        self.queue.push(preset_name, metadata, high_priority)
        
        # Запускаем обработку, если таймер спал
        if not self._timer.isActive():
            self._timer.start()

    def cancel_all(self):
        """Отмена генерации (например, при смене рабочей области)."""
        self.queue.clear()
        self._timer.stop()

    def _process_next(self):
        task = self.queue.pop()
        if not task:
            self._timer.stop()
            return

        preset_name, metadata = task
        pixmap = self.renderer.render_stroke(preset_name, metadata)
        
        if pixmap and not pixmap.isNull():
            self.cache.put(preset_name, metadata.get("mtime", 0), pixmap)
            self.previewReady.emit(preset_name, pixmap)
