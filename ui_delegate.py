from PyQt5.QtWidgets import QStyledItemDelegate, QStyle
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen

class BrushItemDelegate(QStyledItemDelegate):
    def __init__(self, padding=1):
        super().__init__()
        # Padding is reduced to 1px for maximum compactness
        self.padding = padding

    def paint(self, painter, option, index):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Tight bounding box to eliminate empty spaces
        rect = option.rect.adjusted(self.padding, self.padding, -self.padding, -self.padding)
        is_selected = option.state & QStyle.State_Selected
        is_hovered = option.state & QStyle.State_MouseOver

        # 1. Background Fill (Flat, minimal rounding for blocky aesthetic)
        if is_selected:
            bg_color = QColor("#3D5A80")
        elif is_hovered:
            bg_color = QColor("#454545")
        else:
            bg_color = QColor("#2A2A2A")
            
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 2, 2) # 2px radius
        
        # Selection outline
        if is_selected:
            painter.setPen(QPen(QColor("#98C1D9"), 1))
            painter.drawRoundedRect(rect, 2, 2)

        # 2. Icon Drawing
        icon = index.data(Qt.DecorationRole)
        if icon:
            # Icon fills 90% of the shortest side to avoid empty space
            icon_side = min(rect.width(), rect.height()) * 0.9
            icon_rect = QRect(0, 0, int(icon_side), int(icon_side))
            
            # Flex-like positioning (align left if wide, align top if tall)
            if rect.width() > rect.height() * 1.3:
                icon_rect.moveCenter(QPoint(rect.left() + int(rect.height() / 2), rect.center().y()))
            elif rect.height() > rect.width() * 1.3:
                icon_rect.moveCenter(QPoint(rect.center().x(), rect.top() + int(rect.width() / 2)))
            else:
                icon_rect.moveCenter(rect.center())
            
            pixmap = icon.pixmap(int(icon_side), int(icon_side))
            painter.drawPixmap(icon_rect, pixmap)