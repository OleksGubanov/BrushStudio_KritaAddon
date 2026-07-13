import krita
from PyQt5.QtWidgets import QDockWidget, QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QListView
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QColor

class SmartPanelDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Tools")
        
        # Основной виджет и Layout
        self.main_widget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(5, 5, 5, 5) # Минимальные отступы как в вебе
        
        # Создаем адаптивную сетку для кнопок
        self.grid = QListWidget()
        self.grid.setViewMode(QListView.IconMode) # Режим сетки
        self.grid.setResizeMode(QListView.Adjust) # Адаптивное перестроение при ресайзе
        self.grid.setSpacing(8) # Расстояние между кнопками (Figma style)
        
        # Стилизуем под Figma (Dark mode, скругления)
        self.grid.setStyleSheet("""
            QListWidget {
                background-color: #2C2C2C; /* Темный фон */
                border-radius: 10px;       /* Скругленные углы всей панели */
                border: 1px solid #3A3A3A;
                padding: 4px;
            }
            QListWidget::item {
                background-color: #383838;
                border-radius: 6px;        /* Скругления самих кнопок */
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #0D99FF; /* Синий акцент как в Figma */
                color: white;
            }
            QListWidget::item:hover {
                background-color: #4A4A4A;
            }
        """)
        
        # Добавляем тестовые слоты (позже здесь будет подгрузка из пресетов)
        self.add_test_buttons()
        
        self.layout.addWidget(self.grid)
        self.main_widget.setLayout(self.layout)
        self.setWidget(self.main_widget)

    def add_test_buttons(self):
        # Генерируем 10 тестовых ячеек для проверки адаптивной верстки
        for i in range(10):
            item = QListWidgetItem(f"Brush {i+1}")
            # Пока без иконок, задаем жесткий размер слота
            item.setSizeHint(QSize(60, 60)) 
            item.setTextAlignment(Qt.AlignCenter)
            self.grid.addItem(item)
            
        # Подключаем сигнал клика к нашей будущей функции-перехватчику
        self.grid.itemClicked.connect(self.on_brush_clicked)

    def on_brush_clicked(self, item):
        # Здесь будет логика: 
        # 1. Считать текущий размер кисти
        # 2. Переключить пресет в Krita
        # 3. Вернуть размер обратно
        print(f"Выбрана: {item.text()} - Готовим перехват размера!")


class SmartPanelExtension(krita.Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction("smart_brush_panel_id", "Smart Brush Panel", "tools/scripts")
        action.triggered.connect(self.add_docker)

    def add_docker(self):
        # Добавляем наш докер в интерфейс
        docker = SmartPanelDocker()
        Krita.instance().activeWindow().qwindow().addDockWidget(Qt.RightDockWidgetArea, docker)