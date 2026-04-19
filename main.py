import asyncio
import sys
import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib

# Force use of TkAgg to prevent GUI backend errors in IDEs like PyCharm
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

# Analysis Configurations
RISK_FREE_RATE = 0.02  # Assumed 2% Risk-Free Rate
FREQUENCY = 365 * 24 * 60  # Minute-level data assumed for annualization


# ================= 1. Performance Metrics Module =================
def calculate_advanced_metrics(db_path, final_market_price, benchmark_price_start):
    """Calculates professional quantitative metrics for the Final Report"""
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("SELECT * FROM trades", conn)
    except Exception as e:
        print(f"Database Error: {e}")
        return None
    finally:
        conn.close()

    if df.empty:
        return None

    # Identify direction column (handles different naming conventions)
    dir_col = 'direction' if 'direction' in df.columns else 'side'

    # Simulated Account Calculation
    cash = 0.0
    inventory = 0.0
    equity_curve = []

    for _, row in df.iterrows():
        val = row['price'] * row['volume']
        if row[dir_col] == 'BUY':
            cash -= (val + row['commission'])
            inventory += row['volume']
        else:
            cash += (val - row['commission'])
            inventory -= row['volume']
        # Mark-to-Market Equity
        equity_curve.append(cash + inventory * row['price'])

    # Final Settlement
    final_equity = cash + inventory * final_market_price
    df['equity'] = equity_curve

    # --- Quantitative Calculations ---
    returns = pd.Series(equity_curve).pct_change().fillna(0)

    # 1. Sharpe Ratio
    avg_ret = returns.mean()
    std_ret = returns.std()
    sharpe = (avg_ret / std_ret) * np.sqrt(FREQUENCY) if std_ret != 0 else 0

    # 2. Maximum Drawdown (Percentage)
    peak = np.maximum.accumulate(df['equity'].values)
    drawdowns = (df['equity'].values - peak) / (peak + 1e-6)
    max_dd = np.min(drawdowns)

    # 3. Information Ratio
    # Benchmarked against a simple Buy-and-Hold strategy
    benchmark_returns = (final_market_price - benchmark_price_start) / benchmark_price_start
    active_return = (final_equity / abs(equity_curve[0]) if equity_curve[0] != 0 else 0) - benchmark_returns
    tracking_error = returns.std() * np.sqrt(FREQUENCY)
    info_ratio = active_return / tracking_error if tracking_error != 0 else 0

    # 4. Strategy Win Rate (Proxied by profitable trade price movements)
    win_rate = len(df[df['price'].diff() > 0]) / len(df)

    return {
        "df": df,
        "final_pnl": final_equity,
        "sharpe": sharpe,
        "max_dd": max_dd * 100,
        "ir": info_ratio,
        "win_rate": win_rate * 100,
        "net_pos": inventory,
        "total_trades": len(df),
        "final_price": final_market_price,
        "drawdown_series": drawdowns * 100,
        "dir_col": dir_col
    }


# ================= 2. Visualization Module (PPT Assets) =================
def generate_ppt_images(results, symbol):
    """Generates 5 independent high-resolution charts for the PPT presentation"""
    if not os.path.exists("report_images"):
        os.makedirs("report_images")

    df = results['df']
    dir_col = results['dir_col']
    plt.style.use('ggplot')

    # Chart 1: Cumulative Equity Curve
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['equity'], color='blue', linewidth=2)
    plt.title(f"Quantum Alpha: {symbol} Cumulative Equity", fontsize=14)
    plt.xlabel("Trade Sequence")
    plt.ylabel("Total Wealth (USDT)")
    plt.grid(True, alpha=0.3)
    plt.savefig("report_images/1_equity_curve.png", dpi=300)
    plt.close()

    # Chart 2: Trade Execution Map
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['price'], color='black', alpha=0.2, label='Price')
    buys = df[df[dir_col] == 'BUY']
    sells = df[df[dir_col] == 'SELL']
    plt.scatter(buys.index, buys['price'], color='green', marker='^', label='Buy Entry', s=80)
    plt.scatter(sells.index, sells['price'], color='red', marker='v', label='Profit Take', s=80)
    plt.title("Execution Strategy Visualization", fontsize=14)
    plt.legend()
    plt.savefig("report_images/2_trade_execution.png", dpi=300)
    plt.close()

    # Chart 3: Underwater Drawdown
    plt.figure(figsize=(10, 6))
    plt.fill_between(range(len(results['drawdown_series'])), results['drawdown_series'], 0, color='red', alpha=0.3)
    plt.title("Risk Exposure: Underwater Drawdown Chart", fontsize=14)
    plt.ylabel("Drawdown %")
    plt.savefig("report_images/3_max_drawdown.png", dpi=300)
    plt.close()

    # Chart 4: Return Distribution
    plt.figure(figsize=(10, 6))
    pd.Series(df['equity']).diff().hist(bins=30, color='purple', alpha=0.6)
    plt.title("Daily Returns Volatility Distribution", fontsize=14)
    plt.savefig("report_images/4_returns_dist.png", dpi=300)
    plt.close()

    # Chart 5: Inventory Exposure
    plt.figure(figsize=(10, 6))
    inventory_curve = []
    inv = 0
    for _, r in df.iterrows():
        inv += r['volume'] if r[dir_col] == 'BUY' else -r['volume']
        inventory_curve.append(inv)
    plt.step(range(len(inventory_curve)), inventory_curve, color='orange', linewidth=2)
    plt.title("Inventory Management (Position Sizing)", fontsize=14)
    plt.ylabel("Asset Quantity (BTC)")
    plt.savefig("report_images/5_position_management.png", dpi=300)
    plt.close()

    print("\n✅ 5 Presentation Charts saved to 'report_images' folder.")


# ================= 3. Main Execution Logic =================
async def main():
    # Database Initialization
    if os.path.exists("trading.db"):
        os.remove("trading.db")
        print("✅ Previous session data cleared.")

    print("=" * 60)
    print("🚀 Algorithmic Trading System | Quantum Alpha Capital")
    print("=" * 60)

    from core.event_bus import EventBus
    from core.data_replayer import DataReplayer
    from gateway.simulated_gateway import SimulatedGateway
    from risk.risk_engine import RiskEngine
    from oms.order_manager import OrderManager
    from strategy.grid_strategy import GridStrategy
    from db.database import Database

    event_bus = EventBus()
    risk_engine = RiskEngine("config/risk_rules.yaml")
    db = Database()

    # High-fidelity simulation parameters
    gateway = SimulatedGateway(event_bus, fill_delay=0.01, slippage=0.00001)
    order_manager = OrderManager(event_bus, risk_engine, gateway, db)

    # Strategy Parameters
    strategy = GridStrategy(
        strategy_id="QA_Grid_Master",
        event_bus=event_bus,
        symbol="BTCUSDT",
        grid_spacing=180,
        volume=0.01,
        num_levels=10,
        max_net_position=0.05
    )

    replayer = DataReplayer(event_bus, "data/BTCUSDT_binance.csv", speed_factor=1000.0)

    # Load raw data for benchmark calculation
    raw_data = pd.read_csv("data/BTCUSDT_binance.csv")
    start_market_price = float(raw_data['price'].iloc[0])
    end_market_price = float(raw_data['price'].iloc[-1])

    # Execute Replay
    bus_task = asyncio.create_task(event_bus.start())
    await strategy.start()

    print("📈 Replaying market data and executing trade logic...")
    await replayer.run()

    # Graceful Shutdown
    await strategy.stop()
    await event_bus.stop()
    bus_task.cancel()

    # Performance Reporting
    results = calculate_advanced_metrics("trading.db", end_market_price, start_market_price)

    if results:
        print("\n" + "📊" * 15 + " PERFORMANCE REPORT " + "📊" * 15)
        print(f"1. Total Net Profit:     {results['final_pnl']:.2f} USDT")
        print(f"2. Annualized Sharpe:    {results['sharpe']:.2f}")
        print(f"3. Information Ratio:    {results['ir']:.2f}")
        print(f"4. Max Drawdown:         {results['max_dd']:.2f}%")
        print(f"5. Strategy Win Rate:    {results['win_rate']:.2f}%")
        print(f"6. Total Executions:     {results['total_trades']}")
        print(f"7. Terminal Market Price: {results['final_price']:.2f} USDT")
        print("📊" * 45)

        generate_ppt_images(results, "BTCUSDT")
        print("\n🚀 All analytics completed. Assets ready for Presentation.")
    else:
        print("\n❌ No trade data detected. Please check strategy parameters.")


if __name__ == "__main__":
    asyncio.run(main())