from typing import Dict, List, Optional
from exchange_interface import ExchangeInterface
from exchanges.binance_exchange import BinanceExchange
from exchanges.okx_exchange import OKXExchange
from config_manager import config

class ExchangeFactory:
    """交易所工厂类"""
    
    @staticmethod
    def create_exchange(exchange_name: str) -> Optional[ExchangeInterface]:
        """创建交易所实例"""
        exchange_config = config.get(f"exchanges.{exchange_name}")
        
        if not exchange_config or not exchange_config.get("enabled"):
            return None
        
        if exchange_name.lower() == "binance":
            return BinanceExchange(
                api_key=exchange_config.get("api_key", ""),
                api_secret=exchange_config.get("api_secret", ""),
                sandbox=exchange_config.get("sandbox", True)
            )
        elif exchange_name.lower() == "okx":
            return OKXExchange(
                api_key=exchange_config.get("api_key", ""),
                api_secret=exchange_config.get("api_secret", ""),
                passphrase=exchange_config.get("passphrase", ""),
                sandbox=exchange_config.get("sandbox", True)
            )
        else:
            raise ValueError(f"不支持的交易所: {exchange_name}")
    
    @staticmethod
    def get_available_exchanges() -> List[str]:
        """获取可用的交易所列表"""
        exchanges = []
        exchange_configs = config.get("exchanges", {})
        
        for exchange_name, exchange_config in exchange_configs.items():
            if exchange_config.get("enabled", False):
                exchanges.append(exchange_name)
        
        return exchanges

class ExchangeManager:
    """交易所管理器"""
    
    def __init__(self):
        self.exchanges: Dict[str, ExchangeInterface] = {}
        self.active_exchange: Optional[ExchangeInterface] = None
    
    async def initialize_exchanges(self) -> bool:
        """初始化所有启用的交易所"""
        available_exchanges = ExchangeFactory.get_available_exchanges()
        
        for exchange_name in available_exchanges:
            try:
                exchange = ExchangeFactory.create_exchange(exchange_name)
                if exchange and await exchange.connect():
                    self.exchanges[exchange_name] = exchange
                    print(f"成功连接到 {exchange_name}")
                else:
                    print(f"连接 {exchange_name} 失败")
            except Exception as e:
                print(f"初始化 {exchange_name} 时出错: {e}")
        
        # 设置默认交易所
        if self.exchanges:
            self.active_exchange = list(self.exchanges.values())[0]
            return True
        
        return False
    
    def set_active_exchange(self, exchange_name: str) -> bool:
        """设置活跃交易所"""
        if exchange_name in self.exchanges:
            self.active_exchange = self.exchanges[exchange_name]
            return True
        return False
    
    def get_active_exchange(self) -> Optional[ExchangeInterface]:
        """获取当前活跃的交易所"""
        return self.active_exchange
    
    def get_exchange(self, exchange_name: str) -> Optional[ExchangeInterface]:
        """获取指定交易所"""
        return self.exchanges.get(exchange_name)
    
    async def close_all_exchanges(self) -> None:
        """关闭所有交易所连接"""
        for exchange in self.exchanges.values():
            await exchange.disconnect()
        self.exchanges.clear()
        self.active_exchange = None
