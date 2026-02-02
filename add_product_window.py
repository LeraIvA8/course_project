from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QMessageBox, 
                             QFileDialog, QScrollArea, QWidget)
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QPixmap, QImage, QRegExpValidator
import db
import os
import shutil
from ui_styles import (BUTTON_STYLE, TITLE_STYLE, SUBTITLE_STYLE, INPUT_STYLE, COMBOBOX_STYLE,
                      CARD_STYLE, ADD_PRODUCT_TITLE_STYLE, SKU_BOLD_STYLE)
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

class AddProductWindow(QDialog):
    def __init__(self, parent, category_id=None, on_success=None):
        super().__init__(parent)
        self.category_id = category_id
        self.on_success = on_success
        self.setWindowTitle("Добавить товар")
        self.setGeometry(200, 200, 800, 700)
        self.setModal(True)
        
        self.categories = []
        self.suppliers = []
        self.selected_photo_path = None  # Путь к выбранному фото
        self.load_data()
        self.create_widgets()
        
    def load_data(self):
        """Загрузка категорий и поставщиков"""
        self.categories = db.get_categories()
        self.suppliers = db.get_suppliers()
        
    def create_widgets(self):
        # Основной layout с двумя колонками
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)
        
        # Левая колонка: фото
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        
        # Заголовок с названием категории
        category_name = "товар"
        if self.category_id:
            for cat in self.categories:
                if cat[0] == self.category_id:
                    category_name = cat[1].lower()
                    break
        
        title_label = QLabel(f"Добавить {category_name}")
        title_label.setStyleSheet(ADD_PRODUCT_TITLE_STYLE)
        left_layout.addWidget(title_label)
        
        # Поле для фото
        self.photo_label = QLabel("[Фото]")
        self.photo_label.setFixedSize(180, 180)
        self.photo_label.setAlignment(Qt.AlignCenter)
        photo_style = CARD_STYLE.replace("QFrame", "QLabel").replace("border-radius: 10px;", "border-radius: 10px; padding: 0px;")
        self.photo_label.setStyleSheet(photo_style)
        self.photo_label.mousePressEvent = lambda e: self.select_photo()
        left_layout.addWidget(self.photo_label)
        
        # Кнопка "Добавить" внизу слева
        add_button = QPushButton("Добавить")
        add_button.setStyleSheet(BUTTON_STYLE)
        add_button.clicked.connect(self.add_product)
        left_layout.addWidget(add_button, alignment=Qt.AlignLeft)
        
        left_layout.addStretch()
        
        # Правая колонка: поля ввода
        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)
        
        # Наименование (только буквы)
        name_label = QLabel("Наименование")
        name_label.setStyleSheet(SUBTITLE_STYLE)
        right_layout.addWidget(name_label)
        
        self.name_entry = QLineEdit()
        self.name_entry.setValidator(QRegExpValidator(QRegExp(r"[a-zA-Zа-яА-ЯёЁ\s\-]*")))
        self.name_entry.setStyleSheet(INPUT_STYLE)
        right_layout.addWidget(self.name_entry)
        
        # Категория
        category_label = QLabel("Категория")
        category_label.setStyleSheet(SUBTITLE_STYLE)
        right_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems([cat[1] for cat in self.categories])
        if self.categories:
            if self.category_id:
                for i, cat in enumerate(self.categories):
                    if cat[0] == self.category_id:
                        self.category_combo.setCurrentIndex(i)
                        break
                else:
                    self.category_combo.setCurrentIndex(0)
            else:
                self.category_combo.setCurrentIndex(0)
        self.category_combo.setStyleSheet(COMBOBOX_STYLE)
        right_layout.addWidget(self.category_combo)
        
        # Артикул (английские буквы и цифры)
        sku_label = QLabel("Артикул")
        sku_label.setStyleSheet(SKU_BOLD_STYLE)
        right_layout.addWidget(sku_label)
        
        self.sku_entry = QLineEdit()
        self.sku_entry.setValidator(QRegExpValidator(QRegExp(r"[a-zA-Z0-9]*")))
        self.sku_entry.setStyleSheet(INPUT_STYLE + " font-weight: bold;")
        right_layout.addWidget(self.sku_entry)
        
        # Цена (только цифры)
        price_label = QLabel("Цена")
        price_label.setStyleSheet(SUBTITLE_STYLE)
        right_layout.addWidget(price_label)
        
        self.price_entry = QLineEdit()
        self.price_entry.setValidator(QRegExpValidator(QRegExp(r"[0-9]*\.?[0-9]*")))
        self.price_entry.setStyleSheet(INPUT_STYLE)
        right_layout.addWidget(self.price_entry)
        
        # Поставщик
        supplier_label = QLabel("Поставщик")
        supplier_label.setStyleSheet(SUBTITLE_STYLE)
        right_layout.addWidget(supplier_label)
        
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("Не выбран", None)
        for supplier in self.suppliers:
            if len(supplier) > 1:
                self.supplier_combo.addItem(supplier[1], supplier[0])
        self.supplier_combo.setStyleSheet(COMBOBOX_STYLE)
        right_layout.addWidget(self.supplier_combo)
        
        # Габариты (только цифры и разделители: пробел, запятая, x)
        dimensions_label = QLabel("Габариты")
        dimensions_label.setStyleSheet(SUBTITLE_STYLE)
        right_layout.addWidget(dimensions_label)
        
        self.dimensions_entry = QLineEdit()
        self.dimensions_entry.setPlaceholderText("Длина x Ширина x Высота (см)")
        self.dimensions_entry.setValidator(QRegExpValidator(QRegExp(r"[0-9\s,\.xX]*")))
        self.dimensions_entry.setStyleSheet(INPUT_STYLE)
        right_layout.addWidget(self.dimensions_entry)
        
        # Материал (только буквы)
        material_label = QLabel("Материал")
        material_label.setStyleSheet(SUBTITLE_STYLE)
        right_layout.addWidget(material_label)
        
        self.material_entry = QLineEdit()
        self.material_entry.setValidator(QRegExpValidator(QRegExp(r"[a-zA-Zа-яА-ЯёЁ\s\-]*")))
        self.material_entry.setStyleSheet(INPUT_STYLE)
        right_layout.addWidget(self.material_entry)
        
        # Цвет (только буквы)
        color_label = QLabel("Цвет")
        color_label.setStyleSheet(SUBTITLE_STYLE)
        right_layout.addWidget(color_label)
        
        self.color_entry = QLineEdit()
        self.color_entry.setValidator(QRegExpValidator(QRegExp(r"[a-zA-Zа-яА-ЯёЁ\s\-]*")))
        self.color_entry.setStyleSheet(INPUT_STYLE)
        right_layout.addWidget(self.color_entry)
        
        # Скидка (%) — только цифры
        discount_label = QLabel("Скидка (%)")
        discount_label.setStyleSheet(SUBTITLE_STYLE)
        right_layout.addWidget(discount_label)
        
        self.discount_entry = QLineEdit()
        self.discount_entry.setPlaceholderText("0")
        self.discount_entry.setValidator(QRegExpValidator(QRegExp(r"[0-9]*\.?[0-9]*")))
        self.discount_entry.setStyleSheet(INPUT_STYLE)
        right_layout.addWidget(self.discount_entry)
        
        right_layout.addStretch()
        
        # Объединяем левую и правую колонки
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout, 1)
        
        self.setLayout(main_layout)
        
    
    def select_photo(self, event=None):
        """Выбор фотографии товара"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите фотографию товара",
            "",
            "Изображения (*.jpg *.jpeg *.png *.gif *.bmp);;Все файлы (*.*)"
        )
        if filepath:
            self.selected_photo_path = filepath
            # Показываем превью
            if HAS_PIL:
                try:
                    img = Image.open(filepath)
                    img = img.resize((180, 180))
                    # Конвертируем PIL Image в QPixmap
                    img_rgb = img.convert('RGB')
                    img_bytes = img_rgb.tobytes('raw', 'RGB')
                    qimg = QImage(img_bytes, img.width, img.height, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimg)
                    self.photo_label.setPixmap(pixmap)
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить изображение: {e}")
                    self.selected_photo_path = None
            else:
                # Если PIL не установлен, просто показываем имя файла
                filename = os.path.basename(filepath)
                self.photo_label.setText(f"Выбрано:\n{filename[:20]}")
        
    def add_product(self):
        try:
            # Получение данных из формы
            name = self.name_entry.text().strip()
            sku = self.sku_entry.text().strip()
            price_str = self.price_entry.text().strip()
            dimensions_str = self.dimensions_entry.text().strip()
            material = self.material_entry.text().strip()
            color = self.color_entry.text().strip()
            discount_str = self.discount_entry.text().strip() or "0"
            
            # Валидация
            if not name:
                QMessageBox.critical(self, "Ошибка", "Введите наименование товара")
                return
                
            if not sku:
                QMessageBox.critical(self, "Ошибка", "Введите артикул")
                return
                
            if not price_str:
                QMessageBox.critical(self, "Ошибка", "Введите цену")
                return
                
            try:
                price = float(price_str)
                if price <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.critical(self, "Ошибка", "Цена должна быть положительным числом")
                return
            
            try:
                discount = float(discount_str)
                if discount < 0 or discount > 100:
                    raise ValueError
            except ValueError:
                QMessageBox.critical(self, "Ошибка", "Скидка должна быть числом от 0 до 100")
                return
            
            # Получение ID категории
            category_name = self.category_combo.currentText()
            category_id = None
            for cat in self.categories:
                if cat[1] == category_name:
                    category_id = cat[0]
                    break
            
            if not category_id:
                QMessageBox.critical(self, "Ошибка", "Выберите категорию")
                return
            
            # Парсинг габаритов из одного поля (формат: "Длина x Ширина x Высота")
            length = None
            width = None
            height = None
            if dimensions_str:
                try:
                    # Пробуем распарсить формат "Длина x Ширина x Высота" или "Длина, Ширина, Высота"
                    parts = dimensions_str.replace('x', ',').replace('X', ',').split(',')
                    parts = [p.strip() for p in parts if p.strip()]
                    if len(parts) >= 1:
                        length = float(parts[0])
                    if len(parts) >= 2:
                        width = float(parts[1])
                    if len(parts) >= 3:
                        height = float(parts[2])
                except ValueError:
                    # Если не удалось распарсить, оставляем None
                    pass
            
            # Добавление в базу данных (сначала без фото)
            product_id = db.add_product(
                name=name,
                category_id=category_id,
                sku=sku,
                price=price,
                length=length,
                width=width,
                height=height,
                material=material if material else None,
                color=color if color else None,
                discount_percent=discount,
                photo_path=None  # Пока без фото
            )
            
            # Обработка фотографии
            photo_path_db = None
            if self.selected_photo_path and os.path.exists(self.selected_photo_path):
                try:
                    # Создаем папку для товара
                    product_photo_dir = os.path.join(db.PHOTO_BASE_PATH, str(product_id))
                    os.makedirs(product_photo_dir, exist_ok=True)
                    
                    # Копируем фото в папку товара
                    file_ext = os.path.splitext(self.selected_photo_path)[1]
                    photo_filename = f"photo{file_ext}"
                    photo_dest_path = os.path.join(product_photo_dir, photo_filename)
                    shutil.copy2(self.selected_photo_path, photo_dest_path)
                    
                    # Сохраняем относительный путь в БД
                    photo_path_db = os.path.join(db.PHOTO_BASE_PATH, str(product_id), photo_filename)
                    
                    # Обновляем товар с путем к фото
                    db.update_product(
                        product_id=product_id,
                        name=name,
                        category_id=category_id,
                        sku=sku,
                        price=price,
                        length=length,
                        width=width,
                        height=height,
                        material=material if material else None,
                        color=color if color else None,
                        discount_percent=discount,
                        photo_path=photo_path_db
                    )
                except Exception as e:
                    QMessageBox.warning(self, "Предупреждение", 
                                      f"Товар добавлен, но не удалось сохранить фотографию: {e}")
            
            QMessageBox.information(self, "Успех", "Товар успешно добавлен")
            
            if self.on_success:
                self.on_success()
                
            self.accept()
            
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении товара: {str(e)}")
