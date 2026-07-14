import logging
import math

import krita
from PyQt5.QtCore import QEvent, QEventLoop, QPoint, QPointF, Qt
from PyQt5.QtGui import QMouseEvent, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget


LOGGER = logging.getLogger("brush_studio.preview")


class BaseBackend:
    def render(self, preset_name, metadata):
        raise NotImplementedError


class CanvasStrokeBackend(BaseBackend):
    """Experimental renderer that lets Krita's own freehand tool paint a preview.

    Krita's public Python API cannot directly feed a stroke to a brush engine.
    This backend therefore paints into a temporary document through the real
    canvas input path, reads the rendered projection, then restores the user's
    active view before closing the temporary document.
    """

    WIDTH = 384
    HEIGHT = 128
    BRUSH_SIZE = 72.0
    TOOL_ACTION = "KritaShape/KisToolBrush"

    def __init__(self):
        self.last_error = ""

    def render(self, preset_name, metadata):
        self.last_error = ""
        app = krita.Krita.instance()
        window = app.activeWindow()
        if window is None or window.activeView() is None:
            return self._fail("Open a document before running the canvas preview test.")

        preset = app.resources("preset").get(preset_name)
        if preset is None:
            return self._fail("The assigned brush preset is no longer available.")

        source_view = window.activeView()
        source_state = self._capture_view_state(source_view)
        preview_document = None

        try:
            preview_document = app.createDocument(
                self.WIDTH,
                self.HEIGHT,
                "Brush Studio Preview (temporary)",
                "RGBA",
                "U8",
                "",
                96.0,
            )
            preview_view = window.addView(preview_document)
            if preview_view is None:
                return self._fail("Krita could not create a temporary canvas view.")

            window.showView(preview_view)
            self._process_events()
            self._configure_preview_view(preview_view, preset)

            canvas_widget = self._find_canvas_widget(window.qwindow())
            if canvas_widget is None:
                return self._fail("Krita canvas widget was not found. No user document was changed.")

            self._paint_stroke(canvas_widget)
            preview_document.waitForDone()
            preview_document.refreshProjection()
            image = preview_document.projection()

            if image.isNull() or not self._has_visible_pixels(image):
                return self._fail("Krita accepted the test, but the temporary canvas stayed empty.")

            return QPixmap.fromImage(image)
        except Exception as error:
            LOGGER.exception("Canvas preview failed")
            return self._fail("Canvas preview failed: {}".format(error))
        finally:
            self._restore_source_view(window, source_view, source_state)
            if preview_document is not None:
                try:
                    preview_document.close()
                except Exception:
                    LOGGER.exception("Could not close the temporary preview document")

    def _configure_preview_view(self, view, preset):
        view.setCurrentBrushPreset(preset)
        view.setBrushSize(self.BRUSH_SIZE)
        view.setPaintingOpacity(1.0)
        view.setPaintingFlow(1.0)
        view.setEraserMode(False)
        view.setDisablePressure(True)

        canvas = view.canvas()
        canvas.setZoomLevel(1.0)
        canvas.resetRotation()
        canvas.setMirror(False)
        canvas.setWrapAroundMode(False)
        canvas.setPreferredCenter(QPointF(self.WIDTH / 2.0, self.HEIGHT / 2.0))
        self._activate_freehand_tool()
        self._process_events()

    def _activate_freehand_tool(self):
        action = krita.Krita.instance().action(self.TOOL_ACTION)
        if action is None:
            raise RuntimeError("Freehand Brush Tool action is unavailable")
        action.trigger()

    def _paint_stroke(self, widget):
        widget.setFocus(Qt.OtherFocusReason)
        center = widget.rect().center()
        half_length = max(48, min(150, widget.width() // 4))
        start = QPoint(center.x() - half_length, center.y())
        end = QPoint(center.x() + half_length, center.y())

        self._send_mouse_event(widget, QEvent.MouseButtonPress, start, Qt.LeftButton, Qt.LeftButton)
        for step in range(1, 25):
            progress = step / 24.0
            x = round(start.x() + (end.x() - start.x()) * progress)
            y = round(center.y() + 5 * math.sin(progress * math.tau))
            self._send_mouse_event(widget, QEvent.MouseMove, QPoint(x, y), Qt.NoButton, Qt.LeftButton)
            self._process_events()
        self._send_mouse_event(widget, QEvent.MouseButtonRelease, end, Qt.LeftButton, Qt.NoButton)
        self._process_events()

    @staticmethod
    def _send_mouse_event(widget, event_type, point, button, buttons):
        event = QMouseEvent(event_type, QPointF(point), button, buttons, Qt.NoModifier)
        QApplication.sendEvent(widget, event)

    @staticmethod
    def _process_events():
        QApplication.processEvents(QEventLoop.AllEvents, 50)

    @staticmethod
    def _find_canvas_widget(main_window):
        if main_window is None:
            return None

        candidates = []
        for widget in main_window.findChildren(QWidget):
            if not widget.isVisible() or widget.width() < 100 or widget.height() < 100:
                continue

            class_name = widget.metaObject().className().lower()
            object_name = widget.objectName().lower()
            if "canvas" not in class_name and "canvas" not in object_name:
                continue

            score = widget.width() * widget.height()
            if "kiscanvas2" in class_name:
                score += 10 ** 9
            elif "canvas" in class_name:
                score += 10 ** 8
            candidates.append((score, widget))

        return max(candidates, key=lambda item: item[0])[1] if candidates else None

    @staticmethod
    def _capture_view_state(view):
        state = {}
        getters = {
            "preset": "currentBrushPreset",
            "brush_size": "brushSize",
            "opacity": "paintingOpacity",
            "flow": "paintingFlow",
            "rotation": "brushRotation",
            "blend_mode": "currentBlendingMode",
            "eraser": "eraserMode",
            "disable_pressure": "disablePressure",
            "foreground": "foregroundColor",
            "background": "backgroundColor",
        }
        for key, getter_name in getters.items():
            try:
                state[key] = getattr(view, getter_name)()
            except Exception:
                LOGGER.debug("Could not capture %s", getter_name, exc_info=True)
        return state

    def _restore_source_view(self, window, view, state):
        try:
            window.showView(view)
            self._process_events()
        except Exception:
            LOGGER.exception("Could not restore the source view")
            return

        setters = {
            "preset": "setCurrentBrushPreset",
            "brush_size": "setBrushSize",
            "opacity": "setPaintingOpacity",
            "flow": "setPaintingFlow",
            "rotation": "setBrushRotation",
            "blend_mode": "setCurrentBlendingMode",
            "eraser": "setEraserMode",
            "disable_pressure": "setDisablePressure",
            "foreground": "setForeGroundColor",
            "background": "setBackGroundColor",
        }
        for key, setter_name in setters.items():
            if key not in state:
                continue
            try:
                getattr(view, setter_name)(state[key])
            except Exception:
                LOGGER.debug("Could not restore %s", setter_name, exc_info=True)
        self._process_events()

    def _fail(self, message):
        self.last_error = message
        LOGGER.warning(message)
        return None

    @staticmethod
    def _has_visible_pixels(image):
        for y in range(image.height()):
            for x in range(image.width()):
                if image.pixelColor(x, y).alpha() > 0:
                    return True
        return False


class PreviewRenderer:
    """Renderer facade.

    Canvas rendering is deliberately opt-in until it proves stable on Krita
    5.3.2.1. The old procedural curve is removed: an unavailable preview must
    remain unavailable rather than imitate every brush with the same picture.
    """

    def __init__(self, state):
        self.state = state
        self.canvas_backend = CanvasStrokeBackend()
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
