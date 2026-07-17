import sys
from PyQt5.QtWidgets import QApplication, QDockWidget

# 1. Импортируем "голый" класс дизайна напрямую из сгенерированного файла
# Просто меняйте эту строчку для проверки разных окон
from ui_py_file import Ui_DockWidget


def preview_raw_ui(ui_class):
    """Функция берет чертеж (ui_class) и оборачивает его в реальное окно"""
    app = QApplication(sys.argv)

    # 2. Создаем реальный, но пустой докер-контейнер
    mock_docker = QDockWidget()
    mock_docker.setWindowTitle("Универсальный просмотрщик UI")

    # 3. Создаем экземпляр вашего чертежа
    ui_instance = ui_class()

    # 4. Команда setupUi натягивает кнопки и списки из чертежа на пустой докер
    ui_instance.setupUi(mock_docker)

    # 5. Показываем результат
    mock_docker.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    # Передаем импортированный класс чертежа в функцию
    preview_raw_ui(Ui_DockWidget)