from PyQt5.QtWidgets import QStyledItemDelegate, QStyle
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen

class BrushItemDelegate(QStyledItemDelegate):
    def __init__(self, padding=3):
        super().__init__()
        self.padding = padding

    def paint(self, painter, option, index):
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = option.rect.adjusted(self.padding, self.padding, -self.padding, -self.padding)
        is_selected = option.state & QStyle.State_Selected
        is_hovered = option.state & QStyle.State_MouseOver

        # 1. Заливка слота
        if is_selected:
            bg_color = QColor("#3D5A80")
        elif is_hovered:
            bg_color = QColor("#383838")
        else:
            bg_color = QColor("#2A2A2A")
            
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 6, 6)
        
        if is_selected:
            painter.setPen(QPen(QColor("#98C1D9"), 2))
            painter.drawRoundedRect(rect, 6, 6)

        # 2. Отрисовка Иконки
        icon = index.data(Qt.DecorationRole)
        if icon:
            icon_side = min(rect.width(), rect.height()) * 0.8
            icon_rect = QRect(0, 0, int(icon_side), int(icon_side))
            
            # Адаптивное позиционирование (прижим влево/вверх или по центру)
            if rect.width() > rect.height() * 1.5:
                icon_rect.moveCenter(QPoint(rect.left() + int(rect.height() / 2), rect.center().y()))
            elif rect.height() > rect.width() * 1.5:
                icon_rect.moveCenter(QPoint(rect.center().x(), rect.top() + int(rect.width() / 2)))
            else:
                icon_rect.moveCenter(rect.center())
            
            pixmap = icon.pixmap(int(icon_side), int(icon_side))
            painter.drawPixmap(icon_rect, pixmap)