from PyQt5.QtWidgets import QWidget, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QPainter, QPen, QFont, QPalette, QColor

class BrushSlot(QWidget):
    """Чистый виджет (View), получающий BrushData от контроллера."""
    clicked = pyqtSignal(int)
    clear_requested = pyqtSignal(int)

    def __init__(self, index):
        super().__init__()
        self.index = index
        self.data = None
        self.is_hovered = False
        self.setToolTip("Empty Slot\nLeft-click: Assign active brush")

    def set_data(self, brush_data):
        self.data = brush_data
        if self.data and self.data.name:
            self.setToolTip(f"{self.data.name}\nRight-click to clear")
        else:
            self.setToolTip("Empty Slot\nLeft-click: Assign active brush")
        self.update()

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)
        elif event.button() == Qt.RightButton:
            if self.data and self.data.name:
                self.show_context_menu(event.globalPos())

    def show_context_menu(self, pos):
        menu = QMenu(self)
        palette = self.palette()
        border = palette.color(QPalette.Mid).name()
        bg = palette.color(QPalette.Window).name()
        text = palette.color(QPalette.WindowText).name()
        hl = palette.color(QPalette.Highlight).name()
        
        menu.setStyleSheet(
            f"QMenu {{ background-color: {bg}; border: 1px solid {border}; color: {text}; padding: 4px; }}"
            f"QMenu::item:selected {{ background-color: {hl}; color: {palette.color(QPalette.HighlightedText).name()}; }}"
        )
        
        action = QAction("Clear Slot", self)
        action.triggered.connect(lambda: self.clear_requested.emit(self.index))
        menu.addAction(action)
        menu.exec_(pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        rect = self.rect()
        palette = self.palette()
        base_color = palette.color(QPalette.Base)
        hl_color = palette.color(QPalette.Highlight)
        text_color = palette.color(QPalette.Text)
        mid_color = palette.color(QPalette.Mid)
        
        # Dynamic Hover Blending
        if self.is_hovered:
            r = int(base_color.red() * 0.85 + hl_color.red() * 0.15)
            g = int(base_color.green() * 0.85 + hl_color.green() * 0.15)
            b = int(base_color.blue() * 0.85 + hl_color.blue() * 0.15)
            bg_color = QColor(r, g, b)
        else:
            bg_color = base_color
            
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        draw_rect = rect.adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(draw_rect, 4, 4)
        
        # Border
        painter.setPen(QPen(mid_color, 1))
        painter.drawRoundedRect(draw_rect, 4, 4)
        
        if not self.data or not self.data.name:
            plus_color = QColor(text_color)
            plus_color.setAlpha(120)
            painter.setPen(QPen(plus_color, 2))
            cx, cy = draw_rect.center().x(), draw_rect.center().y()
            painter.drawLine(cx - 4, cy, cx + 4, cy)
            painter.drawLine(cx, cy - 4, cx, cy + 4)
            return

        if self.data.icon_pixmap:
            scaled = self.data.icon_pixmap.scaled(rect.width() // 2, rect.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(rect.x() + 4, rect.center().y() - scaled.height() // 2, scaled)
            
        if self.data.stroke_pixmap:
            scaled = self.data.stroke_pixmap.scaled(rect.width() // 2, rect.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(rect.center().x(), rect.center().y() - scaled.height() // 2, scaled)

        if self.data.engine_icon:
            painter.setPen(palette.color(QPalette.WindowText))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(rect.adjusted(4, 4, -4, -4), Qt.AlignRight | Qt.AlignTop, self.data.engine_icon)