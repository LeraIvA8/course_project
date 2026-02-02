from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QApplication)
from PyQt5.QtCore import Qt
import hashlib
import db
from ui_styles import SUBTITLE_STYLE

# Овальные поля: фиксированная высота + border-radius = половина высоты (форма овала/капсулы)
OVAL_INPUT = """
    QLineEdit {
        border: 1px solid #333;
        border-radius: 24px;
        padding: 8px 20px;
        font-size: 11pt;
        background-color: white;
        min-height: 48px;
        selection-background-color: #e0e0e0;
    }
"""
OVAL_BUTTON = """
    QPushButton {
        background-color: white;
        color: black;
        font-size: 11pt;
        border: 1px solid #333;
        border-radius: 24px;
        padding: 10px 28px;
        min-height: 48px;
    }
    QPushButton:hover {
        background-color: #f0f0f0;
    }
"""
BROWN_TITLE = "font-weight: bold; font-size: 14pt; color: #705847;"

class LoginWindow(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.setWindowTitle("Вход в систему")
        self.setFixedSize(460, 380)
        self.setup_ui()

    def showEvent(self, a0):
        """Окно по центру монитора при запуске"""
        super().showEvent(a0)
        screen = QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            geom = self.frameGeometry()
            geom.moveCenter(available.center())
            self.move(geom.topLeft())

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title_label = QLabel("Войдите в систему")
        title_label.setStyleSheet(BROWN_TITLE)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Логин
        login_label = QLabel("Логин")
        login_label.setStyleSheet(SUBTITLE_STYLE)
        layout.addWidget(login_label)
        self.login_entry = QLineEdit()
        self.login_entry.setFixedHeight(48)
        self.login_entry.setStyleSheet(OVAL_INPUT)
        layout.addWidget(self.login_entry)

        # Пароль
        password_label = QLabel("Пароль")
        password_label.setStyleSheet(SUBTITLE_STYLE)
        layout.addWidget(password_label)
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)
        self.password_entry.setStyleSheet(OVAL_INPUT)
        layout.addWidget(self.password_entry)

        layout.addStretch()

        # Кнопка "Вход" справа внизу
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        login_button = QPushButton("Вход")
        login_button.setFixedHeight(48)
        login_button.setStyleSheet(OVAL_BUTTON)
        login_button.clicked.connect(self.login)
        button_layout.addWidget(login_button)
        layout.addLayout(button_layout)

        self.password_entry.returnPressed.connect(self.login)
        self.setLayout(layout)

    def hash_password(self, password):
        """Хэширование пароля с поддержкой SHA256 (для обратной совместимости)"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password, stored_hash):
        """Проверка пароля с поддержкой SHA256 и bcrypt"""
        if not stored_hash:
            return False
        
        # Попытка проверки через bcrypt (если пароль в формате bcrypt)
        try:
            import bcrypt
            if stored_hash.startswith('$2b$') or stored_hash.startswith('$2a$') or stored_hash.startswith('$2y$'):
                return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        except ImportError:
            pass
        except Exception:
            pass
        
        # Проверка через SHA256 (старый формат для обратной совместимости)
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        return sha256_hash == stored_hash

    def login(self):
        username = self.login_entry.text().strip()
        password = self.password_entry.text().strip()

        if not username or not password:
            QMessageBox.critical(self, "Ошибка", "Введите логин и пароль")
            return

        # Получаем пользователя и проверяем пароль
        try:
            # Используем функцию из db.py для получения пользователя
            user = db.get_user_by_username(username)
            
            if not user or len(user) < 5:
                QMessageBox.critical(self, "Ошибка", "Неверные данные")
                return

            # Проверяем пароль (user: id, username, full_name, role, password)
            stored_password = user[4]
            if not stored_password or not self.verify_password(password, stored_password):
                QMessageBox.critical(self, "Ошибка", "Неверные данные")
                return

            user_data = {
                "id": user[0],
                "username": user[1],
                "full_name": user[2],
                "role": user[3]
            }

            self.close()
            self.on_success(user_data)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при входе: {str(e)}")
            print(f"Ошибка входа: {e}")
