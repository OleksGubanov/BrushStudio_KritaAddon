import krita
from PyQt5.QtGui import QImage, QPainter, QColor, QPainterPath
from PyQt5.QtCore import Qt, QPointF, QPoint

def generate_brush_mask_sync(brush_name, width, height, scale_coef=0.4):
    app = krita.Krita.instance()
    window = app.activeWindow()
    if not window: return None

    # Создаем скрытый документ фиксированного высокого разрешения
    doc = app.createDocument(int(width), int(height), f"Test_{brush_name}", "RGBA", "U8", "", 120.0)
    window.addView(doc)
    view = window.activeView()
    
    original_size = None
    target_preset = app.resources("preset").get(brush_name)
    pixel_bytes = None
    
    try:
        if target_preset:
            view.setCurrentBrushPreset(target_preset)
            
            # --- НОРМАЛИЗАЦИЯ КИСТИ И ТЕКСТУРЫ ---
            # Принудительно устанавливаем размер кисти в зависимости от высоты рендер-холста
            if hasattr(target_preset, 'size'):
                original_size = target_preset.size()
                normalized_size = max(5, int(height * scale_coef))
                target_preset.setSize(normalized_size)
        
        black = krita.ManagedColor("RGBA", "U8", "")
        black.fromQColor(QColor(0, 0, 0, 255))
        view.setForeGroundColor(black)
        
        root = doc.rootNode()
        paint_layer = doc.createNode("Stroke", "paintlayer")
        root.addChildNode(paint_layer, None)
        
        empty_bytes = b'\x00' * (int(width) * int(height) * 4)
        paint_layer.setPixelData(empty_bytes, 0, 0, int(width), int(height))
        
        # Оставляем больше отступа по краям для крупных мазков
        padding = int(width * 0.08)
        
        path = QPainterPath()
        start_point = QPointF(padding, height / 2)
        path.moveTo(start_point)
        
        control_point = QPointF(width / 2, height / 5)
        end_point = QPointF(width - padding, height / 2)
        path.quadTo(control_point, end_point)
        
        paint_layer.paintPath(path, "ForegroundColor", "None")
        
        # Длина сужения кончиков (taper)
        taper_len = int(width * 0.05)
        taper_start_end = QPointF(padding + taper_len, (height / 2) - 1) 
        paint_layer.paintLine(start_point.toPoint(), taper_start_end.toPoint(), 0.1, 1.0)
        
        taper_end_start = QPointF(width - padding - taper_len, (height / 2) - 1)
        paint_layer.paintLine(taper_end_start.toPoint(), end_point.toPoint(), 1.0, 0.1)
        
        doc.refreshProjection()
        doc.waitForDone()
        
        pixel_bytes = paint_layer.pixelData(0, 0, int(width), int(height))
        
    finally:
        # Восстанавливаем оригинальный размер
        if target_preset and original_size is not None:
            target_preset.setSize(original_size)
        # Убираем флаг "изменено", чтобы Krita не спрашивала "Сохранить ли?"
        doc.setModified(False)
        doc.close()

    if not pixel_bytes or all(b == 0 for b in pixel_bytes): return None
        
    # Сборка Ч/Б Маски
    original_img = QImage(pixel_bytes, int(width), int(height), QImage.Format_RGBA8888).copy()
    white_stroke = QImage(int(width), int(height), QImage.Format_ARGB32_Premultiplied)
    white_stroke.fill(Qt.transparent)
    
    p1 = QPainter(white_stroke)
    p1.drawImage(0, 0, original_img)
    p1.setCompositionMode(QPainter.CompositionMode_SourceIn)
    p1.fillRect(white_stroke.rect(), Qt.white)
    p1.end()
    
    bw_mask = QImage(int(width), int(height), QImage.Format_RGB32)
    bw_mask.fill(Qt.black)
    
    p2 = QPainter(bw_mask)
    p2.drawImage(0, 0, white_stroke)
    p2.end()
    
    return bw_mask

class PreviewService:
    def __init__(self, state):
        self.state = state

    def request_preview(self, brush_name, width, height):
        pass