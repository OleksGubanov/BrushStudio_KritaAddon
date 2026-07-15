import krita
from PyQt5.QtGui import QImage, QPainter, QColor, QPainterPath
from PyQt5.QtCore import Qt, QPointF, QPoint

def generate_brush_mask_sync(brush_name, width, height, scale_coef=0.4):
    app = krita.Krita.instance()
    window = app.activeWindow()
    if not window: return None

    # Создаем скрытый документ
    doc = app.createDocument(int(width), int(height), f"Test_{brush_name}", "RGBA", "U8", "", 120.0)
    window.addView(doc)
    view = window.activeView()
    
    original_size = None
    target_preset = app.resources("preset").get(brush_name)
    pixel_bytes = None
    
    try:
        if target_preset:
            view.setCurrentBrushPreset(target_preset)
            
            # --- 1. АДАПТИВНЫЙ РАЗМЕР КИСТИ ---
            if hasattr(target_preset, 'size'):
                original_size = target_preset.size()
                # Мягкое ограничение: не меньше 15px (чтобы видеть мелочь) 
                # и не больше 70% от высоты (чтобы гиганты влезали в кадр)
                fixed_size = float(max(15.0, min(original_size, height * 0.7)))
                target_preset.setSize(fixed_size)
        
        black = krita.ManagedColor("RGBA", "U8", "")
        black.fromQColor(QColor(0, 0, 0, 255))
        view.setForeGroundColor(black)
        
        root = doc.rootNode()
        paint_layer = doc.createNode("Stroke", "paintlayer")
        root.addChildNode(paint_layer, None)
        
        # --- 2. БАЗА ДЛЯ РАЗМАЗЫВАЮЩИХ (SMUDGE/BLEND) КИСТЕЙ ---
        engine = ""
        if target_preset:
            # Пытаемся получить ID движка через метод, если он существует
            if hasattr(target_preset, 'paintOpId'):
                engine = target_preset.paintOpId().lower()
            else:
                # Альтернативный способ определения движка через имя (строковое представление)
                # или если объект Resource ведет себя как имя/путь
                engine = str(target_preset.name()).lower()
        
        # Проверяем ключевые слова в названии или ID
        needs_base = any(key in engine for key in ["smudge", "deform", "blend", "liquify"])
        
        if needs_base:
            # Создаем "кляксы", которые кисть будет размазывать
            base_img = QImage(int(width), int(height), QImage.Format_RGBA8888)
            base_img.fill(Qt.transparent)
            p = QPainter(base_img)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 255))
            
            # Рисуем три круга по пути следования мазка
            r = int(height * 0.35)
            p.drawEllipse(int(width * 0.25) - r//2, int(height//2) - r//2, r, r)
            p.drawEllipse(int(width * 0.50) - r//2, int(height//2) - r//2, r, r)
            p.drawEllipse(int(width * 0.75) - r//2, int(height//2) - r//2, r, r)
            p.end()
            
            # Безопасный перенос байтов из QImage в слой Krita
            ptr = base_img.constBits()
            ptr.setsize(base_img.byteCount())
            paint_layer.setPixelData(bytes(ptr), 0, 0, int(width), int(height))
        else:
            # Обычный пустой прозрачный слой для рисующих кистей
            empty_bytes = b'\x00' * (int(width) * int(height) * 4)
            paint_layer.setPixelData(empty_bytes, 0, 0, int(width), int(height))
        
        # --- 3. СЛОЖНЫЙ ПУТЬ МАЗКА (S-кривая для показа динамики/разброса) ---
        padding = int(width * 0.08)
        path = QPainterPath()
        start_point = QPointF(padding, height / 2)
        path.moveTo(start_point)
        
        # S-образная кривая с помощью кубического Безье (лучше показывает форму)
        cp1 = QPointF(width * 0.3, height * 0.1)
        cp2 = QPointF(width * 0.7, height * 0.9)
        end_point = QPointF(width - padding, height / 2)
        path.cubicTo(cp1, cp2, end_point)
        
        paint_layer.paintPath(path, "ForegroundColor", "None")
        
        # Кончики мазка (плавный нажим)
        taper_len = int(width * 0.05)
        taper_start = QPointF(padding + taper_len, (height / 2) - 1) 
        paint_layer.paintLine(start_point.toPoint(), taper_start.toPoint(), 0.5, 1.0)
        
        taper_end = QPointF(width - padding - taper_len, (height / 2) - 1)
        paint_layer.paintLine(taper_end.toPoint(), end_point.toPoint(), 1.0, 0.5)
        
        doc.refreshProjection()
        doc.waitForDone()
        
        pixel_bytes = paint_layer.pixelData(0, 0, int(width), int(height))
        
    finally:
        # Обязательно возвращаем кисти ее оригинальный размер!
        if target_preset and original_size is not None:
            target_preset.setSize(original_size)
        doc.setModified(False)
        doc.close()

    if not pixel_bytes or all(b == 0 for b in pixel_bytes): return None
        
    # Превращаем результат в чисто белую маску на прозрачном фоне
    original_img = QImage(pixel_bytes, int(width), int(height), QImage.Format_RGBA8888).copy()
    
    white_stroke = QImage(int(width), int(height), QImage.Format_ARGB32_Premultiplied)
    white_stroke.fill(Qt.transparent)
    
    p1 = QPainter(white_stroke)
    p1.drawImage(0, 0, original_img)
    p1.setCompositionMode(QPainter.CompositionMode_SourceIn)
    p1.fillRect(white_stroke.rect(), Qt.white)
    p1.end()
    
    return white_stroke

class PreviewService:
    def __init__(self, state):
        self.state = state

    def request_preview(self, brush_name, width, height):
        pass