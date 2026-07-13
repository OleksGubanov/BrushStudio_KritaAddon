import krita
from PyQt5.QtWidgets import (QDockWidget, QListWidget, QListWidgetItem, QWidget, 
                             QVBoxLayout, QHBoxLayout, QListView, QPushButton, 
                             QComboBox, QLabel, QFrame, QSpinBox, QStyledItemDelegate, QSizePolicy, QStyle)
from PyQt5.QtCore import Qt, QSize, QSettings, QRect
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor

# ==========================================
# СЛОЙ 1: STATE MANAGER (Хранитель состояния)
# ==========================================
class PanelState:
    def __init__(self):
        # QSettings привязывается к конфигурации Krita (сохраняется между сессиями)
        self.settings = QSettings("BrushStudio", "CompactPalette")
        self.load()

    def load(self):
        self.mode = self.settings.value("mode", "auto") # 'auto' или 'manual'
        self.manual_layout = self.settings.value("manual_layout", "vertical") # 'vertical', 'horizontal'
        self.main_divider = int(self.settings.value("main_divider", 2)) # Количество колонок/строк
        
        # Соотношение сторон (W к H)
        self.aspect_w = float(self.settings.value("aspect_w", 1.0))
        self.aspect_h = float(self.settings.value("aspect_h", 1.0))
        
        self.start_dir_vert = self.settings.value("start_dir_vert", "left") # 'left' или 'right'
        self.start_dir_horiz = self.settings.value("start_dir_horiz", "top") # 'top' или 'bottom'
        
        self.current_dock_area = Qt.RightDockWidgetArea # По умолчанию (вертикаль)
        self.is_floating = False

    def save(self):
        self.settings.setValue("mode", self.mode)
        self.settings.setValue("manual_layout", self.manual_layout)
        self.settings.setValue("main_divider", self.main_divider)
        self.settings.setValue("aspect_w", self.aspect_w)
        self.settings.setValue("aspect_h", self.aspect_h)
        self.settings.setValue("start_dir_vert", self.start_dir_vert)
        self.settings.setValue("start_dir_horiz", self.start_dir_horiz)

    def get_safe_ratio(self):
        """Возвращает коэффициент соотношения с учетом лимита в 10% разницы"""
        w = max(0.1, self.aspect_w)
        h = max(0.1, self.aspect_h)
        ratio = w / h
        # Диапазон безопасности: от 0.1 (1:10) до 10.0 (10:1)
        return max(0.1, min(ratio, 10.0))

    def get_effective_layout(self):
        """Определяет, какой режим сейчас реально работает"""
        if self.mode == "auto":
            if self.is_floating:
                return self.manual_layout # Фолбэк на ручной режим
            elif self.current_dock_area in (Qt.TopDockWidgetArea, Qt.BottomDockWidgetArea):
                return "horizontal"
            else:
                return "vertical"
        return self.manual_layout

# ==========================================
# СЛОЙ 2: DELEGATE (Отрисовка прямоугольного слота)
# ==========================================
class BrushItemDelegate(QStyledItemDelegate):
    """Делегат позволяет рисовать внутри слота что угодно (мазки, иконки, текст) 
    без искажения пропорций, заданных движком"""
    def paint(self, painter, option, index):
        painter.setRenderHint(QPainter.Antialiasing)
        rect = option.rect
        
        # Проверяем, выбран ли элемент (используем QStyle.State_Selected)
        is_selected = option.state & QStyle.State_Selected
        
        # 1. Отрисовка фона слота
        bg_color = QColor("#3A3A3A") if is_selected else QColor("#2D2D2D")
        painter.fillRect(rect, bg_color)
        
        # Отрисовка обводки при выборе
        if is_selected:
            painter.setPen(QColor("#0D99FF"))
            painter.drawRect(rect.adjusted(1, 1, -1, -1))
        
        # 2. Отрисовка иконки (центрируем внутри прямоугольника)
        icon = index.data(Qt.DecorationRole)
        if icon:
            # Для прототипа иконка занимает 80% от меньшей стороны
            size = min(rect.width(), rect.height()) * 0.8
            icon_rect = QRect(0, 0, int(size), int(size))
            icon_rect.moveCenter(rect.center())
            
            pixmap = icon.pixmap(int(size), int(size))
            painter.drawPixmap(icon_rect, pixmap)

# ==========================================
# СЛОЙ 3: MATH LAYOUT ENGINE (Движок сетки)
# ==========================================
class AdaptiveListWidget(QListWidget):
    def __init__(self, state_manager):
        super().__init__()
        self.state = state_manager
        self.padding = 6
        
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Static)
        self.setUniformItemSizes(True)
        self.setWordWrap(False)
        self.setSpacing(self.padding)
        
        # Подключаем наш умный рендер
        self.setItemDelegate(BrushItemDelegate())
        
        # Убираем дефолтные стили Криты
        self.setStyleSheet("QListWidget { background: transparent; border: none; }")

    def resizeEvent(self, event):
        """Вызывается каждый раз при изменении размера панели"""
        super().resizeEvent(event)
        self.recalculate_math()

    def recalculate_math(self):
        """Математическое вычисление абстрактных единиц"""
        effective_layout = self.state.get_effective_layout()
        ratio = self.state.get_safe_ratio()
        
        # Доступное внутреннее пространство (без скроллбара)
        viewport_w = self.viewport().width()
        viewport_h = self.viewport().height()
        
        div = max(1, self.state.main_divider)
        
        if effective_layout == "vertical":
            # Основной делитель - Колонки
            available_w = viewport_w - (self.padding * (div + 1))
            item_w = max(10, available_w // div)
            item_h = int(item_w / ratio)
            
            self.setFlow(QListView.LeftToRight) # Заполняет ряды, затем переносит вниз
            
            # Направление
            if self.state.start_dir_vert == "right":
                self.setLayoutDirection(Qt.RightToLeft)
            else:
                self.setLayoutDirection(Qt.LeftToRight)
                
        else:
            # Основной делитель - Строки (Горизонтальная панель)
            available_h = viewport_h - (self.padding * (div + 1))
            item_h = max(10, available_h // div)
            item_w = int(item_h * ratio)
            
            self.setFlow(QListView.TopToBottom) # Заполняет колонки, затем переносит вправо
            self.setLayoutDirection(Qt.LeftToRight) # Всегда LTR для горизонтали
            
            # Примечание: В Qt нет нативного потока "Снизу-вверх". 
            # Для реализации start_dir_horiz == "bottom" мы будем реверсировать 
            # сам список кистей в функции load_real_brushes.

        # Применяем идеальные рассчитанные габариты (Bounding Boxes)
        final_size = QSize(item_w, item_h)
        self.setGridSize(QSize(item_w + self.padding, item_h + self.padding))
        # Delegate сам подхватит этот размер для отрисовки

# ==========================================
# ОСНОВНОЙ ДОКЕР И UI НАСТРОЕК
# ==========================================
class SmartPanelDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brush Studio: Compact")
        self.state = PanelState()
        
        self.main_widget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Кнопка вызова настроек
        self.top_bar = QHBoxLayout()
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedSize(24, 24)
        self.btn_settings.clicked.connect(self.toggle_settings)
        self.btn_settings.setStyleSheet("QPushButton { background: transparent; color: #888; } QPushButton:hover { color: white; }")
        
        self.top_bar.addStretch()
        self.top_bar.addWidget(self.btn_settings)
        
        self.build_settings_ui()
        
        # Инициализация математического движка
        self.grid = AdaptiveListWidget(self.state)
        self.grid.itemClicked.connect(self.on_brush_clicked)
        
        # Отслеживание состояний окна (Сигналы Krita/Qt)
        self.dockLocationChanged.connect(self.on_dock_changed)
        self.topLevelChanged.connect(self.on_float_changed)
        
        self.layout.addLayout(self.top_bar)
        self.layout.addWidget(self.settings_frame)
        self.layout.addWidget(self.grid)
        self.main_widget.setLayout(self.layout)
        self.setWidget(self.main_widget)
        
        self.load_real_brushes()

    def build_settings_ui(self):
        """Интерфейс настроек, выпадающий по клику"""
        self.settings_frame = QFrame()
        self.settings_frame.setVisible(False)
        self.settings_frame.setStyleSheet("QFrame { background-color: #252525; border-bottom: 1px solid #444; } QLabel { color: #ccc; }")
        vbox = QVBoxLayout()
        
        # Режим
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["auto", "manual"])
        self.cmb_mode.setCurrentText(self.state.mode)
        self.cmb_mode.currentTextChanged.connect(self.on_settings_changed)
        
        # Ручная раскладка
        self.cmb_layout = QComboBox()
        self.cmb_layout.addItems(["vertical", "horizontal"])
        self.cmb_layout.setCurrentText(self.state.manual_layout)
        self.cmb_layout.currentTextChanged.connect(self.on_settings_changed)
        
        # Основной делитель
        self.spin_divider = QSpinBox()
        self.spin_divider.setRange(1, 10)
        self.spin_divider.setValue(self.state.main_divider)
        self.spin_divider.valueChanged.connect(self.on_settings_changed)
        
        # Соотношение сторон (Векторное поле W к H)
        aspect_layout = QHBoxLayout()
        self.spin_asp_w = QSpinBox()
        self.spin_asp_w.setRange(1, 1000)
        self.spin_asp_w.setValue(int(self.state.aspect_w))
        
        self.spin_asp_h = QSpinBox()
        self.spin_asp_h.setRange(1, 1000)
        self.spin_asp_h.setValue(int(self.state.aspect_h))
        
        self.spin_asp_w.valueChanged.connect(self.on_settings_changed)
        self.spin_asp_h.valueChanged.connect(self.on_settings_changed)
        
        aspect_layout.addWidget(self.spin_asp_w)
        aspect_layout.addWidget(QLabel(":"))
        aspect_layout.addWidget(self.spin_asp_h)
        
        # Направление (Динамически меняется)
        self.cmb_dir = QComboBox()
        self.cmb_dir.currentTextChanged.connect(self.on_dir_changed)
        
        vbox.addWidget(QLabel("Режим:"))
        vbox.addWidget(self.cmb_mode)
        vbox.addWidget(QLabel("Раскладка (Ручная):"))
        vbox.addWidget(self.cmb_layout)
        vbox.addWidget(QLabel("Разделитель (Кол-во):"))
        vbox.addWidget(self.spin_divider)
        vbox.addWidget(QLabel("Пропорции (Ширина : Высота):"))
        vbox.addLayout(aspect_layout)
        vbox.addWidget(QLabel("Начало:"))
        vbox.addWidget(self.cmb_dir)
        
        self.settings_frame.setLayout(vbox)
        self.update_settings_visibility()

    def update_settings_visibility(self):
        """Блокирует/скрывает поля в зависимости от режима"""
        is_manual = (self.cmb_mode.currentText() == "manual")
        self.cmb_layout.setEnabled(is_manual)
        
        # Обновляем список направлений в зависимости от эффективной раскладки
        self.cmb_dir.blockSignals(True)
        self.cmb_dir.clear()
        
        effective = "vertical" if not is_manual else self.cmb_layout.currentText()
        if effective == "vertical":
            self.cmb_dir.addItems(["left", "right"])
            self.cmb_dir.setCurrentText(self.state.start_dir_vert)
        else:
            self.cmb_dir.addItems(["top", "bottom"])
            self.cmb_dir.setCurrentText(self.state.start_dir_horiz)
            
        self.cmb_dir.blockSignals(False)

    def on_settings_changed(self):
        """Сохраняет параметры в State и запрашивает перерисовку у движка"""
        self.state.mode = self.cmb_mode.currentText()
        self.state.manual_layout = self.cmb_layout.currentText()
        self.state.main_divider = self.spin_divider.value()
        self.state.aspect_w = float(self.spin_asp_w.value())
        self.state.aspect_h = float(self.spin_asp_h.value())
        
        self.update_settings_visibility()
        self.state.save()
        self.grid.recalculate_math()
        
    def on_dir_changed(self, val):
        effective = self.state.get_effective_layout()
        if effective == "vertical":
            self.state.start_dir_vert = val
        else:
            self.state.start_dir_horiz = val
        self.state.save()
        self.load_real_brushes() # Перезагружаем кисти, если нужно инвертировать список для "Bottom"
        self.grid.recalculate_math()

    def toggle_settings(self):
        self.settings_frame.setVisible(not self.settings_frame.isVisible())

    # --- СИГНАЛЫ СОСТОЯНИЯ ОКНА ---
    def on_dock_changed(self, area):
        self.state.current_dock_area = area
        self.grid.recalculate_math()

    def on_float_changed(self, is_floating):
        self.state.is_floating = is_floating
        self.grid.recalculate_math()

    # --- ЗАГРУЗКА КИСТЕЙ ---
    def load_real_brushes(self):
        self.grid.clear()
        app = krita.Krita.instance()
        all_presets = list(app.resources("preset").items())[:30] # Берем 30 для теста
        
        # ХАК: Реализация направления "Снизу" для Горизонтальной раскладки
        # Qt не умеет строить сетку снизу-вверх, поэтому мы реверсируем сам массив.
        if self.state.get_effective_layout() == "horizontal" and self.state.start_dir_horiz == "bottom":
            all_presets.reverse()
            
        for name, preset in all_presets:
            icon = QIcon(QPixmap.fromImage(preset.image()))
            item = QListWidgetItem()
            item.setData(Qt.DecorationRole, icon)
            item.setData(Qt.UserRole, name)
            item.setToolTip(name)
            self.grid.addItem(item)

    def on_brush_clicked(self, item):
        preset_name = item.data(Qt.UserRole)
        app = krita.Krita.instance()
        action = app.action('KritaShape/KritaToolFreehand')
        if action: action.trigger()
        window = app.activeWindow()
        if window and window.activeView():
            preset = app.resources("preset").get(preset_name)
            if preset: window.activeView().setCurrentBrushPreset(preset)