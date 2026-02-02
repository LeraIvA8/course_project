from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel,
                             QPushButton, QScrollArea, QFrame,
                             QWidget, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import db
import os
from ui_styles import BUTTON_STYLE

# Стили как в каталоге (тот же back-office вид)
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

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None


class DiscountsWindow(QDialog):
    def __init__(self, parent, category_id=None, category_name=None):
        super().__init__(parent)
        self.category_id = category_id
        self.category_name = category_name or ""
        title = "Товары со скидками"
        if self.category_name:
            title = f"{title} — {self.category_name}"
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 900, 600)
        self.setModal(False)
        self.create_widgets()
        self.load_products()

    def create_widgets(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        title_text = "Товары со скидками"
        if self.category_name:
            title_text = f"{title_text} — {self.category_name}"
        title_label = QLabel(title_text)
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt; color: #333;")
        layout.addWidget(title_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: #f5f5f5; border: none; }")

        self.products_widget = QWidget()
        self.products_widget.setStyleSheet("background: #f5f5f5;")
        self.products_layout = QVBoxLayout()
        self.products_layout.setSpacing(12)
        self.products_layout.setContentsMargins(0, 0, 0, 0)
        self.products_widget.setLayout(self.products_layout)

        scroll_area.setWidget(self.products_widget)
        layout.addWidget(scroll_area, 1)

        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet(BUTTON_STYLE)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

    def load_products(self):
        while self.products_layout.count():
            child = self.products_layout.takeAt(0)
            if child is not None:
                w = child.widget()
                if w is not None:
                    w.deleteLater()

        try:
            if self.category_id is not None:
                products = db.get_discounted_products_by_category(self.category_id)
            else:
                products = db.get_discounted_products()

            if not products:
                no_label = QLabel("Товары со скидками не найдены")
                no_label.setStyleSheet("font-size: 11pt; color: #666;")
                no_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.products_layout.addWidget(no_label, alignment=Qt.AlignmentFlag.AlignCenter)
                return

            for i, product in enumerate(products):
                try:
                    card = self._create_card(product, i + 1)
                    self.products_layout.addWidget(card)
                except Exception as e:
                    print(f"Ошибка при создании карточки: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки товаров: {e}")
            err = QLabel(str(e))
            err.setStyleSheet("color: #c00;")
            self.products_layout.addWidget(err, alignment=Qt.AlignmentFlag.AlignCenter)

    def _create_card(self, product, card_index):
        """Карточка в стиле каталога: фото сверху, под ним Наименование, Цена, Артикул, Скидка."""
        product_id = product[0] if len(product) > 0 and product[0] is not None else 0
        name = product[1] if len(product) > 1 and product[1] is not None else "Без названия"
        sku = product[2] if len(product) > 2 and product[2] is not None else "—"
        price = product[9] if len(product) > 9 and product[9] is not None else 0
        current_price = product[12] if len(product) > 12 and product[12] is not None else price
        discount_percent = product[10] if len(product) > 10 and product[10] is not None else 0
        photo_path = product[13] if len(product) > 13 and product[13] is not None else None

        card_frame = QFrame()
        card_frame.setStyleSheet(UTIL_CARD_FRAME)
        card_frame.setMinimumWidth(220)
        card_frame.setMinimumHeight(320)

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(6)

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

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Наименование <значение>
        name_line = QLabel(f"Наименование {name}")
        name_line.setWordWrap(True)
        name_line.setAlignment(Qt.AlignmentFlag.AlignLeft)
        name_line.setStyleSheet(UTIL_FIELD)
        info_layout.addWidget(name_line)

        # Цена <значение>
        try:
            price_int = int(current_price if (current_price and (not price or current_price < price)) else price)
            price_text = f"{price_int:,}".replace(",", " ") + " руб."
        except (TypeError, ValueError):
            price_text = "— руб."
        price_line = QLabel(f"Цена {price_text}")
        price_line.setAlignment(Qt.AlignmentFlag.AlignLeft)
        price_line.setStyleSheet(UTIL_FIELD)
        info_layout.addWidget(price_line)

        # Артикул <значение>
        sku_line = QLabel(f"Артикул {sku}")
        sku_line.setAlignment(Qt.AlignmentFlag.AlignLeft)
        sku_line.setStyleSheet(UTIL_FIELD)
        info_layout.addWidget(sku_line)

        # Скидка <значение>
        discount_text = f"{discount_percent} %" if discount_percent else "—"
        discount_line = QLabel(f"Скидка {discount_text}")
        discount_line.setAlignment(Qt.AlignmentFlag.AlignLeft)
        discount_line.setStyleSheet(UTIL_FIELD)
        info_layout.addWidget(discount_line)

        card_layout.addLayout(info_layout)
        card_frame.setLayout(card_layout)
        return card_frame
