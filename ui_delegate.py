from PyQt5.QtWidgets import QStyledItemDelegate, QStyle
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen

class BrushItemDelegate(QStyledItemDelegate):
    def __init__(self, padding=2):
        super().__init__()
        self.padding = padding

    def paint(self, painter, option, index):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Container bounds (takes up the entire grid cell minus minimal padding)
        rect = option.rect.adjusted(self.padding, self.padding, -self.padding, -self.padding)
        is_selected = option.state & QStyle.State_Selected
        is_hovered = option.state & QStyle.State_MouseOver

        # 2. Draw Container Background (Fills the entire available slot)
        if is_selected:
            bg_color = QColor("#3D5A80")
        elif is_hovered:
            bg_color = QColor("#454545")
        else:
            bg_color = QColor("#2A2A2A")
            
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 3, 3) 
        
        if is_selected:
            painter.setPen(QPen(QColor("#98C1D9"), 1))
            painter.drawRoundedRect(rect, 3, 3)

        # 3. Draw Icon (Preserves 1:1 aspect ratio, anchors to start)
        icon = index.data(Qt.DecorationRole)
        if icon:
            # Icon size is determined by the shortest side of the slot to remain square
            icon_side = min(rect.width(), rect.height()) - (self.padding * 2)
            icon_rect = QRect(0, 0, int(icon_side), int(icon_side))
            
            # Align icon to Start (Left for horizontal slots, Top for vertical slots)
            if rect.width() > rect.height():
                # Wide container -> Align Left, Center Vertically
                icon_rect.moveCenter(QPoint(rect.left() + int(icon_side / 2) + self.padding, rect.center().y()))
            else:
                # Tall or Square container -> Align Top, Center Horizontally
                icon_rect.moveCenter(QPoint(rect.center().x(), rect.top() + int(icon_side / 2) + self.padding))
            
            pixmap = icon.pixmap(int(icon_side), int(icon_side))
            painter.drawPixmap(icon_rect, pixmap)