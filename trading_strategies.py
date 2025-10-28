import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class Signal(Enum):
    """交易信号"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

@dataclass
class TradingSignal:
    """交易信号数据结构"""
    symbol: str
    signal: Signal
    strength: float  # 信号强度 0-1
    price: float
    timestamp: int
    reason: str  # 信号原因

class TechnicalIndicator(ABC):
    """技术指标抽象基类"""
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """计算技术指标"""
        pass

class RSI(TechnicalIndicator):
    """相对强弱指数"""
    
    def __init__(self, period: int = 14):
        self.period = period
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """计算RSI指标"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

class MACD(TechnicalIndicator):
    """MACD指标"""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def calculate(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算MACD指标"""
        ema_fast = data['close'].ewm(span=self.fast).mean()
        ema_slow = data['close'].ewm(span=self.slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

class BollingerBands(TechnicalIndicator):
    """布林带指标"""
    
    def __init__(self, period: int = 20, std_dev: float = 2):
        self.period = period
        self.std_dev = std_dev
    
    def calculate(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算布林带指标"""
        sma = data['close'].rolling(window=self.period).mean()
        std = data['close'].rolling(window=self.period).std()
        
        upper_band = sma + (std * self.std_dev)
        lower_band = sma - (std * self.std_dev)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }

class MovingAverage(TechnicalIndicator):
    """移动平均线"""
    
    def __init__(self, period: int):
        self.period = period
    
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """计算移动平均线"""
        return data['close'].rolling(window=self.period).mean()

class TradingStrategy(ABC):
    """交易策略抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.indicators = {}
        self._initialize_indicators()
    
    @abstractmethod
    def _initialize_indicators(self) -> None:
        """初始化技术指标"""
        pass
    
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> TradingSignal:
        """生成交易信号"""
        pass
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return self.__class__.__name__

class RSIMACDStrategy(TradingStrategy):
    """RSI + MACD 组合策略"""
    
    def _initialize_indicators(self) -> None:
        """初始化技术指标"""
        self.indicators['rsi'] = RSI(period=self.config.get('rsi_period', 14))
        self.indicators['macd'] = MACD(
            fast=self.config.get('macd_fast', 12),
            slow=self.config.get('macd_slow', 26),
            signal=self.config.get('macd_signal', 9)
        )
    
    def generate_signal(self, data: pd.DataFrame) -> TradingSignal:
        """生成交易信号"""
        if len(data) < max(self.config.get('macd_slow', 26), self.config.get('rsi_period', 14)):
            return TradingSignal(
                symbol=data.iloc[-1].get('symbol', ''),
                signal=Signal.HOLD,
                strength=0.0,
                price=data['close'].iloc[-1],
                timestamp=data.index[-1],
                reason="数据不足"
            )
        
        # 计算指标
        rsi = self.indicators['rsi'].calculate(data)
        macd_data = self.indicators['macd'].calculate(data)
        
        current_rsi = rsi.iloc[-1]
        current_macd = macd_data['macd'].iloc[-1]
        current_signal = macd_data['signal'].iloc[-1]
        current_price = data['close'].iloc[-1]
        
        # 买入信号：RSI超卖 + MACD金叉
        if (current_rsi < self.config.get('rsi_oversold', 30) and 
            current_macd > current_signal and 
            macd_data['macd'].iloc[-2] <= macd_data['signal'].iloc[-2]):
            
            strength = (self.config.get('rsi_oversold', 30) - current_rsi) / 30
            return TradingSignal(
                symbol=data.iloc[-1].get('symbol', ''),
                signal=Signal.BUY,
                strength=min(strength, 1.0),
                price=current_price,
                timestamp=data.index[-1],
                reason=f"RSI超卖({current_rsi:.2f}) + MACD金叉"
            )
        
        # 卖出信号：RSI超买 + MACD死叉
        elif (current_rsi > self.config.get('rsi_overbought', 70) and 
              current_macd < current_signal and 
              macd_data['macd'].iloc[-2] >= macd_data['signal'].iloc[-2]):
            
            strength = (current_rsi - self.config.get('rsi_overbought', 70)) / 30
            return TradingSignal(
                symbol=data.iloc[-1].get('symbol', ''),
                signal=Signal.SELL,
                strength=min(strength, 1.0),
                price=current_price,
                timestamp=data.index[-1],
                reason=f"RSI超买({current_rsi:.2f}) + MACD死叉"
            )
        
        return TradingSignal(
            symbol=data.iloc[-1].get('symbol', ''),
            signal=Signal.HOLD,
            strength=0.0,
            price=current_price,
            timestamp=data.index[-1],
            reason="无明确信号"
        )

class BollingerBandsStrategy(TradingStrategy):
    """布林带策略"""
    
    def _initialize_indicators(self) -> None:
        """初始化技术指标"""
        self.indicators['bb'] = BollingerBands(
            period=self.config.get('bollinger_period', 20),
            std_dev=self.config.get('bollinger_std', 2)
        )
    
    def generate_signal(self, data: pd.DataFrame) -> TradingSignal:
        """生成布林带交易信号"""
        if len(data) < self.config.get('bollinger_period', 20):
            return TradingSignal(
                symbol=data.iloc[-1].get('symbol', ''),
                signal=Signal.HOLD,
                strength=0.0,
                price=data['close'].iloc[-1],
                timestamp=data.index[-1],
                reason="数据不足"
            )
        
        bb_data = self.indicators['bb'].calculate(data)
        current_price = data['close'].iloc[-1]
        upper_band = bb_data['upper'].iloc[-1]
        lower_band = bb_data['lower'].iloc[-1]
        middle_band = bb_data['middle'].iloc[-1]
        
        # 买入信号：价格触及下轨
        if current_price <= lower_band:
            strength = (lower_band - current_price) / (upper_band - lower_band)
            return TradingSignal(
                symbol=data.iloc[-1].get('symbol', ''),
                signal=Signal.BUY,
                strength=min(strength, 1.0),
                price=current_price,
                timestamp=data.index[-1],
                reason=f"价格触及布林带下轨({lower_band:.2f})"
            )
        
        # 卖出信号：价格触及上轨
        elif current_price >= upper_band:
            strength = (current_price - upper_band) / (upper_band - lower_band)
            return TradingSignal(
                symbol=data.iloc[-1].get('symbol', ''),
                signal=Signal.SELL,
                strength=min(strength, 1.0),
                price=current_price,
                timestamp=data.index[-1],
                reason=f"价格触及布林带上轨({upper_band:.2f})"
            )
        
        return TradingSignal(
            symbol=data.iloc[-1].get('symbol', ''),
            signal=Signal.HOLD,
            strength=0.0,
            price=current_price,
            timestamp=data.index[-1],
            reason="价格在布林带区间内"
        )

class MovingAverageStrategy(TradingStrategy):
    """移动平均线策略"""
    
    def _initialize_indicators(self) -> None:
        """初始化技术指标"""
        self.indicators['ma_short'] = MovingAverage(period=self.config.get('ma_short', 10))
        self.indicators['ma_long'] = MovingAverage(period=self.config.get('ma_long', 30))
    
    def generate_signal(self, data: pd.DataFrame) -> TradingSignal:
        """生成移动平均线交易信号"""
        if len(data) < self.config.get('ma_long', 30):
            return TradingSignal(
                symbol=data.iloc[-1].get('symbol', ''),
                signal=Signal.HOLD,
                strength=0.0,
                price=data['close'].iloc[-1],
                timestamp=data.index[-1],
                reason="数据不足"
            )
        
        ma_short = self.indicators['ma_short'].calculate(data)
        ma_long = self.indicators['ma_long'].calculate(data)
        
        current_price = data['close'].iloc[-1]
        current_ma_short = ma_short.iloc[-1]
        current_ma_long = ma_long.iloc[-1]
        prev_ma_short = ma_short.iloc[-2]
        prev_ma_long = ma_long.iloc[-2]
        
        # 买入信号：短期均线上穿长期均线
        if (current_ma_short > current_ma_long and 
            prev_ma_short <= prev_ma_long):
            
            strength = abs(current_ma_short - current_ma_long) / current_ma_long
            return TradingSignal(
                symbol=data.iloc[-1].get('symbol', ''),
                signal=Signal.BUY,
                strength=min(strength, 1.0),
                price=current_price,
                timestamp=data.index[-1],
                reason=f"短期均线({current_ma_short:.2f})上穿长期均线({current_ma_long:.2f})"
            )
        
        # 卖出信号：短期均线下穿长期均线
        elif (current_ma_short < current_ma_long and 
              prev_ma_short >= prev_ma_long):
            
            strength = abs(current_ma_short - current_ma_long) / current_ma_long
            return TradingSignal(
                symbol=data.iloc[-1].get('symbol', ''),
                signal=Signal.SELL,
                strength=min(strength, 1.0),
                price=current_price,
                timestamp=data.index[-1],
                reason=f"短期均线({current_ma_short:.2f})下穿长期均线({current_ma_long:.2f})"
            )
        
        return TradingSignal(
            symbol=data.iloc[-1].get('symbol', ''),
            signal=Signal.HOLD,
            strength=0.0,
            price=current_price,
            timestamp=data.index[-1],
            reason="均线无交叉信号"
        )
