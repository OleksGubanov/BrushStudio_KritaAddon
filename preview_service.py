import krita
from PyQt5.QtGui import QImage, QPainter, QColor, QPainterPath, QBitmap, QRegion
from PyQt5.QtCore import Qt, QPointF, QRect

def auto_crop_image(original_img, target_width, target_height, padding=5):
    """Обрезает пустые пиксели и масштабирует мазок ровно по центру заданного холста"""
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
    if not window: return {"stroke": None, "tip": None}
    
    target_preset = app.resources("preset").get(brush_name)
    if not target_preset: return {"stroke": None, "tip": None}
    
    view = window.activeView()
    
    final_stroke_cropped = None
    final_tip_cropped = None
    original_size = None
    
    doc_tip = None
    doc_stroke = None

    try:
        view.setCurrentBrushPreset(target_preset)
        
        # 1. СТАРАЯ НАДЕЖНАЯ ЛОГИКА: Нормализация размера кисти, чтобы она не вылезала за холст
        if hasattr(target_preset, 'size'):
            original_size = target_preset.size()
            fixed_size = float(max(5, int(stroke_h * scale_coef)))
            target_preset.setSize(fixed_size)[cite: 8]

        black = krita.ManagedColor("RGBA", "U8", "")
        black.fromQColor(QColor(0, 0, 0, 255))
        view.setForeGroundColor(black)
        
        # --- ГЕНЕРАЦИЯ НАКОНЕЧНИКА (TIP) ---
        doc_tip = app.createDocument(int(tip_size), int(tip_size), "TipTemp", "RGBA", "U8", "", 120.0)
        window.addView(doc_tip)
        
        tip_layer = doc_tip.createNode("Tip", "paintlayer")
        doc_tip.rootNode().addChildNode(tip_layer, None)
        tip_layer.setPixelData(b'\x00' * (int(tip_size) * int(tip_size) * 4), 0, 0, int(tip_size), int(tip_size))
        
        center = QPointF(tip_size / 2, tip_size / 2)
        tip_layer.paintLine(
            QPointF(center.x() - 1, center.y()).toPoint(), 
            QPointF(center.x() + 1, center.y()).toPoint(), 
            1.0, 1.0
        )
        
        doc_tip.refreshProjection()
        doc_tip.waitForDone()
        tip_bytes = tip_layer.pixelData(0, 0, int(tip_size), int(tip_size))
        
        if tip_bytes and not all(b == 0 for b in tip_bytes):
            tip_img = QImage(tip_bytes, int(tip_size), int(tip_size), QImage.Format_RGBA8888)
            final_tip_cropped = auto_crop_image(tip_img, tip_size, tip_size, padding=2)
        
        doc_tip.setModified(False)
        doc_tip.close()
        doc_tip = None

        # --- ГЕНЕРАЦИЯ МАЗКА (STROKE) ---
        # Создаем холст чуть с запасом, функция auto_crop_image потом всё идеально обрежет
        draw_w = int(stroke_w * 1.5)
        draw_h = int(stroke_h * 2.0)
        
        doc_stroke = app.createDocument(draw_w, draw_h, "StrokeTemp", "RGBA", "U8", "", 120.0)
        window.addView(doc_stroke)
        
        stroke_layer = doc_stroke.createNode("Stroke", "paintlayer")
        doc_stroke.rootNode().addChildNode(stroke_layer, None)
        stroke_layer.setPixelData(b'\x00' * (draw_w * draw_h * 4), 0, 0, draw_w, draw_h)
        
        # 2. СТАРАЯ НАДЕЖНАЯ ЛОГИКА: Отрисовка красивой кривой с изменяющимся нажимом
        padding = int(draw_w * 0.08)
        path = QPainterPath()
        start_point = QPointF(padding, draw_h / 2)
        path.moveTo(start_point)
        
        control_point = QPointF(draw_w / 2, draw_h / 5)
        end_point = QPointF(draw_w - padding, draw_h / 2)
        path.quadTo(control_point, end_point)[cite: 8]
        
        stroke_layer.paintPath(path, "ForegroundColor", "None")[cite: 8]
        
        taper_len = int(draw_w * 0.05)
        taper_start_end = QPointF(padding + taper_len, (draw_h / 2) - 1) 
        stroke_layer.paintLine(start_point.toPoint(), taper_start_end.toPoint(), 0.5, 1.0)[cite: 8]
        
        taper_end_start = QPointF(draw_w - padding - taper_len, (draw_h / 2) - 1)
        stroke_layer.paintLine(taper_end_start.toPoint(), end_point.toPoint(), 1.0, 0.5)[cite: 8]
        
        doc_stroke.refreshProjection()
        doc_stroke.waitForDone()
        
        stroke_bytes = stroke_layer.pixelData(0, 0, draw_w, draw_h)
        
        if stroke_bytes and not all(b == 0 for b in stroke_bytes):
            stroke_img = QImage(stroke_bytes, draw_w, draw_h, QImage.Format_RGBA8888)
            final_stroke_cropped = auto_crop_image(stroke_img, stroke_w, stroke_h, padding=10)
            
        doc_stroke.setModified(False)
        doc_stroke.close()
        doc_stroke = None

    except Exception as e:
        print(f"[Brush Studio] Render Error: {e}")
    finally:
        # 3. СТАРАЯ НАДЕЖНАЯ ЛОГИКА: Гарантированная уборка мусора и закрытие документов!
        if target_preset and original_size is not None:
            target_preset.setSize(original_size)[cite: 8]
        
        # Если произошла ошибка, мы принудительно закрываем повисшие документы без всплывающих окон[cite: 8]
        if doc_tip:
            doc_tip.setModified(False)
            doc_tip.close()
        if doc_stroke:
            doc_stroke.setModified(False)
            doc_stroke.close()
            
    return {"stroke": final_stroke_cropped, "tip": final_tip_cropped}