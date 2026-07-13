import krita
from PyQt5.QtWidgets import (QDockWidget, QListWidget, QListWidgetItem, QWidget, 
                             QVBoxLayout, QHBoxLayout, QListView, QPushButton, 
                             QComboBox, QLabel, QFrame, QSpinBox, QStyledItemDelegate, 
                             QSizePolicy, QStyle, QMenu, QWidgetAction)
from PyQt5.QtCore import Qt, QSize, QSettings, QRect, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen

# ==========================================
# СЛОЙ 1: STATE MANAGER
# ==========================================
class PanelState:
    def __init__(self):
        self.settings = QSettings("BrushStudio", "CompactPalette")
        self.load()

    def load(self):
        self.mode = self.settings.value("mode", "auto")
        self.manual_layout = self.settings.value("manual_layout", "vertical")
        self.main_divider = int(self.settings.value("main_divider", 3))
        self.aspect_w = float(self.settings.value("aspect_w", 3.0)) # По умолчанию длинные плашки 3:1
        self.aspect_h = float(self.settings.value("aspect_h", 1.0))
        self.start_dir_vert = self.settings.value("start_dir_vert", "left")
        self.start_dir_horiz = self.settings.value("start_dir_horiz", "top")
        self.current_dock_area = Qt.RightDockWidgetArea
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
        w = max(0.1, self.aspect_w)
        h = max(0.1, self.aspect_h)
        return max(0.1, min(w / h, 10.0))

    def get_effective_layout(self):
        if self.mode == "auto":
            if self.is_floating:
                return self.manual_layout
            elif self.current_dock_area in (Qt.TopDockWidgetArea, Qt.BottomDockWidgetArea):
                return "horizontal"
            else:
                return "vertical"
        return self.manual_layout

# ==========================================
# СЛОЙ 2: DELEGATE (Отрисовка кнопки)
# ==========================================
class BrushItemDelegate(QStyledItemDelegate):
    def __init__(self, padding=3):
        super().__init__()
        self.padding = padding # Внутренний отступ между слотами

    def paint(self, painter, option, index):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Получаем математический бокс от движка и вычитаем отступы (padding)
        # Это дает нам идеальные промежутки без использования кривого spacing-а в Qt
        rect = option.rect.adjusted(self.padding, self.padding, -self.padding, -self.padding)
        
        is_selected = option.state & QStyle.State_Selected
        is_hovered = option.state & QStyle.State_MouseOver

        # 1. Заливка слота (Фон)
        if is_selected:
            bg_color = QColor("#3D5A80") # Акцентный цвет выделения
        elif is_hovered:
            bg_color = QColor("#383838") # Цвет при наведении
        else:
            bg_color = QColor("#2A2A2A") # Базовый цвет слота
            
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        # Рисуем скругленный прямоугольник (весь слот целиком)
        painter.drawRoundedRect(rect, 6, 6)
        
        # Обводка при выделении
        if is_selected:
            painter.setPen(QPen(QColor("#98C1D9"), 2))
            painter.drawRoundedRect(rect, 6, 6)

        # 2. Отрисовка Иконки (Умное позиционирование)
        icon = index.data(Qt.DecorationRole)
        if icon:
            # Иконка всегда квадратная, ее размер = 80% от меньшей стороны слота
            icon_side = min(rect.width(), rect.height()) * 0.8
            icon_rect = QRect(0, 0, int(icon_side), int(icon_side))
            
            # Логика Flexbox-позиционирования
            if rect.width() > rect.height() * 1.5:
                # Если это прямоугольник (ширина сильно больше высоты) -> прижимаем влево
                icon_rect.moveCenter(QPoint(rect.left() + int(rect.height() / 2), rect.center().y()))
            elif rect.height() > rect.width() * 1.5:
                # Если вертикальный прямоугольник -> прижимаем наверх
                icon_rect.moveCenter(QPoint(rect.center().x(), rect.top() + int(rect.width() / 2)))
            else:
                # Если почти квадрат -> по центру
                icon_rect.moveCenter(rect.center())
            
            pixmap = icon.pixmap(int(icon_side), int(icon_side))
            painter.drawPixmap(icon_rect, pixmap)

# ==========================================
# СЛОЙ 3: MATH LAYOUT ENGINE (Без дерганий)
# ==========================================
class AdaptiveListWidget(QListWidget):
    def __init__(self, state_manager):
        super().__init__()
        self.state = state_manager
        self._last_w = 0
        self._last_h = 0
        
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Static)
        self.setUniformItemSizes(True)
        self.setWordWrap(False)
        self.setSpacing(0) # ВАЖНО: Отключаем отступы Qt, всё считает Delegate
        
        self.setItemDelegate(BrushItemDelegate(padding=3))
        self.setStyleSheet("QListWidget { background: transparent; border: none; }")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.recalculate_math()

    def recalculate_math(self):
        w = self.viewport().width()
        h = self.viewport().height()
        
        # Предохранитель от петли ресайза (Моргания)
        if abs(w - self._last_w) < 2 and abs(h - self._last_h) < 2:
            return
        self._last_w = w
        self._last_h = h

        effective_layout = self.state.get_effective_layout()
        ratio = self.state.get_safe_ratio()
        div = max(1, self.state.main_divider)
        
        # Получаем ширину системного скроллбара
        scroll_w = self.style().pixelMetric(QStyle.PM_ScrollBarExtent)

        if effective_layout == "vertical":
            # Жестко включаем скролл, чтобы ширина не прыгала
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            # Математика: Доступная ширина = полная ширина - скроллбар
            available_w = self.width() - scroll_w - 4
            item_w = available_w / div
            item_h = item_w / ratio
            
            self.setFlow(QListView.LeftToRight)
            if self.state.start_dir_vert == "right":
                self.setLayoutDirection(Qt.RightToLeft)
            else:
                self.setLayoutDirection(Qt.LeftToRight)
        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            
            available_h = self.height() - scroll_w - 4
            item_h = available_h / div
            item_w = item_h * ratio
            
            self.setFlow(QListView.TopToBottom)
            self.setLayoutDirection(Qt.LeftToRight)

        # Передаем идеальные значения (с плавающей точкой) в сетку
        self.setGridSize(QSize(int(item_w), int(item_h)))

# ==========================================
# ОСНОВНОЙ ДОКЕР И ПЛАВАЮЩИЙ POP-UP
# ==========================================
class SmartPanelDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brush Studio")
        self.state = PanelState()
        
        self.main_widget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Верхний бар с кнопкой
        self.top_bar = QWidget()
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(4, 4, 4, 0)
        
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedSize(24, 24)
        self.btn_settings.setStyleSheet("""
            QPushButton { background: transparent; color: #888; border: none; font-size: 16px; }
            QPushButton:hover { color: white; }
        """)
        self.btn_settings.clicked.connect(self.show_popup_settings)
        
        top_layout.addStretch()
        top_layout.addWidget(self.btn_settings)
        self.top_bar.setLayout(top_layout)
        
        # Создаем настоящее плавающее меню (Pop-up)
        self.build_popup_menu()
        
        # Инициализация сетки
        self.grid = AdaptiveListWidget(self.state)
        self.grid.itemClicked.connect(self.on_brush_clicked)
        
        self.dockLocationChanged.connect(self.on_dock_changed)
        self.topLevelChanged.connect(self.on_float_changed)
        
        self.layout.addWidget(self.top_bar)
        self.layout.addWidget(self.grid)
        self.main_widget.setLayout(self.layout)
        self.setWidget(self.main_widget)
        
        self.load_real_brushes()

    def build_popup_menu(self):
        """Создает настоящее плавающее меню через QMenu"""
        self.settings_menu = QMenu(self)
        self.settings_menu.setStyleSheet("""
            QMenu { background-color: #2D2D2D; border: 1px solid #555; border-radius: 8px; }
        """)
        
        # Виджет, который будет внутри поп-апа
        settings_widget = QWidget()
        vbox = QVBoxLayout()
        vbox.setContentsMargins(10, 10, 10, 10)
        
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["auto", "manual"])
        self.cmb_mode.setCurrentText(self.state.mode)
        self.cmb_mode.currentTextChanged.connect(self.on_settings_changed)
        
        self.cmb_layout = QComboBox()
        self.cmb_layout.addItems(["vertical", "horizontal"])
        self.cmb_layout.setCurrentText(self.state.manual_layout)
        self.cmb_layout.currentTextChanged.connect(self.on_settings_changed)
        
        self.spin_divider = QSpinBox()
        self.spin_divider.setRange(1, 10)
        self.spin_divider.setValue(self.state.main_divider)
        self.spin_divider.valueChanged.connect(self.on_settings_changed)
        
        aspect_layout = QHBoxLayout()
        self.spin_asp_w = QSpinBox()
        self.spin_asp_w.setRange(1, 100)
        self.spin_asp_w.setValue(int(self.state.aspect_w))
        self.spin_asp_h = QSpinBox()
        self.spin_asp_h.setRange(1, 100)
        self.spin_asp_h.setValue(int(self.state.aspect_h))
        self.spin_asp_w.valueChanged.connect(self.on_settings_changed)
        self.spin_asp_h.valueChanged.connect(self.on_settings_changed)
        
        aspect_layout.addWidget(self.spin_asp_w)
        aspect_layout.addWidget(QLabel(":"))
        aspect_layout.addWidget(self.spin_asp_h)
        
        self.cmb_dir = QComboBox()
        self.cmb_dir.currentTextChanged.connect(self.on_dir_changed)
        
        # Добавляем элементы в виджет с белым текстом
        style_lbl = "color: #EEE;"
        
        lbl1 = QLabel("Режим:"); lbl1.setStyleSheet(style_lbl); vbox.addWidget(lbl1)
        vbox.addWidget(self.cmb_mode)
        
        self.lbl_layout = QLabel("Раскладка:"); self.lbl_layout.setStyleSheet(style_lbl); vbox.addWidget(self.lbl_layout)
        vbox.addWidget(self.cmb_layout)
        
        lbl3 = QLabel("Разделитель:"); lbl3.setStyleSheet(style_lbl); vbox.addWidget(lbl3)
        vbox.addWidget(self.spin_divider)
        
        lbl4 = QLabel("Пропорции:"); lbl4.setStyleSheet(style_lbl); vbox.addWidget(lbl4)
        vbox.addLayout(aspect_layout)
        
        lbl5 = QLabel("Начало:"); lbl5.setStyleSheet(style_lbl); vbox.addWidget(lbl5)
        vbox.addWidget(self.cmb_dir)
        
        settings_widget.setLayout(vbox)
        
        # Превращаем виджет в экшен и кладем в меню
        action = QWidgetAction(self.settings_menu)
        action.setDefaultWidget(settings_widget)
        self.settings_menu.addAction(action)
        
        self.update_settings_visibility()

    def update_settings_visibility(self):
        is_manual = (self.cmb_mode.currentText() == "manual")
        self.cmb_layout.setVisible(is_manual)
        self.lbl_layout.setVisible(is_manual)
        
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

    def show_popup_settings(self):
        """Открывает меню точно под шестеренкой"""
        pos = self.btn_settings.mapToGlobal(QPoint(0, self.btn_settings.height()))
        self.settings_menu.exec_(pos)

    def on_settings_changed(self):
        self.state.mode = self.cmb_mode.currentText()
        self.state.manual_layout = self.cmb_layout.currentText()
        self.state.main_divider = self.spin_divider.value()
        self.state.aspect_w = float(self.spin_asp_w.value())
        self.state.aspect_h = float(self.spin_asp_h.value())
        
        self.update_settings_visibility()
        self.state.save()
        self.grid.recalculate_math()
        
    def on_dir_changed(self, val):
        if self.state.get_effective_layout() == "vertical":
            self.state.start_dir_vert = val
        else:
            self.state.start_dir_horiz = val
        self.state.save()
        self.load_real_brushes()
        self.grid.recalculate_math()

    def on_dock_changed(self, area):
        self.state.current_dock_area = area
        self.grid.recalculate_math()

    def on_float_changed(self, is_floating):
        self.state.is_floating = is_floating
        self.grid.recalculate_math()

    def load_real_brushes(self):
        self.grid.clear()
        app = krita.Krita.instance()
        all_presets = list(app.resources("preset").items())[:30]
        
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
        
        # 1. Принудительно включаем инструмент кисти
        action = app.action('KritaShape/KritaToolFreehand')
        if action: 
            action.trigger()
            
        # 2. Вызов пресета
        window = app.activeWindow()
        if window and window.activeView():
            preset = app.resources("preset").get(preset_name)
            if preset: 
                window.activeView().setCurrentBrushPreset(preset)