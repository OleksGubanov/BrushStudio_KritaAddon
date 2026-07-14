import krita
from PyQt5.QtGui import QImage, QPainter, QColor, QPainterPath
from PyQt5.QtCore import Qt, QPointF, QPoint

def generate_brush_mask_sync(brush_name, width, height):
    """
    МАКСИМАЛЬНО ГРЯЗНЫЙ И ОТКРЫТЫЙ МЕТОД РЕНДЕРА.
    Создает видимый документ, рисует на нем и оставляет его открытым!
    """
    print(f"\n[Brush Studio] 🧨 НАЧАЛО ГРЯЗНОГО РЕНДЕРА: {brush_name}")
    app = krita.Krita.instance()
    window = app.activeWindow()
    
    if not window:
        print("[Brush Studio] ❌ Ошибка: Нет активного окна Krita.")
        return None

    # 1. СОЗДАЕМ ДОКУМЕНТ ОТКРЫТО
    doc = app.createDocument(int(width), int(height), f"Test_{brush_name}", "RGBA", "U8", "", 120.0)
    
    # 2. ВАЖНО: ДОБАВЛЯЕМ ЕГО В ИНТЕРФЕЙС
    window.addView(doc)
    print(f"[Brush Studio] 👁 Документ 'Test_{brush_name}' открыт в интерфейсе.")
    
    view = window.activeView()
    
    # 3. ПЕРЕКЛЮЧАЕМ КИСТЬ И ЦВЕТ
    target_preset = app.resources("preset").get(brush_name)
    if target_preset:
        view.setCurrentBrushPreset(target_preset)
        print("[Brush Studio] ✅ Кисть переключена.")
        
    black = krita.ManagedColor("RGBA", "U8", "")
    black.fromQColor(QColor(0, 0, 0, 255))
    view.setForeGroundColor(black)
    
    # 4. СОЗДАЕМ И ДОБАВЛЯЕМ СЛОЙ
    root = doc.rootNode()
    paint_layer = doc.createNode("Stroke", "paintlayer")
    root.addChildNode(paint_layer, None)
    
    # 5. ОЧИСТКА И ОТРИСОВКА ЧЕРЕЗ QPainterPath
    empty_bytes = b'\x00' * (int(width) * int(height) * 4)
    paint_layer.setPixelData(empty_bytes, 0, 0, int(width), int(height))
    
    # Создаем путь
    path = QPainterPath()
    start_point = QPointF(10, height / 2)
    path.moveTo(start_point)
    
    control_point = QPointF(width / 2, height / 4)
    end_point = QPointF(width - 10, height / 2)
    path.quadTo(control_point, end_point)
    
    print("[Brush Studio] ✍ Вызываем paintPath...")
    paint_layer.paintPath(path, "ForegroundColor", "None")
    
    # Имитация сужающихся кончиков (Давление)
    print("[Brush Studio] ✍ Добавляем Taper (низкое давление) по краям...")
    
    # Taper в начале (легкое касание)
    taper_start_end = QPointF(15, (height / 2) - 2) 
    # ИСПРАВЛЕНИЕ: Используем .toPoint() для конвертации QPointF -> QPoint
    paint_layer.paintLine(start_point.toPoint(), taper_start_end.toPoint(), 0.1, 1.0)
    
    # Taper в конце (отрыв кисти)
    taper_end_start = QPointF(width - 15, (height / 2) - 2)
    # ИСПРАВЛЕНИЕ: Используем .toPoint()
    paint_layer.paintLine(taper_end_start.toPoint(), end_point.toPoint(), 0.1, 1.0)
    
    # 6. ПРИНУДИТЕЛЬНО ОБНОВЛЯЕМ ЭКРАН И ЖДЕМ
    doc.refreshProjection()
    doc.waitForDone()
    
    # 7. ЧИТАЕМ ПИКСЕЛИ
    pixel_bytes = paint_layer.pixelData(0, 0, int(width), int(height))
    is_empty = all(b == 0 for b in pixel_bytes)
    
    print(f"[Brush Studio] 📊 БУФЕР ПИКСЕЛЕЙ ПУСТ? -> {is_empty}")
    
    if is_empty:
        print("[Brush Studio] 🚨 ВЕРДИКТ: Krita отказывается рисовать путь в открытом документе!")
        return None
        
    # 8. СБИРАЕМ Ч/Б МАСКУ
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
    
    print("[Brush Studio] 🟢 УСПЕХ: Маска кривой сгенерирована!")
    return bw_mask

class PreviewService:
    def __init__(self, state):
        self.state = state

    def request_preview(self, brush_name, width, height):
        pass