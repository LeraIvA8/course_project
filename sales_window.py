# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit)
from PyQt5.QtCore import Qt, QDate
from datetime import datetime
import db
from ui_styles import BUTTON_STYLE, TITLE_STYLE

# Стили как в окне склада
UTIL_LABEL = "font-size: 10pt; color: #333;"
UTIL_INPUT = """
    QDateEdit {
        border: 1px solid #999;
        padding: 4px 8px;
        font-size: 10pt;
        background-color: white;
        border-radius: 20px;
    }
"""

# Константы через Unicode
TITLE_SALES = "ПРОДАЖИ"
PERIOD = "\u041f\u0435\u0440\u0438\u043e\u0434"  # Период


class SalesWindow(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
        self.load_sales()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        title_label = QLabel(TITLE_SALES)
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt; color: #705847;")
        layout.addWidget(title_label)
        
        # Период: надпись и два поля выбора даты
        period_layout = QHBoxLayout()
        period_label = QLabel(PERIOD + ":")
        period_label.setStyleSheet(UTIL_LABEL)
        period_layout.addWidget(period_label)
        
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd.MM.yyyy")
        self.date_from.setStyleSheet(UTIL_INPUT)
        self.date_from.dateChanged.connect(self.on_date_changed)
        period_layout.addWidget(self.date_from)
        
        dash_label = QLabel("—")
        dash_label.setStyleSheet(UTIL_LABEL)
        period_layout.addWidget(dash_label)
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd.MM.yyyy")
        self.date_to.setStyleSheet(UTIL_INPUT)
        self.date_to.dateChanged.connect(self.on_date_changed)
        period_layout.addWidget(self.date_to)
        
        period_layout.addStretch()
        layout.addLayout(period_layout)
        
        # Таблица продаж: встроенный заголовок — значения строго под наименованиями колонок
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Наименование товара",
            "Количество",
            "Цена товара",
            "Дата продажи",
            "Сумма покупки",
            "ФИО покупателя"
        ])
        self.table.setStyleSheet("""
            QHeaderView::section {
                font-size: 11pt;
                font-weight: bold;
                color: #705847;
                padding: 6px;
            }
        """)
        
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.Stretch)
        
        v_header = self.table.verticalHeader()
        if v_header:
            v_header.hide()
        
        layout.addWidget(self.table, 1)
        self.setLayout(layout)
    
    def on_date_changed(self):
        """Обновление данных при изменении даты"""
        self.load_sales()
    
    def load_sales(self):
        """Загрузка данных о продажах с фильтром по периоду"""
        try:
            date_from = self.date_from.date().toPyDate()
            date_to = self.date_to.date().toPyDate()
            
            sales_data = db.get_sales_with_items(date_from=date_from, date_to=date_to)
            # Возвращает: (product_name, quantity, sale_price, sale_date, line_total, customer_name)
            
            self.table.setRowCount(len(sales_data))
            
            for row, item in enumerate(sales_data):
                if len(item) >= 6:
                    product_name = item[0] or "\u2014"  # Наименование
                    quantity = item[1] or 0  # Количество
                    sale_price = item[2] or 0  # Цена товара
                    sale_date = item[3]  # Дата продажи
                    line_total = item[4] or 0  # Сумма покупки
                    customer_name = item[5] or "\u2014"  # ФИО покупателя
                    
                    date_str = sale_date.strftime('%d.%m.%Y') if hasattr(sale_date, 'strftime') and sale_date else "\u2014"
                    
                    self.table.setItem(row, 0, QTableWidgetItem(str(product_name)))
                    self.table.setItem(row, 1, QTableWidgetItem(str(quantity)))
                    self.table.setItem(row, 2, QTableWidgetItem(f"{float(sale_price):,.2f}".replace(",", " ") + " \u0440\u0443\u0431."))
                    self.table.setItem(row, 3, QTableWidgetItem(date_str))
                    self.table.setItem(row, 4, QTableWidgetItem(f"{float(line_total):,.2f}".replace(",", " ") + " \u0440\u0443\u0431."))
                    self.table.setItem(row, 5, QTableWidgetItem(str(customer_name)))
        except Exception as e:
            print(f"Ошибка загрузки продаж: {e}")
