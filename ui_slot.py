import os
import tempfile
import krita
import base64
from PyQt5.QtWidgets import QWidget, QMenu, QAction
from PyQt5.QtCore import Qt, QBuffer, QIODevice, pyqtSignal, QRect, QPoint, QSize
from PyQt5.QtGui import QPainter, QColor, QPen, QPalette, QPixmap, QImage

def image_to_base64(image):
    if not image or image.isNull(): return ""
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, "PNG")
    return base64.b64encode(buffer.data()).decode("utf-8")

def base64_to_image(b64_string):
    if not b64_string: return None
    try:
        image_data = base64.b64decode(b64_string)
        image = QImage()
        image.loadFromData(image_data, "PNG")
        return image
    except Exception:
        return None

def recolor_mask(mask_image, color):
    """
    Превращает Ч/Б маску (белый мазок на черном фоне) в цветной мазок
    на прозрачном фоне с сохранением идеального сглаживания (anti-aliasing).
    """
    if not mask_image or mask_image.isNull():
        return QImage()
    
    w, h = mask_image.width(), mask_image.height()
    out_img = QImage(w, h, QImage.Format_ARGB32)
    
    r_color = color.red()
    g_color = color.green()
    b_color = color.blue()
    
    # Быстрый пиксельный проход для переноса яркости маски в альфа-канал
    for y in range(h):
        for x in range(w):
            pixel = mask_image.pixel(x, y)
            # Извлекаем интенсивность белого из красного канала (0-255)
            alpha = (pixel >> 16) & 0xFF 
            # Формируем пиксель: Alpha + целевой RGB
            out_img.setPixel(x, y, (alpha << 24) | (r_color << 16) | (g_color << 8) | b_color)
            
    return out_img

def get_engine_emoji(brush_name):
    """
    Определяет движок (Engine ID) кисти в Krita и возвращает смайлик-иконку.
    """
    if not brush_name:
        return ""
    try:
        all_presets = krita.Krita.instance().resources("preset")
        preset = all_presets.get(brush_name)
        if preset:
            engine_id = preset.paintOpId()
            if not engine_id:
                return "🖌"
            
            engine_id = engine_id.lower()
            if "colorsmudge" in engine_id or "smudge" in engine_id:
                return "💧"  # Смазывание / смешивание
            elif "deform" in engine_id:
                return "🌀"  # Деформация
            elif "pixel" in engine_id:
                return "🖌"  # Стандартный пиксельный движок
            elif "sketch" in engine_id or "pencil" in engine_id:
                return "✏"  # Карандаш / Скетч
            elif "spray" in engine_id:
                return "💨"  # Распылитель / Аэрограф
            elif "hatching" in engine_id:
                return "✍"  # Штриховка
            elif "particle" in engine_id:
                return "✨"  # Частицы
            elif "clone" in engine_id:
                return "👥"  # Клон-кисть
            elif "curve" in engine_id:
                return "↪"  # Кривые
            elif "grid" in engine_id:
                return "▩"  # Сетка
            else:
                return "🖌"
    except Exception as e:
        print(f"[Brush Studio] Ошибка определения движка для {brush_name}: {e}")
    return "🖌"

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
        self.stroke_mask = None 
        self.is_hovered = False
        self._last_requested_size = QSize(0, 0)
        
        self.setToolTip("Empty Slot\nLeft-click: Assign active brush")
        
        if self.preview_service:
            self.preview_service.preview_generated.connect(self._on_preview_generated)
            
        # Загружаем кешированные данные при инициализации
        self.load_from_state()

    def load_from_state(self):
        slot_key = str(self.index)
        data = self.state.slot_data.get(slot_key)
        
        if isinstance(data, dict):
            self.brush_name = data.get("brush_name", "")
            mask_b64 = data.get("stroke_mask_b64", "")
            if mask_b64:
                self.stroke_mask = base64_to_image(mask_b64)
        elif isinstance(data, str):
            # Поддержка старого формата, где хранилось только имя
            self.brush_name = data
            
        if self.brush_name:
            try:
                preset = krita.Krita.instance().resources("preset").get(self.brush_name)
                if preset:
                    self.icon_pixmap = QPixmap.fromImage(preset.image())
            except Exception:
                pass
        self.update()

    def set_brush(self, name, preset_image=None, stroke_mask=None):
        self.brush_name = name
        self.stroke_mask = stroke_mask
        
        if name:
            if preset_image is not None:
                self.icon_pixmap = QPixmap.fromImage(preset_image)
            else:
                try:
                    preset = krita.Krita.instance().resources("preset").get(name)
                    if preset: self.icon_pixmap = QPixmap.fromImage(preset.image())
                except Exception:
                    self.icon_pixmap = None
            self.setToolTip(f"{name}\nRight-click to clear / test")
        else:
            self.icon_pixmap = None
            self.stroke_mask = None
            self.setToolTip("Empty Slot\nLeft-click: Assign active brush")
            
        # Сохранение в state
        slot_key = str(self.index)
        if name:
            if slot_key not in self.state.slot_data or not isinstance(self.state.slot_data[slot_key], dict):
                self.state.slot_data[slot_key] = {}
            self.state.slot_data[slot_key]["brush_name"] = name
            
            if stroke_mask and not stroke_mask.isNull():
                self.state.slot_data[slot_key]["stroke_mask_b64"] = image_to_base64(stroke_mask)
        else:
            if slot_key in self.state.slot_data:
                del self.state.slot_data[slot_key]
                
        self.state.save()
        self.update()

    def _on_preview_generated(self, brush_name, mask_image):
        if brush_name == self.brush_name:
            self.stroke_mask = mask_image
            self.update()

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.brush_name and self.preview_service:
            new_size = event.size()
            width_diff = abs(new_size.width() - self._last_requested_size.width())
            height_diff = abs(new_size.height() - self._last_requested_size.height())
            
            if width_diff > 15 or height_diff > 10:
                self._last_requested_size = new_size
                w = max(100, new_size.width())
                h = max(30, new_size.height())
                self.preview_service.request_preview(self.brush_name, w, h)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index, self.brush_name)
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())

    def show_context_menu(self, global_pos):
        menu = QMenu(self)
        menu.setPalette(self.palette())
        
        assign_action = QAction("Assign Active Brush", self)
        assign_action.triggered.connect(lambda: self.clicked.emit(self.index, ""))
        menu.addAction(assign_action)
        
        if self.brush_name:
            # ТЕСТОВАЯ КНОПКА ДИАГНОСТИКИ (ПКМ -> Тест: Принудительный рендер)
            test_action = QAction("⚡ Тест: Принудительный рендер", self)
            test_action.triggered.connect(self._force_sync_render)
            menu.addAction(test_action)
            
            menu.addSeparator()
            
            clear_action = QAction("Clear Slot", self)
            clear_action.triggered.connect(lambda: self.clear_requested.emit(self.index))
            menu.addAction(clear_action)
            
        menu.exec_(global_pos)

    def _force_sync_render(self):
        if not self.brush_name: return
        w, h = max(100, self.width()), max(30, self.height())
        from .preview_service import generate_brush_mask_sync
        
        mask = generate_brush_mask_sync(self.brush_name, w, h)
        if mask:
            # Сохраняем кисть и свежую маску
            self.set_brush(self.brush_name, stroke_mask=mask)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        palette = self.palette()
        base_color = palette.color(QPalette.Button)
        hl_color = palette.color(QPalette.Highlight)
        mid_color = palette.color(QPalette.Mid)
        text_color = palette.color(QPalette.WindowText)
        
        draw_rect = self.rect().adjusted(1, 1, -1, -1)
        
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
        
        is_active = False
        try:
            current_preset = krita.Krita.instance().currentBrushPreset()
            if current_preset and self.brush_name and current_preset.name() == self.brush_name:
                is_active = True
        except Exception:
            pass
            
        if is_active:
            painter.setPen(QPen(hl_color, 2))
        else:
            painter.setPen(QPen(mid_color, 1))
        painter.drawRoundedRect(draw_rect, 3, 3)

        if not self.brush_name:
            if self.is_hovered:
                painter.setPen(QPen(mid_color, 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(draw_rect.adjusted(2, 2, -2, -2), 3, 3)
            return

        show_icon = getattr(self.state, "show_icon", True)
        show_stroke = getattr(self.state, "show_stroke", True)
        show_engine = getattr(self.state, "show_engine", True)

        padding = 4
        current_x = draw_rect.left() + padding
        available_width = draw_rect.width() - (padding * 2)
        
        # Отрисовка Иконки
        if show_icon and self.icon_pixmap and not self.icon_pixmap.isNull():
            icon_side = min(draw_rect.width(), draw_rect.height()) - (padding * 2)
            icon_rect = QRect(current_x, draw_rect.top() + padding, int(icon_side), int(icon_side))
            icon_rect.moveCenter(QPoint(icon_rect.center().x(), draw_rect.center().y()))
            
            scaled_icon = self.icon_pixmap.scaled(icon_rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(
                icon_rect.left() + (icon_rect.width() - scaled_icon.width()) // 2,
                icon_rect.top() + (icon_rect.height() - scaled_icon.height()) // 2,
                scaled_icon
            )
            current_x += icon_rect.width() + padding
            available_width -= icon_rect.width() + padding

        # Расчет зоны под иконку Движка (Emoji в правом верхнем углу)
        engine_rect = QRect()
        engine_emoji = ""
        if show_engine:
            engine_emoji = get_engine_emoji(self.brush_name)
            if engine_emoji:
                font = painter.font()
                font.setPointSize(max(8, int(draw_rect.height() * 0.25)))
                painter.setFont(font)
                
                metrics = painter.fontMetrics()
                em_w = metrics.horizontalAdvance(engine_emoji)
                em_h = metrics.height()
                
                engine_rect = QRect(draw_rect.right() - em_w - padding,
                                    draw_rect.top() + padding,
                                    em_w, em_h)
                available_width -= (em_w + padding)

        # Отрисовка Мазка
        if show_stroke and self.stroke_mask and not self.stroke_mask.isNull():
            stroke_rect = QRect(current_x, draw_rect.top() + padding,
                                int(available_width), draw_rect.height() - (padding * 2))
            
            stroke_color = hl_color if (self.is_hovered or is_active) else text_color
            recolored_stroke = recolor_mask(self.stroke_mask, stroke_color)
            
            if not recolored_stroke.isNull():
                scaled_stroke = recolored_stroke.scaled(stroke_rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                target_rect = QRect(0, 0, scaled_stroke.width(), scaled_stroke.height())
                target_rect.moveCenter(stroke_rect.center())
                painter.drawImage(target_rect, scaled_stroke)

        # Отрисовка Emoji
        if show_engine and engine_emoji and not engine_rect.isEmpty():
            painter.setPen(text_color)
            painter.drawText(engine_rect, Qt.AlignCenter, engine_emoji)