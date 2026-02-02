"""
Единые стили для всех окон приложения
"""

# Цветовая палитра
COLORS = {
    'background': 'white',
    'text': 'black',
    'text_secondary': '#666666',
    'category_bg': '#7A6E5B',
    'category_border': '#5A4F40',
    'category_text': 'white',
    'button_bg': 'white',
    'button_text': 'black',
    'button_border': 'black',
    'button_hover': '#f0f0f0',
    'card_border': '#705847',
    'title_color': '#666666'
}

# Стили кнопок
BUTTON_STYLE = """
    QPushButton {{
        background-color: {bg};
        color: {text};
        font-family: Consolas;
        font-size: 10pt;
        border: 1px solid {border};
        border-radius: 20px;
        padding: 10px 20px;
    }}
    QPushButton:hover {{
        background-color: {hover};
    }}
""".format(
    bg=COLORS['button_bg'],
    text=COLORS['button_text'],
    border=COLORS['button_border'],
    hover=COLORS['button_hover']
)

# Стиль кнопки категории
CATEGORY_BUTTON_STYLE = """
    QPushButton {{
        background-color: {bg};
        color: {text};
        font-family: Arial, sans-serif;
        font-size: 10pt;
        border: 1px solid {border};
        border-radius: 20px;
        padding: 10px 20px;
    }}
    QPushButton:hover {{
        background-color: {hover};
    }}
""".format(
    bg=COLORS['category_bg'],
    text=COLORS['category_text'],
    border=COLORS['category_border'],
    hover='#8B7D6B'
)

# Стиль поля ввода
INPUT_STYLE = """
    QLineEdit {{
        border: none;
        border-bottom: 1px solid {border};
        padding: 5px 0px;
        font-size: 11pt;
        background-color: transparent;
    }}
    QLineEdit:focus {{
        border-bottom: 2px solid {border};
    }}
""".format(border=COLORS['card_border'])

# Стиль выпадающего списка
COMBOBOX_STYLE = """
    QComboBox {{
        border: none;
        border-bottom: 1px solid {border};
        padding: 5px 0px;
        font-size: 11pt;
        background-color: transparent;
    }}
    QComboBox:focus {{
        border-bottom: 2px solid {border};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {border};
        width: 0;
        height: 0;
    }}
""".format(border=COLORS['card_border'])

# Стиль заголовка
TITLE_STYLE = "font-weight: bold; font-size: 16pt; color: {color}; font-family: Arial, sans-serif;".format(
    color=COLORS['title_color']
)

# Стиль подзаголовка
SUBTITLE_STYLE = "font-size: 11pt; font-family: Arial, sans-serif; color: {color};".format(
    color=COLORS['text']
)

# Стиль для имени пользователя
USER_NAME_STYLE = "font-weight: bold; font-size: 12pt; font-family: Arial, sans-serif; color: {color};".format(
    color=COLORS['text']
)

# Стиль для роли пользователя
USER_ROLE_STYLE = "font-size: 10pt; font-family: Arial, sans-serif; color: {color};".format(
    color=COLORS['text']
)

# Стиль для поисковой строки
SEARCH_STYLE = """
    QLineEdit {{
        border: 1px solid {border};
        border-radius: 20px;
        padding: 8px 15px;
        font-family: Arial, sans-serif;
        font-size: 10pt;
        background-color: white;
    }}
""".format(border=COLORS['button_border'])

# Стиль для карточки товара
CARD_STYLE = """
    QFrame {{
        background-color: white;
        border: 1px solid {border};
        border-radius: 10px;
    }}
""".format(border=COLORS['card_border'])

# Стиль для фото в карточке
PHOTO_STYLE = """
    border: none;
    background-color: white;
"""

# Стиль для названия товара
PRODUCT_NAME_STYLE = """
    font-family: Inter, Arial, sans-serif;
    font-size: 10pt;
    font-weight: bold;
    border: none;
    color: {color};
""".format(color=COLORS['text'])

# Стиль для артикула
PRODUCT_SKU_STYLE = """
    font-family: Inter, Arial, sans-serif;
    font-size: 10pt;
    font-weight: bold;
    border: none;
    color: {color};
""".format(color=COLORS['text'])

# Стиль для цены
PRODUCT_PRICE_STYLE = """
    font-family: Inter, Arial, sans-serif;
    font-size: 11pt;
    font-weight: bold;
    border: none;
    color: {color};
""".format(color=COLORS['text'])

# Стиль для информационных сообщений
INFO_STYLE = "font-size: 12pt; font-family: Arial, sans-serif; color: {color};".format(
    color=COLORS['text_secondary']
)

# Стиль для ошибок
ERROR_STYLE = "color: red; font-size: 12pt; font-family: Arial, sans-serif;"

# Стиль для заголовка деталей товара
DETAILS_TITLE_STYLE = "font-weight: bold; font-size: 18pt; font-family: Arial, sans-serif; color: {color};".format(
    color=COLORS['title_color']
)

# Стиль для фото в деталях товара
DETAILS_PHOTO_STYLE = """
    border: 1px solid {border};
    border-radius: 10px;
    background-color: white;
""".format(border=COLORS['card_border'])

# Стиль для названия товара в деталях
DETAILS_NAME_STYLE = "font-size: 12pt; font-weight: bold; font-family: Arial, sans-serif; color: {color};".format(
    color=COLORS['text']
)

# Стиль для заголовка поставки
DELIVERY_HEADER_STYLE = "font-weight: bold; font-size: 12pt; font-family: Arial, sans-serif; color: {color};".format(
    color=COLORS['text']
)

# Стиль для суммы поставки
DELIVERY_TOTAL_STYLE = "font-weight: bold; font-size: 11pt; font-family: Arial, sans-serif; color: green;"

# Стиль для карточки товара в поставке
DELIVERY_CARD_STYLE = "font-size: 9pt; font-family: Arial, sans-serif; color: {color};".format(
    color=COLORS['text']
)

# Стиль для рамки поставки
DELIVERY_FRAME_STYLE = """
    QFrame {{
        border: 2px solid {color};
    }}
""".format(color=COLORS['text_secondary'])

# Стиль для заголовка окна добавления товара
ADD_PRODUCT_TITLE_STYLE = "font-weight: bold; font-size: 18pt; font-family: Arial, sans-serif; color: {color};".format(
    color=COLORS['title_color']
)

# Стиль для артикула (жирный)
SKU_BOLD_STYLE = "font-size: 11pt; font-weight: bold; font-family: Arial, sans-serif; color: {color};".format(
    color=COLORS['text']
)

# Стиль вертикального разделителя
SEPARATOR_STYLE = """
    QFrame {{
        background-color: {color};
        max-width: 1px;
        border: none;
    }}
""".format(color=COLORS['text_secondary'])
