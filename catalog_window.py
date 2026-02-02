from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QMessageBox, QScrollArea,
                             QFrame, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from functools import partial
import db
import os
from ui_styles import (BUTTON_STYLE, TITLE_STYLE, SUBTITLE_STYLE,
                      INFO_STYLE, ERROR_STYLE)
from add_product_window import AddProductWindow
from edit_product_window import EditProductWindow
from search_window import SearchWindow
from discounts_window import DiscountsWindow
from product_details_window import ProductDetailsWindow
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None  # type: ignore[misc, assignment]

# Утилитарные стили для back-office
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
UTIL_INPUT = """
    QLineEdit {
        border: 1px solid #999;
        padding: 4px 8px;
        font-size: 10pt;
        background-color: white;
    }
"""


class CatalogWindow(QWidget):
    def __init__(self, parent, category_id=None, category_name=None, on_refresh=None, user_data=None):
        super().__init__(parent)
        self.category_id = category_id
        self.category_name = category_name
        self.on_refresh = on_refresh
        self.user = user_data or {}
        self.selected_product_id = None

        self.create_interface()

    def create_interface(self):
        """Создание интерфейса каталога: заголовок, поля Поиск и Скидки %, сетка карточек, панель Удалить/Добавить."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Верхняя часть: заголовок категории слева, справа — Поиск и кнопка Скидки
        top_layout = QHBoxLayout()
        top_layout.setSpacing(16)

        title_text = (self.category_name if self.category_name else "Каталог").upper()
        title_label = QLabel(title_text)
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt; color: #705847;")
        top_layout.addWidget(title_label)

        top_layout.addStretch()

        search_label = QLabel("Поиск")
        search_label.setStyleSheet(UTIL_LABEL)
        top_layout.addWidget(search_label)
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("артикул")
        self.search_entry.setMinimumWidth(180)
        self.search_entry.setStyleSheet(UTIL_INPUT)
        self.search_entry.returnPressed.connect(self._on_search_enter)
        top_layout.addWidget(self.search_entry)

        discounts_btn = QPushButton("Скидки")
        discounts_btn.setStyleSheet(BUTTON_STYLE)
        discounts_btn.clicked.connect(self.open_discounts_window)
        top_layout.addWidget(discounts_btn)

        main_layout.addLayout(top_layout)

        # Сетка товаров (карточки)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: #f5f5f5; border: none; }")

        self.products_widget = QWidget()
        self.products_widget.setStyleSheet("background: #f5f5f5;")
        self.products_layout = QGridLayout()
        self.products_layout.setSpacing(12)
        self.products_layout.setContentsMargins(0, 0, 0, 0)
        self.products_widget.setLayout(self.products_layout)

        scroll_area.setWidget(self.products_widget)
        main_layout.addWidget(scroll_area, 1)

        # Панель управления: слева "Удалить", справа "Добавить"
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)

        user_role = (self.user.get('role', '') or '').lower()
        is_admin = user_role in ('администратор', 'administrator', 'admin')

        bottom_layout.addStretch()

        delete_btn = QPushButton("Удалить")
        delete_btn.setStyleSheet(BUTTON_STYLE)
        delete_btn.clicked.connect(self.delete_product)
        bottom_layout.addWidget(delete_btn)

        add_btn = QPushButton("Добавить")
        add_btn.setStyleSheet(BUTTON_STYLE)
        add_btn.clicked.connect(self.open_add_product_window)
        bottom_layout.addWidget(add_btn)

        if not is_admin:
            delete_btn.setEnabled(False)
            delete_btn.setToolTip("Доступно только администратору")
            add_btn.setEnabled(False)
            add_btn.setToolTip("Доступно только администратору")

        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

        if self.category_id is not None:
            self.load_products()
        else:
            no_category_label = QLabel("Выберите категорию для просмотра товаров")
            no_category_label.setStyleSheet(INFO_STYLE)
            no_category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.products_layout.addWidget(no_category_label, 0, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)
    
    def _on_search_enter(self):
        """По Enter в поле поиска — поиск по артикулу/названию или сброс."""
        if self.search_entry.text().strip():
            self.search_product()
        else:
            self.load_products()

    def load_products(self):
        """Загрузка товаров категории с учётом фильтра скидок."""
        while self.products_layout.count():
            child = self.products_layout.takeAt(0)
            if child is not None:
                w = child.widget()
                if w is not None:
                    w.deleteLater()

        try:
            products = db.get_products(category_id=self.category_id)
            if not products:
                no_products_label = QLabel("Товары не найдены")
                no_products_label.setStyleSheet(INFO_STYLE)
                no_products_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.products_layout.addWidget(no_products_label, 0, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)
                return

            row, col, cols_per_row = 0, 0, 3
            for i, product in enumerate(products):
                if col >= cols_per_row:
                    col = 0
                    row += 1
                try:
                    card = self.create_product_card(product, card_index=i + 1)
                    self.products_layout.addWidget(card, row, col)
                    col += 1
                except Exception as e:
                    print(f"Ошибка при создании карточки товара {i}: {e}")
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки товаров: {e}")
            err = QLabel(f"Ошибка загрузки товаров: {e}")
            err.setStyleSheet(ERROR_STYLE)
            self.products_layout.addWidget(err, 0, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)
    
    def create_product_card(self, product, card_index=1):
        """Карточка товара: серый квадрат-заглушка с номером, справа — Наименование, Артикул, Цена, Скидка. Текст по левому краю."""
        try:
            product_id = product[0] if len(product) > 0 and product[0] is not None else 0
            name = product[1] if len(product) > 1 and product[1] is not None else "Без названия"
            sku = product[2] if len(product) > 2 and product[2] is not None else "—"
            price = product[9] if len(product) > 9 and product[9] is not None else 0
            current_price = product[12] if len(product) > 12 and product[12] is not None else price
            discount_percent = product[10] if len(product) > 10 and product[10] is not None else 0
            photo_path = product[13] if len(product) > 13 and product[13] is not None else None

            card_frame = QFrame()
            card_frame.setStyleSheet(UTIL_CARD_FRAME)
            card_frame.setMinimumWidth(160)
            card_frame.setMinimumHeight(220)

            card_layout = QVBoxLayout()
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(6)

            # Фото сверху
            photo_label = QLabel(str(card_index))
            photo_label.setFixedSize(200, 200)
            photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            photo_label.setStyleSheet(UTIL_PLACEHOLDER)

            if photo_path and HAS_PIL and Image is not None:
                try:
                    full_path = photo_path if os.path.isabs(photo_path) else os.path.join(os.getcwd(), photo_path)
                    if os.path.exists(full_path):
                        img = Image.open(full_path)
                        img = img.resize((200, 200))
                        img_rgb = img.convert('RGB')
                        img_bytes = img_rgb.tobytes('raw', 'RGB')
                        qimg = QImage(img_bytes, img.width, img.height, QImage.Format_RGB888)
                        pixmap = QPixmap.fromImage(qimg)
                        photo_label.setPixmap(pixmap)
                except Exception as e:
                    print(f"Ошибка загрузки фото для товара {product_id}: {e}")

            card_layout.addWidget(photo_label, alignment=Qt.AlignmentFlag.AlignCenter)

            # Под фото: Наименование, Цена, Артикул, Скидка — в одну строку с значением
            info_layout = QVBoxLayout()
            info_layout.setSpacing(0)
            info_layout.setContentsMargins(0, 0, 0, 0)
            info_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

            # Наименование <значение>
            name_line = QLabel(f"Наименование {name}")
            name_line.setWordWrap(True)
            name_line.setAlignment(Qt.AlignmentFlag.AlignLeft)
            name_line.setStyleSheet(UTIL_FIELD)
            info_layout.addWidget(name_line)

            # Цена, Артикул, Скидка — без промежутков между строками
            compact_style = UTIL_FIELD + " margin: 0; padding: 0;"
            try:
                price_int = int(current_price if (current_price and (not price or current_price < price)) else price)
                price_text = f"{price_int:,}".replace(",", " ") + " руб."
            except (TypeError, ValueError):
                price_text = "— руб."
            price_line = QLabel(f"Цена {price_text}")
            price_line.setAlignment(Qt.AlignmentFlag.AlignLeft)
            price_line.setStyleSheet(compact_style)
            info_layout.addWidget(price_line)

            sku_line = QLabel(f"Артикул {sku}")
            sku_line.setAlignment(Qt.AlignmentFlag.AlignLeft)
            sku_line.setStyleSheet(compact_style)
            info_layout.addWidget(sku_line)

            discount_text = f"{discount_percent} %" if discount_percent else "—"
            discount_line = QLabel(f"Скидка {discount_text}")
            discount_line.setAlignment(Qt.AlignmentFlag.AlignLeft)
            discount_line.setStyleSheet(compact_style)
            info_layout.addWidget(discount_line)

            card_layout.addLayout(info_layout)

            # Кнопка редактирования товара
            edit_btn = QPushButton("Редактировать")
            edit_btn.setStyleSheet(BUTTON_STYLE)
            edit_btn.clicked.connect(partial(self.edit_product, product_id))
            user_role = (self.user.get('role', '') or '').lower()
            is_admin = user_role in ('администратор', 'administrator', 'admin')
            if not is_admin:
                edit_btn.setEnabled(False)
                edit_btn.setToolTip("Доступно только администратору")
            card_layout.addWidget(edit_btn)

            card_frame.setLayout(card_layout)
            card_frame.product_id = product_id

            def mouse_press_handler(a0):
                self.select_product(product_id)
                QFrame.mousePressEvent(card_frame, a0)

            def mouse_double_click_handler(a0):
                self.show_product_details(product_id)
                QFrame.mouseDoubleClickEvent(card_frame, a0)

            card_frame.mousePressEvent = mouse_press_handler
            card_frame.mouseDoubleClickEvent = mouse_double_click_handler

            return card_frame
        except Exception as e:
            print(f"Критическая ошибка при создании карточки товара: {e}")
            import traceback
            traceback.print_exc()
            error_frame = QFrame()
            error_frame.setStyleSheet(UTIL_CARD_FRAME)
            error_label = QLabel("Ошибка загрузки товара")
            error_label.setStyleSheet(ERROR_STYLE)
            el = QVBoxLayout()
            el.addWidget(error_label)
            error_frame.setLayout(el)
            return error_frame
    
    def select_product(self, product_id):
        """Выбор товара"""
        self.selected_product_id = product_id
    
    def search_product(self):
        """Поиск товара по артикулу"""
        sku = self.search_entry.text().strip()
        if not sku:
            QMessageBox.information(self, "Поиск", "Введите артикул для поиска")
            return
        
        try:
            product = db.search_product(sku)
            if product:
                search_window = SearchWindow(self.window(), product)
                search_window.show()
            else:
                QMessageBox.information(self, "Поиск", f"Товар с артикулом {sku} не найден")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка поиска: {e}")
    
    def open_discounts_window(self):
        """Открыть окно со всеми товарами со скидками по выбранной категории (тот же стиль, что и каталог)."""
        discounts_window = DiscountsWindow(  # type: ignore[call-arg]
            self.window(),
            category_id=self.category_id,
            category_name=self.category_name,
        )
        discounts_window.show()

    
    
    def delete_product(self):
        """Удаление товара"""
        if not self.selected_product_id:
            QMessageBox.warning(self, "Удаление", "Сначала выберите товар")
            return
        
        reply = QMessageBox.question(self, "Удаление", 
                                    "Вы уверены, что хотите удалить выбранный товар?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                db.delete_product(self.selected_product_id)
                QMessageBox.information(self, "Успех", "Товар удален")
                self.selected_product_id = None
                self.load_products()
                if self.on_refresh:
                    self.on_refresh()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить товар: {e}")
    
    def show_product_details(self, product_id):
        """Показать все характеристики товара"""
        try:
            product = db.get_product_by_id(product_id)
            if product:
                details_window = ProductDetailsWindow(self.window(), product)
                details_window.show()
            else:
                QMessageBox.critical(self, "Ошибка", "Товар не найден")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке товара: {e}")
    
    def edit_product(self, product_id):
        """Редактирование товара"""
        try:
            product = db.get_product_by_id(product_id)
            if product:
                edit_window = EditProductWindow(self.window(), product, 
                                              on_success=self.load_products)
                edit_window.show()
            else:
                QMessageBox.critical(self, "Ошибка", "Товар не найден")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке товара: {e}")
    
    def open_add_product_window(self):
        """Открытие окна для добавления товара"""
        if not self.category_id:
            QMessageBox.warning(self, "Добавление", "Сначала выберите категорию")
            return
        
        add_window = AddProductWindow(self.window(), 
                                    category_id=self.category_id,
                                    on_success=self.load_products)
        add_window.show()
