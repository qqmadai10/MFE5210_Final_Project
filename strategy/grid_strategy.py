from strategy.base import BaseStrategy
from core.models import Tick, Direction


class GridStrategy(BaseStrategy):
    def __init__(self, strategy_id, event_bus, symbol, grid_spacing, volume,
                 num_levels=8, max_net_position=0.05):
        super().__init__(strategy_id, event_bus, symbol)
        self.grid_spacing = grid_spacing
        self.volume = volume
        self.num_levels = num_levels
        self.max_net_position = max_net_position

        self.buy_levels = []
        self.sell_levels = []
        self.initialized = False
        self.net_position = 0.0

        # --- 激进获利系数 ---
        # 卖出价比买入价高出 1.3 倍间距，确保每一单扣完手续费还有大肉
        self.profit_ratio = 1.3

    def init_grid(self, current_price):
        """初始化分布网格"""
        self.buy_levels = []
        self.sell_levels = []
        for i in range(1, self.num_levels + 1):
            self.buy_levels.append(round(current_price - i * self.grid_spacing, 2))
            self.sell_levels.append(round(current_price + i * self.grid_spacing, 2))
        self.initialized = True
        print(f"\n💰 利润收割模式重置 | 价格: {current_price} | 当前持仓: {self.net_position:.4f}")

    async def on_tick(self, tick: Tick):
        # 1. 初始化底仓逻辑：分三笔，每笔 0.01，总计 0.03
        if not self.initialized:
            self.init_grid(tick.price)

            total_target_base = 0.03  # 想要建立的总底仓
            single_max_vol = 0.01  # 必须遵守风控单笔 0.01 的限制

            print(f"🚀 正在分三笔建立饱和底仓...")
            for i in range(3):
                # 稍微偏离一点价格，确保被系统识别为不同信号
                target_p = tick.price - (i * 5)
                await self.emit_signal(Direction.BUY, target_p, single_max_vol)
                self.net_position += single_max_vol
                print(f"📦 底仓第 {i + 1} 笔已发出 | 价格: {target_p} | 累计持仓: {self.net_position:.4f}")
            return

        # 2. 动态追踪：当价格大幅上涨，整体抬升网格
        if tick.price > max(self.sell_levels):
            print(f"🚀 价格起飞，平移网格至 {tick.price}")
            self.init_grid(tick.price)
            return

        # 3. 买入逻辑 (补仓)
        triggered_buys = [p for p in self.buy_levels if tick.price <= p]
        if triggered_buys:
            for b_p in sorted(triggered_buys, reverse=True):
                # 补仓也用 0.01 提高威力，但不能超过 0.05 的总上限
                if self.net_position + 0.01 <= self.max_net_position:
                    await self.emit_signal(Direction.BUY, tick.price, 0.01)
                    self.net_position += 0.01
                    print(f"🔵 密集补仓 | 价格:{tick.price} | 仓位:{self.net_position:.4f}")

                    self.buy_levels.remove(b_p)
                    self.buy_levels.append(round(b_p - self.grid_spacing, 2))
                    self.sell_levels.append(round(tick.price + self.grid_spacing * self.profit_ratio, 2))
                    break

        # 4. 卖出逻辑 (止盈)
        # 核心保护：只有持仓 > 0.03 (即超过底仓) 时，才卖出获利，保留最肥的利润在手里
        if self.net_position > 0.03:
            triggered_sells = [p for p in self.sell_levels if tick.price >= p]
            if triggered_sells:
                for s_p in sorted(triggered_sells):
                    await self.emit_signal(Direction.SELL, tick.price, 0.01)
                    self.net_position -= 0.01
                    print(f"🔴 利润止盈 | 价格:{tick.price} | 仓位:{self.net_position:.4f}")

                    self.sell_levels.remove(s_p)
                    self.sell_levels.append(round(s_p + self.grid_spacing, 2))
                    self.buy_levels.append(round(tick.price - self.grid_spacing * self.profit_ratio, 2))
                    break