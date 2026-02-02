from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFrame, QLineEdit, QMessageBox,
                             QDialog, QComboBox, QApplication)
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator
from functools import partial
import db
from ui_styles import (BUTTON_STYLE, CATEGORY_BUTTON_STYLE, TITLE_STYLE, SUBTITLE_STYLE,
                      USER_NAME_STYLE, USER_ROLE_STYLE, SEPARATOR_STYLE)
from warehouse_window import WarehouseWindow
from sales_window import SalesWindow
from deliveries_window import DeliveriesWindow
from suppliers_window import SuppliersWindow
from purchase_window import PurchaseWindow
from catalog_window import CatalogWindow


class MainWindow(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user = user_data
        self.setWindowTitle("Учет мебельного магазина")
        self.setGeometry(100, 100, 1200, 800)
        
        self.active_button = None
        self.menu_buttons = {}
        
        self.setup_ui()
        self.show_catalog()
    
    def setup_ui(self):
        """Создание основного макета окна"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Левая колонка
        self.create_left_column(main_layout)
        
        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(SEPARATOR_STYLE)
        main_layout.addWidget(separator)
        
        # Правая часть
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        self.create_user_info(right_layout)
        
        # Контентная область
        self.content = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content.setLayout(self.content_layout)
        right_layout.addWidget(self.content, 1)
        
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 1)
        
        central_widget.setLayout(main_layout)
    
    def create_left_column(self, parent_layout):
        """Создание левой колонки с навигацией"""
        left_widget = QWidget()
        left_widget.setFixedWidth(200)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(15)
        
        # Информация о пользователе (сначала ФИО, ниже роль)
        user_info_widget = QWidget()
        user_info_layout = QVBoxLayout()
        user_info_layout.setContentsMargins(0, 0, 0, 0)

        # Формируем отображаемое ФИО.
        # Если в БД в full_name случайно записана роль ("Администратор"),
        # то вместо неё показываем логин (username) или заглушку.
        last_name = (self.user.get('last_name') or "").strip()
        first_name = (self.user.get('first_name') or "").strip()
        middle_name = (self.user.get('middle_name') or "").strip()

        raw_role_for_name = (self.user.get('role') or "").strip()
        full_name_db = (self.user.get('full_name') or "").strip()

        if last_name and first_name:
            full_name = " ".join(part for part in [last_name, first_name, middle_name] if part)
        else:
            # Если full_name совпадает с ролью, считаем, что это не ФИО
            if full_name_db and raw_role_for_name and full_name_db.lower() == raw_role_for_name.lower():
                full_name = (self.user.get('username') or "Иванов И. И.")
            else:
                full_name = (full_name_db or self.user.get('username') or "Иванов И. И.")

        name_label = QLabel(full_name)
        name_label.setStyleSheet(USER_NAME_STYLE)
        user_info_layout.addWidget(name_label)

        # Нормализуем роль: admin/administrator -> Администратор, seller -> Продавец и т.п.
        raw_role = (self.user.get('role') or "Администратор").strip()
        role_lower = raw_role.lower()
        if role_lower in ("администратор", "administrator", "admin"):
            display_role = "Администратор"
        elif "продав" in role_lower or role_lower in ("пользователь", "user", "seller", "cashier"):
            display_role = "Продавец"
        else:
            display_role = raw_role

        role_label = QLabel(display_role)
        role_label.setStyleSheet(USER_ROLE_STYLE)
        user_info_layout.addWidget(role_label)

        user_info_widget.setLayout(user_info_layout)
        left_layout.addWidget(user_info_widget)
        left_layout.addStretch()
        
        # Доступ по ролям: администратор — всё кроме покупок; пользователь/продавец — только каталог и покупки
        self._is_admin = role_lower in ("администратор", "administrator", "admin")
        if self._is_admin:
            allowed_menus = {"КАТАЛОГ", "СКЛАД", "ПРОДАЖИ", "ПОСТАВКИ", "ПОСТАВЩИКИ"}
        else:
            allowed_menus = {"КАТАЛОГ", "ПОКУПКИ"}

        all_nav_buttons = [
            ("КАТАЛОГ", self.show_catalog),
            ("СКЛАД", self.show_warehouse),
            ("ПРОДАЖИ", self.show_sales),
            ("ПОКУПКИ", self.show_purchase),
            ("ПОСТАВКИ", self.show_deliveries),
            ("ПОСТАВЩИКИ", self.show_suppliers),
        ]
        nav_buttons = [(t, c) for t, c in all_nav_buttons if t in allowed_menus]

        for text, command in nav_buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(BUTTON_STYLE)
            btn.clicked.connect(lambda checked, t=text, c=command: self.set_active_menu(t, c))
            left_layout.addWidget(btn)
            self.menu_buttons[text] = btn
        
        left_layout.addStretch()
        
        # Кнопка выхода
        exit_btn = QPushButton("Выход")
        exit_btn.setStyleSheet(BUTTON_STYLE)
        exit_btn.clicked.connect(self._on_exit_clicked)
        left_layout.addWidget(exit_btn)
        
        left_widget.setLayout(left_layout)
        parent_layout.addWidget(left_widget)
    
    def set_active_menu(self, button_name, command):
        """Установка активной кнопки меню и выполнение команды"""
        for btn in self.menu_buttons.values():
            btn.setStyleSheet(BUTTON_STYLE)
        
        if button_name in self.menu_buttons:
            active_style = BUTTON_STYLE.replace(
                'background-color: white;',
                'background-color: #f0f0f0; font-weight: bold;'
            )
            self.menu_buttons[button_name].setStyleSheet(active_style)
        
        self.active_button = button_name
        # Категории отображаются только во вкладке «КАТАЛОГ»
        self.catalog_header_widget.setVisible(button_name == "КАТАЛОГ")
        command()
    
    def create_user_info(self, parent_layout):
        """Создание правой верхней части с категориями (только для вкладки Каталог)"""
        self.catalog_header_widget = QWidget()
        user_cat_layout = QVBoxLayout()
        user_cat_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("Каталог")
        title_label.setStyleSheet(TITLE_STYLE)
        user_cat_layout.addWidget(title_label)
        
        # Фрейм для категорий
        self.categories_widget = QWidget()
        self.categories_layout = QHBoxLayout()
        self.categories_layout.setContentsMargins(0, 0, 0, 0)
        self.categories_widget.setLayout(self.categories_layout)
        user_cat_layout.addWidget(self.categories_widget)
        
        self.load_categories()
        
        role = (self.user.get('role', 'Администратор') or '').lower()
        if role in ('администратор', 'administrator', 'admin'):
            cat_buttons_layout = QHBoxLayout()
            cat_buttons_layout.setContentsMargins(0, 0, 0, 0)
            cat_buttons_layout.setSpacing(10)
            add_cat_btn = QPushButton("Добавить категорию")
            add_cat_btn.setStyleSheet(BUTTON_STYLE)
            add_cat_btn.clicked.connect(self.open_add_category_window)
            cat_buttons_layout.addWidget(add_cat_btn)
            del_cat_btn = QPushButton("Удалить категорию")
            del_cat_btn.setStyleSheet(BUTTON_STYLE)
            del_cat_btn.clicked.connect(self.open_delete_category_window)
            cat_buttons_layout.addWidget(del_cat_btn)
            cat_buttons_layout.addStretch()
            user_cat_layout.addLayout(cat_buttons_layout)
        
        self.catalog_header_widget.setLayout(user_cat_layout)
        parent_layout.addWidget(self.catalog_header_widget)
    
    def _on_exit_clicked(self) -> None:
        """Обработчик кнопки Выход — закрыть окно и завершить приложение."""
        self.close()
        QApplication.quit()

    def load_categories(self):
        """Загрузка категорий из базы данных"""
        # Очищаем виджеты категорий
        while self.categories_layout.count():
            child = self.categories_layout.takeAt(0)
            if child is not None:
                w = child.widget()
                if w is not None:
                    w.deleteLater()
        
        try:
            categories = db.get_categories()
            if categories:
                for cat in categories:
                    if len(cat) >= 2:
                        cat_id, cat_name = cat[0], cat[1]
                        btn = QPushButton(cat_name)
                        btn.setStyleSheet("""
                            QPushButton {
                                background-color: #7A6E5B;
                                color: white;
                                font-family: Arial, sans-serif;
                                font-size: 10pt;
                                border: 1px solid #5A4F40;
                                border-radius: 20px;
                                padding: 10px 20px;
                            }
                            QPushButton:hover {
                                background-color: #8B7D6B;
                            }
                        """)
                        btn.clicked.connect(partial(self.show_category_products, cat_id, cat_name))
                        self.categories_layout.addWidget(btn)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки категорий: {e}")
    
    def show_category_products(self, category_id, category_name):
        """Показать товары выбранной категории"""
        self.clear_content()
        catalog = CatalogWindow(self.content, category_id=category_id, 
                               category_name=category_name,
                               on_refresh=self.load_categories, user_data=self.user)
        self.content_layout.addWidget(catalog)
    
    def open_add_category_window(self):
        """Открытие окна для добавления категории"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить категорию")
        dialog.setGeometry(200, 200, 400, 200)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("Добавить категорию")
        title_label.setStyleSheet(TITLE_STYLE)
        layout.addWidget(title_label)
        
        name_label = QLabel("Наименование:")
        name_label.setStyleSheet(SUBTITLE_STYLE)
        layout.addWidget(name_label)
        
        name_entry = QLineEdit()
        name_entry.setValidator(QRegExpValidator(QRegExp(r"[a-zA-Zа-яА-ЯёЁ\s\-]*")))
        layout.addWidget(name_entry)
        
        button_layout = QHBoxLayout()
        
        def add_category():
            name = name_entry.text().strip()
            if not name:
                QMessageBox.warning(dialog, "Ошибка", "Введите название категории")
                return
            
            try:
                db.add_category(name)
                self.load_categories()
                dialog.accept()
                QMessageBox.information(self, "Успех", "Категория добавлена")
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось добавить категорию: {e}")
        
        add_btn = QPushButton("Добавить")
        add_btn.setStyleSheet(BUTTON_STYLE)
        add_btn.clicked.connect(add_category)
        button_layout.addWidget(add_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet(BUTTON_STYLE)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        name_entry.setFocus()
        name_entry.returnPressed.connect(add_category)
        
        dialog.exec_()

    def open_delete_category_window(self):
        """Открытие окна для удаления категории"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Удалить категорию")
        dialog.setGeometry(200, 200, 400, 200)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("Удалить категорию")
        title_label.setStyleSheet(TITLE_STYLE)
        layout.addWidget(title_label)
        
        name_label = QLabel("Категория:")
        name_label.setStyleSheet(SUBTITLE_STYLE)
        layout.addWidget(name_label)
        
        try:
            categories = db.get_categories()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки категорий: {e}")
            return
        
        if not categories:
            QMessageBox.information(self, "Информация", "Нет категорий для удаления")
            return
        
        cat_combo = QComboBox()
        for cat in categories:
            if len(cat) >= 2:
                cat_combo.addItem(cat[1], cat[0])
        layout.addWidget(cat_combo)
        
        button_layout = QHBoxLayout()
        
        def do_delete():
            cat_id = cat_combo.currentData()
            if cat_id is None:
                QMessageBox.warning(dialog, "Ошибка", "Выберите категорию")
                return
            try:
                deleted = db.delete_category(cat_id)
                if deleted:
                    self.load_categories()
                    dialog.accept()
                    QMessageBox.information(self, "Успех", "Категория удалена")
                else:
                    QMessageBox.warning(
                        dialog, "Ошибка",
                        "Не удалось удалить категорию (возможно, в ней есть товары)"
                    )
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Ошибка удаления: {e}")
        
        del_btn = QPushButton("Удалить")
        del_btn.setStyleSheet(BUTTON_STYLE)
        del_btn.clicked.connect(do_delete)
        button_layout.addWidget(del_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet(BUTTON_STYLE)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec_()
    
    def clear_content(self):
        """Очистка центральной области"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child is not None:
                w = child.widget()
                if w is not None:
                    w.deleteLater()
    
    def show_catalog(self):
        """Показать категории (без товаров)"""
        self.clear_content()
        # При входе показываем только категории, товары не загружаем
        # Категории уже отображаются в верхней части через load_categories()
    
    def show_warehouse(self):
        """Показать склад"""
        self.clear_content()
        warehouse = WarehouseWindow(self.content)
        self.content_layout.addWidget(warehouse)
    
    def show_sales(self):
        """Показать продажи"""
        self.clear_content()
        sales = SalesWindow(self.content)
        self.content_layout.addWidget(sales)
    
    def show_purchase(self):
        """Открыть окно оформления покупки"""
        purchase = PurchaseWindow(self, user=self.user)
        purchase.show()
    
    def show_deliveries(self):
        """Показать поставки"""
        self.clear_content()
        deliveries = DeliveriesWindow(self.content)
        self.content_layout.addWidget(deliveries)
    
    def show_suppliers(self):
        """Показать поставщиков"""
        self.clear_content()
        suppliers = SuppliersWindow(self.content)
        self.content_layout.addWidget(suppliers)
