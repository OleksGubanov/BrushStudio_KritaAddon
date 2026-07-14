from PyQt5.QtWidgets import QStyledItemDelegate, QStyle
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen

class BrushItemDelegate(QStyledItemDelegate):
    def __init__(self, state_manager):
        super().__init__()
        self.state = state_manager

    def paint(self, painter, option, index):
        painter.setRenderHint(QPainter.Antialiasing)
        
        pad = self.state.slot_padding
        rect = option.rect.adjusted(pad, pad, -pad, -pad)
        
        is_selected = option.state & QStyle.State_Selected
        is_hovered = option.state & QStyle.State_MouseOver

        # Dense dark background
        if is_selected:
            bg_color = QColor("#2A4365")
        elif is_hovered:
            bg_color = QColor("#404040")
        else:
            bg_color = QColor("#2D2D2D")
            
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 3, 3) 
        
        # Border
        painter.setPen(QPen(QColor("#181818"), 1))
        painter.drawRoundedRect(rect, 3, 3)
        
        if is_selected:
            painter.setPen(QPen(QColor("#63B3ED"), 1))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 3, 3)

        # Icon
        icon = index.data(Qt.DecorationRole)
        if icon:
            icon_side = min(rect.width(), rect.height()) - 4
            icon_rect = QRect(0, 0, int(icon_side), int(icon_side))
            
            if rect.width() > rect.height():
                icon_rect.moveCenter(QPoint(rect.left() + int(icon_side / 2) + 2, rect.center().y()))
            else:
                icon_rect.moveCenter(QPoint(rect.center().x(), rect.top() + int(icon_side / 2) + 2))
            
            pixmap = icon.pixmap(int(icon_side), int(icon_side))
            painter.drawPixmap(icon_rect, pixmap)