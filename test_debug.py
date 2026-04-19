import asyncio
from strategy.grid_strategy import GridStrategy
from core.models import Tick
from datetime import datetime

async def test():
    strategy = GridStrategy("test", None, "BTCUSDT", 74420, 74480, 0.001)
    tick = Tick(symbol="BTCUSDT", price=74575.88, timestamp=datetime.now())
    await strategy.on_tick(tick)

asyncio.run(test())