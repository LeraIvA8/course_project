from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, 
                             QComboBox, QLineEdit, QDateEdit, QDialog)
from PyQt5.QtCore import Qt, QDate, QRegExp
from PyQt5.QtGui import QPixmap, QImage, QRegExpValidator
from datetime import datetime
import os
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None
import db
from ui_styles import (
    BUTTON_STYLE,
    TITLE_STYLE,
    SUBTITLE_STYLE,
    INPUT_STYLE,
    COMBOBOX_STYLE,
    INFO_STYLE,
    DELIVERY_HEADER_STYLE,
    DELIVERY_TOTAL_STYLE,
    DELIVERY_CARD_STYLE,
    DELIVERY_FRAME_STYLE,
    CARD_STYLE,
    SKU_BOLD_STYLE,
)

# Локальные утилитарные стили, визуально такие же как в окне склада
UTIL_CARD_FRAME = """
    QFrame {
        background-color: white;
        border: 1px solid #ccc;
    }
"""
UTIL_PLACEHOLDER = """
    QLabel {
        background-color: #e0e0e0;
        color: #666;
        font-size: 11pt;
        border: 1px solid #bbb;
    }
"""
UTIL_LABEL = "font-size: 10pt; color: #333;"
UTIL_FIELD = "font-size: 10pt; color: #000; border: none; background-color: transparent;"

# Коричневый цвет для подписей и сумм (как в общем стиле проекта)
BROWN_LABEL_STYLE = "font-size: 10pt; font-weight: bold; color: #705847;"
BROWN_TOTAL_STYLE = "font-weight: bold; font-size: 11pt; color: #705847;"


class DeliveriesWindow(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
        self.load_deliveries()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Заголовок и кнопка "Новая поставка"
        header_layout = QHBoxLayout()
        
        title_label = QLabel("ПОСТАВКИ")
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt; color: #705847;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        new_delivery_btn = QPushButton("Новая поставка")
        new_delivery_btn.setStyleSheet(BUTTON_STYLE)
        new_delivery_btn.clicked.connect(self.open_new_delivery)
        header_layout.addWidget(new_delivery_btn)
        
        layout.addLayout(header_layout)
        
        # Контейнер для карточек товаров с прокруткой
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: #f5f5f5; border: none; }")
        
        self.scrollable_widget = QWidget()
        self.scrollable_widget.setStyleSheet("background: #f5f5f5;")
        self.scrollable_layout = QVBoxLayout()
        self.scrollable_layout.setContentsMargins(0, 0, 0, 0)
        self.scrollable_layout.setSpacing(12)
        self.scrollable_widget.setLayout(self.scrollable_layout)
        
        scroll_area.setWidget(self.scrollable_widget)
        layout.addWidget(scroll_area, 1)
        
        self.setLayout(layout)

    def load_deliveries(self):
        """Загрузка поставок с товарами"""
        # Очищаем layout
        while self.scrollable_layout.count():
            child = self.scrollable_layout.takeAt(0)
            if child is not None:
                w = child.widget()
                if w is not None:
                    w.deleteLater()
        
        try:
            deliveries_data = db.get_deliveries_with_items()
            
            if not deliveries_data:
                no_deliveries_label = QLabel("Поставки не найдены")
                no_deliveries_label.setStyleSheet(INFO_STYLE)
                self.scrollable_layout.addWidget(no_deliveries_label)
                return

            # Группируем по дате поставки
            deliveries_by_date = {}
            for row in deliveries_data:
                # row: (delivery_id, delivery_date, supplier_name, total_amount, 
                #       product_id, product_name, sku, quantity, purchase_price, photo_path)
                delivery_date = row[1]
                date_str = delivery_date.strftime('%d.%m.%Y') if hasattr(delivery_date, 'strftime') else str(delivery_date)
                
                if date_str not in deliveries_by_date:
                    deliveries_by_date[date_str] = {
                        'delivery_id': row[0],
                        'supplier': row[2],
                        'total_amount': row[3],
                        'items': []
                    }
                
                deliveries_by_date[date_str]['items'].append({
                    'product_id': row[4],
                    'name': row[5],
                    'sku': row[6],
                    'quantity': row[7],
                    'price': row[8],
                    'photo_path': row[9],
                    'supplier': deliveries_by_date[date_str]['supplier']
                })

            # Отображаем поставки по датам
            for date_str in sorted(deliveries_by_date.keys(), reverse=True):
                delivery_info = deliveries_by_date[date_str]
                
                # Фрейм для одной даты поставки
                date_frame = QFrame()
                date_frame.setFrameShape(QFrame.Box)
                date_frame.setLineWidth(2)
                date_frame.setStyleSheet(DELIVERY_FRAME_STYLE)
                
                date_layout = QVBoxLayout()
                date_layout.setSpacing(5)
                date_layout.setContentsMargins(10, 10, 10, 10)
                
                # Заголовок с датой и поставщиком
                header_label = QLabel(
                    f"Дата поставки: {date_str} | Поставщик: {delivery_info['supplier']}"
                )
                header_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
                date_layout.addWidget(header_label)
                
                # Отображаем товары в столбик
                for item in delivery_info['items']:
                    card = self.create_product_card(item, date_str)
                    date_layout.addWidget(card)
                
                # Общая сумма в правом нижнем углу
                total_label = QLabel(
                    f"Общая сумма поставки: {delivery_info['total_amount']:.2f} руб."
                )
                total_label.setStyleSheet(BROWN_TOTAL_STYLE)
                total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                date_layout.addWidget(total_label)
                
                date_frame.setLayout(date_layout)
                self.scrollable_layout.addWidget(date_frame)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки поставок: {e}")

    def create_product_card(self, item, date_str):
        """Создание карточки товара"""
        card_frame = QFrame()
        # Оформление карточки как в окне "Склад"
        card_frame.setStyleSheet(UTIL_CARD_FRAME)
        
        main_layout = QHBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Левая часть - фото (как в add_product_window)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        
        photo_label = QLabel("[Фото]")
        photo_label.setFixedSize(200, 200)
        photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Плейсхолдер фото в стиле склада
        photo_label.setStyleSheet(UTIL_PLACEHOLDER)
        
        try:
            photo_path = item['photo_path']
            if HAS_PIL and Image is not None and photo_path:
                full_path = photo_path if os.path.isabs(photo_path) else os.path.join(os.getcwd(), photo_path)
                if os.path.exists(full_path):
                    img = Image.open(full_path)
                    img = img.resize((200, 200))
                    # Конвертируем PIL Image в QPixmap
                    img_rgb = img.convert('RGB')
                    img_bytes = img_rgb.tobytes('raw', 'RGB')
                    w, h = img.width, img.height
                    qimg = QImage(img_bytes, w, h, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimg)
                    photo_label.setPixmap(pixmap)
        except Exception as e:
            print(f"Ошибка загрузки фото: {e}")
        
        left_layout.addWidget(photo_label)
        left_layout.addStretch()
        
        # Правая часть - данные (как в add_product_window)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)
        
        # Дата поставки
        date_label_text = QLabel("Дата поставки")
        date_label_text.setStyleSheet(BROWN_LABEL_STYLE)
        right_layout.addWidget(date_label_text)
        
        date_value = QLabel(date_str)
        date_value.setStyleSheet(UTIL_FIELD)
        right_layout.addWidget(date_value)
        
        # Наименование
        name_label_text = QLabel("Наименование")
        name_label_text.setStyleSheet(BROWN_LABEL_STYLE)
        right_layout.addWidget(name_label_text)
        
        name_value = QLabel(item['name'])
        name_value.setStyleSheet(UTIL_FIELD)
        right_layout.addWidget(name_value)
        
        # Артикул
        sku_label_text = QLabel("Артикул")
        # Подпись жирная коричневая
        sku_label_text.setStyleSheet("font-size: 10pt; font-weight: bold; color: #705847;")
        right_layout.addWidget(sku_label_text)
        
        # Значение артикула обычное коричневое
        sku_value = QLabel(item['sku'])
        sku_value.setStyleSheet("font-size: 10pt; color: #705847;")
        right_layout.addWidget(sku_value)
        
        # Количество
        quantity_label_text = QLabel("Количество")
        quantity_label_text.setStyleSheet(BROWN_LABEL_STYLE)
        right_layout.addWidget(quantity_label_text)
        
        quantity_value = QLabel(f"{item['quantity']} шт.")
        quantity_value.setStyleSheet(UTIL_FIELD)
        right_layout.addWidget(quantity_value)
        
        # Поставщик (если есть в данных)
        supplier_label_text = QLabel("Поставщик")
        supplier_label_text.setStyleSheet(BROWN_LABEL_STYLE)
        right_layout.addWidget(supplier_label_text)
        
        supplier_value = QLabel(item.get('supplier', 'Не указан'))
        supplier_value.setStyleSheet(UTIL_FIELD)
        right_layout.addWidget(supplier_value)
        
        # Цена (из БД)
        price_label_text = QLabel("Цена")
        price_label_text.setStyleSheet(BROWN_LABEL_STYLE)
        right_layout.addWidget(price_label_text)
        
        price_value = QLabel(f"{item.get('price', 0):.2f} руб.")
        price_value.setStyleSheet(UTIL_FIELD)
        right_layout.addWidget(price_value)
        
        right_layout.addStretch()
        
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout, 1)
        
        card_frame.setLayout(main_layout)
        return card_frame

    # === создание новой поставки ===

    def open_new_delivery(self):
        """Открытие окна создания новой поставки"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Новая поставка")
        dialog.setGeometry(200, 200, 800, 600)
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Поставщик и дата
        top_layout = QVBoxLayout()
        
        supplier_layout = QHBoxLayout()
        supplier_label = QLabel("Поставщик:")
        supplier_label.setStyleSheet(SUBTITLE_STYLE)
        supplier_layout.addWidget(supplier_label)
        
        suppliers = db.get_suppliers()
        supplier_combo = QComboBox()
        supplier_combo.addItems([f"{s[1]} ({s[2]})" for s in suppliers])
        if suppliers:
            supplier_combo.setCurrentIndex(0)
        supplier_combo.setStyleSheet(COMBOBOX_STYLE)
        supplier_layout.addWidget(supplier_combo, 1)
        top_layout.addLayout(supplier_layout)
        
        date_layout = QHBoxLayout()
        date_label = QLabel("Дата:")
        date_label.setStyleSheet(SUBTITLE_STYLE)
        date_layout.addWidget(date_label)
        
        date_entry = QDateEdit()
        date_entry.setDate(QDate.currentDate())
        date_entry.setCalendarPopup(True)
        date_entry.setDisplayFormat("dd.MM.yyyy")
        date_layout.addWidget(date_entry)
        date_layout.addStretch()
        top_layout.addLayout(date_layout)
        
        layout.addLayout(top_layout)
        
        # Таблица позиций поставки (цена подставляется из БД при выборе товара)
        items_table = QTableWidget()
        items_table.setColumnCount(5)
        items_table.setHorizontalHeaderLabels([
            "Товар", "Артикул", "Количество", "Цена", "Сумма"
        ])
        
        header = items_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        layout.addWidget(items_table, 1)
        
        delivery_items = []  # (product_id, quantity, price_from_db)
        
        # Кнопки управления позициями
        buttons_layout = QHBoxLayout()
        
        def add_item_dialog():
            item_dialog = QDialog(dialog)
            item_dialog.setWindowTitle("Добавить товар в поставку")
            item_dialog.setGeometry(300, 300, 500, 200)
            item_dialog.setModal(True)
            
            item_layout = QVBoxLayout()
            item_layout.setSpacing(10)
            item_layout.setContentsMargins(20, 20, 20, 20)
            
            product_label = QLabel("Товар:")
            product_label.setStyleSheet(SUBTITLE_STYLE)
            item_layout.addWidget(product_label)
            
            products = db.get_products()
            display_products = []
            for p in products:
                name = p[1]
                sku = p[2]
                display_products.append((p[0], f"{name} ({sku})"))
            
            product_combo = QComboBox()
            product_combo.addItems([d[1] for d in display_products])
            if display_products:
                product_combo.setCurrentIndex(0)
            product_combo.setStyleSheet(COMBOBOX_STYLE)
            item_layout.addWidget(product_combo)
            
            quantity_label = QLabel("Количество:")
            quantity_label.setStyleSheet(SUBTITLE_STYLE)
            item_layout.addWidget(quantity_label)
            
            quantity_entry = QLineEdit()
            quantity_entry.setText("1")
            quantity_entry.setValidator(QRegExpValidator(QRegExp(r"[0-9]*")))
            quantity_entry.setStyleSheet(INPUT_STYLE)
            item_layout.addWidget(quantity_entry)
            
            def on_add():
                try:
                    idx = product_combo.currentIndex()
                    if idx < 0:
                        QMessageBox.critical(item_dialog, "Ошибка", "Выберите товар")
                        return
                    product_id = display_products[idx][0]
                    quantity = int(quantity_entry.text())
                    if quantity <= 0:
                        raise ValueError
                except ValueError:
                    QMessageBox.critical(item_dialog, "Ошибка", 
                                       "Введите положительное количество")
                    return

                # Цена из БД подставляется автоматически при выборе товара
                for p in products:
                    if p[0] == product_id:
                        name = p[1]
                        sku = p[2]
                        price = float(p[9] or 0)
                        amount = quantity * price
                        delivery_items.append((product_id, quantity, price))
                        row = items_table.rowCount()
                        items_table.insertRow(row)
                        items_table.setItem(row, 0, QTableWidgetItem(name))
                        items_table.setItem(row, 1, QTableWidgetItem(sku))
                        items_table.setItem(row, 2, QTableWidgetItem(str(quantity)))
                        items_table.setItem(row, 3, QTableWidgetItem(f"{price:.2f}"))
                        items_table.setItem(row, 4, QTableWidgetItem(f"{amount:.2f}"))
                        update_total()
                        break

                item_dialog.accept()
            
            add_btn = QPushButton("Добавить")
            add_btn.setStyleSheet(BUTTON_STYLE)
            add_btn.clicked.connect(on_add)
            item_layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignCenter)
            
            item_dialog.setLayout(item_layout)
            item_dialog.exec_()
        
        add_btn = QPushButton("Добавить товар")
        add_btn.setStyleSheet(BUTTON_STYLE)
        add_btn.clicked.connect(add_item_dialog)
        buttons_layout.addWidget(add_btn)
        
        def remove_selected_item():
            current_row = items_table.currentRow()
            if current_row < 0:
                return
            items_table.removeRow(current_row)
            if 0 <= current_row < len(delivery_items):
                delivery_items.pop(current_row)
            update_total()
        
        remove_btn = QPushButton("Удалить выбранный")
        remove_btn.setStyleSheet(BUTTON_STYLE)
        remove_btn.clicked.connect(remove_selected_item)
        buttons_layout.addWidget(remove_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Итоговая сумма и кнопка сохранения
        bottom_layout = QHBoxLayout()
        
        total_label = QLabel("Итого: 0.00 руб.")
        # Коричневый стиль для "Итого" в новой поставке
        total_label.setStyleSheet(BROWN_TOTAL_STYLE)
        bottom_layout.addWidget(total_label)
        
        def update_total():
            total = 0.0
            for row in range(items_table.rowCount()):
                amount_item = items_table.item(row, 4)
                if amount_item:
                    total += float(amount_item.text())
            total_label.setText(f"Итого: {total:.2f} руб.")
        
        bottom_layout.addStretch()
        
        def save_delivery():
            if not delivery_items:
                QMessageBox.critical(dialog, "Ошибка", "Добавьте хотя бы один товар в поставку")
                return

            supplier_text = supplier_combo.currentText()
            supplier_id = None
            for s in suppliers:
                if f"{s[1]} ({s[2]})" == supplier_text:
                    supplier_id = s[0]
                    break
            if not supplier_id:
                QMessageBox.critical(dialog, "Ошибка", "Выберите поставщика")
                return

            delivery_date = date_entry.date().toPyDate()

            try:
                db.create_delivery(supplier_id, delivery_date, delivery_items)
                QMessageBox.information(dialog, "Успех", "Поставка успешно сохранена")
                dialog.accept()
                self.load_deliveries()
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось сохранить поставку: {e}")
        save_btn = QPushButton("Сохранить поставку")
        save_btn.setStyleSheet(BUTTON_STYLE)
        save_btn.clicked.connect(save_delivery)
        bottom_layout.addWidget(save_btn)
        
        layout.addLayout(bottom_layout)
        dialog.setLayout(layout)
        
        dialog.exec_()
