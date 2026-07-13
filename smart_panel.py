import krita
from PyQt5.QtWidgets import QDockWidget, QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QListView
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap

class SmartPanelDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Tools")
        
        self.main_widget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(8, 8, 8, 8)
        
        # --- Адаптивная Сетка ---
        self.grid = QListWidget()
        self.grid.setViewMode(QListView.IconMode) # Режим плитки
        self.grid.setResizeMode(QListView.Adjust) # Автоматический перенос строк при сужении окна
        self.grid.setMovement(QListView.Static)
        self.grid.setSpacing(6) # Отступы между слотами (Figma style)
        self.grid.setUniformItemSizes(True) # КРИТИЧНО: делает все слоты идеально ровными, без "кривизны"
        self.grid.setWordWrap(False)
        
        # --- Минималистичный Дизайн (QSS) ---
        self.grid.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: #2D2D2D;
                border-radius: 8px; /* Скругление слотов */
            }
            QListWidget::item:selected {
                background-color: #3A3A3A;
                border: 2px solid #0D99FF; /* Синий акцент как в Figma */
                border-radius: 8px;
            }
            QListWidget::item:hover {
                background-color: #3D3D3D;
            }
        """)
        
        self.load_real_brushes()
        
        self.layout.addWidget(self.grid)
        self.main_widget.setLayout(self.layout)
        self.setWidget(self.main_widget)
        
        # Подключаем клик
        self.grid.itemClicked.connect(self.on_brush_clicked)

    def load_real_brushes(self):
        """Загружаем реальные кисти из движка Krita"""
        app = krita.Krita.instance()
        all_presets = app.resources("preset") # Получаем словарь всех кистей
        
        # Для прототипа загрузим первые 20 кистей, чтобы панель была компактной.
        # Позже мы привяжем это к конкретным тегам (например, только "Скетчинг").
        count = 0
        for name, preset in all_presets.items():
            if count >= 20: break
            
            # Достаем картинку пресета и сжимаем её под интерфейс, сохраняя пропорции и сглаживание
            img = preset.image()
            scaled_img = img.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon = QIcon(QPixmap.fromImage(scaled_img))
            
            # Создаем слот
            item = QListWidgetItem(icon, "") # Имя не пишем, чтобы не засорять дизайн
            item.setToolTip(name) # Имя будет всплывать при наведении мыши
            item.setData(Qt.UserRole, name) # Прячем системное имя кисти внутрь слота
            item.setSizeHint(QSize(60, 60)) # Жесткий размер слота (иконка 50 + отступы)
            
            self.grid.addItem(item)
            count += 1

    def on_brush_clicked(self, item):
        """Логика при выборе кисти"""
        preset_name = item.data(Qt.UserRole)
        print(f"[Smart Panel] Переключаю на кисть: {preset_name}")
        
        # Обращаемся к ядру Krita для смены кисти
        app = krita.Krita.instance()
        window = app.activeWindow()
        
        if window and window.views():
            # Получаем объект пресета
            preset = app.resources("preset").get(preset_name)
            
            if preset:
                # Включаем инструмент кисти (на случай, если был выбран ластик или выделение)
                window.action("paint_tool").trigger()
                
                # Применяем пресет к активному холсту (Внимание: API Krita тут бывает капризным)
                # Если эта строка выдаст ошибку в консоль - скинь мне traceback.
                try:
                    view = window.views()[0]
                    view.setCurrentBrushPreset(preset)
                except Exception as e:
                    print(f"Ошибка применения кисти: {e}")