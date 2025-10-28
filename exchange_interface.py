from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REJECTED = "rejected"

@dataclass
class Order:
    """订单数据结构"""
    id: str
    symbol: str
    side: OrderSide
    type: OrderType
    amount: float
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled: float = 0.0
    remaining: float = 0.0
    timestamp: Optional[int] = None
    fee: Optional[float] = None

@dataclass
class Ticker:
    """行情数据结构"""
    symbol: str
    bid: float
    ask: float
    last: float
    high: float
    low: float
    volume: float
    timestamp: int

@dataclass
class Balance:
    """余额数据结构"""
    currency: str
    free: float
    used: float
    total: float

class ExchangeInterface(ABC):
    """交易所接口抽象基类"""
    
    def __init__(self, api_key: str, api_secret: str, sandbox: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.sandbox = sandbox
        self.is_connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """连接到交易所"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker:
        """获取行情数据"""
        pass
    
    @abstractmethod
    async def get_balance(self, currency: str = None) -> Dict[str, Balance]:
        """获取账户余额"""
        pass
    
    @abstractmethod
    async def create_order(self, symbol: str, side: OrderSide, order_type: OrderType, 
                          amount: float, price: Optional[float] = None) -> Order:
        """创建订单"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """取消订单"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str, symbol: str) -> Order:
        """获取订单信息"""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: str = None) -> List[Order]:
        """获取未成交订单"""
        pass
    
    @abstractmethod
    async def get_order_history(self, symbol: str = None, limit: int = 100) -> List[Order]:
        """获取订单历史"""
        pass
    
    @abstractmethod
    async def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取K线数据"""
        pass
    
    @abstractmethod
    def get_exchange_name(self) -> str:
        """获取交易所名称"""
        pass
