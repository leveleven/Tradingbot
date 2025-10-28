from typing import Dict, List, Any, Optional
from trading_strategies import TradingStrategy, RSIMACDStrategy, BollingerBandsStrategy, MovingAverageStrategy
from config_manager import config

class StrategyFactory:
    """策略工厂类"""
    
    @staticmethod
    def create_strategy(strategy_name: str) -> Optional[TradingStrategy]:
        """创建交易策略实例"""
        algorithm_config = config.get("algorithm", {})
        
        if strategy_name.lower() == "rsi_macd":
            return RSIMACDStrategy(algorithm_config)
        elif strategy_name.lower() == "bollinger":
            return BollingerBandsStrategy(algorithm_config)
        elif strategy_name.lower() == "moving_average":
            return MovingAverageStrategy(algorithm_config)
        else:
            raise ValueError(f"不支持的策略: {strategy_name}")
    
    @staticmethod
    def get_available_strategies() -> List[str]:
        """获取可用的策略列表"""
        return ["rsi_macd", "bollinger", "moving_average"]

class StrategyManager:
    """策略管理器"""
    
    def __init__(self):
        self.strategies: Dict[str, TradingStrategy] = {}
        self.active_strategy: Optional[TradingStrategy] = None
    
    def initialize_strategies(self) -> bool:
        """初始化所有策略"""
        try:
            strategy_name = config.get("algorithm.strategy", "rsi_macd")
            strategy = StrategyFactory.create_strategy(strategy_name)
            
            if strategy:
                self.strategies[strategy_name] = strategy
                self.active_strategy = strategy
                print(f"成功初始化策略: {strategy_name}")
                return True
            else:
                print(f"初始化策略失败: {strategy_name}")
                return False
                
        except Exception as e:
            print(f"初始化策略时出错: {e}")
            return False
    
    def set_active_strategy(self, strategy_name: str) -> bool:
        """设置活跃策略"""
        if strategy_name in self.strategies:
            self.active_strategy = self.strategies[strategy_name]
            return True
        
        # 如果策略不存在，尝试创建
        try:
            strategy = StrategyFactory.create_strategy(strategy_name)
            if strategy:
                self.strategies[strategy_name] = strategy
                self.active_strategy = strategy
                return True
        except Exception as e:
            print(f"创建策略失败: {e}")
        
        return False
    
    def get_active_strategy(self) -> Optional[TradingStrategy]:
        """获取当前活跃的策略"""
        return self.active_strategy
    
    def get_strategy(self, strategy_name: str) -> Optional[TradingStrategy]:
        """获取指定策略"""
        return self.strategies.get(strategy_name)
