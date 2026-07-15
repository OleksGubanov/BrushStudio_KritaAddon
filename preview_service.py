import krita
from PyQt5.QtGui import QImage, QPainter, QColor, QPainterPath, QBitmap, QRegion
from PyQt5.QtCore import Qt, QPointF, QRect
from PyQt5.QtWidgets import QApplication

def auto_crop_image(original_img, target_width, target_height, padding=50):
    """Crops by alpha channel with padding, then packs into a fixed size canvas."""
    alpha_mask = original_img.createAlphaMask()
    bitmap = QBitmap.fromImage(alpha_mask)
    region = QRegion(bitmap)
    bbox = region.boundingRect()
    
    if bbox.isNull() or bbox.isEmpty(): 
        return None
        
    bbox.adjust(-padding, -padding, padding, padding)
    bbox = bbox.intersected(original_img.rect())
    
    cropped_img = original_img.copy(bbox)
    
    scaled_img = cropped_img.scaled(int(target_width), int(target_height), Qt.KeepAspectRatio, Qt.SmoothTransformation)
    
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
    final_tip_cropped = None
    
    try:
        if target_preset:
            view = window.activeView()
            view.setCurrentBrushPreset(target_preset)
        
        black = krita.ManagedColor("RGBA", "U8", "")
        black.fromQColor(QColor(0, 0, 0, 255))
        view.setForeGroundColor(black)
        
        doc = app.createDocument(int(tip_size), int(tip_size), "TipTemp", "RGBA", "U8", "", 120.0)
        app.activeWindow().addView(doc)
        
        root = doc.rootNode()
        tip_layer = doc.createNode("Tip", "paintlayer")
        root.addChildNode(tip_layer, None)
        tip_layer.setPixelData(b'\x00' * (tip_size * tip_size * 4), 0, 0, tip_size, tip_size)
        
        center = QPointF(tip_size / 2, tip_size / 2)
        tip_layer.paintLine(
            QPointF(center.x() - 1, center.y()).toPoint(), 
            QPointF(center.x() + 1, center.y()).toPoint(), 
            1.0, 1.0
        )
        
        doc.refreshProjection()
        doc.waitForDone()
        tip_bytes = tip_layer.pixelData(0, 0, tip_size, tip_size)
        
        if tip_bytes and not all(b == 0 for b in tip_bytes):
            tip_img = QImage(tip_bytes, tip_size, tip_size, QImage.Format_RGBA8888)
            final_tip_cropped = auto_crop_image(tip_img, tip_size, tip_size, padding=2)
        
        doc.setModified(False)    
        doc.close()
        
        current_w = stroke_w
        current_h = stroke_h
        
        for iteration in range(max_iterations):
            s_doc = app.createDocument(int(current_w), int(current_h), "StrokeTemp", "RGBA", "U8", "", 120.0)
            app.activeWindow().addView(s_doc)
            s_root = s_doc.rootNode()
            stroke_layer = s_doc.createNode("Stroke", "paintlayer")
            s_root.addChildNode(stroke_layer, None)
            stroke_layer.setPixelData(b'\x00' * (current_w * current_h * 4), 0, 0, current_w, current_h)
            
            base_draw_w = stroke_w * 0.8
            base_draw_h = stroke_h * 0.6
            
            path = QPainterPath()
            path.moveTo(current_w / 2 - base_draw_w / 2, current_h / 2 + base_draw_h / 2)
            path.cubicTo(current_w / 2 - base_draw_w * 0.2, current_h / 2 - base_draw_h / 2, 
                         current_w / 2 + base_draw_w * 0.2, current_h / 2 + base_draw_h / 2, 
                         current_w / 2 + base_draw_w / 2, current_h / 2 - base_draw_h / 2)
                         
            stroke_layer.paintPainterPath(path)
            
            s_doc.refreshProjection()
            s_doc.waitForDone()
            stroke_bytes = stroke_layer.pixelData(0, 0, current_w, current_h)
            
            # ИСПРАВЛЕНО: Снимаем флаг изменений именно с s_doc, а не с doc
            s_doc.setModified(False)
            s_doc.close()
            
            if not stroke_bytes or all(b == 0 for b in stroke_bytes):
                break
                
            stroke_img = QImage(stroke_bytes, current_w, current_h, QImage.Format_RGBA8888)
            alpha_mask = stroke_img.createAlphaMask()
            bbox = QRegion(QBitmap.fromImage(alpha_mask)).boundingRect()
            
            if bbox.isNull() or bbox.isEmpty():
                break
                
            safe_rect = QRect(safe_zone_padding, safe_zone_padding, 
                              current_w - 2 * safe_zone_padding, 
                              current_h - 2 * safe_zone_padding)
                              
            if not safe_rect.contains(bbox) and iteration < max_iterations - 1:
                current_w = int(current_w * canvas_modifier)
                current_h = int(current_h * canvas_modifier)
                continue
                
            final_stroke_cropped = auto_crop_image(stroke_img, stroke_w, stroke_h, padding=safe_zone_padding)
            break
            
    except Exception as e:
        print(f"[Brush Studio] Render Error: {e}")
        
    return {"stroke": final_stroke_cropped, "tip": final_tip_cropped}