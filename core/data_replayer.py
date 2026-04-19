import asyncio
import pandas as pd
from core.event_bus import EventBus, Event
from core.models import Tick


class DataReplayer:
    def __init__(self, event_bus: EventBus, csv_path: str, speed_factor: float = 1.0):
        self.event_bus = event_bus
        self.csv_path = csv_path
        self.speed_factor = speed_factor

    async def run(self):
        print(f"Loading data from {self.csv_path}...")
        df = pd.read_csv(self.csv_path)
        print(f"Loaded {len(df)} records. Starting replay...")

        for i, row in df.iterrows():
            tick = Tick(
                symbol=row.get('symbol', 'BTCUSDT'),
                price=float(row['price']),
                timestamp=pd.to_datetime(row['timestamp'])
            )
            await self.event_bus.put(Event("TICK", tick))

            if i % 100 == 0:
                print(f"Replayed {i} ticks, price={tick.price}")

            await asyncio.sleep(0.01)  # 每 tick 10ms 延迟

        print("Data replay finished.")