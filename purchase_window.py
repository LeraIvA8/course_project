from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QComboBox, QDateEdit)
from PyQt5.QtCore import Qt, QDate, QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator
from datetime import datetime
import db
from ui_styles import BUTTON_STYLE, TITLE_STYLE, SUBTITLE_STYLE, INPUT_STYLE

# Более тёмный коричневый цвет для надписей в этом окне
BROWN_LABEL_STYLE = "font-size: 11pt; color: #5A3B22;"
BROWN_SUBTITLE_STYLE = "font-size: 11pt; font-weight: bold; color: #5A3B22;"


class PurchaseWindow(QDialog):
    """
    Окно оформления покупки:
      - поле ФИО покупателя
      - выбор даты
      - добавление товаров в чек
      - автоматический расчет суммы
      - проверка остатков выполняется внутри db.create_sale
    """

    def __init__(self, parent, user=None):
        super().__init__(parent)
        self.user = user or {}
        self.setWindowTitle("Оформление покупки")
        self.setGeometry(200, 200, 800, 600)
        self.setModal(True)
        
        # Список позиций для передачи в db.create_sale
        self.items = []  # (product_id, quantity, discount_override)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Верхняя часть: данные покупателя и дата
        top_layout = QVBoxLayout()
        
        customer_layout = QHBoxLayout()
        customer_label = QLabel("ФИО покупателя:")
        customer_label.setStyleSheet(BROWN_SUBTITLE_STYLE)
        customer_layout.addWidget(customer_label)
        self.customer_entry = QLineEdit()
        self.customer_entry.setMinimumWidth(300)
        self.customer_entry.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"[a-zA-Zа-яА-ЯёЁ\s\-\.]*"))
        )
        self.customer_entry.setStyleSheet(INPUT_STYLE)
        self.customer_entry.setPlaceholderText("Иванов И. И.")
        customer_layout.addWidget(self.customer_entry, 1)
        top_layout.addLayout(customer_layout)
        
        date_layout = QHBoxLayout()
        date_label = QLabel("Дата продажи:")
        date_label.setStyleSheet(BROWN_SUBTITLE_STYLE)
        date_layout.addWidget(date_label)
        self.date_entry = QDateEdit()
        self.date_entry.setDate(QDate.currentDate())
        self.date_entry.setCalendarPopup(True)
        self.date_entry.setDisplayFormat("dd.MM.yyyy")
        date_layout.addWidget(self.date_entry)
        date_layout.addStretch()
        top_layout.addLayout(date_layout)
        
        layout.addLayout(top_layout)
        
        # Таблица товаров в чеке
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            "Товар", "Артикул", "Количество", "Цена", "Сумма"
        ])
        
        header = self.items_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            # Коричневый цвет для заголовков колонок
            header.setStyleSheet("QHeaderView::section { color: #705847; font-weight: bold; }")
        
        layout.addWidget(self.items_table, 1)
        
        # Кнопки добавления / удаления
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("Добавить товар")
        add_btn.setStyleSheet(BUTTON_STYLE)
        add_btn.clicked.connect(self.add_item_dialog)
        buttons_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Удалить выбранный")
        remove_btn.setStyleSheet(BUTTON_STYLE)
        remove_btn.clicked.connect(self.remove_selected_item)
        buttons_layout.addWidget(remove_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Итоговая сумма и кнопка оформления
        bottom_layout = QHBoxLayout()
        
        self.total_label = QLabel("Итого: 0.00 руб.")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        bottom_layout.addWidget(self.total_label)
        
        bottom_layout.addStretch()
        
        confirm_btn = QPushButton("Оформить покупку")
        confirm_btn.setStyleSheet(BUTTON_STYLE)
        confirm_btn.clicked.connect(self.confirm_purchase)
        bottom_layout.addWidget(confirm_btn)
        
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    # ==== Работа с позициями ====

    def add_item_dialog(self):
        """Окно выбора товара и количества"""
        from PyQt5.QtWidgets import QDialog
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить товар")
        dialog.setGeometry(300, 300, 500, 250)
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        product_label = QLabel("Товар:")
        product_label.setStyleSheet(BROWN_LABEL_STYLE)
        layout.addWidget(product_label)
        
        products = db.get_products()
        self.display_products = []
        # Показываем только товары, у которых есть остаток на складе
        for p in products:
            stock = p[11]
            stock_value = stock if stock is not None else 0
            if stock_value <= 0:
                continue
            name = p[1]
            sku = p[2]
            price = p[12]  # current_price
            self.display_products.append(
                (p[0], f"{name} ({sku}) — {price:.2f} руб., остаток: {stock_value}")
            )

        product_combo = QComboBox()
        product_combo.addItems([d[1] for d in self.display_products])
        if self.display_products:
            product_combo.setCurrentIndex(0)
        layout.addWidget(product_combo)
        
        quantity_label = QLabel("Количество:")
        quantity_label.setStyleSheet(BROWN_SUBTITLE_STYLE)
        layout.addWidget(quantity_label)
        
        quantity_entry = QLineEdit()
        quantity_entry.setText("1")
        quantity_entry.setStyleSheet(INPUT_STYLE)
        layout.addWidget(quantity_entry)
        
        def on_add():
            try:
                idx = product_combo.currentIndex()
                if idx < 0:
                    QMessageBox.critical(dialog, "Ошибка", "Выберите товар")
                    return
                product_id = self.display_products[idx][0]
                quantity = int(quantity_entry.text())
                if quantity <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.critical(dialog, "Ошибка", "Количество должно быть положительным целым числом")
                return

            # найдём товар ещё раз для цены
            for p in products:
                if p[0] == product_id:
                    name = p[1]
                    sku = p[2]
                    price = p[12]
                    amount = price * quantity
                    # добавляем в список для create_sale (discount_override = None)
                    self.items.append((product_id, quantity, None))
                    row = self.items_table.rowCount()
                    self.items_table.insertRow(row)
                    self.items_table.setItem(row, 0, QTableWidgetItem(name))
                    self.items_table.setItem(row, 1, QTableWidgetItem(sku))
                    self.items_table.setItem(row, 2, QTableWidgetItem(str(quantity)))
                    self.items_table.setItem(row, 3, QTableWidgetItem(f"{price:.2f}"))
                    self.items_table.setItem(row, 4, QTableWidgetItem(f"{amount:.2f}"))
                    self.update_total()
                    break

            dialog.accept()

        add_btn = QPushButton("Добавить")
        add_btn.setStyleSheet(BUTTON_STYLE)
        add_btn.clicked.connect(on_add)
        layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def remove_selected_item(self):
        current_row = self.items_table.currentRow()
        if current_row < 0:
            return
        self.items_table.removeRow(current_row)
        if 0 <= current_row < len(self.items):
            self.items.pop(current_row)
        self.update_total()

    def update_total(self):
        total = 0.0
        for row in range(self.items_table.rowCount()):
            amount_item = self.items_table.item(row, 4)
            if amount_item:
                total += float(amount_item.text())
        self.total_label.setText(f"Итого: {total:.2f} руб.")

    # ==== Оформление покупки ====

    def confirm_purchase(self):
        if not self.items:
            QMessageBox.critical(self, "Ошибка", "Добавьте хотя бы один товар в чек")
            return

        customer_name = self.customer_entry.text().strip()
        if not customer_name:
            QMessageBox.critical(self, "Ошибка", "Введите ФИО покупателя")
            return

        sale_date = self.date_entry.date().toPyDate()

        try:
            # Получаем employee_id из таблицы employees по user_id
            employee_id = None
            if self.user:
                user_id = self.user.get('id')
                if user_id:
                    employee = db.get_employee_by_user_id(user_id)
                    if employee:
                        employee_id = employee[0]  # employee[0] - это id сотрудника
            
            # Вызываем create_sale с customer_name напрямую
            db.create_sale(customer_name, employee_id, sale_date, self.items)
            QMessageBox.information(self, "Успех", "Покупка успешно оформлена и записана в раздел 'Продажи'")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось оформить покупку: {e}")
