import logging
import math
import time

import krita
from PyQt5.QtCore import QEvent, QEventLoop, QPoint, QPointF, Qt
from PyQt5.QtGui import QMouseEvent, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget

try:
    from PyQt5.QtTest import QTest
    HAS_QTEST = True
except ImportError:
    HAS_QTEST = False


LOGGER = logging.getLogger("brush_studio.preview")


class BaseBackend:
    def render(self, preset_name, metadata):
        raise NotImplementedError


class CppEngineBackend(BaseBackend):
    """C++ Native Renderer Backend.
    
    This backend requires the brush_studio_engine.pyd module compiled from src/.
    It uses Krita's internal C++ API (KisPainter) to generate perfect strokes
    without spawning temporary views or hijacking the user's mouse.
    """

    def __init__(self):
        self.last_error = ""

    def render(self, preset_name, metadata):
        self.last_error = ""
        
        try:
            import brush_studio_engine
        except ImportError:
            return self._fail(
                "C++ Engine is not compiled.\n"
                "Please compile src/preview_engine.cpp using CMake\n"
                "and place brush_studio_engine.pyd in the plugin folder."
            )
            
        try:
            width = 384
            height = 128
            image_bytes = brush_studio_engine.render_preview(preset_name, width, height)
            
            if not image_bytes:
                return self._fail("C++ Engine failed to render the preset.")
                
            # Load bytes into QImage
            image = QImage.fromData(image_bytes, "PNG")
            if image.isNull():
                return self._fail("C++ Engine returned invalid PNG data.")
                
            return QPixmap.fromImage(image)
            
        except Exception as error:
            LOGGER.exception("C++ Engine preview failed")
            return self._fail(f"C++ Engine preview failed: {error}")

    def _fail(self, message):
        self.last_error = message
        LOGGER.warning(message)
        return None


class PreviewRenderer:
    """Renderer facade.

    Canvas rendering is deliberately opt-in until it proves stable on Krita
    5.3.2.1. The old procedural curve is removed: an unavailable preview must
    remain unavailable rather than imitate every brush with the same picture.
    """

    def __init__(self, state):
        self.state = state
        self.canvas_backend = CppEngineBackend()
        self.last_error = ""

    def render_stroke(self, preset_name, metadata):
        # Automatic generation is intentionally disabled while the canvas path
        # is being verified. Only the explicit settings-menu probe may create a
        # temporary Krita document.
        return None

    @staticmethod
    def can_render_automatically():
        return False

    def render_canvas_probe(self, preset_name, metadata=None):
        pixmap = self.canvas_backend.render(preset_name, metadata or {})
        self.last_error = self.canvas_backend.last_error
        return pixmap
