from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QPainter, QPen, QFont, QPalette

class BrushSlot(QWidget):
    """Чистый виджет (View), получающий BrushData от контроллера."""
    clicked = pyqtSignal(int)
    clear_requested = pyqtSignal(int)

    def __init__(self, index):
        super().__init__()
        self.index = index
        self.data = None
        self.is_hovered = False

    def set_data(self, brush_data):
        self.data = brush_data
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
            self.clear_requested.emit(self.index)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        rect = self.rect()
        palette = self.palette()
        bg_color = palette.color(QPalette.Window)
        
        if self.is_hovered:
            painter.setBrush(bg_color.lighter(110))
            painter.setPen(QPen(palette.color(QPalette.Highlight), 1.5))
        else:
            painter.setBrush(bg_color)
            painter.setPen(QPen(palette.color(QPalette.Mid), 1))
            
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 4, 4)
        
        if not self.data: return

        # Отрисовка иконки, мазка и текста на основе self.data (без запросов к сервисам)
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