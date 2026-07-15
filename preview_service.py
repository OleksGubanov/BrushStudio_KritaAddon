import krita
import math
from PyQt5.QtGui import QImage, QPainter, QColor, QPainterPath, QBitmap, QRegion
from PyQt5.QtCore import Qt, QPointF, QRect

def auto_crop_image(img_bytes, canvas_size, target_width, target_height):
    """Преобразует байты в QImage, находит границы через QRegion и кадрирует"""
    original_img = QImage(img_bytes, canvas_size, canvas_size, QImage.Format_RGBA8888).copy()
    
    # Решение ошибки: используем QBitmap и QRegion для поиска границ
    alpha_mask = original_img.createAlphaMask()
    bitmap = QBitmap.fromImage(alpha_mask)
    region = QRegion(bitmap)
    bbox = region.boundingRect()
    
    if bbox.isNull() or bbox.isEmpty(): 
        return None
        
    pad = 15
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
            base_img = QImage(canvas_size, canvas_size, QImage.Format_RGBA8888)
            base_img.fill(Qt.transparent)
            p = QPainter(base_img)
            p.setPen(Qt.NoPen)
            r = int(canvas_size * 0.25)
            p.setBrush(QColor(255, 100, 100, 255)); p.drawEllipse(int(canvas_size * 0.25) - r//2, int(canvas_size//2) - r//2, r, r)
            p.setBrush(QColor(100, 255, 100, 255)); p.drawEllipse(int(canvas_size * 0.50) - r//2, int(canvas_size//2) - r//2, r, r)
            p.setBrush(QColor(100, 100, 255, 255)); p.drawEllipse(int(canvas_size * 0.75) - r//2, int(canvas_size//2) - r//2, r, r)
            p.end()
            ptr = base_img.constBits(); ptr.setsize(base_img.byteCount())
            stroke_layer.setPixelData(bytes(ptr), 0, 0, canvas_size, canvas_size)
        else:
            empty_bytes = b'\x00' * (canvas_size * canvas_size * 4)
            stroke_layer.setPixelData(empty_bytes, 0, 0, canvas_size, canvas_size)
        
        padding = int(canvas_size * 0.15)
        path = QPainterPath()
        path.moveTo(QPointF(padding, canvas_size / 2))
        path.cubicTo(QPointF(canvas_size * 0.3, canvas_size * 0.2), 
                     QPointF(canvas_size * 0.7, canvas_size * 0.8), 
                     QPointF(canvas_size - padding, canvas_size / 2))
        
        steps = 50
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
        
        # Рисуем одиночный клик (короткая линия для активации отпечатка)
        center = QPointF(canvas_size / 2, canvas_size / 2)
        tip_layer.paintLine(center.toPoint(), QPointF(center.x() + 1, center.y()).toPoint(), 1.0, 1.0)
        
        doc.refreshProjection()
        doc.waitForDone()
        tip_bytes = tip_layer.pixelData(0, 0, canvas_size, canvas_size)
        
    finally:
        doc.setModified(False)
        doc.close()

    result = {'stroke': None, 'tip': None}
    
    if stroke_bytes and not all(b == 0 for b in stroke_bytes):
        result['stroke'] = auto_crop_image(stroke_bytes, canvas_size, stroke_w, stroke_h)
        
    if tip_bytes and not all(b == 0 for b in tip_bytes):
        result['tip'] = auto_crop_image(tip_bytes, canvas_size, tip_size, tip_size)
        
    return result

class PreviewService:
    def __init__(self, state):
        self.state = state

    def request_preview(self, brush_name, width, height):
        pass