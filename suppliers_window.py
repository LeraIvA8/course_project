from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QDialog,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator
import db
from ui_styles import TITLE_STYLE, SUBTITLE_STYLE, BUTTON_STYLE
import traceback


class SuppliersWindow(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.suppliers_table = None
        try:
            self.setup_ui()
            self.load_suppliers()
        except Exception as e:
            error_msg = f"Ошибка инициализации окна поставщиков: {e}"
            print(error_msg)
            print(traceback.format_exc())
            if self.suppliers_table is not None:
                self.suppliers_table.setRowCount(1)
                self.suppliers_table.setItem(0, 0, QTableWidgetItem(f"Ошибка: {e}"))

    def showEvent(self, a0):
        super().showEvent(a0)
        if self.suppliers_table is not None and self.suppliers_table.rowCount() == 0:
            self.load_suppliers()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel("ПОСТАВЩИКИ")
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt; color: #705847;")
        layout.addWidget(title_label)

        # Таблица поставщиков
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(5)
        self.suppliers_table.setHorizontalHeaderLabels(
            ["Наименование", "Город", "Телефон", "Email", "ИНН"]
        )
        self.suppliers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.suppliers_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.suppliers_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.suppliers_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.Stretch)
        self.suppliers_table.setMinimumHeight(200)
        self.suppliers_table.setStyleSheet(
            "QTableWidget { font-size: 10pt; } "
            "QHeaderView::section { background-color: #f0e6dc; color: #705847; padding: 6px; }"
        )
        layout.addWidget(self.suppliers_table, 1)

        # Нижняя панель с кнопками "Удалить" и "Добавить" в правом нижнем углу
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        delete_btn = QPushButton("Удалить")
        delete_btn.setStyleSheet(BUTTON_STYLE)
        delete_btn.clicked.connect(self.delete_selected_supplier)
        bottom_layout.addWidget(delete_btn)

        add_btn = QPushButton("Добавить")
        add_btn.setStyleSheet(BUTTON_STYLE)
        add_btn.clicked.connect(self.open_add_supplier_dialog)
        bottom_layout.addWidget(add_btn)
        layout.addLayout(bottom_layout)

        self.setLayout(layout)

    @staticmethod
    def _str_val(row, idx):
        """Безопасное получение строки из строки БД."""
        if idx >= len(row):
            return ""
        v = row[idx]
        return str(v).strip() if v is not None else ""

    @staticmethod
    def _date_val(row, idx):
        """Безопасное форматирование даты из строки БД."""
        if idx >= len(row):
            return ""
        v = row[idx]
        if v is None:
            return ""
        if hasattr(v, "strftime"):
            return v.strftime("%d.%m.%Y")
        return str(v)

    def open_add_supplier_dialog(self):
        """Окно добавления нового поставщика"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить поставщика")
        dialog.setModal(True)
        dialog.setGeometry(300, 300, 400, 250)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Наименование (только буквы)
        name_label = QLabel("Наименование:")
        name_label.setStyleSheet(SUBTITLE_STYLE + " color: #705847;")
        layout.addWidget(name_label)
        name_edit = QLineEdit()
        name_edit.setValidator(QRegExpValidator(QRegExp(r"[a-zA-Zа-яА-ЯёЁ\s\-]*")))
        layout.addWidget(name_edit)

        # Город (только буквы)
        city_label = QLabel("Город:")
        city_label.setStyleSheet(SUBTITLE_STYLE + " color: #705847;")
        layout.addWidget(city_label)
        city_edit = QLineEdit()
        city_edit.setValidator(QRegExpValidator(QRegExp(r"[a-zA-Zа-яА-ЯёЁ\s\-]*")))
        layout.addWidget(city_edit)

        # Телефон: маска +7 и только цифры
        phone_label = QLabel("Телефон:")
        phone_label.setStyleSheet(SUBTITLE_STYLE + " color: #705847;")
        layout.addWidget(phone_label)
        phone_edit = QLineEdit()
        phone_edit.setPlaceholderText("+7 (999) 123-45-67")
        phone_edit.setInputMask("+79999999999")
        layout.addWidget(phone_edit)

        # ИНН (только цифры, не более 12)
        inn_label = QLabel("ИНН:")
        inn_label.setStyleSheet(SUBTITLE_STYLE + " color: #705847;")
        layout.addWidget(inn_label)
        inn_edit = QLineEdit()
        inn_edit.setMaxLength(12)
        inn_edit.setValidator(QRegExpValidator(QRegExp(r"[0-9]*")))
        layout.addWidget(inn_edit)

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        def on_save():
            name = name_edit.text().strip()
            city = city_edit.text().strip()
            phone = phone_edit.text().strip()
            inn = inn_edit.text().strip()

            if not name or not inn:
                QMessageBox.critical(dialog, "Ошибка", "Наименование и ИНН обязательны для заполнения")
                return
            try:
                db.add_supplier(name, city, phone, inn)
                self.load_suppliers()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось добавить поставщика: {e}")

        save_btn = QPushButton("Сохранить")
        save_btn.setStyleSheet(BUTTON_STYLE)
        save_btn.clicked.connect(on_save)
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        dialog.exec_()

    def delete_selected_supplier(self):
        """Удаление выбранного поставщика из таблицы."""
        if self.suppliers_table is None:
            return
        row = self.suppliers_table.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "Удаление", "Выберите поставщика в таблице (клик по строке), затем нажмите «Удалить»."
            )
            return
        item = self.suppliers_table.item(row, 0)
        supplier_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        if supplier_id is None:
            QMessageBox.information(self, "Удаление", "Выберите строку поставщика в таблице.")
            return
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить выбранного поставщика?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,  # type: ignore[arg-type]
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            deleted = db.delete_supplier_by_id(supplier_id)
            if deleted == 0:
                QMessageBox.information(self, "Информация", "Поставщик не найден")
            else:
                QMessageBox.information(self, "Успех", "Поставщик удалён")
            self.load_suppliers()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить поставщика: {e}")

    def load_suppliers(self):
        """Загрузка данных о поставщиках в таблицу."""
        if self.suppliers_table is None:
            return
        try:
            suppliers = db.get_suppliers()
            self.suppliers_table.setRowCount(len(suppliers) if suppliers else 0)
            if not suppliers:
                return
            for row_idx, s in enumerate(suppliers):
                try:
                    row = tuple(s) if s else ()
                    if len(row) < 2:
                        continue
                    supplier_id = row[0]
                    name = self._str_val(row, 1) or "—"
                    city = self._str_val(row, 2) or "—"
                    phone = self._str_val(row, 3) or "—"
                    email = self._str_val(row, 4) or "—"
                    inn = self._str_val(row, 5)
                    inn_str = "—" if inn is None or (isinstance(inn, str) and not inn.strip()) else str(inn)
                    self.suppliers_table.setItem(row_idx, 0, QTableWidgetItem(name))
                    self.suppliers_table.setItem(row_idx, 1, QTableWidgetItem(city))
                    self.suppliers_table.setItem(row_idx, 2, QTableWidgetItem(phone))
                    self.suppliers_table.setItem(row_idx, 3, QTableWidgetItem(email))
                    self.suppliers_table.setItem(row_idx, 4, QTableWidgetItem(inn_str))
                    # ID поставщика храним в первой ячейке для удаления
                    first = self.suppliers_table.item(row_idx, 0)
                    if first is not None:
                        first.setData(Qt.ItemDataRole.UserRole, supplier_id)
                except Exception as e:
                    print(f"Ошибка обработки поставщика {s}: {e}")
                    traceback.print_exc()
        except Exception as e:
            error_msg = f"Ошибка загрузки поставщиков: {e}"
            print(error_msg)
            print(traceback.format_exc())
            self.suppliers_table.setRowCount(1)
            self.suppliers_table.setItem(0, 0, QTableWidgetItem(f"Ошибка: {e}"))
