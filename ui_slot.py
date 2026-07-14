import os
import tempfile
import krita
import base64
from PyQt5.QtWidgets import QWidget, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint, QSize, QBuffer, QIODevice
from PyQt5.QtGui import QPainter, QColor, QPen, QPalette, QPixmap, QImage

def image_to_base64(image):
    """Конвертирует QImage в Base64 строку (PNG)"""
    if not image or image.isNull():
        return ""
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, "PNG")
    return base64.b64encode(buffer.data()).decode("utf-8")

def base64_to_image(b64_string):
    """Декодирует Base64 строку обратно в QImage"""
    if not b64_string:
        return None
    try:
        image_data = base64.b64decode(b64_string)
        image = QImage()
        image.loadFromData(image_data, "PNG")
        return image
    except Exception as e:
        print(f"[Brush Studio] Ошибка декодирования маски: {e}")
        return None

def recolor_mask(mask_image, color):
    # Твой существующий код recolor_mask...
    if not mask_image or mask_image.isNull():
        return QImage()
    w, h = mask_image.width(), mask_image.height()
    out_img = QImage(w, h, QImage.Format_ARGB32)
    r_color, g_color, b_color = color.red(), color.green(), color.blue()
    for y in range(h):
        for x in range(w):
            pixel = mask_image.pixel(x, y)
            alpha = (pixel >> 16) & 0xFF 
            out_img.setPixel(x, y, (alpha << 24) | (r_color << 16) | (g_color << 8) | b_color)
    return out_img

class BrushSlot(QWidget):
    # --- ОБЪЯВЛЕНИЕ СИГНАЛОВ ---
    clicked = pyqtSignal(int, str)  # Передает ID слота и имя кисти
    updated = pyqtSignal(int)       # Передает ID слота при обновлении
    clear_requested = pyqtSignal(int) # <--- ДОБАВЬ ВОТ ЭТУ СТРОКУ

    def __init__(self, slot_id, state):
        super().__init__()
        self.slot_id = slot_id
        self.state = state
        self.brush_name = ""
        self.stroke_mask = None # Храним QImage маски
        self.is_hovered = False
        
        self.setMouseTracking(True)
        self.load_from_state()

    def load_from_state(self):
        """Загрузка данных слота из глобального состояния с учетом старой структуры."""
        slot_key = str(self.slot_id)
        if slot_key in self.state.slot_data:
            data = self.state.slot_data[slot_key]
            
            # ПРОВЕРКА: Если данные - это словарь (новая структура)
            if isinstance(data, dict):
                self.brush_name = data.get("brush_name", "")
                cached_mask_b64 = data.get("stroke_mask_b64", "")
                if cached_mask_b64:
                    self.stroke_mask = base64_to_image(cached_mask_b64)
            
            # ПРОВЕРКА: Если данные - это просто строка (старая структура)
            elif isinstance(data, str):
                self.brush_name = data
                self.stroke_mask = None # Старые записи не имели масок, придется перекликнуть
        else:
            self.brush_name = ""
            self.stroke_mask = None
        self.update()

    def set_brush(self, brush_name, mask_image=None):
        """Установка кисти и сохранение маски в стейт"""
        self.brush_name = brush_name
        self.stroke_mask = mask_image
        
        # Обновляем структуру данных в state
        slot_key = str(self.slot_id)
        if slot_key not in self.state.slot_data:
            self.state.slot_data[slot_key] = {}
            
        self.state.slot_data[slot_key]["brush_name"] = brush_name
        
        if mask_image and not mask_image.isNull():
            # Кодируем картинку в текст для сохранения в JSON QSettings
            self.state.slot_data[slot_key]["stroke_mask_b64"] = image_to_base64(mask_image)
        else:
            self.state.slot_data[slot_key]["stroke_mask_b64"] = ""
            
        # Принудительно заставляем PanelState сохранить изменения на диск
        self.state.save()
        self.update()

    def clear_slot(self):
        """Очистка слота"""
        self.brush_name = ""
        self.stroke_mask = None
        slot_key = str(self.slot_id)
        if slot_key in self.state.slot_data:
            del self.state.slot_data[slot_key]
        self.state.save()
        self.update()

    # Оставь методы paintEvent, mousePressEvent и др. без изменений, 
    # так как они работают с переменной self.stroke_mask, которую мы теперь успешно восстанавливаем.