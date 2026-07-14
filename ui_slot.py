# ui_slot.py
from PyQt5.QtWidgets import QWidget, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPointF
from PyQt5.QtGui import QPainter, QColor, QFont, QPixmapCache, QPixmap, QPen, QPainterPath, QPalette
from .preview_service import BrushEngineParser

class BrushSlot(QWidget):
    clicked = pyqtSignal(int, str)
    clear_requested = pyqtSignal(int)

    def __init__(self, index, state, preview_service=None):
        super().__init__()
        self.index = index
        self.state = state
        self.preview_service = preview_service 
        self.brush_name = ""
        self.icon_pixmap = None
        self.stroke_pixmap = None 
        self.engine_icon = ""
        self.is_hovered = False
        
        if self.preview_service:
            self.preview_service.previewReady.connect(self.on_preview_ready)

    def set_brush(self, name, preset_image=None):
        self.brush_name = name
        self.stroke_pixmap = None 
        
        if name:
            if preset_image is not None:
                self.icon_pixmap = QPixmap.fromImage(preset_image)
            
            # Быстро получаем иконку движка
            if getattr(self.state, 'show_engine', False):
                self.engine_icon = BrushEngineParser.get_engine_icon(name)
            else:
                self.engine_icon = ""
                
            # Запрашиваем рендер мазка, если он включен
            if getattr(self.state, 'show_stroke', False) and self.preview_service:
                self.preview_service.request_stroke(name)
        else:
            self.icon_pixmap = None
            self.engine_icon = ""
            
        self.update()

    def on_preview_ready(self, preset_name, pixmap):
        if preset_name == self.brush_name:
            self.stroke_pixmap = pixmap
            self.update()

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index, self.brush_name)
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.pos())

    def show_context_menu(self, pos):
        if not self.brush_name:
            return
            
        menu = QMenu(self)
        clear_action = QAction("Clear Slot", self)
        clear_action.triggered.connect(lambda: self.clear_requested.emit(self.index))
        menu.addAction(clear_action)
        menu.exec_(self.mapToGlobal(pos))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        rect = self.rect()
        
        # Получаем стандартные цвета темы Критьы
        palette = self.palette()
        bg_color = palette.color(QPalette.Window)
        border_color = palette.color(QPalette.Mid)
        highlight_color = palette.color(QPalette.Highlight)
        text_color = palette.color(QPalette.WindowText)
        
        # Рисуем фон
        if self.is_hovered:
            painter.setBrush(bg_color.lighter(110))
            painter.setPen(QPen(highlight_color, 1.5))
        else:
            painter.setBrush(bg_color)
            painter.setPen(QPen(border_color, 1))
            
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 4, 4)
        
        if not self.brush_name:
            # Отрисовка пустого плюсика
            painter.setPen(QPen(border_color, 1.5))
            size = min(rect.width(), rect.height()) // 4
            cx, cy = rect.center().x(), rect.center().y()
            painter.drawLine(cx - size, cy, cx + size, cy)
            painter.drawLine(cx, cy - size, cx, cy + size)
            return

        # Расчет зон отрисовки в зависимости от настроек отображения
        show_icon = getattr(self.state, 'show_icon', True)
        show_stroke = getattr(self.state, 'show_stroke', True)
        
        active_parts = []
        if show_icon: active_parts.append("icon")
        if show_stroke: active_parts.append("stroke")
        
        if not active_parts:
            # Если всё выключено, показываем хотя бы имя
            painter.setPen(text_color)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(rect, Qt.AlignCenter | Qt.TextWordWrap, self.brush_name)
            return
            
        total_parts = len(active_parts)
        part_w = rect.width() / total_parts
        current_x = rect.x()

        for part in active_parts:
            zone = QRect(int(current_x), rect.y(), int(part_w), rect.height()).adjusted(4, 4, -4, -4)
            
            # Отрисовка иконки пресета
            if part == "icon":
                if self.icon_pixmap and not self.icon_pixmap.isNull():
                    scaled_icon = self.icon_pixmap.scaled(zone.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    ix = zone.center().x() - scaled_icon.width() // 2
                    iy = zone.center().y() - scaled_icon.height() // 2
                    painter.drawPixmap(ix, iy, scaled_icon)
                else:
                    # Заглушка, если иконка не загрузилась (рисуем абстрактную кисть)
                    painter.setBrush(Qt.NoBrush)
                    icon_side = min(zone.width(), zone.height())
                    path = QPainterPath()
                    start_p = QPointF(zone.left() + 10, zone.center().y() + 5)
                    ctrl1 = QPointF(zone.center().x(), zone.top() + 5)
                    ctrl2 = QPointF(zone.center().x(), zone.bottom() - 5)
                    end_p = QPointF(zone.right() - 10, zone.center().y() - 5)
                    path.moveTo(start_p)
                    path.cubicTo(ctrl1, ctrl2, end_p)
                    
                    pen = QPen(text_color, int(icon_side/2.5))
                    pen.setCapStyle(Qt.RoundCap)
                    painter.setPen(pen)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawPath(path)

            current_x += part_w

        # Отрисовка мазка (если включен и загрузился)
        if part == "stroke" and self.stroke_pixmap:
            # Масштабируем сгенерированный мазок под ячейку
            scaled_stroke = self.stroke_pixmap.scaled(zone.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            sx = zone.center().x() - scaled_stroke.width() // 2
            sy = zone.center().y() - scaled_stroke.height() // 2
            painter.drawPixmap(sx, sy, scaled_stroke)
            
        # Отрисовка иконки движка (поверх всего)
        if getattr(self.state, 'show_engine', False) and self.engine_icon:
            painter.setPen(text_color)
            painter.setFont(QFont("Arial", 10))
            painter.drawText(rect.adjusted(4, 4, -4, -4), Qt.AlignRight | Qt.AlignTop, self.engine_icon)