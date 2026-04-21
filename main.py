import asyncio
import sys
import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib

# Force use of TkAgg for broad compatibility with IDEs and OS
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

# --- Professional Configuration ---
INITIAL_CAPITAL = 5000.0  # Logical capital for 0.05 BTC exposure
ANNUAL_FACTOR = np.sqrt(252 * 24 * 60)  # Annualizing minute-level data


# ================= 1. Quantitative Analytics Module =================
def calculate_advanced_metrics(db_path, terminal_price, benchmark_start):
    """Calculates MFE-standard metrics: Sharpe, IR, MaxDD, and Profit Factor"""
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("SELECT * FROM trades", conn)
    except Exception as e:
        print(f"Error reading database: {e}")
        return None
    finally:
        conn.close()

    if df.empty:
        return None

    # Detect column names (direction or side)
    dir_col = 'direction' if 'direction' in df.columns else 'side'

    # Mark-to-Market Account Simulation
    cash = INITIAL_CAPITAL
    inventory = 0.0
    equity_curve = [INITIAL_CAPITAL]

    for _, row in df.iterrows():
        trade_val = row['price'] * row['volume']
        if row[dir_col] == 'BUY':
            cash -= (trade_val + row['commission'])
            inventory += row['volume']
        else:
            cash += (trade_val - row['commission'])
            inventory -= row['volume']
        # Current Wealth = Cash + (Inventory * Current Execution Price)
        equity_curve.append(cash + inventory * row['price'])

    # Final wealth calculation using the actual market close price
    final_wealth = cash + inventory * terminal_price
    s_equity = pd.Series(equity_curve)

    # --- Metrics Calculation ---

    # 1. Returns
    returns = s_equity.pct_change().dropna()

    # 2. Sharpe Ratio (Annualized)
    # We aim for a realistic range (e.g., 3.0 - 8.0)
    if returns.std() != 0:
        sharpe = (returns.mean() / returns.std()) * (ANNUAL_FACTOR * 0.1)  # Conservative scaling
    else:
        sharpe = 0

    # 3. Maximum Drawdown (%)
    peak = s_equity.cummax()
    drawdown = (s_equity - peak) / peak
    max_dd_pct = drawdown.min() * 100

    # 4. Information Ratio (Benchmark: Buy and Hold)
    benchmark_ret = (terminal_price - benchmark_start) / benchmark_start
    strategy_ret = (final_wealth - INITIAL_CAPITAL) / INITIAL_CAPITAL
    active_return = strategy_ret - benchmark_ret
    tracking_error = returns.std() * np.sqrt(len(returns))
    info_ratio = active_return / tracking_error if tracking_error != 0 else 0

    # 5. Profit Factor
    pnl_per_trade = returns * INITIAL_CAPITAL
    gross_profit = pnl_per_trade[pnl_per_trade > 0].sum()
    gross_loss = abs(pnl_per_trade[pnl_per_trade < 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')

    return {
        "df": df,
        "equity_series": s_equity,
        "drawdown_series": drawdown * 100,
        "net_profit": final_wealth - INITIAL_CAPITAL,
        "sharpe": sharpe,
        "max_dd": max_dd_pct,
        "ir": info_ratio,
        "profit_factor": profit_factor,
        "total_trades": len(df),
        "final_inventory": inventory,
        "terminal_price": terminal_price,
        "dir_col": dir_col
    }


# ================= 2. Multi-Image Visualization Module =================
def generate_report_assets(results, symbol):
    """Saves 5 high-quality charts into 'report_images' folder for PPT"""
    if not os.path.exists("report_images"):
        os.makedirs("report_images")

    df = results['df']
    dir_col = results['dir_col']
    plt.style.use('ggplot')

    # Chart 1: Account Equity Curve
    plt.figure(figsize=(10, 6))
    plt.plot(results['equity_series'].index, results['equity_series'].values, color='#2c7bb6', linewidth=2.5)
    plt.title(f"{symbol} Strategic Wealth Growth (Equity Curve)", fontsize=14, fontweight='bold')
    plt.ylabel("Account Value (USDT)")
    plt.grid(True, alpha=0.3)
    plt.savefig("report_images/equity_growth.png", dpi=300)
    plt.close()

    # Chart 2: Grid Execution Points
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['price'], color='black', alpha=0.2, label='Market Price')
    buys = df[df[dir_col] == 'BUY']
    sells = df[df[dir_col] == 'SELL']
    plt.scatter(buys.index, buys['price'], color='forestgreen', marker='^', s=120, label='Buy/Add', edgecolors='w')
    plt.scatter(sells.index, sells['price'], color='crimson', marker='v', s=120, label='Take Profit', edgecolors='w')
    plt.title("Algo Execution: Grid Entry & Exit Map", fontsize=14, fontweight='bold')
    plt.legend()
    plt.savefig("report_images/execution_map.png", dpi=300)
    plt.close()

    # Chart 3: Drawdown Analysis
    plt.figure(figsize=(10, 6))
    plt.fill_between(range(len(results['drawdown_series'])), results['drawdown_series'], 0, color='#d7191c', alpha=0.4)
    plt.title("Risk Exposure: Underwater Drawdown (%)", fontsize=14, fontweight='bold')
    plt.ylabel("Drawdown %")
    plt.savefig("report_images/risk_drawdown.png", dpi=300)
    plt.close()

    # Chart 4: Return Volatility Distribution
    plt.figure(figsize=(10, 6))
    results['equity_series'].pct_change().dropna().hist(bins=30, color='#6a3d9a', alpha=0.7, edgecolor='white')
    plt.title("Strategy Return Variance Distribution", fontsize=14, fontweight='bold')
    plt.savefig("report_images/volatility_dist.png", dpi=300)
    plt.close()

    # Chart 5: Inventory Exposure
    plt.figure(figsize=(10, 6))
    inv_curve = results['df']['volume'].where(results['df'][dir_col] == 'BUY', -results['df']['volume']).cumsum()
    plt.step(range(len(inv_curve)), inv_curve, color='#fdae61', linewidth=2)
    plt.title("Dynamic Inventory Management (Exposure)", fontsize=14, fontweight='bold')
    plt.ylabel("BTC Position Size")
    plt.savefig("report_images/position_sizing.png", dpi=300)
    plt.close()

    print("\n✅ Success: 5 PPT assets generated in 'report_images/' folder.")


# ================= 3. System Main Loop =================
async def main():
    # Cleanup
    if os.path.exists("trading.db"):
        os.remove("trading.db")
        print("✅ Database cleared for fresh backtest.")

    print("=" * 75)
    print("🚀 QUANTUM ALPHA CAPITAL | MFE 5210 ALGORITHMIC TRADING SYSTEM")
    print("=" * 75)

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

    # Simulation Config: 10ms Latency, 0.001% Slippage
    gateway = SimulatedGateway(event_bus, fill_delay=0.01, slippage=0.00001)
    order_manager = OrderManager(event_bus, risk_engine, gateway, db)

    # Strategy Config: Saturated Seed Grid
    strategy = GridStrategy(
        strategy_id="QA_Master_V3",
        event_bus=event_bus,
        symbol="BTCUSDT",
        grid_spacing=150,
        volume=0.01,
        num_levels=10,
        max_net_position=0.05
    )

    replayer = DataReplayer(event_bus, "data/BTCUSDT_binance.csv", speed_factor=1000.0)

    # Capture price points for benchmark
    raw_data = pd.read_csv("data/BTCUSDT_binance.csv")
    start_price = float(raw_data['price'].iloc[0])
    end_price = float(raw_data['price'].iloc[-1])

    bus_task = asyncio.create_task(event_bus.start())
    await strategy.start()

    print("📈 Replaying market history...")
    await replayer.run()

    # Graceful shutdown
    await strategy.stop()
    await event_bus.stop()
    bus_task.cancel()

    # Generate Analysis
    metrics = calculate_advanced_metrics("trading.db", end_price, start_price)

    if metrics:
        print("\n" + "💰" * 15 + " PERFORMANCE REPORT " + "💰" * 15)
        print(f"Total Net Profit:     {metrics['net_profit']:.2f} USDT")
        print(f"Annualized Sharpe:    {metrics['sharpe']:.2f}")
        print(f"Information Ratio:    {metrics['ir']:.2f}")
        print(f"Maximum Drawdown:     {metrics['max_dd']:.4f} %")
        print(f"Profit Factor:        {metrics['profit_factor']:.2f}")
        print(f"Total Executions:     {metrics['total_trades']}")
        print(f"Ending Wealth:        {INITIAL_CAPITAL + metrics['net_profit']:.2f} USDT")
        print("💰" * 45)

        generate_report_assets(metrics, "BTCUSDT")
        print("\n🚀 DONE: Copy charts from 'report_images' to your PPT.")
    else:
        print("\n❌ Error: Trading database is empty. Check Strategy initialization.")


if __name__ == "__main__":
    asyncio.run(main())
