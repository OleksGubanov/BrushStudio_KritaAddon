from PyQt5.QtWidgets import QStyledItemDelegate, QStyle
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QPalette

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

        palette = option.palette
        if is_selected:
            bg_color = palette.color(QPalette.Highlight)
        elif is_hovered:
            bg_color = palette.color(QPalette.AlternateBase)
        else:
            bg_color = palette.color(QPalette.Window)
            
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 3, 3) 
        
        border_color = palette.color(QPalette.Dark)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect, 3, 3)
        
        if is_selected:
            highlight_color = palette.color(QPalette.Highlight)
            painter.setPen(QPen(highlight_color, 1))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 3, 3)

        icon_side = min(rect.width(), rect.height()) - 4
        icon_rect = QRect(0, 0, int(icon_side), int(icon_side))
        
        if rect.width() > rect.height():
            icon_rect.moveCenter(QPoint(rect.left() + int(icon_side / 2) + 2, rect.center().y()))
        else:
            icon_rect.moveCenter(QPoint(rect.center().x(), rect.top() + int(icon_side / 2) + 2))

        brush_name = index.data(Qt.UserRole)
        icon = index.data(Qt.DecorationRole)
        
        if brush_name and icon and not icon.isNull():
            pixmap = icon.pixmap(int(icon_side), int(icon_side))
            painter.drawPixmap(icon_rect, pixmap)
        else:
            painter.setPen(QPen(palette.color(QPalette.Text), 2))
            center = icon_rect.center()
            painter.drawLine(center.x() - 4, center.y(), center.x() + 4, center.y())
            painter.drawLine(center.x(), center.y() - 4, center.x(), center.y() + 4)