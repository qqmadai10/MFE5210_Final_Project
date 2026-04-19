import tkinter as tk
from tkinter import ttk
import threading
from core.event_bus import EventBus, Event


class TradingMonitor:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.root = tk.Tk()
        self.root.title("Trading Monitor - Algo Trading System")
        self.root.geometry("1300x700")

        # 线程安全的队列
        self.order_queue = []
        self.trade_queue = []
        self.queue_lock = threading.Lock()

        self._setup_ui()
        self._register_handlers()

        # 启动 UI 更新（使用 after 确保在主线程）
        self._update_ui()

    def _setup_ui(self):
        """设置 UI 布局"""
        # 创建 Notebook（标签页）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # === 订单标签页 ===
        self.order_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.order_frame, text="Orders")

        # 订单表格
        columns = ('ID', 'Symbol', 'Direction', 'Price', 'Volume', 'Status', 'Time')
        self.order_tree = ttk.Treeview(self.order_frame, columns=columns, show='headings', height=20)

        self.order_tree.heading('ID', text='Order ID')
        self.order_tree.heading('Symbol', text='Symbol')
        self.order_tree.heading('Direction', text='Direction')
        self.order_tree.heading('Price', text='Price')
        self.order_tree.heading('Volume', text='Volume')
        self.order_tree.heading('Status', text='Status')
        self.order_tree.heading('Time', text='Time')

        self.order_tree.column('ID', width=150)
        self.order_tree.column('Symbol', width=100)
        self.order_tree.column('Direction', width=80)
        self.order_tree.column('Price', width=100)
        self.order_tree.column('Volume', width=100)
        self.order_tree.column('Status', width=100)
        self.order_tree.column('Time', width=150)

        scrollbar = ttk.Scrollbar(self.order_frame, orient=tk.VERTICAL, command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=scrollbar.set)

        self.order_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # === 成交标签页 ===
        self.trade_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.trade_frame, text="Trades")

        trade_columns = ('ID', 'Order ID', 'Symbol', 'Direction', 'Price', 'Volume', 'Commission', 'Time')
        self.trade_tree = ttk.Treeview(self.trade_frame, columns=trade_columns, show='headings', height=20)

        self.trade_tree.heading('ID', text='Trade ID')
        self.trade_tree.heading('Order ID', text='Order ID')
        self.trade_tree.heading('Symbol', text='Symbol')
        self.trade_tree.heading('Direction', text='Direction')
        self.trade_tree.heading('Price', text='Price')
        self.trade_tree.heading('Volume', text='Volume')
        self.trade_tree.heading('Commission', text='Commission')
        self.trade_tree.heading('Time', text='Time')

        self.trade_tree.column('ID', width=120)
        self.trade_tree.column('Order ID', width=120)
        self.trade_tree.column('Symbol', width=100)
        self.trade_tree.column('Direction', width=80)
        self.trade_tree.column('Price', width=100)
        self.trade_tree.column('Volume', width=100)
        self.trade_tree.column('Commission', width=100)
        self.trade_tree.column('Time', width=150)

        trade_scrollbar = ttk.Scrollbar(self.trade_frame, orient=tk.VERTICAL, command=self.trade_tree.yview)
        self.trade_tree.configure(yscrollcommand=trade_scrollbar.set)

        self.trade_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        trade_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # === 统计标签页 ===
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="Statistics")

        self.stats_text = tk.Text(self.stats_frame, height=20, width=80, font=('Courier', 10))
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === 日志标签页 ===
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="Logs")

        self.log_text = tk.Text(self.log_frame, height=20, width=80, font=('Courier', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        log_scrollbar = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 底部状态栏
        self.status_bar = ttk.Label(self.root, text="System running...", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _register_handlers(self):
        """注册事件处理器"""
        self.event_bus.subscribe("ORDER", self._on_order_event)
        self.event_bus.subscribe("TRADE", self._on_trade_event)

    def _on_order_event(self, event: Event):
        """接收订单事件（在 asyncio 线程中调用）"""
        with self.queue_lock:
            self.order_queue.append(event.data)
            print(f"[GUI] Order queued: {event.data.order_id}")

    def _on_trade_event(self, event: Event):
        """接收成交事件（在 asyncio 线程中调用）"""
        with self.queue_lock:
            self.trade_queue.append(event.data)
            print(f"[GUI] Trade queued: {event.data.trade_id}")

    def _update_ui(self):
        """定时更新 UI（在主线程中执行）"""
        try:
            # 处理订单队列
            with self.queue_lock:
                orders = self.order_queue.copy()
                self.order_queue.clear()
                trades = self.trade_queue.copy()
                self.trade_queue.clear()

            # 更新订单表格
            for order in orders:
                values = (
                    order.order_id[:12],
                    order.symbol,
                    order.direction.value,
                    f"{order.price:.2f}",
                    f"{order.volume:.4f}",
                    order.status.value,
                    order.created_at.strftime("%H:%M:%S") if order.created_at else ""
                )
                self.order_tree.insert('', 0, values=values)
                print(f"[GUI] Added order to table: {order.order_id[:12]}")

                # 限制显示行数
                if len(self.order_tree.get_children()) > 100:
                    last_item = self.order_tree.get_children()[-1]
                    self.order_tree.delete(last_item)

            # 更新成交表格
            for trade in trades:
                values = (
                    trade.trade_id[:12],
                    trade.order_id[:12],
                    trade.symbol,
                    trade.direction.value,
                    f"{trade.price:.2f}",
                    f"{trade.volume:.4f}",
                    f"{trade.commission:.6f}",
                    trade.trade_time.strftime("%H:%M:%S")
                )
                self.trade_tree.insert('', 0, values=values)
                print(f"[GUI] Added trade to table: {trade.trade_id[:12]}")

                if len(self.trade_tree.get_children()) > 100:
                    last_item = self.trade_tree.get_children()[-1]
                    self.trade_tree.delete(last_item)

                # 添加日志
                log_msg = f"[{trade.trade_time.strftime('%H:%M:%S')}] TRADE: {trade.direction.value} {trade.volume:.4f} BTC @ {trade.price:.2f} | Commission: {trade.commission:.6f}\n"
                self.log_text.insert(tk.END, log_msg)
                self.log_text.see(tk.END)
                if len(self.log_text.get('1.0', tk.END).split('\n')) > 500:
                    self.log_text.delete('1.0', '100.0')

                # 更新统计信息
                self._update_statistics()

            # 更新状态栏
            trade_count = len(self.trade_tree.get_children())
            order_count = len(self.order_tree.get_children())
            self.status_bar.config(text=f"System running | Orders: {order_count} | Trades: {trade_count}")

        except Exception as e:
            print(f"[GUI] Update error: {e}")

        # 每 500ms 更新一次
        self.root.after(500, self._update_ui)

    def _update_statistics(self):
        """更新统计信息"""
        try:
            import sqlite3
            conn = sqlite3.connect('trading.db')
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM trades")
            trade_count = cursor.fetchone()[0] or 0

            cursor.execute("SELECT SUM(commission) FROM trades")
            total_commission = cursor.fetchone()[0] or 0

            cursor.execute("SELECT SUM(price * volume) FROM trades")
            total_turnover = cursor.fetchone()[0] or 0

            conn.close()

            stats = f"""
╔══════════════════════════════════════════════════════════════╗
║                    TRADING STATISTICS                        ║
╠══════════════════════════════════════════════════════════════╣
║  Total Trades:        {trade_count:>6}                                       ║
║  Total Commission:    {total_commission:>10.6f}  USDT                       ║
║  Total Turnover:      {total_turnover:>12.2f}  USDT                       ║
╠══════════════════════════════════════════════════════════════╣
║  Average Commission:  {(total_commission / trade_count) if trade_count > 0 else 0:>10.6f}  USDT/trade              ║
╚══════════════════════════════════════════════════════════════╝

System Architecture:
  ┌────────────┐    ┌────────────┐    ┌────────────┐
  │ DataReplayer│───▶│  EventBus  │───▶│  Strategy  │
  └────────────┘    └────────────┘    └──────┬─────┘
                                              │ Signal
                                              ▼
  ┌────────────┐    ┌────────────┐    ┌────────────┐
  │  Database  │◀───│    OMS     │◀───│   Signal   │
  └────────────┘    └──────┬─────┘    └────────────┘
                           │
                           ▼
                    ┌────────────┐
                    │    RMS     │
                    └──────┬─────┘
                           │
                           ▼
                    ┌────────────┐
                    │  Gateway   │
                    └────────────┘
"""
            self.stats_text.delete('1.0', tk.END)
            self.stats_text.insert('1.0', stats)
        except Exception as e:
            print(f"Stats error: {e}")

    def run(self):
        """运行 GUI 主循环"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()

    def _on_closing(self):
        """关闭窗口时的处理"""
        self.root.destroy()


def run_gui(event_bus):
    """在独立线程中运行 GUI"""
    monitor = TradingMonitor(event_bus)
    monitor.run()