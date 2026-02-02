from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import os
from ui_styles import (BUTTON_STYLE, TITLE_STYLE, SUBTITLE_STYLE, DETAILS_TITLE_STYLE,
                      DETAILS_PHOTO_STYLE, DETAILS_NAME_STYLE, ERROR_STYLE)
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class ProductDetailsWindow(QDialog):
    def __init__(self, parent, product):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Характеристики товара")
        self.setGeometry(200, 200, 600, 700)
        self.setModal(True)
        self.create_widgets()
    
    def create_widgets(self):
        """Создание интерфейса"""
        # Создаем scroll area для прокрутки
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("Характеристики товара")
        title_label.setStyleSheet(DETAILS_TITLE_STYLE)
        layout.addWidget(title_label)
        
        # product: (id, name, sku, category, material, color, length, width, height, price, discount_percent, stock_quantity, current_price, photo_path)
        if self.product:
            # Фотография товара
            photo_label = QLabel()
            photo_label.setAlignment(Qt.AlignCenter)
            photo_label.setFixedHeight(250)
            photo_label.setStyleSheet(DETAILS_PHOTO_STYLE)
            
            photo_path = self.product[13] if len(self.product) > 13 else None
            if photo_path and HAS_PIL:
                try:
                    full_path = photo_path if os.path.isabs(photo_path) else os.path.join(os.getcwd(), photo_path)
                    if os.path.exists(full_path):
                        img = Image.open(full_path)
                        # Масштабируем изображение, сохраняя пропорции
                        img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                        img_rgb = img.convert('RGB')
                        img_bytes = img_rgb.tobytes('raw', 'RGB')
                        qimg = QImage(img_bytes, img.width, img.height, QImage.Format_RGB888)
                        pixmap = QPixmap.fromImage(qimg)
                        photo_label.setPixmap(pixmap)
                        photo_label.setScaledContents(True)
                except Exception as e:
                    photo_label.setText("[Фото не загружено]")
                    print(f"Ошибка загрузки фото: {e}")
            else:
                photo_label.setText("[Фото отсутствует]")
            
            layout.addWidget(photo_label)
            
            # Информация о товаре
            info_layout = QVBoxLayout()
            info_layout.setSpacing(10)
            
            # Наименование
            name_label = QLabel(f"Наименование: {self.product[1] or 'Не указано'}")
            name_label.setStyleSheet(DETAILS_NAME_STYLE)
            info_layout.addWidget(name_label)
            
            # Артикул
            sku_label = QLabel(f"Артикул: {self.product[2] or 'Не указано'}")
            sku_label.setStyleSheet(SUBTITLE_STYLE)
            info_layout.addWidget(sku_label)
            
            # Категория
            category_label = QLabel(f"Категория: {self.product[3] or 'Не указано'}")
            category_label.setStyleSheet(SUBTITLE_STYLE)
            info_layout.addWidget(category_label)
            
            # Цена
            price_value = self.product[9] if self.product[9] else 0
            price_int = int(price_value)
            price_text = f"{price_int:,}".replace(",", ".") + " руб"
            price_label = QLabel(f"Цена: {price_text}")
            price_label.setStyleSheet(SUBTITLE_STYLE)
            info_layout.addWidget(price_label)
            
            # Цена со скидкой
            if len(self.product) > 12 and self.product[12] and self.product[12] < price_value:
                discount_percent = self.product[10] if self.product[10] else 0
                current_price_int = int(self.product[12])
                current_price_text = f"{current_price_int:,}".replace(",", ".") + " руб"
                disc_price_label = QLabel(
                    f"Цена со скидкой: {current_price_text} (скидка {discount_percent:.0f}%)"
                )
                disc_price_label.setStyleSheet(SUBTITLE_STYLE + " font-weight: bold; color: red;")
                info_layout.addWidget(disc_price_label)
            
            # Остаток на складе
            stock_quantity = self.product[11] if len(self.product) > 11 else 0
            stock_label = QLabel(f"Остаток на складе: {stock_quantity} шт.")
            stock_label.setStyleSheet(SUBTITLE_STYLE)
            info_layout.addWidget(stock_label)
            
            # Материал
            if self.product[4]:
                material_label = QLabel(f"Материал: {self.product[4]}")
                material_label.setStyleSheet(SUBTITLE_STYLE)
                info_layout.addWidget(material_label)
            
            # Цвет
            if self.product[5]:
                color_label = QLabel(f"Цвет: {self.product[5]}")
                color_label.setStyleSheet(SUBTITLE_STYLE)
                info_layout.addWidget(color_label)
            
            # Размеры
            dimensions = []
            if self.product[6]:  # length
                dimensions.append(f"Длина: {self.product[6]} см")
            if self.product[7]:  # width
                dimensions.append(f"Ширина: {self.product[7]} см")
            if self.product[8]:  # height
                dimensions.append(f"Высота: {self.product[8]} см")
            
            if dimensions:
                dimensions_label = QLabel(" | ".join(dimensions))
                dimensions_label.setStyleSheet(SUBTITLE_STYLE)
                info_layout.addWidget(dimensions_label)
            
            layout.addLayout(info_layout)
        
        layout.addStretch()
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet(BUTTON_STYLE)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        content_widget.setLayout(layout)
        scroll_area.setWidget(content_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
