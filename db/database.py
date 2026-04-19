import sqlite3
import threading
from core.models import Order, Trade


class Database:
    _local = threading.local()

    def __init__(self, db_path: str = "trading.db"):
        self.db_path = db_path
        self._create_tables()

    def _get_connection(self):
        """获取当前线程的数据库连接"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return self._local.conn

    def _create_tables(self):
        """创建表（使用主线程连接）"""
        conn = self._get_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                signal_id TEXT,
                symbol TEXT,
                direction TEXT,
                price REAL,
                volume REAL,
                status TEXT,
                created_at TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                order_id TEXT,
                symbol TEXT,
                direction TEXT,
                price REAL,
                volume REAL,
                commission REAL,
                trade_time TEXT
            )
        ''')
        conn.commit()

    def save_order(self, order: Order):
        """保存订单（线程安全）"""
        conn = self._get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?,?,?,?)",
            (order.order_id, order.signal_id, order.symbol, order.direction.value,
             order.price, order.volume, order.status.value, order.created_at.isoformat())
        )
        conn.commit()
        print(f"DB: saved order {order.order_id}")

    def save_trade(self, trade: Trade):
        """保存成交（线程安全）"""
        conn = self._get_connection()
        conn.execute(
            "INSERT INTO trades VALUES (?,?,?,?,?,?,?,?)",
            (trade.trade_id, trade.order_id, trade.symbol, trade.direction.value,
             trade.price, trade.volume, trade.commission, trade.trade_time.isoformat())
        )
        conn.commit()
        print(f"DB: saved trade {trade.trade_id}")