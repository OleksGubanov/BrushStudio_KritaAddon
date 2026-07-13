from PyQt5.QtWidgets import QStyledItemDelegate, QStyle
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen

class BrushItemDelegate(QStyledItemDelegate):
    def __init__(self):
        super().__init__()

    def paint(self, painter, option, index):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Absolute exact bounds (0 margin for seamless block layout)
        rect = option.rect
        is_selected = option.state & QStyle.State_Selected
        is_hovered = option.state & QStyle.State_MouseOver

        # 1. Background Fill (100% of slot area)
        if is_selected:
            bg_color = QColor("#2A4365")
        elif is_hovered:
            bg_color = QColor("#404040")
        else:
            bg_color = QColor("#2D2D2D")
            
        painter.fillRect(rect, bg_color)
        
        # 1px Dark border to separate buttons (Blender style)
        painter.setPen(QPen(QColor("#181818"), 1))
        painter.drawRect(rect)
        
        if is_selected:
            painter.setPen(QPen(QColor("#63B3ED"), 1))
            painter.drawRect(rect.adjusted(1, 1, -1, -1))

        # 2. Icon Drawing
        icon = index.data(Qt.DecorationRole)
        if icon:
            # 2px internal padding for the icon
            icon_side = min(rect.width(), rect.height()) - 4
            icon_rect = QRect(0, 0, int(icon_side), int(icon_side))
            
            # Anchor to start, preserving aspect ratio
            if rect.width() > rect.height():
                icon_rect.moveCenter(QPoint(rect.left() + int(icon_side / 2) + 2, rect.center().y()))
            else:
                icon_rect.moveCenter(QPoint(rect.center().x(), rect.top() + int(icon_side / 2) + 2))
            
            pixmap = icon.pixmap(int(icon_side), int(icon_side))
            painter.drawPixmap(icon_rect, pixmap)