# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QFrame, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import db
import os

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
CHAR_LINE_COLOR = "#705847"

TITLE = "\u0421\u041a\u041b\u0410\u0414"
NO_GOODS = "\u041d\u0430 \u0441\u043a\u043b\u0430\u0434\u0435 \u043d\u0435\u0442 \u0442\u043e\u0432\u0430\u0440\u043e\u0432"
ERR = "\u041e\u0448\u0438\u0431\u043a\u0430"
ERR_LOAD = "\u041e\u0448\u0438\u0431\u043a\u0430 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438 \u0434\u0430\u043d\u043d\u044b\u0445 \u0441\u043a\u043b\u0430\u0434\u0430"
NO_NAME = "\u0411\u0435\u0437 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u044f"
DASH = "\u2014"
RUB = "\u0440\u0443\u0431."
DATE_DELIVERY = "\u0414\u0430\u0442\u0430 \u043f\u043e\u0441\u0442\u0430\u0432\u043a\u0438"
ARTICUL = "\u0410\u0440\u0442\u0438\u043a\u0443\u043b"
QTY = "\u041a\u043e\u043b-\u0432\u043e"
PRICE = "\u0426\u0435\u043d\u0430"
PHOTO_PLACEHOLDER = "[\u0424\u043e\u0442\u043e]"
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None


class WarehouseWindow(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
        self.load_warehouse_data()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        title_label = QLabel(TITLE)
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt; color: #705847;")
        layout.addWidget(title_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: #f5f5f5; border: none; }")

        self.cards_widget = QWidget()
        self.cards_widget.setStyleSheet("background: #f5f5f5;")
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(12)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_widget.setLayout(self.cards_layout)

        scroll_area.setWidget(self.cards_widget)
        layout.addWidget(scroll_area, 1)

        self.setLayout(layout)

    def load_warehouse_data(self):
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child is not None:
                w = child.widget()
                if w is not None:
                    w.deleteLater()

        try:
            inventory = db.get_inventory()
            if not inventory:
                no_label = QLabel(NO_GOODS)
                no_label.setStyleSheet("font-size: 11pt; color: #666;")
                no_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.cards_layout.addWidget(no_label, alignment=Qt.AlignmentFlag.AlignCenter)
                return

            for item in inventory:
                card = self._create_card(item)
                if card is not None:
                    self.cards_layout.addWidget(card)
        except Exception as e:
            QMessageBox.critical(self, ERR, ERR_LOAD + ": " + str(e))
            err = QLabel(str(e))
            err.setStyleSheet("color: #c00;")
            self.cards_layout.addWidget(err, alignment=Qt.AlignmentFlag.AlignCenter)

    def _create_card(self, item):
        if len(item) < 6:
            return None
        product_id = item[0]
        name = item[1] if item[1] is not None else NO_NAME
        sku = item[2] if item[2] is not None else DASH
        quantity = item[3] if item[3] is not None else 0
        last_updated = item[4]
        category = item[5] if len(item) > 5 and item[5] else DASH
        price = item[6] if len(item) > 6 and item[6] is not None else None
        photo_path = item[7] if len(item) > 7 else None

        date_str = last_updated.strftime('%d.%m.%Y %H:%M') if hasattr(last_updated, 'strftime') and last_updated else DASH
        price_str = (f"{int(price):,} {RUB}".replace(",", " ") if price is not None else DASH)

        card_frame = QFrame()
        card_frame.setStyleSheet(UTIL_CARD_FRAME)
        card_frame.setMinimumHeight(280)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(20)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        left_layout.addWidget(self._char_block(DATE_DELIVERY, date_str))
        left_layout.addWidget(self._char_block(ARTICUL, sku))
        left_layout.addWidget(self._char_block(QTY, str(quantity)))
        left_layout.addWidget(self._char_block(PRICE, price_str))

        main_layout.addLayout(left_layout)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(8)

        photo_label = QLabel(PHOTO_PLACEHOLDER)
        photo_label.setFixedSize(300, 300)
        photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_label.setStyleSheet(UTIL_PLACEHOLDER)

        if photo_path and HAS_PIL and Image is not None:
            try:
                full_path = photo_path if os.path.isabs(photo_path) else os.path.join(os.getcwd(), photo_path)
                if os.path.exists(full_path):
                    img = Image.open(full_path)
                    img = img.resize((300, 300))
                    img_rgb = img.convert('RGB')
                    img_bytes = img_rgb.tobytes('raw', 'RGB')
                    w, h = img.width, img.height
                    qimg = QImage(img_bytes, w, h, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimg)
                    photo_label.setPixmap(pixmap)
            except Exception as e:
                print("Photo load error:", product_id, e)

        right_layout.addWidget(photo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        name_label = QLabel(name)
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(UTIL_FIELD)
        right_layout.addWidget(name_label)

        main_layout.addLayout(right_layout)
        card_frame.setLayout(main_layout)
        return card_frame

    def _char_block(self, label_text, value_text):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        value_label = QLabel(value_text)
        value_label.setStyleSheet(UTIL_FIELD)
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        value_label.setFrameShape(QFrame.NoFrame)
        layout.addWidget(value_label)

        line = QFrame()
        # ?????????? ????? ? ?????? ??????? ?????
        line.setFixedHeight(3)
        line.setFixedWidth(400)
        line.setStyleSheet("background-color: " + CHAR_LINE_COLOR + "; border: none;")
        layout.addWidget(line)

        caption = QLabel(label_text)
        caption.setStyleSheet(UTIL_LABEL)
        caption.setAlignment(Qt.AlignmentFlag.AlignLeft)
        caption.setFrameShape(QFrame.NoFrame)
        layout.addWidget(caption)

        return container
