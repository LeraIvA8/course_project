from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QMessageBox, 
                             QFileDialog, QScrollArea, QWidget)
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QPixmap, QImage, QRegExpValidator
import db
import os
import shutil
from ui_styles import (BUTTON_STYLE, TITLE_STYLE, SUBTITLE_STYLE, INPUT_STYLE, COMBOBOX_STYLE,
                      CARD_STYLE)
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class EditProductWindow(QDialog):
    def __init__(self, parent, product, on_success=None):
        super().__init__(parent)
        self.product = product
        self.on_success = on_success
        self.setWindowTitle("Редактировать товар")
        self.setGeometry(200, 200, 500, 600)
        self.setModal(True)
        
        self.categories = db.get_categories()
        self.selected_photo_path = None  # Путь к выбранному фото
        self.create_widgets()
        self.load_product_data()
    
    def create_widgets(self):
        """Создание интерфейса"""
        # Создаем scroll area для формы
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        form_widget = QWidget()
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("Редактировать товар")
        title_label.setStyleSheet(TITLE_STYLE)
        form_layout.addWidget(title_label)
        
        # Наименование (только буквы)
        name_label = QLabel("Наименование")
        name_label.setStyleSheet(SUBTITLE_STYLE)
        form_layout.addWidget(name_label)
        
        self.name_entry = QLineEdit()
        self.name_entry.setValidator(QRegExpValidator(QRegExp(r"[a-zA-Zа-яА-ЯёЁ\s\-]*")))
        self.name_entry.setStyleSheet(INPUT_STYLE)
        form_layout.addWidget(self.name_entry)
        
        # Категория
        category_label = QLabel("Категория")
        category_label.setStyleSheet(SUBTITLE_STYLE)
        form_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems([cat[1] for cat in self.categories])
        self.category_combo.setStyleSheet(COMBOBOX_STYLE)
        form_layout.addWidget(self.category_combo)
        
        # Артикул
        sku_label = QLabel("Артикул")
        sku_label.setStyleSheet(SUBTITLE_STYLE)
        form_layout.addWidget(sku_label)
        
        self.sku_entry = QLineEdit()
        self.sku_entry.setStyleSheet(INPUT_STYLE)
        form_layout.addWidget(self.sku_entry)
        
        # Цена (только цифры)
        price_label = QLabel("Цена")
        price_label.setStyleSheet(SUBTITLE_STYLE)
        form_layout.addWidget(price_label)
        
        self.price_entry = QLineEdit()
        self.price_entry.setValidator(QRegExpValidator(QRegExp(r"[0-9]*\.?[0-9]*")))
        self.price_entry.setStyleSheet(INPUT_STYLE)
        form_layout.addWidget(self.price_entry)
        
        # Длина (только цифры)
        length_label = QLabel("Длина")
        length_label.setStyleSheet(SUBTITLE_STYLE)
        form_layout.addWidget(length_label)
        
        self.length_entry = QLineEdit()
        self.length_entry.setValidator(QRegExpValidator(QRegExp(r"[0-9]*\.?[0-9]*")))
        self.length_entry.setStyleSheet(INPUT_STYLE)
        form_layout.addWidget(self.length_entry)
        
        # Ширина (только цифры)
        width_label = QLabel("Ширина")
        width_label.setStyleSheet(SUBTITLE_STYLE)
        form_layout.addWidget(width_label)
        
        self.width_entry = QLineEdit()
        self.width_entry.setValidator(QRegExpValidator(QRegExp(r"[0-9]*\.?[0-9]*")))
        self.width_entry.setStyleSheet(INPUT_STYLE)
        form_layout.addWidget(self.width_entry)
        
        # Высота (только цифры)
        height_label = QLabel("Высота")
        height_label.setStyleSheet(SUBTITLE_STYLE)
        form_layout.addWidget(height_label)
        
        self.height_entry = QLineEdit()
        self.height_entry.setValidator(QRegExpValidator(QRegExp(r"[0-9]*\.?[0-9]*")))
        self.height_entry.setStyleSheet(INPUT_STYLE)
        form_layout.addWidget(self.height_entry)
        
        # Материал (только буквы)
        material_label = QLabel("Материал")
        material_label.setStyleSheet(SUBTITLE_STYLE)
        form_layout.addWidget(material_label)
        
        self.material_entry = QLineEdit()
        self.material_entry.setValidator(QRegExpValidator(QRegExp(r"[a-zA-Zа-яА-ЯёЁ\s\-]*")))
        self.material_entry.setStyleSheet(INPUT_STYLE)
        form_layout.addWidget(self.material_entry)
        
        # Цвет (только буквы)
        color_label = QLabel("Цвет")
        color_label.setStyleSheet(SUBTITLE_STYLE)
        form_layout.addWidget(color_label)
        
        self.color_entry = QLineEdit()
        self.color_entry.setValidator(QRegExpValidator(QRegExp(r"[a-zA-Zа-яА-ЯёЁ\s\-]*")))
        self.color_entry.setStyleSheet(INPUT_STYLE)
        form_layout.addWidget(self.color_entry)
        
        # Скидка % (только цифры)
        discount_label = QLabel("Скидка (%)")
        discount_label.setStyleSheet(SUBTITLE_STYLE)
        form_layout.addWidget(discount_label)
        
        self.discount_entry = QLineEdit()
        self.discount_entry.setValidator(QRegExpValidator(QRegExp(r"[0-9]*\.?[0-9]*")))
        self.discount_entry.setStyleSheet(INPUT_STYLE)
        form_layout.addWidget(self.discount_entry)
        
        # Фотография товара
        photo_label = QLabel("Фотография")
        photo_label.setStyleSheet(SUBTITLE_STYLE)
        form_layout.addWidget(photo_label)
        
        photo_layout = QHBoxLayout()
        
        self.photo_label = QLabel("Фото не выбрано")
        self.photo_label.setFixedSize(100, 100)
        self.photo_label.setAlignment(Qt.AlignCenter)
        photo_style = CARD_STYLE.replace("QFrame", "QLabel").replace("border-radius: 10px;", "border-radius: 10px; padding: 0px;")
        self.photo_label.setStyleSheet(photo_style)
        photo_layout.addWidget(self.photo_label)
        
        select_photo_btn = QPushButton("Выбрать фото")
        select_photo_btn.setStyleSheet(BUTTON_STYLE)
        select_photo_btn.clicked.connect(self.select_photo)
        photo_layout.addWidget(select_photo_btn)
        photo_layout.addStretch()
        
        form_layout.addLayout(photo_layout)
        form_layout.addStretch()
        
        form_widget.setLayout(form_layout)
        scroll_area.setWidget(form_widget)
        
        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area, 1)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Сохранить изменения")
        save_button.setStyleSheet(BUTTON_STYLE)
        save_button.clicked.connect(self.save_product)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.setStyleSheet(BUTTON_STYLE)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def load_product_data(self):
        """Загрузка данных товара в форму"""
        if not self.product:
            return
        
        # product: (id, name, sku, category, material, color, length, width, height, price, discount_percent, stock_quantity, current_price, photo_path)
        self.name_entry.setText(self.product[1] or "")
        self.sku_entry.setText(self.product[2] or "")
        self.price_entry.setText(str(self.product[9] or 0))
        self.length_entry.setText(str(self.product[6] or ""))
        self.width_entry.setText(str(self.product[7] or ""))
        self.height_entry.setText(str(self.product[8] or ""))
        self.material_entry.setText(self.product[4] or "")
        self.color_entry.setText(self.product[5] or "")
        self.discount_entry.setText(str(self.product[10] or 0))
        
        # Загружаем фотографию, если есть
        photo_path = self.product[13] if len(self.product) > 13 else None
        if photo_path and HAS_PIL:
            try:
                full_path = photo_path if os.path.isabs(photo_path) else os.path.join(os.getcwd(), photo_path)
                if os.path.exists(full_path):
                    img = Image.open(full_path)
                    img = img.resize((100, 100))
                    # Конвертируем PIL Image в QPixmap
                    img_rgb = img.convert('RGB')
                    img_bytes = img_rgb.tobytes('raw', 'RGB')
                    qimg = QImage(img_bytes, img.width, img.height, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimg)
                    self.photo_label.setPixmap(pixmap)
            except Exception as e:
                print(f"Ошибка загрузки фото: {e}")
        
        # Устанавливаем категорию
        category_name = self.product[3] or ""
        for i, cat in enumerate(self.categories):
            if cat[1] == category_name:
                self.category_combo.setCurrentIndex(i)
                break
    
    def select_photo(self):
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
                    img = img.resize((100, 100))
                    # Конвертируем PIL Image в QPixmap
                    img_rgb = img.convert('RGB')
                    img_bytes = img_rgb.tobytes('raw', 'RGB')
                    qimg = QImage(img_bytes, img.width, img.height, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimg)
                    self.photo_label.setPixmap(pixmap)
                    QMessageBox.information(self, "Фото выбрано", 
                                          "Фотография выбрана. Нажмите 'Сохранить изменения' для сохранения.")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить изображение: {e}")
                    self.selected_photo_path = None
            else:
                # Если PIL не установлен, просто показываем имя файла
                filename = os.path.basename(filepath)
                self.photo_label.setText(f"Выбрано:\n{filename[:20]}")
                QMessageBox.information(self, "Фото выбрано", 
                                      "Фотография выбрана. Нажмите 'Сохранить изменения' для сохранения.")
    
    def save_product(self):
        """Сохранение изменений товара"""
        try:
            # Валидация
            name = self.name_entry.text().strip()
            sku = self.sku_entry.text().strip()
            price_str = self.price_entry.text().strip()
            
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
                length = float(self.length_entry.text().strip()) if self.length_entry.text().strip() else None
            except ValueError:
                length = None
            
            try:
                width = float(self.width_entry.text().strip()) if self.width_entry.text().strip() else None
            except ValueError:
                width = None
            
            try:
                height = float(self.height_entry.text().strip()) if self.height_entry.text().strip() else None
            except ValueError:
                height = None
            
            try:
                discount = float(self.discount_entry.text().strip() or "0")
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
            
            # Получаем текущий путь к фото (если не выбрано новое)
            photo_path_db = self.product[13] if len(self.product) > 13 else None
            photo_saved = False
            
            # Обработка новой фотографии, если выбрана
            if self.selected_photo_path and os.path.exists(self.selected_photo_path):
                try:
                    product_id = self.product[0]
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
                    photo_saved = True
                except Exception as e:
                    QMessageBox.warning(self, "Предупреждение", 
                                      f"Товар обновлен, но не удалось сохранить фотографию: {e}")
            
            # Обновление товара
            db.update_product(
                product_id=self.product[0],
                name=name,
                category_id=category_id,
                sku=sku,
                price=price,
                length=length,
                width=width,
                height=height,
                material=self.material_entry.text().strip() or None,
                color=self.color_entry.text().strip() or None,
                discount_percent=discount,
                photo_path=photo_path_db
            )
            
            # Формируем сообщение об успехе
            success_msg = "Товар успешно обновлен"
            if photo_saved:
                success_msg += "\nФотография сохранена и будет отображаться в карточке товара"
            
            QMessageBox.information(self, "Успех", success_msg)
            
            if self.on_success:
                self.on_success()
            
            self.accept()
            
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении товара: {str(e)}")
