import krita
import math
from PyQt5.QtGui import QImage, QPainter, QColor, QPainterPath, QBitmap, QRegion
from PyQt5.QtCore import Qt, QPointF, QRect

def auto_crop_image(original_img, target_width, target_height, padding=10):
    """Crops by alpha channel with padding, then packs into a fixed size canvas."""
    alpha_mask = original_img.createAlphaMask()
    bitmap = QBitmap.fromImage(alpha_mask)
    region = QRegion(bitmap)
    bbox = region.boundingRect()
    
    if bbox.isNull() or bbox.isEmpty(): 
        return None
        
    # Expand bbox to include the safe padding around the stroke
    bbox.adjust(-padding, -padding, padding, padding)
    bbox = bbox.intersected(original_img.rect())
    
    # Crop the raw stroke data
    cropped_img = original_img.copy(bbox)
    
    # Scale to fit target size while preserving aspect ratio
    scaled_img = cropped_img.scaled(int(target_width), int(target_height), Qt.KeepAspectRatio, Qt.SmoothTransformation)
    
    # Pack into uniform transparent canvas
    final_canvas = QImage(int(target_width), int(target_height), QImage.Format_RGBA8888)
    final_canvas.fill(Qt.transparent)
    
    painter = QPainter(final_canvas)
    x_offset = (final_canvas.width() - scaled_img.width()) // 2
    y_offset = (final_canvas.height() - scaled_img.height()) // 2
    painter.drawImage(x_offset, y_offset, scaled_img)
    painter.end()
    
    return final_canvas


def generate_brush_masks_sync(brush_name, stroke_w, stroke_h, tip_size, scale_coef=0.4, 
                              canvas_modifier=2.0, max_iterations=5, safe_zone_padding=50):
    app = krita.Krita.instance()
    window = app.activeWindow()
    if not window: return None
    
    target_preset = app.resources("preset").get(brush_name)
    final_stroke_cropped = None
    
    # 1. DYNAMIC STROKE RENDER
    current_canvas_size = 1024
    stroke_length = 800 
    
    for iteration in range(max_iterations):
        doc = app.createDocument(current_canvas_size, current_canvas_size, f"Test_Stroke_{brush_name}", "RGBA", "U8", "", 120.0)
        window.addView(doc)
        view = window.activeView()
        
        try:
            if target_preset:
                view.setCurrentBrushPreset(target_preset)
            
            black = krita.ManagedColor("RGBA", "U8", "")
            black.fromQColor(QColor(0, 0, 0, 255))
            view.setForeGroundColor(black)
            
            root = doc.rootNode()
            stroke_layer = doc.createNode("Stroke", "paintlayer")
            root.addChildNode(stroke_layer, None)
            stroke_layer.setPixelData(b'\x00' * (current_canvas_size * current_canvas_size * 4), 0, 0, current_canvas_size, current_canvas_size)
            
            engine = ""
            if target_preset:
                if hasattr(target_preset, 'paintOpId'): engine = target_preset.paintOpId().lower()
                else: engine = str(target_preset.name()).lower()
            
            if any(key in engine for key in ["smudge", "deform", "blend", "liquify"]):
                base_img = QImage(current_canvas_size, current_canvas_size, QImage.Format_RGBA8888)
                base_img.fill(Qt.transparent)
                p = QPainter(base_img)
                p.setPen(Qt.NoPen)
                r = int(stroke_length * 0.25)
                start_x = (current_canvas_size - stroke_length) / 2
                p.setBrush(QColor(255, 100, 100, 255)); p.drawEllipse(int(start_x + stroke_length * 0.25) - r//3, int(current_canvas_size//2) - r//3, r, r)
                p.setBrush(QColor(100, 255, 100, 255)); p.drawEllipse(int(start_x + stroke_length * 0.50) - r//3, int(current_canvas_size//2) - r//3, r, r)
                p.setBrush(QColor(100, 100, 255, 255)); p.drawEllipse(int(start_x + stroke_length * 0.75) - r//3, int(current_canvas_size//2) - r//3, r, r)
                p.end()
                ptr = base_img.constBits(); ptr.setsize(base_img.byteCount())
                stroke_layer.setPixelData(bytes(ptr), 0, 0, current_canvas_size, current_canvas_size)
            
            path = QPainterPath()
            start_x = (current_canvas_size - stroke_length) / 2
            end_x = start_x + stroke_length
            
            if any(key in engine for key in ["spray", "airbrush"]):
                path.moveTo(QPointF(start_x, current_canvas_size / 2))
                path.lineTo(QPointF(end_x, current_canvas_size / 2))
            else:
                path.moveTo(QPointF(start_x, current_canvas_size / 2))
                path.cubicTo(QPointF(start_x + stroke_length * 0.3, current_canvas_size / 2 - stroke_length * 0.25), 
                             QPointF(start_x + stroke_length * 0.7, current_canvas_size / 2 + stroke_length * 0.25), 
                             QPointF(end_x, current_canvas_size / 2))
            
            steps = 80
            for i in range(steps):
                t1 = i / steps
                t2 = (i + 1) / steps
                pressure1 = max(0.01, math.sin(t1 * math.pi))
                pressure2 = max(0.01, math.sin(t2 * math.pi))
                stroke_layer.paintLine(path.pointAtPercent(t1).toPoint(), path.pointAtPercent(t2).toPoint(), pressure1, pressure2)
                
            doc.refreshProjection()
            doc.waitForDone()
            stroke_bytes = stroke_layer.pixelData(0, 0, current_canvas_size, current_canvas_size)
            
            img = QImage(stroke_bytes, current_canvas_size, current_canvas_size, QImage.Format_RGBA8888).copy()
            alpha_mask = img.createAlphaMask()
            bbox = QRegion(QBitmap.fromImage(alpha_mask)).boundingRect()
            
            if bbox.isNull() or bbox.isEmpty():
                break 
                
            # Verify if stroke fits completely inside the safe zone boundaries
            safe_rect = QRect(
                safe_zone_padding, 
                safe_zone_padding, 
                current_canvas_size - safe_zone_padding * 2, 
                current_canvas_size - safe_zone_padding * 2
            )
            
            if safe_rect.contains(bbox) or iteration == max_iterations - 1:
                final_stroke_cropped = auto_crop_image(img, stroke_w, stroke_h, padding=safe_zone_padding)
                break
            else:
                current_canvas_size = int(current_canvas_size * canvas_modifier)
                
        finally:
            doc.setModified(False)
            doc.close()
            
    # 2. TIP RENDER
    tip_canvas = 1024
    doc = app.createDocument(tip_canvas, tip_canvas, f"Test_Tip_{brush_name}", "RGBA", "U8", "", 120.0)
    window.addView(doc)
    view = window.activeView()
    final_tip_cropped = None
    
    try:
        if target_preset:
            view.setCurrentBrushPreset(target_preset)
        
        black = krita.ManagedColor("RGBA", "U8", "")
        black.fromQColor(QColor(0, 0, 0, 255))
        view.setForeGroundColor(black)
        
        root = doc.rootNode()
        tip_layer = doc.createNode("Tip", "paintlayer")
        root.addChildNode(tip_layer, None)
        tip_layer.setPixelData(b'\x00' * (tip_canvas * tip_canvas * 4), 0, 0, tip_canvas, tip_canvas)
        
        center = QPointF(tip_canvas / 2, tip_canvas / 2)
        tip_layer.paintLine(
            QPointF(center.x() - 15, center.y()).toPoint(), 
            QPointF(center.x() + 15, center.y()).toPoint(), 
            1.0, 1.0
        )
        
        doc.refreshProjection()
        doc.waitForDone()
        tip_bytes = tip_layer.pixelData(0, 0, tip_canvas, tip_canvas)
        
        if tip_bytes and not all(b == 0 for b in tip_bytes):
            tip_img = QImage(tip_bytes, tip_canvas, tip_canvas, QImage.Format_RGBA8888).copy()
            final_tip_cropped = auto_crop_image(tip_img, tip_size, tip_size, padding=safe_zone_padding)
            
    finally:
        doc.setModified(False)
        doc.close()

    return {'stroke': final_stroke_cropped, 'tip': final_tip_cropped}

class PreviewService:
    def __init__(self, state):
        self.state = state

    def request_preview(self, brush_name, width, height):
        pass