import krita
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QPen, QColor, QLinearGradient
from PyQt5.QtCore import Qt

class BaseBackend:
    def render(self, preset_name, metadata):
        raise NotImplementedError

class HiddenDocumentBackend(BaseBackend):
    """Backend A: Рендеринг в невидимом документе Krita."""
    def render(self, preset_name, metadata):
        # Архитектурная заглушка для Krita API
        # В Krita Python API пока нет прямого метода "нарисовать мазок кистью по координатам" 
        # без хаков с DBus, но архитектурно это место для вызова:
        # doc = Krita.instance().createDocument(150, 50, "Temp", "RGBA", "U8", "", 120.0)
        # ... применение пресета к временному слою ...
        return None # Возвращаем None, чтобы сработал Fallback (до полной реализации API)

class ActiveDocumentBackend(BaseBackend):
    """Backend B: Рендеринг на временном слое активного документа."""
    def render(self, preset_name, metadata):
        app = krita.Krita.instance()
        doc = app.activeDocument()
        if not doc: return None
        # ... логика инъекции временного векторного слоя и stroke path ...
        return None

class FallbackBackend(BaseBackend):
    """Процедурная заглушка, если нативные движки Krita недоступны."""
    def render(self, preset_name, metadata):
        pix = QPixmap(150, 50)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        path.moveTo(15, 25)
        path.cubicTo(45, 5, 105, 45, 135, 25)
        
        pen = QPen(QColor(90, 90, 90, 255), 5)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.end()
        return pix

class PreviewRenderer:
    def __init__(self, state):
        self.state = state
        self.backends = {
            "A": HiddenDocumentBackend(),
            "B": ActiveDocumentBackend(),
            "fallback": FallbackBackend()
        }

    def render_stroke(self, preset_name, metadata):
        method = self.state.preview.render_method
        pixmap = None
        
        if method in self.backends:
            pixmap = self.backends[method].render(preset_name, metadata)
            
        if not pixmap or pixmap.isNull():
            pixmap = self.backends["fallback"].render(preset_name, metadata)
            
        return pixmap