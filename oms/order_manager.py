import uuid
import traceback
from core.event_bus import EventBus, Event
from core.models import Signal, Order, OrderStatus, OrderType, Trade, Direction
from risk.risk_engine import RiskEngine
from gateway.simulated_gateway import SimulatedGateway
from db.database import Database


class OrderManager:
    def __init__(self, event_bus: EventBus, risk_engine: RiskEngine, gateway: SimulatedGateway, db: Database):
        self.event_bus = event_bus
        self.risk = risk_engine
        self.gateway = gateway
        self.db = db
        self.orders = {}
        self.event_bus.subscribe("SIGNAL", self.on_signal)
        self.event_bus.subscribe("ORDER", self.on_order)
        self.event_bus.subscribe("TRADE", self.on_trade)

    async def on_signal(self, event: Event):
        try:
            signal: Signal = event.data
            print(
                f"OMS received SIGNAL: {signal.symbol} {signal.direction} price={signal.price} volume={signal.volume}")
            allowed, reason = self.risk.check_signal(signal)
            print(f"OMS check_signal result: allowed={allowed}, reason={reason}")

            order_id = f"ORD_{uuid.uuid4().hex[:8]}"
            print(f"OMS: created order_id={order_id}")

            order = Order(
                order_id=order_id,
                signal_id=signal.strategy_id,
                symbol=signal.symbol,
                direction=signal.direction,
                order_type=OrderType.LIMIT,
                price=signal.price,
                volume=signal.volume,
                status=OrderStatus.REJECTED if not allowed else OrderStatus.PENDING,
                reject_reason=reason if not allowed else None
            )
            self.orders[order_id] = order
            print(f"OMS: order object created, allowed={allowed}")

            if allowed:
                print(f"OMS: calling gateway.send_order for {order_id}")
                result = await self.gateway.send_order(order)
                print(f"OMS: gateway.send_order returned {result}")
            else:
                print(f"OMS: signal REJECTED: {reason}")
                await self.event_bus.put(Event("ORDER", order))
        except Exception as e:
            print(f"OMS on_signal ERROR: {e}")
            traceback.print_exc()

    async def on_order(self, event: Event):
        """处理订单状态更新，保存到数据库"""
        try:
            order: Order = event.data
            self.db.save_order(order)
            print(f"OMS: order {order.order_id} saved to DB, status={order.status}")
        except Exception as e:
            print(f"OMS on_order ERROR: {e}")
            traceback.print_exc()

    async def on_trade(self, event: Event):
        try:
            trade: Trade = event.data
            print(
                f"OMS received TRADE: {trade.symbol} {trade.direction} price={trade.price} volume={trade.volume} commission={trade.commission}")
            signed = trade.volume if trade.direction == Direction.BUY else -trade.volume
            self.risk.update_position(trade.symbol, signed)
            # 保存成交记录到数据库
            self.db.save_trade(trade)
            print(f"OMS: trade {trade.trade_id} saved to DB")
        except Exception as e:
            print(f"OMS on_trade ERROR: {e}")
            traceback.print_exc()