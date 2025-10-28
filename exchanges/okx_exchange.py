import ccxt
import asyncio
from typing import Dict, List, Optional, Any
from exchange_interface import ExchangeInterface, Order, OrderSide, OrderType, OrderStatus, Ticker, Balance

class OKXExchange(ExchangeInterface):
    """OKX交易所实现"""
    
    def __init__(self, api_key: str, api_secret: str, passphrase: str, sandbox: bool = True):
        super().__init__(api_key, api_secret, sandbox)
        self.passphrase = passphrase
        self.exchange = None
    
    async def connect(self) -> bool:
        """连接到OKX交易所"""
        try:
            self.exchange = ccxt.okx({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'password': self.passphrase,
                'sandbox': self.sandbox,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',  # 现货交易
                }
            })
            
            # 测试连接
            await self.exchange.load_markets()
            self.is_connected = True
            return True
            
        except Exception as e:
            print(f"连接OKX失败: {e}")
            return False
    
    async def disconnect(self) -> None:
        """断开连接"""
        if self.exchange:
            self.exchange.close()
            self.is_connected = False
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """获取行情数据"""
        if not self.is_connected:
            raise Exception("交易所未连接")
        
        ticker_data = await self.exchange.fetch_ticker(symbol)
        return Ticker(
            symbol=symbol,
            bid=ticker_data['bid'],
            ask=ticker_data['ask'],
            last=ticker_data['last'],
            high=ticker_data['high'],
            low=ticker_data['low'],
            volume=ticker_data['baseVolume'],
            timestamp=ticker_data['timestamp']
        )
    
    async def get_balance(self, currency: str = None) -> Dict[str, Balance]:
        """获取账户余额"""
        if not self.is_connected:
            raise Exception("交易所未连接")
        
        balance_data = await self.exchange.fetch_balance()
        balances = {}
        
        for curr, data in balance_data.items():
            if isinstance(data, dict) and curr != 'info':
                balances[curr] = Balance(
                    currency=curr,
                    free=data['free'],
                    used=data['used'],
                    total=data['total']
                )
        
        if currency:
            return {currency: balances.get(currency)} if currency in balances else {}
        
        return balances
    
    async def create_order(self, symbol: str, side: OrderSide, order_type: OrderType, 
                          amount: float, price: Optional[float] = None) -> Order:
        """创建订单"""
        if not self.is_connected:
            raise Exception("交易所未连接")
        
        try:
            order_data = await self.exchange.create_order(
                symbol=symbol,
                type=order_type.value,
                side=side.value,
                amount=amount,
                price=price
            )
            
            return Order(
                id=str(order_data['id']),
                symbol=symbol,
                side=side,
                type=order_type,
                amount=amount,
                price=price,
                status=OrderStatus(order_data['status']),
                filled=order_data.get('filled', 0),
                remaining=order_data.get('remaining', amount),
                timestamp=order_data.get('timestamp'),
                fee=order_data.get('fee', {}).get('cost')
            )
            
        except Exception as e:
            print(f"创建订单失败: {e}")
            raise
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """取消订单"""
        if not self.is_connected:
            raise Exception("交易所未连接")
        
        try:
            await self.exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            print(f"取消订单失败: {e}")
            return False
    
    async def get_order(self, order_id: str, symbol: str) -> Order:
        """获取订单信息"""
        if not self.is_connected:
            raise Exception("交易所未连接")
        
        order_data = await self.exchange.fetch_order(order_id, symbol)
        return Order(
            id=str(order_data['id']),
            symbol=symbol,
            side=OrderSide(order_data['side']),
            type=OrderType(order_data['type']),
            amount=order_data['amount'],
            price=order_data.get('price'),
            status=OrderStatus(order_data['status']),
            filled=order_data.get('filled', 0),
            remaining=order_data.get('remaining', order_data['amount']),
            timestamp=order_data.get('timestamp'),
            fee=order_data.get('fee', {}).get('cost')
        )
    
    async def get_open_orders(self, symbol: str = None) -> List[Order]:
        """获取未成交订单"""
        if not self.is_connected:
            raise Exception("交易所未连接")
        
        orders_data = await self.exchange.fetch_open_orders(symbol)
        orders = []
        
        for order_data in orders_data:
            orders.append(Order(
                id=str(order_data['id']),
                symbol=order_data['symbol'],
                side=OrderSide(order_data['side']),
                type=OrderType(order_data['type']),
                amount=order_data['amount'],
                price=order_data.get('price'),
                status=OrderStatus(order_data['status']),
                filled=order_data.get('filled', 0),
                remaining=order_data.get('remaining', order_data['amount']),
                timestamp=order_data.get('timestamp'),
                fee=order_data.get('fee', {}).get('cost')
            ))
        
        return orders
    
    async def get_order_history(self, symbol: str = None, limit: int = 100) -> List[Order]:
        """获取订单历史"""
        if not self.is_connected:
            raise Exception("交易所未连接")
        
        orders_data = await self.exchange.fetch_orders(symbol, limit=limit)
        orders = []
        
        for order_data in orders_data:
            orders.append(Order(
                id=str(order_data['id']),
                symbol=order_data['symbol'],
                side=OrderSide(order_data['side']),
                type=OrderType(order_data['type']),
                amount=order_data['amount'],
                price=order_data.get('price'),
                status=OrderStatus(order_data['status']),
                filled=order_data.get('filled', 0),
                remaining=order_data.get('remaining', order_data['amount']),
                timestamp=order_data.get('timestamp'),
                fee=order_data.get('fee', {}).get('cost')
            ))
        
        return orders
    
    async def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取K线数据"""
        if not self.is_connected:
            raise Exception("交易所未连接")
        
        ohlcv = await self.exchange.fetch_ohlcv(symbol, interval, limit=limit)
        klines = []
        
        for candle in ohlcv:
            klines.append({
                'timestamp': candle[0],
                'open': candle[1],
                'high': candle[2],
                'low': candle[3],
                'close': candle[4],
                'volume': candle[5]
            })
        
        return klines
    
    def get_exchange_name(self) -> str:
        """获取交易所名称"""
        return "OKX"
