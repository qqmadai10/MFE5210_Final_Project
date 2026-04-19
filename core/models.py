from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional

class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class Tick(BaseModel):
    symbol: str
    price: float
    timestamp: datetime

class Signal(BaseModel):
    strategy_id: str
    symbol: str
    direction: Direction
    price: float
    volume: float
    signal_time: datetime

class Order(BaseModel):
    order_id: str
    signal_id: str
    symbol: str
    direction: Direction
    order_type: OrderType
    price: float
    volume: float
    filled_volume: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    exchange_order_id: Optional[str] = None
    reject_reason: Optional[str] = None
    created_at: datetime = datetime.now()

class Trade(BaseModel):
    trade_id: str
    order_id: str
    symbol: str
    direction: Direction
    price: float
    volume: float
    commission: float = 0.0
    trade_time: datetime