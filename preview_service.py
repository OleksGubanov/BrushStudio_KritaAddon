import krita
import math
from PyQt5.QtGui import QImage, QPainter, QColor, QPainterPath, QBitmap, QRegion
from PyQt5.QtCore import Qt, QPointF, QRect

def auto_crop_image(img_bytes, canvas_size, target_width, target_height, is_stroke=False):
    """Преобразует байты в QImage, находит границы через QRegion и кадрирует"""
    original_img = QImage(img_bytes, canvas_size, canvas_size, QImage.Format_RGBA8888).copy()
    
    # Ищем границы контента (альфа-канал)
    alpha_mask = original_img.createAlphaMask()
    bitmap = QBitmap.fromImage(alpha_mask)
    region = QRegion(bitmap)
    bbox = region.boundingRect()
    
    if bbox.isNull() or bbox.isEmpty(): 
        return None
        
    if is_stroke:
        # КАРДИНАЛЬНОЕ РЕШЕНИЕ ДЛЯ СПРЕЕВ И AIRBRUSH:
        # Игнорируем гигантский разлет частиц по высоте, который делает рамку квадратной.
        # Вычисляем идеальную высоту исходя из реальной ширины мазка и пропорций слота.
        target_aspect = target_height / float(target_width)
        ideal_height = int(bbox.width() * target_aspect)
        
        # Центрируем новую высоту относительно реального центра мазка по Y
        center_y = bbox.center().y()
        new_top = int(max(0, center_y - ideal_height / 2))
        new_bottom = int(min(canvas_size - 1, center_y + ideal_height / 2))
        
        # Жестко переписываем координаты рамки
        bbox.setRect(bbox.left(), new_top, bbox.width(), new_bottom - new_top)
    
    # Небольшой отступ, чтобы края не прилипали впритык
    pad = 10
    bbox.adjust(-pad, -pad, pad, pad)
    bbox = bbox.intersected(original_img.rect())
    
    cropped_img = original_img.copy(bbox)
    return cropped_img.scaled(int(target_width), int(target_height), Qt.KeepAspectRatio, Qt.SmoothTransformation)


def generate_brush_masks_sync(brush_name, stroke_w, stroke_h, tip_size, scale_coef=0.4):
    app = krita.Krita.instance()
    window = app.activeWindow()
    if not window: return None

    canvas_size = 1024
    doc = app.createDocument(canvas_size, canvas_size, f"Test_{brush_name}", "RGBA", "U8", "", 120.0)
    window.addView(doc)
    view = window.activeView()
    
    target_preset = app.resources("preset").get(brush_name)
    stroke_bytes, tip_bytes = None, None
    
    try:
        if target_preset:
            view.setCurrentBrushPreset(target_preset)
        
        black = krita.ManagedColor("RGBA", "U8", "")
        black.fromQColor(QColor(0, 0, 0, 255))
        view.setForeGroundColor(black)
        
        root = doc.rootNode()
        
        # --- 1. РЕНДЕР МАЗКА (STROKE) ---
        stroke_layer = doc.createNode("Stroke", "paintlayer")
        root.addChildNode(stroke_layer, None)
        
        engine = ""
        if target_preset:
            if hasattr(target_preset, 'paintOpId'): engine = target_preset.paintOpId().lower()
            else: engine = str(target_preset.name()).lower()
        
        if any(key in engine for key in ["smudge", "deform", "blend", "liquify"]):
            # Заглушка для блендеров (они не рисуют черным цветом)
            base_img = QImage(canvas_size, canvas_size, QImage.Format_RGBA8888)
            base_img.fill(Qt.transparent)
            p = QPainter(base_img)
            p.setPen(Qt.NoPen)
            r = int(canvas_size * 0.25)
            p.setBrush(QColor(255, 100, 100, 255)); p.drawEllipse(int(canvas_size * 0.25) - r//3, int(canvas_size//2) - r//3, r, r)
            p.setBrush(QColor(100, 255, 100, 255)); p.drawEllipse(int(canvas_size * 0.50) - r//3, int(canvas_size//2) - r//3, r, r)
            p.setBrush(QColor(100, 100, 255, 255)); p.drawEllipse(int(canvas_size * 0.75) - r//3, int(canvas_size//2) - r//3, r, r)
            p.end()
            ptr = base_img.constBits(); ptr.setsize(base_img.byteCount())
            stroke_layer.setPixelData(bytes(ptr), 0, 0, canvas_size, canvas_size)
        else:
            empty_bytes = b'\x00' * (canvas_size * canvas_size * 4)
            stroke_layer.setPixelData(empty_bytes, 0, 0, canvas_size, canvas_size)
        
        padding = int(canvas_size * 0.08)
        path = QPainterPath()
        
        if any(key in engine for key in ["spray", "airbrush"]):
            # Спрей делаем прямой линией ближе к центру, чтобы не плодить пыль по углам
            path.moveTo(QPointF(padding * 2, canvas_size / 2))
            path.lineTo(QPointF(canvas_size - padding * 2, canvas_size / 2))
        else:
            # Классическая волна для обычных кистей
            path.moveTo(QPointF(padding, canvas_size / 2))
            path.cubicTo(QPointF(canvas_size * 0.3, canvas_size * 0.25), 
                         QPointF(canvas_size * 0.7, canvas_size * 0.75), 
                         QPointF(canvas_size - padding, canvas_size / 2))
        
        steps = 80
        for i in range(steps):
            t1 = i / steps
            t2 = (i + 1) / steps
            pressure1 = max(0.01, math.sin(t1 * math.pi))
            pressure2 = max(0.01, math.sin(t2 * math.pi))
            stroke_layer.paintLine(path.pointAtPercent(t1).toPoint(), path.pointAtPercent(t2).toPoint(), pressure1, pressure2)
            
        doc.refreshProjection()
        doc.waitForDone()
        stroke_bytes = stroke_layer.pixelData(0, 0, canvas_size, canvas_size)
        
        # --- 2. РЕНДЕР КОНЧИКА КИСТИ (TIP) ---
        tip_layer = doc.createNode("Tip", "paintlayer")
        root.addChildNode(tip_layer, None)
        tip_layer.setPixelData(b'\x00' * (canvas_size * canvas_size * 4), 0, 0, canvas_size, canvas_size)
        
        # РАДИКАЛЬНОЕ РЕШЕНИЕ ДЛЯ КОНЧИКА:
        # Вместо 1 пикселя рисуем короткую плотную линию (30px).
        # Это "пробьет" ограничение Spacing (интервал) у любой кисти.
        center = QPointF(canvas_size / 2, canvas_size / 2)
        tip_layer.paintLine(
            QPointF(center.x() - 15, center.y()).toPoint(), 
            QPointF(center.x() + 15, center.y()).toPoint(), 
            1.0, 1.0
        )
        
        doc.refreshProjection()
        doc.waitForDone()
        tip_bytes = tip_layer.pixelData(0, 0, canvas_size, canvas_size)
        
    finally:
        doc.setModified(False)
        doc.close()

    result = {'stroke': None, 'tip': None}
    
    if stroke_bytes and not all(b == 0 for b in stroke_bytes):
        # Включаем жесткий режим форматирования пропорций (is_stroke=True)
        result['stroke'] = auto_crop_image(stroke_bytes, canvas_size, stroke_w, stroke_h, is_stroke=True)
        
    if tip_bytes and not all(b == 0 for b in tip_bytes):
        # Кончик вырезаем как есть (is_stroke=False)
        result['tip'] = auto_crop_image(tip_bytes, canvas_size, tip_size, tip_size, is_stroke=False)
        
    return result

class PreviewService:
    def __init__(self, state):
        self.state = state

    def request_preview(self, brush_name, width, height):
        pass