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
    """Перекрашивает пиксели в нужный цвет для минималистичного вида"""
    if not mask_image or mask_image.isNull(): return QImage()
    alpha_mask = mask_image.convertToFormat(QImage.Format_Alpha8)
    out_img = QImage(mask_image.width(), mask_image.height(), QImage.Format_ARGB32_Premultiplied)
    out_img.fill(Qt.transparent)
    painter = QPainter(out_img)
    painter.setPen(Qt.NoPen)
    painter.fillRect(out_img.rect(), color)
    painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
    painter.drawImage(0, 0, alpha_mask)
    painter.end()
    return out_img

def get_engine_emoji(brush_name):
    if not brush_name: return ""
    try:
        preset = krita.Krita.instance().resources("preset").get(brush_name)
        if preset:
            engine_id = preset.paintOpId().lower() if preset.paintOpId() else ""
            if "smudge" in engine_id: return "💧"
            elif "deform" in engine_id: return "🌀"
            elif "sketch" in engine_id or "pencil" in engine_id: return "✏"
            elif "spray" in engine_id: return "💨"
            elif "hatching" in engine_id: return "✍"
            elif "particle" in engine_id: return "✨"
            elif "clone" in engine_id: return "👥"
            elif "curve" in engine_id: return "↪"
            elif "grid" in engine_id: return "▩"
    except Exception: pass
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
        self.tip_mask = None
        self.is_hovered = False
        
        self.setToolTip("Empty Slot\nLeft-click: Assign active brush")
        self.load_from_state()

    def load_from_state(self):
        slot_key = str(self.index)
        data = self.state.slot_data.get(slot_key)
        
        if isinstance(data, dict):
            self.brush_name = data.get("brush_name", "")
            stroke_b64 = data.get("stroke_mask_b64", "")
            tip_b64 = data.get("tip_mask_b64", "")
            if stroke_b64: self.stroke_mask = base64_to_image(stroke_b64)
            if tip_b64: self.tip_mask = base64_to_image(tip_b64)
        elif isinstance(data, str):
            self.brush_name = data
            
        if self.brush_name:
            try:
                preset = krita.Krita.instance().resources("preset").get(self.brush_name)
                if preset: self.icon_pixmap = QPixmap.fromImage(preset.image())
            except Exception: pass
        self.update()

    def set_brush(self, name, preset_image=None, stroke_mask=None, tip_mask=None):
        self.brush_name = name
        self.stroke_mask = stroke_mask
        self.tip_mask = tip_mask
        
        if name:
            if preset_image is not None: self.icon_pixmap = QPixmap.fromImage(preset_image)
            else:
                try:
                    preset = krita.Krita.instance().resources("preset").get(name)
                    if preset: self.icon_pixmap = QPixmap.fromImage(preset.image())
                except Exception: self.icon_pixmap = None
            self.setToolTip(f"{name}\nRight-click to clear / test")
        else:
            self.icon_pixmap, self.stroke_mask, self.tip_mask = None, None, None
            self.setToolTip("Empty Slot\nLeft-click: Assign active brush")
            
        slot_key = str(self.index)
        if name:
            if slot_key not in self.state.slot_data or not isinstance(self.state.slot_data[slot_key], dict):
                self.state.slot_data[slot_key] = {}
            self.state.slot_data[slot_key]["brush_name"] = name
            
            if stroke_mask and not stroke_mask.isNull():
                self.state.slot_data[slot_key]["stroke_mask_b64"] = image_to_base64(stroke_mask)
            if tip_mask and not tip_mask.isNull():
                self.state.slot_data[slot_key]["tip_mask_b64"] = image_to_base64(tip_mask)
        else:
            if slot_key in self.state.slot_data:
                del self.state.slot_data[slot_key]
                
        self.state.save()
        self.update()

    def enterEvent(self, event):
        self.is_hovered = True; self.update(); super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False; self.update(); super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.clicked.emit(self.index, self.brush_name)
        elif event.button() == Qt.RightButton: self.show_context_menu(event.globalPos())

    def show_context_menu(self, global_pos):
        menu = QMenu(self)
        menu.setPalette(self.palette())
        
        assign_action = QAction("Assign Active Brush", self)
        assign_action.triggered.connect(lambda: self.clicked.emit(self.index, ""))
        menu.addAction(assign_action)
        
        if self.brush_name:
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
        from .preview_service import generate_brush_masks_sync
        
        # Получаем словарь с обеими масками
        masks = generate_brush_masks_sync(
            self.brush_name, 
            self.state.preview_render_w, 
            self.state.preview_render_h,
            self.state.tip_render_size,
            self.state.brush_scale_coef
        )
        if masks:
            self.set_brush(self.brush_name, stroke_mask=masks.get('stroke'), tip_mask=masks.get('tip'))

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
        except Exception: pass
            
        painter.setPen(QPen(hl_color if is_active else mid_color, 2 if is_active else 1))
        painter.drawRoundedRect(draw_rect, 3, 3)

        if not self.brush_name:
            if self.is_hovered:
                painter.setPen(QPen(mid_color, 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(draw_rect.adjusted(2, 2, -2, -2), 3, 3)
            return

        # Загрузка состояний видимости
        show_icon = self.state.show_icon
        show_stroke = self.state.show_stroke
        show_tip = self.state.show_tip
        show_engine = self.state.show_engine
        is_recolored = self.state.recolor_preview

        padding = 4
        current_x = draw_rect.left() + padding
        right_edge = draw_rect.right() - padding
        
        target_color = hl_color if (self.is_hovered or is_active) else text_color

        # 1. Отрисовка Emoji Движка (Справа)
        if show_engine:
            engine_emoji = get_engine_emoji(self.brush_name)
            if engine_emoji:
                font = painter.font()
                font.setPointSize(max(8, int(draw_rect.height() * 0.25)))
                painter.setFont(font)
                em_w = painter.fontMetrics().horizontalAdvance(engine_emoji)
                engine_rect = QRect(right_edge - em_w, draw_rect.top() + padding, em_w, draw_rect.height() - (padding*2))
                painter.setPen(text_color)
                painter.drawText(engine_rect, Qt.AlignCenter, engine_emoji)
                right_edge -= (em_w + padding)

        # 2. Отрисовка Кончика кисти (Правее мазка, левее Emoji)
        if show_tip and self.tip_mask and not self.tip_mask.isNull():
            tip_side = min(right_edge - current_x, draw_rect.height() - (padding * 2))
            if tip_side > 5:
                tip_rect = QRect(right_edge - tip_side, draw_rect.top() + padding, tip_side, tip_side)
                tip_rect.moveCenter(QPoint(tip_rect.center().x(), draw_rect.center().y()))
                scaled_tip = self.tip_mask.scaled(tip_rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                final_tip = recolor_mask(scaled_tip, target_color) if is_recolored else scaled_tip
                
                t_rect = QRect(0, 0, final_tip.width(), final_tip.height())
                t_rect.moveCenter(tip_rect.center())
                painter.drawImage(t_rect, final_tip)
                right_edge -= (tip_side + padding)

        # 3. Отрисовка Иконки (Слева)
        if show_icon and self.icon_pixmap and not self.icon_pixmap.isNull():
            icon_side = min(right_edge - current_x, draw_rect.height() - (padding * 2))
            if icon_side > 5:
                icon_rect = QRect(current_x, draw_rect.top() + padding, icon_side, icon_side)
                icon_rect.moveCenter(QPoint(icon_rect.center().x(), draw_rect.center().y()))
                scaled_icon = self.icon_pixmap.scaled(icon_rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap(
                    icon_rect.left() + (icon_rect.width() - scaled_icon.width()) // 2,
                    icon_rect.top() + (icon_rect.height() - scaled_icon.height()) // 2,
                    scaled_icon
                )
                current_x += icon_rect.width() + padding

        # 4. Отрисовка Мазка (По центру, занимает все оставшееся место)
        if show_stroke and self.stroke_mask and not self.stroke_mask.isNull():
            stroke_w = right_edge - current_x
            if stroke_w > 10:
                stroke_rect = QRect(current_x, draw_rect.top() + padding, stroke_w, draw_rect.height() - (padding * 2))
                scaled_stroke = self.stroke_mask.scaled(stroke_rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                final_stroke = recolor_mask(scaled_stroke, target_color) if is_recolored else scaled_stroke
                
                t_rect = QRect(0, 0, final_stroke.width(), final_stroke.height())
                t_rect.moveCenter(stroke_rect.center())
                painter.drawImage(t_rect, final_stroke)