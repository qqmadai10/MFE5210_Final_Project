import sqlite3
import pandas as pd
import numpy as np


class TCAAnalyzer:
    def __init__(self, db_path: str = "trading.db"):
        self.db_path = db_path

    def compute_slippage(self) -> pd.DataFrame:
        """计算滑点统计"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM trades", conn)
        conn.close()
        if df.empty:
            return pd.DataFrame()
        # 这里简化处理，实际需要预期价格
        df['slippage_bps'] = (df['price'] - df['price']) * 10000
        return df.describe()

    def compute_total_cost(self) -> float:
        """计算总交易成本（手续费）"""
        conn = sqlite3.connect(self.db_path)
        result = pd.read_sql_query("SELECT SUM(commission) as total FROM trades", conn)
        conn.close()
        total = result.iloc[0, 0]
        return total if total is not None else 0.0

    def compute_sharpe_ratio(self, returns: pd.Series, rf_rate: float = 0.02) -> float:
        """计算年化夏普比率"""
        if len(returns) < 2:
            return 0.0
        excess_returns = returns - rf_rate / 252
        if excess_returns.std() == 0:
            return 0.0
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

    def compute_max_drawdown(self, equity_curve: pd.Series) -> float:
        """计算最大回撤"""
        if len(equity_curve) < 2:
            return 0.0
        cumulative_max = equity_curve.cummax()
        drawdown = (equity_curve - cumulative_max) / cumulative_max
        return drawdown.min()

    def get_equity_curve(self) -> pd.Series:
        """从成交记录计算权益曲线"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM trades ORDER BY trade_time", conn)
        conn.close()

        if df.empty:
            return pd.Series()

        # 计算累计盈亏
        df['pnl'] = df['price'] * df['volume']
        df['cumulative_pnl'] = df['pnl'].cumsum() - df['commission'].cumsum()

        # 假设初始资金 10000 USDT
        initial_capital = 10000
        equity = initial_capital + df['cumulative_pnl']
        equity.index = pd.to_datetime(df['trade_time'])

        return equity

    def print_full_report(self):
        """打印完整的 TCA 报告"""
        print("\n" + "=" * 50)
        print("TCA REPORT - Transaction Cost Analysis")
        print("=" * 50)

        total_cost = self.compute_total_cost()
        print(f"Total Commission: {total_cost:.6f} USDT")

        equity = self.get_equity_curve()
        if not equity.empty:
            sharpe = self.compute_sharpe_ratio(equity.pct_change().dropna())
            max_dd = self.compute_max_drawdown(equity)
            print(f"Sharpe Ratio (Annualized): {sharpe:.4f}")
            print(f"Maximum Drawdown: {max_dd:.4%}")
            print(f"Final Equity: {equity.iloc[-1]:.2f} USDT")
            print(f"Total Return: {(equity.iloc[-1] / equity.iloc[0] - 1):.4%}")

        print("=" * 50)