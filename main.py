# main.py - Точка входа в приложение
import sys
from PyQt5.QtWidgets import QApplication  # type: ignore[reportMissingImports]
from PyQt5.QtGui import QFont  # type: ignore[reportMissingImports]
from logic import LoginWindow

class FurnitureStoreApp:
    def __init__(self):
        self.user = None
        self.app = QApplication(sys.argv)
        # Шрифт с поддержкой кириллицы, чтобы вместо букв не отображались знаки вопроса
        font = QFont("Segoe UI", 10)
        font.setStyleHint(QFont.SansSerif)
        self.app.setFont(font)

    def run(self):
        """Запуск приложения - показывает окно логина"""
        login_window = LoginWindow(self.on_login)
        login_window.show()
        sys.exit(self.app.exec_())

    def on_login(self, user_data):
        """Обработчик успешного входа"""
        self.user = user_data
        
        # Импортируем и создаем главное окно
        from main_window import MainWindow
        self.main_window = MainWindow(self.user)
        self.main_window.show()

def main():
    """Точка входа в приложение"""
    app = FurnitureStoreApp()
    app.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
