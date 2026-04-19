from core.event_bus import EventBus, Event
from core.models import Tick, Signal, Direction
from datetime import datetime


class BaseStrategy:
    def __init__(self, strategy_id: str, event_bus: EventBus, symbol: str):
        self.strategy_id = strategy_id
        self.event_bus = event_bus
        self.symbol = symbol
        self._running = False

    async def start(self):
        self._running = True
        self.event_bus.subscribe("TICK", self._on_tick)

    async def stop(self):
        self._running = False

    async def _on_tick(self, event: Event):
        if not self._running:
            return
        tick: Tick = event.data

        # 调试打印：显示所有高价 tick
        if tick.price >= 74480:
            print(f"[DEBUG] _on_tick: price={tick.price}, tick.symbol={tick.symbol}, self.symbol={self.symbol}")

        # 暂时注释掉 symbol 检查，确保所有 tick 都能传递给 on_tick
        # if tick.symbol != self.symbol:
        #     return

        await self.on_tick(tick)

    async def on_tick(self, tick: Tick):
        pass

    async def emit_signal(self, direction: Direction, price: float, volume: float):
        signal = Signal(
            strategy_id=self.strategy_id,
            symbol=self.symbol,
            direction=direction,
            price=price,
            volume=volume,
            signal_time=datetime.now()
        )
        await self.event_bus.put(Event("SIGNAL", signal))