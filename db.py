import psycopg2
from contextlib import contextmanager

# Параметры подключения к PostgreSQL (ранее config.py)
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "furniture_store",
    "user": "postgres",
    "password": "1234",
}

# Путь к папке с фотографиями товаров
PHOTO_BASE_PATH = "photo"

# ==================================================
# CONNECTION
# ==================================================

@contextmanager
def get_connection():
    """Получение подключения к базе данных"""
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            port=str(DB_CONFIG["port"]),
        )
        conn.set_client_encoding("UTF8")
        conn.autocommit = True
        yield conn
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        raise
    finally:
        if conn is not None:
            conn.close()


@contextmanager
def get_cursor():
    with get_connection() as conn:
        with conn.cursor() as cur:
            yield cur


# ==================================================
# INITIALIZATION
# ==================================================

# ==================================================
# AUTH
# ==================================================

def get_user_by_username(username):
    """Получить пользователя по имени для проверки пароля"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, username, full_name, role, password
            FROM users
            WHERE username = %s
        """, (username,))
        return cur.fetchone()


# ==================================================
# CATEGORIES
# ==================================================

def get_categories():
    """Получение списка категорий"""
    with get_cursor() as cur:
        cur.execute("SELECT id, name FROM categories ORDER BY name")
        return cur.fetchall()


def add_category(name):
    """Добавление категории"""
    with get_cursor() as cur:
        cur.execute("INSERT INTO categories (name) VALUES (%s) RETURNING id", (name,))
        row = cur.fetchone()
        return row[0] if row else None


def delete_category(category_id):
    """Удаление категории по ID. Не удалит, если в категории есть товары."""
    with get_cursor() as cur:
        cur.execute("DELETE FROM categories WHERE id = %s", (category_id,))
        return cur.rowcount > 0


# ==================================================
# PRODUCTS
# ==================================================

def get_products(category_id=None):
    """Получение товаров с полной информацией, включая остатки и цену со скидкой"""
    with get_cursor() as cur:
        base_sql = """
            SELECT
                p.id,
                p.name,
                p.sku,
                c.name AS category,
                p.material,
                p.color,
                p.length,
                p.width,
                p.height,
                p.price,
                p.discount_percent,
                COALESCE(w.quantity, 0) AS stock_quantity,
                CASE
                    WHEN p.discount_percent IS NOT NULL AND p.discount_percent > 0
                        THEN ROUND(p.price * (1 - p.discount_percent / 100.0), 2)
                    ELSE p.price
                END AS current_price,
                p.photo_path
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN warehouse w ON w.product_id = p.id
        """
        params = []
        if category_id:
            base_sql += " WHERE p.category_id = %s"
            params.append(category_id)

        base_sql += " ORDER BY p.name"
        cur.execute(base_sql, params)
        return cur.fetchall()


def add_product(name, category_id, sku, price,
                length=None, width=None, height=None,
                material=None, color=None,
                discount_percent=0.0, photo_path=None):
    """
    Добавление товара.
    По ТЗ: проверка уникальности артикула, начальный stock_quantity = 0.
    Ожидается, что реальные складские остатки ведутся в таблице warehouse.
    
    Args:
        photo_path: Путь к фотографии товара (относительный, например photo/{product_id}/filename.jpg)
    """
    with get_cursor() as cur:
        # проверка уникальности артикула
        cur.execute("SELECT id FROM products WHERE sku = %s", (sku,))
        if cur.fetchone():
            raise ValueError("Товар с таким артикулом уже существует")

        cur.execute(
            """
            INSERT INTO products
                (name, category_id, sku, price,
                 length, width, height,
                 material, color, discount_percent, photo_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (name, category_id, sku, price,
             length, width, height,
             material, color, discount_percent, photo_path),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError("Не удалось добавить товар")
        product_id = row[0]

        # создаём запись на складе с количеством 0
        cur.execute(
            """
            INSERT INTO warehouse (product_id, quantity)
            VALUES (%s, 0)
            """,
            (product_id,),
        )

        return product_id


def update_product(product_id, name, category_id, sku, price,
                   length=None, width=None, height=None,
                   material=None, color=None,
                   discount_percent=0.0, photo_path=None):
    """
    Обновление товара с проверкой уникальности артикула.
    
    Args:
        photo_path: Путь к фотографии товара (относительный, например photo/{product_id}/filename.jpg)
    """
    with get_cursor() as cur:
        cur.execute(
            "SELECT id FROM products WHERE sku = %s AND id <> %s",
            (sku, product_id),
        )
        if cur.fetchone():
            raise ValueError("Товар с таким артикулом уже существует")

        cur.execute(
            """
            UPDATE products
            SET
                name = %s,
                category_id = %s,
                sku = %s,
                price = %s,
                length = %s,
                width = %s,
                height = %s,
                material = %s,
                color = %s,
                discount_percent = %s,
                photo_path = %s
            WHERE id = %s
            """,
            (name, category_id, sku, price,
             length, width, height,
             material, color, discount_percent, photo_path,
             product_id),
        )


def delete_product(product_id):
    """Удаление товара"""
    with get_cursor() as cur:
        # Удаляем складские остатки
        cur.execute("DELETE FROM warehouse WHERE product_id = %s", (product_id,))
        # Удаляем товар
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))


def get_products_by_category(category_id):
    """Получение товаров по ID категории с полной информацией"""
    return get_products(category_id=category_id)


def search_product(sku):
    """Поиск товара по артикулу"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                p.id,
                p.name,
                p.sku,
                c.name AS category,
                p.material,
                p.color,
                p.length,
                p.width,
                p.height,
                p.price,
                p.discount_percent,
                COALESCE(w.quantity, 0) AS stock_quantity,
                CASE
                    WHEN p.discount_percent IS NOT NULL AND p.discount_percent > 0
                        THEN ROUND(p.price * (1 - p.discount_percent / 100.0), 2)
                    ELSE p.price
                END AS current_price,
                p.photo_path
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN warehouse w ON w.product_id = p.id
            WHERE p.sku = %s
        """, (sku,))
        return cur.fetchone()


def get_discounted_products():
    """Получение товаров со скидками"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                p.id,
                p.name,
                p.sku,
                c.name AS category,
                p.material,
                p.color,
                p.length,
                p.width,
                p.height,
                p.price,
                p.discount_percent,
                COALESCE(w.quantity, 0) AS stock_quantity,
                CASE
                    WHEN p.discount_percent IS NOT NULL AND p.discount_percent > 0
                        THEN ROUND(p.price * (1 - p.discount_percent / 100.0), 2)
                    ELSE p.price
                END AS current_price,
                p.photo_path
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN warehouse w ON w.product_id = p.id
            WHERE p.discount_percent IS NOT NULL AND p.discount_percent > 0
            ORDER BY p.discount_percent DESC
        """)
        return cur.fetchall()


def get_discounted_products_by_category(category_id):
    """Получение товаров со скидками по категории"""
    if category_id is None:
        return get_discounted_products()
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                p.id,
                p.name,
                p.sku,
                c.name AS category,
                p.material,
                p.color,
                p.length,
                p.width,
                p.height,
                p.price,
                p.discount_percent,
                COALESCE(w.quantity, 0) AS stock_quantity,
                CASE
                    WHEN p.discount_percent IS NOT NULL AND p.discount_percent > 0
                        THEN ROUND(p.price * (1 - p.discount_percent / 100.0), 2)
                    ELSE p.price
                END AS current_price,
                p.photo_path
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN warehouse w ON w.product_id = p.id
            WHERE p.discount_percent IS NOT NULL AND p.discount_percent > 0
              AND p.category_id = %s
            ORDER BY p.discount_percent DESC
        """, (category_id,))
        return cur.fetchall()


def get_product_by_id(product_id):
    """Получение товара по ID"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                p.id,
                p.name,
                p.sku,
                c.name AS category,
                p.material,
                p.color,
                p.length,
                p.width,
                p.height,
                p.price,
                p.discount_percent,
                COALESCE(w.quantity, 0) AS stock_quantity,
                CASE
                    WHEN p.discount_percent IS NOT NULL AND p.discount_percent > 0
                        THEN ROUND(p.price * (1 - p.discount_percent / 100.0), 2)
                    ELSE p.price
                END AS current_price,
                p.photo_path
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN warehouse w ON w.product_id = p.id
            WHERE p.id = %s
        """, (product_id,))
        return cur.fetchone()


# ==================================================
# WAREHOUSE / INVENTORY
# ==================================================

def get_inventory():
    """Получение данных склада: id, name, sku, quantity, last_updated, category, price, photo_path"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                p.id,
                p.name,
                p.sku,
                w.quantity,
                w.last_updated,
                c.name AS category,
                p.price,
                p.photo_path
            FROM warehouse w
            JOIN products p ON p.id = w.product_id
            LEFT JOIN categories c ON c.id = p.category_id
            ORDER BY p.name
        """)
        return cur.fetchall()


# ==================================================
# SUPPLIERS
# ==================================================

def get_suppliers():
    """Получение списка поставщиков из БД.
    Возвращает список кортежей: (id, name, city, phone, email, inn, created_at, updated_at)."""
    table = _suppliers_table()
    with get_cursor() as cur:
        try:
            cur.execute("SELECT * FROM " + table + " ORDER BY name")
        except psycopg2.ProgrammingError:
            return []
        rows = cur.fetchall()
        if not rows or not cur.description:
            return []
        col_names = [d[0].lower() for d in cur.description]
        result = []
        for r in rows:
            row_dict = dict(zip(col_names, r))
            result.append((
                row_dict.get("id"),
                row_dict.get("name"),
                row_dict.get("city"),
                row_dict.get("phone"),
                row_dict.get("email"),
                row_dict.get("inn"),
                row_dict.get("created_at"),
                row_dict.get("updated_at"),
            ))
        return result


def _suppliers_table():
    """Возвращает имя таблицы поставщиков: ту, которая есть в БД."""
    with get_cursor() as cur:
        for table in ("suppliers", "suppliens", "supplier"):
            try:
                cur.execute("SELECT 1 FROM " + table + " LIMIT 1")
                return table
            except psycopg2.ProgrammingError as e:
                if "does not exist" not in str(e).lower():
                    raise
                continue
        raise ValueError("Таблица поставщиков (suppliers / suppliens / supplier) не найдена в БД")


def add_supplier(name, city, phone, inn, email=None):
    """Добавление нового поставщика в ту же таблицу, из которой читаются поставщики."""
    table = _suppliers_table()
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO """ + table + """ (name, city, phone, inn, email)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (name or None, city or None, phone or None, inn, email or None),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError("Не удалось добавить поставщика")
        return row[0]


def delete_supplier_by_inn(inn: str) -> int:
    """Удаление поставщика по ИНН. Возвращает количество удалённых строк."""
    table = _suppliers_table()
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM " + table + " WHERE inn = %s",
            (inn,),
        )
        return cur.rowcount


def delete_supplier_by_id(supplier_id) -> int:
    """Удаление поставщика по ID. Возвращает количество удалённых строк."""
    table = _suppliers_table()
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM " + table + " WHERE id = %s",
            (supplier_id,),
        )
        return cur.rowcount


# ==================================================
# DELIVERIES
# ==================================================

def get_deliveries():
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                d.id,
                d.delivery_date,
                s.name AS supplier,
                d.total_amount
            FROM deliveries d
            JOIN suppliers s ON s.id = d.supplier_id
            ORDER BY d.delivery_date DESC
        """)
        return cur.fetchall()


def get_deliveries_with_items():
    """Получение всех поставок с детальной информацией о товарах"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                d.id AS delivery_id,
                d.delivery_date,
                s.name AS supplier_name,
                d.total_amount,
                p.id AS product_id,
                p.name AS product_name,
                p.sku,
                di.quantity,
                di.purchase_price,
                p.photo_path
            FROM deliveries d
            JOIN suppliers s ON s.id = d.supplier_id
            JOIN delivery_items di ON di.delivery_id = d.id
            JOIN products p ON p.id = di.product_id
            ORDER BY d.delivery_date DESC, d.id DESC, p.name
        """)
        return cur.fetchall()


def create_delivery(supplier_id, delivery_date, items):
    """
    Создание поставки.
    items: список кортежей (product_id, quantity, purchase_price).
    
    По ТЗ:
      - дата поставки фиксируется;
      - общая сумма поставки считается;
      - stock_quantity (warehouse.quantity) увеличивается.
    
    После оформления поставки розничная цена товара (products.price) устанавливается
    на 20% выше закупочной: price = ROUND(purchase_price * 1.2, 2).
    Цены не берутся из БД — только из введённой пользователем закупочной цены.
    """
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                # создаём поставку с временной суммой 0
                cur.execute(
                    """
                    INSERT INTO deliveries (supplier_id, delivery_date, total_amount)
                    VALUES (%s, %s, 0)
                    RETURNING id
                    """,
                    (supplier_id, delivery_date),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError("Не удалось создать поставку")
                delivery_id = row[0]

                total_amount = 0

                for product_id, quantity, purchase_price in items:
                    line_amount = quantity * purchase_price
                    total_amount += line_amount

                    # строки поставки
                    cur.execute(
                        """
                        INSERT INTO delivery_items
                            (delivery_id, product_id, quantity, purchase_price)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (delivery_id, product_id, quantity, purchase_price),
                    )

                    # обновляем склад (увеличиваем остаток)
                    # Используем UPSERT: создаем запись, если её нет, или обновляем существующую
                    cur.execute(
                        """
                        INSERT INTO warehouse (product_id, quantity, last_updated)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (product_id) 
                        DO UPDATE SET 
                            quantity = warehouse.quantity + EXCLUDED.quantity,
                            last_updated = NOW()
                        """,
                        (product_id, quantity),
                    )

                    # розничная цена = закупочная + 20% (не берём из БД)
                    retail_price = round(float(purchase_price) * 1.2, 2)
                    cur.execute(
                        "UPDATE products SET price = %s WHERE id = %s",
                        (retail_price, product_id),
                    )

                # обновляем общую сумму поставки
                cur.execute(
                    """
                    UPDATE deliveries
                    SET total_amount = %s
                    WHERE id = %s
                    """,
                    (total_amount, delivery_id),
                )

            conn.commit()
            return delivery_id
        except Exception:
            conn.rollback()
            raise


def create_sale(customer_name, employee_id, sale_date, items):
    """
    Создание продажи.
    items: список кортежей (product_id, quantity, discount_percent_override или None).

    По ТЗ:
      - дата продажи фиксируется;
      - сумма считается по текущей цене (с учётом скидки);
      - stock_quantity (warehouse.quantity) уменьшается, проверяется достаточность остатков.
    
    Args:
        customer_name: ФИО покупателя (VARCHAR(150))
        employee_id: ID сотрудника из таблицы employees
    """
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                total_amount = 0

                # предварительная проверка остатков и расчет сумм
                for product_id, quantity, discount_override in items:
                    cur.execute(
                        """
                        SELECT
                            p.price,
                            p.discount_percent,
                            COALESCE(w.quantity, 0) AS stock
                        FROM products p
                        LEFT JOIN warehouse w ON w.product_id = p.id
                        WHERE p.id = %s
                        """,
                        (product_id,),
                    )
                    row = cur.fetchone()
                    if not row:
                        raise ValueError(f"Товар id={product_id} не найден")

                    price, base_discount, stock = row
                    if stock < quantity:
                        raise ValueError(
                            f"Недостаточно товара id={product_id} на складе "
                            f"(доступно {stock}, нужно {quantity})"
                        )

                    # Конвертируем Decimal в float для расчетов
                    price_float = float(price) if price is not None else 0.0
                    base_discount_float = float(base_discount) if base_discount is not None else 0.0
                    
                    # текущая скидка = либо override, либо discount_percent в товаре
                    discount = discount_override if discount_override is not None else base_discount_float
                    current_price = price_float * (1 - discount / 100.0) if discount > 0 else price_float
                    line_amount = round(current_price * quantity, 2)
                    total_amount += line_amount

                # создаём запись о продаже
                cur.execute(
                    """
                    INSERT INTO sales (sale_date, total_amount, customer_name, employee_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (sale_date, total_amount, customer_name, employee_id),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError("Не удалось создать продажу")
                sale_id = row[0]

                # создаём позиции продажи и уменьшаем остатки
                for product_id, quantity, discount_override in items:
                    cur.execute(
                        """
                        SELECT
                            p.price,
                            p.discount_percent
                        FROM products p
                        WHERE p.id = %s
                        """,
                        (product_id,),
                    )
                    price_row = cur.fetchone()
                    if price_row is None:
                        raise ValueError(f"Товар id={product_id} не найден")
                    price, base_discount = price_row

                    # Конвертируем Decimal в float для расчетов
                    price_float = float(price) if price is not None else 0.0
                    base_discount_float = float(base_discount) if base_discount is not None else 0.0
                    
                    discount = discount_override if discount_override is not None else base_discount_float
                    sale_price = price_float * (1 - discount / 100.0) if discount > 0 else price_float
                    line_amount = round(sale_price * quantity, 2)

                    cur.execute(
                        """
                        INSERT INTO sale_items
                            (sale_id, product_id, quantity, sale_price, discount_percent)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (sale_id, product_id, quantity, sale_price, discount),
                    )

                    # уменьшаем остаток на складе
                    cur.execute(
                        """
                        UPDATE warehouse
                        SET quantity = COALESCE(quantity, 0) - %s,
                            last_updated = NOW()
                        WHERE product_id = %s
                        """,
                        (quantity, product_id),
                    )

            conn.commit()
            return sale_id
        except Exception:
            conn.rollback()
            raise


# ==================================================
# SALES
# ==================================================

def get_sales():
    """Получение списка продаж"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                s.id,
                s.sale_date,
                s.total_amount,
                COALESCE(s.customer_name, 'Не указан') AS customer,
                COALESCE(
                    e.last_name || ' ' || e.first_name || 
                    COALESCE(' ' || e.middle_name, ''),
                    'Не указан'
                ) AS employee
            FROM sales s
            LEFT JOIN employees e ON e.id = s.employee_id
            ORDER BY s.sale_date DESC
        """)
        return cur.fetchall()


def get_sale_items(sale_id):
    """Получение позиций продажи"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                p.name,
                si.quantity,
                si.sale_price,
                si.discount_percent
            FROM sale_items si
            JOIN products p ON p.id = si.product_id
            WHERE si.sale_id = %s
        """, (sale_id,))
        return cur.fetchall()


def get_sales_with_items(date_from=None, date_to=None):
    """Получение всех позиций продаж с информацией о продаже для отображения в таблице"""
    with get_cursor() as cur:
        query = """
            SELECT
                p.name AS product_name,
                si.quantity,
                si.sale_price,
                s.sale_date,
                (si.sale_price * si.quantity) AS line_total,
                s.customer_name
            FROM sale_items si
            JOIN products p ON p.id = si.product_id
            JOIN sales s ON s.id = si.sale_id
        """
        params = []
        if date_from or date_to:
            conditions = []
            if date_from:
                conditions.append("s.sale_date >= %s")
                params.append(date_from)
            if date_to:
                conditions.append("s.sale_date <= %s")
                params.append(date_to)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY s.sale_date DESC, p.name"
        cur.execute(query, params)
        return cur.fetchall()


# ==================================================
# EMPLOYEES
# ==================================================

def get_employee_by_Auser_id(user_id):
    """Получение сотрудника по user_id"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, last_name, first_name, middle_name, position
            FROM employees
            WHERE user_id = %s
        """, (user_id,))
        return cur.fetchone()
