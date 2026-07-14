from PyQt5.QtWidgets import QStyledItemDelegate, QStyle
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QPalette

class BrushItemDelegate(QStyledItemDelegate):
    def __init__(self, state_manager):
        super().__init__()
        self.state = state_manager

    def blend_colors(self, c1, c2, factor=0.5):
        """Helper to blend two QColors gracefully for a dynamic theme UI"""
        return QColor(
            int(c1.red() * (1 - factor) + c2.red() * factor),
            int(c1.green() * (1 - factor) + c2.green() * factor),
            int(c1.blue() * (1 - factor) + c2.blue() * factor)
        )

    def paint(self, painter, option, index):
        painter.setRenderHint(QPainter.Antialiasing)
        
        pad = self.state.slot_padding
        rect = option.rect.adjusted(pad, pad, -pad, -pad)
        
        is_selected = option.state & QStyle.State_Selected
        is_hovered = option.state & QStyle.State_MouseOver

        palette = option.palette
        highlight_color = palette.color(QPalette.Highlight)
        base_color = palette.color(QPalette.Base)
        text_color = palette.color(QPalette.Text)
        mid_color = palette.color(QPalette.Mid)

        # Dynamic Slot Background using native colors
        if is_selected:
            bg_color = highlight_color
        elif is_hovered:
            bg_color = self.blend_colors(base_color, highlight_color, 0.15)
        else:
            bg_color = base_color
            
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 3, 3) 
        
        # Subtle dynamic borders
        painter.setPen(QPen(mid_color, 1))
        painter.drawRoundedRect(rect, 3, 3)
        
        if is_selected:
            # Highlight border
            painter.setPen(QPen(highlight_color, 1))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 3, 3)

        # Universal Inner Bounds (Maintains aspect ratio positioning for both icons and plus signs)
        icon_side = min(rect.width(), rect.height()) - 4
        icon_rect = QRect(0, 0, int(icon_side), int(icon_side))
        
        if rect.width() > rect.height():
            icon_rect.moveCenter(QPoint(rect.left() + int(icon_side / 2) + 2, rect.center().y()))
        else:
            icon_rect.moveCenter(QPoint(rect.center().x(), rect.top() + int(icon_side / 2) + 2))

        brush_name = index.data(Qt.UserRole)
        icon = index.data(Qt.DecorationRole)
        
        if brush_name and icon and not icon.isNull():
            # Draw assigned brush icon
            pixmap = icon.pixmap(int(icon_side), int(icon_side))
            painter.drawPixmap(icon_rect, pixmap)
        else:
            # Draw subtle '+' for empty slot with semi-transparent native text color
            plus_color = QColor(text_color)
            plus_color.setAlpha(120)
            painter.setPen(QPen(plus_color, 2))
            center = icon_rect.center()
            painter.drawLine(center.x() - 4, center.y(), center.x() + 4, center.y())
            painter.drawLine(center.x(), center.y() - 4, center.x(), center.y() + 4)