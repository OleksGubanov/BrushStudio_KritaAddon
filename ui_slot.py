from PyQt5.QtWidgets import QWidget, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QPalette, QPixmap, QPainterPath

class BrushSlot(QWidget):
    clicked = pyqtSignal(int, str)
    clear_requested = pyqtSignal(int)

    def __init__(self, index, state):
        super().__init__()
        self.index = index
        self.state = state
        self.brush_name = ""
        self.icon_pixmap = None
        self.is_hovered = False

    def set_brush(self, name, preset_image=None):
        self.brush_name = name
        if name and preset_image is not None:
            self.icon_pixmap = QPixmap.fromImage(preset_image)
            self.setToolTip(f"{name}\nRight-click to clear")
        else:
            self.icon_pixmap = None
            self.setToolTip("Empty Slot\nLeft-click: Assign active brush")
        self.update()

    def enterEvent(self, event):
        self.is_hovered = True; self.update(); super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False; self.update(); super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.clicked.emit(self.index, self.brush_name)
        elif event.button() == Qt.RightButton and self.brush_name: self.show_context_menu(event.globalPos())
        super().mousePressEvent(event)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        pal = self.palette()
        menu.setStyleSheet(
            f"QMenu {{ background-color: {pal.color(QPalette.Window).name()}; border: 1px solid {pal.color(QPalette.Mid).name()}; color: {pal.color(QPalette.WindowText).name()}; padding: 4px; }}"
            f"QMenu::item:selected {{ background-color: {pal.color(QPalette.Highlight).name()}; color: {pal.color(QPalette.HighlightedText).name()}; }}"
        )
        action = QAction("Clear Slot", self)
        action.triggered.connect(lambda: self.clear_requested.emit(self.index))
        menu.addAction(action)
        menu.exec_(pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        pad = self.state.slot_padding
        draw_rect = rect.adjusted(pad, pad, -pad, -pad)

        palette = self.palette()
        base_color = palette.color(QPalette.Base)
        hl_color = palette.color(QPalette.Highlight)
        text_color = palette.color(QPalette.Text)
        mid_color = palette.color(QPalette.Mid)

        if self.is_hovered:
            bg_color = QColor(
                int(base_color.red()*0.85 + hl_color.red()*0.15),
                int(base_color.green()*0.85 + hl_color.green()*0.15),
                int(base_color.blue()*0.85 + hl_color.blue()*0.15)
            )
        else:
            bg_color = base_color
            
        painter.setBrush(bg_color)
        painter.setPen(QPen(mid_color, 1))
        painter.drawRoundedRect(draw_rect, 3, 3)

        if not self.brush_name:
            # Draw Empty Cross
            plus_color = QColor(text_color); plus_color.setAlpha(120)
            painter.setPen(QPen(plus_color, 2))
            cx, cy = draw_rect.center().x(), draw_rect.center().y()
            painter.drawLine(cx - 4, cy, cx + 4, cy)
            painter.drawLine(cx, cy - 4, cx, cy + 4)
            return

        # Determine Layout Partitions based on active checkboxes
        parts = []
        if self.state.show_icon: parts.append("icon")
        if self.state.show_tip: parts.append("tip")
        if self.state.show_stroke: parts.append("stroke")
        
        if not parts: return # Nothing to draw

        # Logic for proportional sizing (Stroke gets more room if available)
        total_weight = len(parts)
        if "stroke" in parts and len(parts) > 1:
            total_weight += 1 # Give stroke 2x width
            
        unit_w = draw_rect.width() / total_weight
        current_x = draw_rect.left()

        for part in parts:
            part_w = unit_w * 2 if part == "stroke" else unit_w
            zone = QRect(int(current_x), draw_rect.top(), int(part_w), draw_rect.height())
            
            # Draw dividers between elements
            if current_x > draw_rect.left():
                painter.setPen(QPen(mid_color, 1))
                painter.drawLine(int(current_x), draw_rect.top() + 2, int(current_x), draw_rect.bottom() - 2)

            icon_side = min(zone.width(), zone.height()) - 4
            
            if part == "icon" and self.icon_pixmap:
                scaled = self.icon_pixmap.scaled(int(icon_side), int(icon_side), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                x = zone.center().x() - scaled.width() // 2
                y = zone.center().y() - scaled.height() // 2
                painter.drawPixmap(x, y, scaled)
                
            elif part == "tip":
                # Procedural mock of a brush tip
                painter.setPen(Qt.NoPen)
                painter.setBrush(text_color)
                painter.drawEllipse(zone.center(), int(icon_side/3), int(icon_side/3))
                
            elif part == "stroke":
                # Procedural mock of a fading stroke
                path = QPainterPath()
                start_p = QPointF(zone.left() + 10, zone.center().y() + 5)
                ctrl1 = QPointF(zone.center().x(), zone.top() + 5)
                ctrl2 = QPointF(zone.center().x(), zone.bottom() - 5)
                end_p = QPointF(zone.right() - 10, zone.center().y() - 5)
                path.moveTo(start_p)
                path.cubicTo(ctrl1, ctrl2, end_p)
                
                pen = QPen(text_color, int(icon_side/2.5))
                pen.setCapStyle(Qt.RoundCap)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)

            current_x += part_w