import krita
import math
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
                
                # ИСПРАВЛЕНИЕ 1: Уменьшаем макс. порог с 70% до 45%. 
                # Для мягких кистей (Airbrush) их градиент значительно шире базового размера.
                max_allowed_size = height * 0.45
                fixed_size = float(max(15.0, min(original_size, max_allowed_size)))
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
            if hasattr(target_preset, 'paintOpId'):
                engine = target_preset.paintOpId().lower()
            else:
                engine = str(target_preset.name()).lower()
        
        needs_base = any(key in engine for key in ["smudge", "deform", "blend", "liquify"])
        
        if needs_base:
            base_img = QImage(int(width), int(height), QImage.Format_RGBA8888)
            base_img.fill(Qt.transparent)
            p = QPainter(base_img)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 255))
            
            r = int(height * 0.35)
            p.drawEllipse(int(width * 0.25) - r//2, int(height//2) - r//2, r, r)
            p.drawEllipse(int(width * 0.50) - r//2, int(height//2) - r//2, r, r)
            p.drawEllipse(int(width * 0.75) - r//2, int(height//2) - r//2, r, r)
            p.end()
            
            ptr = base_img.constBits()
            ptr.setsize(base_img.byteCount())
            paint_layer.setPixelData(bytes(ptr), 0, 0, int(width), int(height))
        else:
            empty_bytes = b'\x00' * (int(width) * int(height) * 4)
            paint_layer.setPixelData(empty_bytes, 0, 0, int(width), int(height))
        
        # --- 3. СЛОЖНЫЙ ПУТЬ МАЗКА С ИМИТАЦИЕЙ ДАВЛЕНИЯ ПЕРА ---
        padding = int(width * 0.08)
        path = QPainterPath()
        start_point = QPointF(padding, height / 2)
        path.moveTo(start_point)
        
        # ИСПРАВЛЕНИЕ 2: Сжимаем контрольные точки ближе к центру по высоте.
        # Раньше было 0.1 и 0.9, из-за чего кисть билась о верхний и нижний края холста.
        cp1 = QPointF(width * 0.3, height * 0.25)
        cp2 = QPointF(width * 0.7, height * 0.75)
        end_point = QPointF(width - padding, height / 2)
        path.cubicTo(cp1, cp2, end_point)
        
        # ИСПРАВЛЕНИЕ 3: Полноценное давление.
        # Разбиваем путь на 50 сегментов. Высчитываем точку на кривой Безье
        # и применяем давление по форме синусоиды (плавный нажим и отпускание).
        steps = 50
        for i in range(steps):
            t1 = i / steps
            t2 = (i + 1) / steps
            
            pt1 = path.pointAtPercent(t1)
            pt2 = path.pointAtPercent(t2)
            
            # math.sin(t * math.pi) дает идеальную дугу: от 0.0 в начале, до 1.0 в середине, и обратно к 0.0
            pressure1 = max(0.01, math.sin(t1 * math.pi))
            pressure2 = max(0.01, math.sin(t2 * math.pi))
            
            # Отрисовываем микро-линии с реальным давлением на каждом этапе
            paint_layer.paintLine(pt1.toPoint(), pt2.toPoint(), pressure1, pressure2)
        
        doc.refreshProjection()
        doc.waitForDone()
        
        pixel_bytes = paint_layer.pixelData(0, 0, int(width), int(height))
        
    finally:
        if target_preset and original_size is not None:
            target_preset.setSize(original_size)
        doc.setModified(False)
        doc.close()

    if not pixel_bytes or all(b == 0 for b in pixel_bytes): return None
        
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