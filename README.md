# Algorithmic Trading System & Alpha Factors

**Course:** MFE5210 Algorithmic Trading  
**Members:** 
Qiao Lanying 225040361  
Li Xianfei 225040293  
Luo Jiahao 225040400 

---
### 📁 Project Structure
```bash
MFE5210_Final_Project/
├── main.py                         # Main entry point
├── requirements.txt                # Python dependencies
├── trading.db                      # SQLite database (orders/trades)
├── core/                           # Event bus, data models, data replayer
├── gateway/                        # Simulated gateway
├── strategy/                       # Base strategy + grid strategy
├── oms/                            # Order management system
├── report_images/
├── risk/                           # Risk engine
├── db/                             # Database operations
├── tca/                            # Transaction cost analysis
├── gui/                            # Tkinter monitoring GUI
├── config/                         # Risk rules configuration
├── data/                           # Market data (BTCUSDT_binance.csv)
└── alpha_factors/                  # Alpha factor generation & analysis
    ├── btc_data.csv                # BTC daily data
    ├── final_factors.py            # 15 factor calculations
    ├── select_best_factors.py      # Low-correlation factor selection
    ├── analysis.py                 # Correlation and Sharpe ratio analysis
    ├── selected_5_factors.csv      # Final 5 selected factors
    ├── correlation_matrix.png      # Correlation heatmap
    └── sharpe_ratios.csv           # Sharpe ratios per factor
```


---
### System Architecture (Event-Driven)
```bash
CSV Data → DataReplayer → EventBus → Strategy → Signal → OMS → RiskEngine → Gateway → Simulated Execution
↑ ↓
└──────────────────────── Order/Trade Feedback ─────────────────────────┘
```

### Core Components

| Module | Class | Responsibility |
|--------|-------|----------------|
| Event Bus | `EventBus` | Asynchronous message dispatch (asyncio.Queue) |
| Data Replayer | `DataReplayer` | Reads historical ticks from CSV and publishes |
| Strategy | `GridStrategy` | Grid trading logic, generates buy/sell signals |
| Order Management | `OrderManager` | Receives signals, applies risk, sends orders |
| Risk Engine | `RiskEngine` | Checks position limits and order volume |
| Gateway | `SimulatedGateway` | Simulates execution (delay, slippage, commission) |
| Database | `Database` | SQLite storage for orders and trades |
| TCA | `TCAAnalyzer` | Computes total commission, Sharpe ratio, max drawdown |

### Backtest Results
1. Total Net Profit:     41.87 USDT
2. Annualized Sharpe:    -251.08
3. Information Ratio:    0.01
4. Max Drawdown:         -20.75%
5. Strategy Win Rate:    28.57%
6. Total Executions:     7
7. Terminal Market Price: 74569.05 USDT
---


### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Trading System
```bash
cd MFE5210_Final_Project
python main.py
```

### 3. View Database
```bash
cd MFE5210_Final_Project
python -c "import sqlite3; conn = sqlite3.connect('trading.db'); rows = conn.execute('SELECT * FROM trades LIMIT 10;').fetchall(); [print(row) for row in rows]; conn.close()"
```

---
## Summary
### Trading System

| Requirement | Status |
|-------------|--------|
| Event-driven architecture | ✅ |
| CEP + OMS + RMS + Gateway | ✅ |
| Strategy only generates signals | ✅ |
| Holding period < 1 day | ✅ |
| Simulated gateway | ✅ |
| Database storage | ✅ |
| TCA analysis | ✅ |
| GUI monitoring | ✅ |



## References
- Binance API: https://binance-docs.github.io/apidocs
- vn.py Framework: https://github.com/vnpy/vnpy
- Pandas Documentation: https://pandas.pydata.org

