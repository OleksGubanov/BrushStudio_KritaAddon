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
            for _ in range(5):
                self._process_events()
                time.sleep(0.05)
                
            self._configure_preview_view(preview_view, preset)

            canvas_widget = self._find_canvas_widget(window.qwindow())
            if canvas_widget is None:
                return self._fail("Krita canvas widget was not found. No user document was changed.")

            self._paint_stroke(canvas_widget)
            preview_document.waitForDone()
            preview_document.refreshProjection()
            image = preview_document.projection()

            if image.isNull() or not self._has_visible_pixels(image):
                focus_cls = QApplication.focusWidget().metaObject().className() if QApplication.focusWidget() else "None"
                target_cls = canvas_widget.property("brush_studio_target_class") or "Unknown"
                msg = (
                    f"Empty canvas.\n"
                    f"Found: {canvas_widget.metaObject().className()} ({canvas_widget.width()}x{canvas_widget.height()})\n"
                    f"Target: {target_cls}\n"
                    f"Focus: {focus_cls}"
                )
                return self._fail(msg)

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
        self._wait_for_events(100)  # Wait for Krita to fully load the preset
        
        view.setBrushSize(self.BRUSH_SIZE)
        view.setPaintingOpacity(1.0)
        view.setPaintingFlow(1.0)
        view.setEraserMode(False)
        view.setDisablePressure(True)
        
        try:
            color = krita.ManagedColor("RGBA", "U8", "")
            color.setComponents([0.0, 0.0, 0.0, 1.0])
            view.setForeGroundColor(color)
        except Exception:
            pass

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

        target_widget = widget.childAt(center)
        if target_widget is None:
            target_widget = widget

        half_length = max(48, min(150, widget.width() // 4))
        start = QPoint(center.x() - half_length, center.y())
        end = QPoint(center.x() + half_length, center.y())
        
        start_mapped = target_widget.mapFrom(widget, start)
        end_mapped = target_widget.mapFrom(widget, end)
        center_mapped = target_widget.mapFrom(widget, center)

        if HAS_QTEST:
            self._paint_stroke_qtest(target_widget, start_mapped, end_mapped, center_mapped)
        else:
            import sys
            if sys.platform == 'win32':
                self._paint_stroke_windows_hardware(widget, start, end, center)
            else:
                self._paint_stroke_qt(target_widget, start_mapped, end_mapped, center_mapped)
                
        widget.setProperty("brush_studio_target_class", target_widget.metaObject().className())

    def _paint_stroke_qtest(self, widget, start, end, center):
        QTest.mousePress(widget, Qt.LeftButton, Qt.NoModifier, start)
        self._wait_for_events(20)
        
        steps = 25
        for i in range(1, steps + 1):
            progress = i / float(steps)
            x = int(start.x() + (end.x() - start.x()) * progress)
            y = int(center.y() + 5 * math.sin(progress * math.tau))
            QTest.mouseMove(widget, QPoint(x, y))
            self._wait_for_events(10)
            
        QTest.mouseRelease(widget, Qt.LeftButton, Qt.NoModifier, end)
        self._wait_for_events(300)

    def _paint_stroke_windows_hardware(self, widget, start, end, center):
        import ctypes
        
        start_global = widget.mapToGlobal(start)
        end_global = widget.mapToGlobal(end)
        center_global = widget.mapToGlobal(center)
        
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        original_pos = (pt.x, pt.y)
        
        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP = 0x0004
        
        ctypes.windll.user32.SetCursorPos(start_global.x(), start_global.y())
        self._wait_for_events(50)
        
        # Super fast stroke to beat human reaction time
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        steps = 15
        for i in range(1, steps + 1):
            progress = i / float(steps)
            x = int(start_global.x() + (end_global.x() - start_global.x()) * progress)
            y = int(center_global.y() + 5 * math.sin(progress * math.tau))
            ctypes.windll.user32.SetCursorPos(x, y)
            time.sleep(0.002)
            
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        ctypes.windll.user32.SetCursorPos(*original_pos)
        self._wait_for_events(300)

    def _paint_stroke_qt(self, widget, start, end, center):
        self._send_mouse_event(widget, QEvent.MouseButtonPress, start, Qt.LeftButton, Qt.LeftButton)
        self._wait_for_events(50)
        
        steps = 25
        for i in range(1, steps + 1):
            progress = i / float(steps)
            x = round(start.x() + (end.x() - start.x()) * progress)
            y = round(center.y() + 5 * math.sin(progress * math.tau))
            self._send_mouse_event(widget, QEvent.MouseMove, QPoint(x, y), Qt.NoButton, Qt.LeftButton)
            self._wait_for_events(10)
            
        self._send_mouse_event(widget, QEvent.MouseButtonRelease, end, Qt.LeftButton, Qt.NoButton)
        self._wait_for_events(250)

    @staticmethod
    def _send_mouse_event(widget, event_type, point, button, buttons):
        global_point = widget.mapToGlobal(point)
        event = QMouseEvent(
            event_type, 
            QPointF(point), 
            QPointF(global_point), 
            button, 
            buttons, 
            Qt.NoModifier
        )
        QApplication.sendEvent(widget, event)

    @staticmethod
    def _process_events():
        QApplication.processEvents(QEventLoop.AllEvents, 50)
        
    @staticmethod
    def _wait_for_events(ms):
        end_time = time.time() + ms / 1000.0
        while time.time() < end_time:
            QApplication.processEvents(QEventLoop.AllEvents, 10)
            time.sleep(0.005)

    @staticmethod
    def _find_canvas_widget(main_window):
        if main_window is None:
            return None

        focus_widget = QApplication.focusWidget()
        if focus_widget:
            w = focus_widget
            while w:
                class_name = w.metaObject().className().lower()
                object_name = w.objectName().lower()
                if "canvas" in class_name or "canvas" in object_name:
                    return focus_widget
                w = w.parentWidget()

        candidates = []
        for widget in main_window.findChildren(QWidget):
            if not widget.isVisible() or widget.width() < 50 or widget.height() < 50:
                continue

            class_name = widget.metaObject().className().lower()
            object_name = widget.objectName().lower()
            if "canvas" not in class_name and "canvas" not in object_name:
                continue

            score = 0
            if "kiscanvas2" in class_name:
                score += 1000
            elif "canvas" in class_name:
                score += 500
                
            if widget.hasFocus():
                score += 10000

            candidates.append((score, widget))

        if candidates:
            candidates.sort(key=lambda item: item[0], reverse=True)
            return candidates[0][1]
            
        return None

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
