from PyQt5.QtWidgets import QWidget, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QPainter, QColor, QPen, QPalette, QPixmap

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
        self.setToolTip("Empty Slot\nLeft-click: Assign active brush")

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
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index, self.brush_name)
        elif event.button() == Qt.RightButton:
            if self.brush_name:
                self.show_context_menu(event.globalPos())
        super().mousePressEvent(event)

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
        
        rect = self.rect()
        pad = self.state.slot_padding
        draw_rect = rect.adjusted(pad, pad, -pad, -pad)

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
        painter.drawRoundedRect(draw_rect, 3, 3) 
        
        # Border
        painter.setPen(QPen(mid_color, 1))
        painter.drawRoundedRect(draw_rect, 3, 3)

        icon_side = min(draw_rect.width(), draw_rect.height()) - 4
        icon_rect = QRect(0, 0, int(icon_side), int(icon_side))
        icon_rect.moveCenter(draw_rect.center())
        
        if self.icon_pixmap:
            scaled = self.icon_pixmap.scaled(int(icon_side), int(icon_side), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = icon_rect.center().x() - scaled.width() // 2
            y = icon_rect.center().y() - scaled.height() // 2
            painter.drawPixmap(x, y, scaled)
        else:
            plus_color = QColor(text_color)
            plus_color.setAlpha(120)
            painter.setPen(QPen(plus_color, 2))
            cx, cy = icon_rect.center().x(), icon_rect.center().y()
            painter.drawLine(cx - 4, cy, cx + 4, cy)
            painter.drawLine(cx, cy - 4, cx, cy + 4)