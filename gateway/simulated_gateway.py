import asyncio
import uuid
import traceback
from datetime import datetime
from core.event_bus import EventBus, Event
from core.models import Order, Trade, OrderStatus

class SimulatedGateway:
    def __init__(self, event_bus: EventBus, fill_delay: float = 0.1, slippage: float = 0.0):
        self.event_bus = event_bus
        self.fill_delay = fill_delay
        self.slippage = slippage

    async def send_order(self, order: Order) -> str:
        try:
            print(f"Gateway.send_order called for order {order.order_id}")
            order.status = OrderStatus.SUBMITTED
            order.exchange_order_id = f"SIM_{order.order_id}"
            await self.event_bus.put(Event("ORDER", order))
            print(f"Gateway: Order {order.order_id} submitted event sent")

            await asyncio.sleep(self.fill_delay)
            print(f"Gateway: Order {order.order_id} fill delay completed")

            fill_price = order.price * (1 + self.slippage if order.direction == 'BUY' else 1 - self.slippage)
            order.status = OrderStatus.FILLED
            order.filled_volume = order.volume
            await self.event_bus.put(Event("ORDER", order))
            print(f"Gateway: Order {order.order_id} filled event sent at {fill_price}")

            trade = Trade(
                trade_id=f"TRD_{uuid.uuid4().hex[:8]}",
                order_id=order.order_id,
                symbol=order.symbol,
                direction=order.direction,
                price=fill_price,
                volume=order.volume,
                commission=fill_price * order.volume * 0.001,
                trade_time=datetime.now()
            )
            await self.event_bus.put(Event("TRADE", trade))
            print(f"Gateway: Trade {trade.trade_id} event sent")
            return order.order_id
        except Exception as e:
            print(f"Gateway.send_order ERROR: {e}")
            traceback.print_exc()
            return ""

    async def cancel_order(self, order_id: str):
        pass