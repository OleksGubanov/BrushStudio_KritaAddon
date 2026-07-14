import os
import hashlib
import krita
from PyQt5.QtCore import QObject, pyqtSignal, QStandardPaths, Qt
from PyQt5.QtGui import QPixmap, QPixmapCache, QPainter, QPainterPath, QPen, QColor, QLinearGradient
from ..core.parser import BrushEngineParser

class PreviewService(QObject):
    """Управление асинхронной генерацией мазков кисти и многоуровневым кэшированием."""
    previewReady = pyqtSignal(str, QPixmap)

    def __init__(self, state):
        super().__init__()
        self.state = state
        
        cache_base = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
        self.cache_dir = os.path.join(cache_base, "smart_brush_panel", "strokes")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_safe_cache_path(self, preset_name):
        """Генерация безопасного хэш-имени файла во избежание сбоев ОС."""
        hashed = hashlib.md5(preset_name.encode('utf-8')).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed}.png")

    def request_stroke(self, preset_name):
        if not preset_name: return

        # 1. Быстрый кэш в оперативной памяти (RAM)
        pixmap = QPixmapCache.find(preset_name)
        if pixmap and not pixmap.isNull():
            self.previewReady.emit(preset_name, pixmap)
            return

        # 2. Постоянный кэш на жестком диске (Disk)
        disk_path = self._get_safe_cache_path(preset_name)
        if os.path.exists(disk_path):
            pixmap = QPixmap()
            if pixmap.load(disk_path):
                QPixmapCache.insert(preset_name, pixmap)
                self.previewReady.emit(preset_name, pixmap)
                return

        # 3. Генерация при отсутствии кэша
        self.generate_stroke_preview(preset_name)

    def generate_stroke_preview(self, preset_name):
        """ИСПРАВЛЕНО: Безопасный процедурный рендеринг мазка без деструкции холста Krita."""
        pix = QPixmap(150, 50)
        pix.fill(Qt.transparent)
        
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Считываем тип движка кисти, чтобы адаптировать форму линии
        engine_icon = BrushEngineParser.get_engine_icon(preset_name)
        
        # Элегантная S-образная кривая мазка
        path = QPainterPath()
        path.moveTo(15, 25)
        path.cubicTo(45, 5, 105, 45, 135, 25)
        
        pen = QPen()
        pen.setCapStyle(Qt.RoundCap)
        
        # Настройка градиента (имитация текстуры мазка)
        grad = QLinearGradient(15, 25, 135, 25)
        
        if engine_icon == "💧":  # Растушевка / Смазывание
            grad.setColorAt(0, QColor(0, 140, 255, 220))
            grad.setColorAt(0.6, QColor(0, 80, 200, 240))
            grad.setColorAt(1, QColor(0, 80, 200, 30))
            pen.setWidth(7)
            pen.setBrush(grad)
            painter.setPen(pen)
            painter.drawPath(path)
            
        elif engine_icon == "🧹":  # Щетина (Hairy) — рисуем несколько тонких волокон
            pen.setColor(QColor(140, 140, 140, 200))
            pen.setWidth(1)
            for offset in [-4, -2, 0, 2, 4]:
                p = QPainterPath()
                p.moveTo(15, 25 + offset)
                p.cubicTo(45, 5 + offset, 105, 45 + offset, 135, 25 + offset)
                painter.drawPath(p)
                
        elif engine_icon in ["✏", "///"]:  # Карандаш / Штриховка
            pen.setColor(QColor(110, 110, 110, 240))
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawPath(path)
            
        else:  # Стандартная круглая кисть (Pixel Brush)
            grad.setColorAt(0, QColor(90, 90, 90, 255))
            grad.setColorAt(0.8, QColor(50, 50, 50, 255))
            grad.setColorAt(1, QColor(50, 50, 50, 0))
            pen.setWidth(5)
            pen.setBrush(grad)
            painter.setPen(pen)
            painter.drawPath(path)
            
        painter.end()
        
        # Сохраняем в кэш
        disk_path = self._get_safe_cache_path(preset_name)
        pix.save(disk_path, "PNG")
        QPixmapCache.insert(preset_name, pix)
        self.previewReady.emit(preset_name, pix)