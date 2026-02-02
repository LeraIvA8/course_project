from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton)
from PyQt5.QtCore import Qt
from ui_styles import BUTTON_STYLE, TITLE_STYLE, SUBTITLE_STYLE


class SearchWindow(QDialog):
    def __init__(self, parent, product):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Результат поиска")
        self.setGeometry(200, 200, 500, 400)
        self.setModal(True)
        self.create_widgets()
    
    def create_widgets(self):
        """Создание интерфейса"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("Результат поиска")
        title_label.setStyleSheet(TITLE_STYLE)
        layout.addWidget(title_label)
        
        # product: (id, name, sku, category, material, color, length, width, height, price, discount_percent, stock_quantity, current_price, ...)
        p = self.product
        if p and len(p) >= 13:
            info_layout = QVBoxLayout()
            info_layout.setSpacing(5)

            def _val(i, default=""):
                if i >= len(p) or p[i] is None:
                    return default
                return p[i]

            def _num(i, default=0):
                try:
                    return float(p[i]) if i < len(p) and p[i] is not None else default
                except (TypeError, ValueError):
                    return default

            name_label = QLabel(f"Наименование: {_val(1)}")
            name_label.setStyleSheet("font-size: 11pt;")
            info_layout.addWidget(name_label)

            sku_label = QLabel(f"Артикул: {_val(2)}")
            sku_label.setStyleSheet("font-size: 11pt;")
            info_layout.addWidget(sku_label)

            category_label = QLabel(f"Категория: {_val(3)}")
            category_label.setStyleSheet("font-size: 11pt;")
            info_layout.addWidget(category_label)

            price = _num(9)
            price_label = QLabel(f"Цена: {price:.2f} руб.")
            price_label.setStyleSheet("font-size: 11pt;")
            info_layout.addWidget(price_label)

            current_price = _num(12)
            discount = _num(10)
            if current_price < price and discount > 0:
                disc_price_label = QLabel(
                    f"Цена со скидкой: {current_price:.2f} руб. (скидка {discount:.0f}%)"
                )
                disc_price_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: red;")
                info_layout.addWidget(disc_price_label)

            stock_label = QLabel(f"Остаток: {_val(11, '0')} шт.")
            stock_label.setStyleSheet(SUBTITLE_STYLE)
            info_layout.addWidget(stock_label)

            if _val(4):
                material_label = QLabel(f"Материал: {_val(4)}")
                material_label.setStyleSheet(SUBTITLE_STYLE)
                info_layout.addWidget(material_label)

            if _val(5):
                color_label = QLabel(f"Цвет: {_val(5)}")
                color_label.setStyleSheet(SUBTITLE_STYLE)
                info_layout.addWidget(color_label)

            layout.addLayout(info_layout)
        elif not p or len(p) < 2:
            not_found = QLabel("Товар не найден")
            not_found.setStyleSheet(SUBTITLE_STYLE)
            layout.addWidget(not_found)
        
        layout.addStretch()
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet(BUTTON_STYLE)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)
