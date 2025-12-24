import sqlite3
from datetime import datetime
from contextlib import contextmanager
from config import Config

class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    name TEXT,
                    current_price REAL,
                    currency TEXT DEFAULT 'EUR',
                    image_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_checked TIMESTAMP,
                    active INTEGER DEFAULT 1
                )
            ''')

            # Price history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    price REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                )
            ''')

            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_price_history_product_id
                ON price_history(product_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_price_history_timestamp
                ON price_history(timestamp)
            ''')

    def add_product(self, url, name=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO products (url, name) VALUES (?, ?)',
                (url, name)
            )
            return cursor.lastrowid

    def get_product(self, product_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
            return cursor.fetchone()

    def get_all_products(self, active_only=True):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = 'SELECT * FROM products'
            if active_only:
                query += ' WHERE active = 1'
            query += ' ORDER BY created_at DESC'
            cursor.execute(query)
            return cursor.fetchall()

    def update_product(self, product_id, **kwargs):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
            values = list(kwargs.values())
            values.append(product_id)

            cursor.execute(
                f'UPDATE products SET {set_clause} WHERE id = ?',
                values
            )

    def delete_product(self, product_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))

    def add_price_history(self, product_id, price):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO price_history (product_id, price) VALUES (?, ?)',
                (product_id, price)
            )
            return cursor.lastrowid

    def get_price_history(self, product_id, limit=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = '''
                SELECT * FROM price_history
                WHERE product_id = ?
                ORDER BY timestamp DESC
            '''
            if limit:
                query += f' LIMIT {limit}'

            cursor.execute(query, (product_id,))
            return cursor.fetchall()

    def get_lowest_price(self, product_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT MIN(price) as min_price FROM price_history WHERE product_id = ?',
                (product_id,)
            )
            result = cursor.fetchone()
            return result['min_price'] if result else None

    def get_highest_price(self, product_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT MAX(price) as max_price FROM price_history WHERE product_id = ?',
                (product_id,)
            )
            result = cursor.fetchone()
            return result['max_price'] if result else None
