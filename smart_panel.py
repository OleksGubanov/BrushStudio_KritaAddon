import krita
from PyQt5.QtWidgets import (QDockWidget, QListWidget, QListWidgetItem, QWidget, 
                             QVBoxLayout, QHBoxLayout, QListView, QPushButton, 
                             QSlider, QLabel, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap

class SmartPanelDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        # Задел под Brush Studio
        self.setWindowTitle("Brush Studio: Compact")
        
        # --- Базовые параметры (Аналог SceneProps из Blender) ---
        self.icon_size = 50
        self.padding = 8
        self.is_horizontal_flow = True
        self.is_inverted = False # Для смены направления (Слева-Направо / Справа-Налево)
        
        self.main_widget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        # --- 1. ВЕРХНЯЯ ПАНЕЛЬ УПРАВЛЕНИЯ (Минималистичная) ---
        self.top_bar = QHBoxLayout()
        self.top_bar.setContentsMargins(0, 0, 0, 0)
        self.top_bar.addStretch() # Прижимаем кнопки вправо
        
        # Кнопка свитчера направления (Tab-style)
        self.btn_flow = QPushButton("⭾") 
        self.btn_flow.setFixedSize(24, 24)
        self.btn_flow.setToolTip("Переключить направление раскладки")
        self.btn_flow.clicked.connect(self.toggle_flow)
        
        # Кнопка настроек
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedSize(24, 24)
        self.btn_settings.setToolTip("Настройки панели")
        self.btn_settings.clicked.connect(self.toggle_settings)
        
        self.top_bar.addWidget(self.btn_flow)
        self.top_bar.addWidget(self.btn_settings)
        
        # --- 2. ВЫПАДАЮЩАЯ ПАНЕЛЬ НАСТРОЕК (Скрыта по умолчанию) ---
        self.settings_frame = QFrame()
        self.settings_frame.setVisible(False) # Скрываем
        self.settings_layout = QVBoxLayout()
        self.settings_layout.setContentsMargins(5, 5, 5, 5)
        
        self.lbl_size = QLabel(f"Размер кисти: {self.icon_size}px")
        self.slider_size = QSlider(Qt.Horizontal)
        self.slider_size.setRange(20, 150)
        self.slider_size.setValue(self.icon_size)
        self.slider_size.valueChanged.connect(self.update_icon_size)
        
        self.settings_layout.addWidget(self.lbl_size)
        self.settings_layout.addWidget(self.slider_size)
        self.settings_frame.setLayout(self.settings_layout)
        
        # Стилизация меню настроек (Figma/Web UI)
        self.settings_frame.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border-radius: 6px;
                border: 1px solid #444444;
            }
            QLabel { color: #DDDDDD; font-size: 11px; }
        """)
        
        # --- 3. АДАПТИВНАЯ СЕТКА КИСТЕЙ ---
        self.grid = QListWidget()
        self.grid.setViewMode(QListView.IconMode)
        self.grid.setResizeMode(QListView.Adjust)
        self.grid.setMovement(QListView.Static)
        self.grid.setSpacing(self.padding)
        self.grid.setUniformItemSizes(True)
        self.grid.setWordWrap(False)
        
        # Динамические стили
        self.update_grid_style()
        
        # Сборка UI
        self.layout.addLayout(self.top_bar)
        self.layout.addWidget(self.settings_frame)
        self.layout.addWidget(self.grid)
        self.main_widget.setLayout(self.layout)
        self.setWidget(self.main_widget)
        
        # Подключения
        self.grid.itemClicked.connect(self.on_brush_clicked)
        
        # Инициализация
        self.load_real_brushes()
        self.apply_grid_layout() # Применяем параметры позиционирования

    # --- ЛОГИКА ИНТЕРФЕЙСА ---

    def toggle_settings(self):
        """Прячет или показывает веб-стайл меню настроек"""
        is_visible = self.settings_frame.isVisible()
        self.settings_frame.setVisible(not is_visible)

    def toggle_flow(self):
        """Умный свитчер: инвертирует направление (Слева-Направо / Справа-Налево)"""
        self.is_inverted = not self.is_inverted
        self.apply_grid_layout()

    def update_icon_size(self, value):
        """Динамическое изменение размера ячеек (как в Blender UI)"""
        self.icon_size = value
        self.lbl_size.setText(f"Размер слота: {value}px")
        
        # Обновляем размер иконок и ячеек (GridSize чуть больше иконки для паддинга)
        self.grid.setIconSize(QSize(self.icon_size, self.icon_size))
        self.grid.setGridSize(QSize(self.icon_size + 10, self.icon_size + 10))

    def apply_grid_layout(self):
        """Применяет параметры раскладки в зависимости от флагов"""
        # Смена направления рендера слотов (RTL / LTR)
        if self.is_inverted:
            self.grid.setLayoutDirection(Qt.RightToLeft)
        else:
            self.grid.setLayoutDirection(Qt.LeftToRight)
            
        # Обновляем отступы на всякий случай
        self.grid.setSpacing(self.padding)

    def update_grid_style(self):
        self.main_widget.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888888;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #444444; color: white; }
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: #2D2D2D;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background-color: #3A3A3A;
                border: 2px solid #0D99FF;
                border-radius: 6px;
            }
            QListWidget::item:hover { background-color: #3D3D3D; }
        """)

    # --- ЛОГИКА КРИТЫ ---

    def load_real_brushes(self):
        app = krita.Krita.instance()
        all_presets = app.resources("preset")
        
        # Загружаем базовые кисти (в будущем здесь будет парсинг конкретного тега)
        count = 0
        for name, preset in all_presets.items():
            if count >= 30: break
            
            # Извлекаем и сохраняем оригинальное изображение
            img = preset.image()
            icon = QIcon(QPixmap.fromImage(img))
            
            item = QListWidgetItem(icon, "")
            item.setToolTip(name)
            item.setData(Qt.UserRole, name)
            self.grid.addItem(item)
            count += 1
            
        # Применяем стартовые размеры
        self.update_icon_size(self.icon_size)

    def on_brush_clicked(self, item):
        preset_name = item.data(Qt.UserRole)
        app = krita.Krita.instance()
        
        # 1. ИСПРАВЛЕНИЕ ОШИБКИ: Глобальный вызов инструмента кисти
        action = app.action('KritaShape/KritaToolFreehand')
        if action:
            action.trigger()
            
        # 2. Вызов пресета
        window = app.activeWindow()
        if window:
            view = window.activeView() # Безопасное получение активного холста
            if view:
                preset = app.resources("preset").get(preset_name)
                if preset:
                    view.setCurrentBrushPreset(preset)