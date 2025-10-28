import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Position:
    """持仓信息"""
    symbol: str
    side: str  # 'long' or 'short'
    amount: float
    entry_price: float
    current_price: float
    entry_time: datetime
    unrealized_pnl: float
    unrealized_pnl_percent: float

@dataclass
class RiskMetrics:
    """风险指标"""
    total_balance: float
    available_balance: float
    total_exposure: float
    max_drawdown: float
    daily_pnl: float
    daily_trades: int
    win_rate: float
    sharpe_ratio: float
    risk_level: RiskLevel

class RiskManager:
    """风险管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.trade_history: List[Dict[str, Any]] = []
        self.max_drawdown = 0.0
        self.peak_balance = 0.0
        self.last_reset_date = datetime.now().date()
    
    def reset_daily_metrics(self) -> None:
        """重置每日指标"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.last_reset_date = current_date
    
    def calculate_position_size(self, symbol: str, price: float, signal_strength: float) -> float:
        """计算仓位大小"""
        self.reset_daily_metrics()
        
        # 基础仓位大小（总资金的百分比）
        base_position_percent = self.config.get("position_size_percent", 0.1)
        
        # 根据信号强度调整仓位
        adjusted_position_percent = base_position_percent * signal_strength
        
        # 获取可用余额
        available_balance = self.get_available_balance()
        
        # 计算最大仓位金额
        max_position_amount = available_balance * adjusted_position_percent
        
        # 确保不超过最小交易金额
        min_trade_amount = self.config.get("min_trade_amount", 10)
        if max_position_amount < min_trade_amount:
            return 0.0
        
        # 确保不超过最大持仓金额
        max_position_size = self.config.get("max_position_size", 1000)
        max_position_amount = min(max_position_amount, max_position_size)
        
        # 计算可购买的数量
        position_amount = max_position_amount / price
        
        return position_amount
    
    def check_risk_limits(self, symbol: str, side: str, amount: float, price: float) -> Tuple[bool, str]:
        """检查风险限制"""
        self.reset_daily_metrics()
        
        # 检查每日交易次数限制
        max_daily_trades = self.config.get("max_daily_trades", 50)
        if self.daily_trades >= max_daily_trades:
            return False, f"已达到每日最大交易次数限制: {max_daily_trades}"
        
        # 检查最大同时持仓数
        max_concurrent_positions = self.config.get("max_concurrent_positions", 3)
        if len(self.positions) >= max_concurrent_positions:
            return False, f"已达到最大同时持仓数限制: {max_concurrent_positions}"
        
        # 检查单个交易对是否已有持仓
        if symbol in self.positions:
            return False, f"交易对 {symbol} 已有持仓"
        
        # 检查最大回撤限制
        max_drawdown_limit = self.config.get("max_drawdown", 0.1)
        if self.max_drawdown > max_drawdown_limit:
            return False, f"超过最大回撤限制: {max_drawdown_limit * 100:.1f}%"
        
        # 检查紧急止损
        emergency_stop_loss = self.config.get("emergency_stop_loss", 0.15)
        if self.max_drawdown > emergency_stop_loss:
            return False, f"触发紧急止损: {emergency_stop_loss * 100:.1f}%"
        
        return True, "风险检查通过"
    
    def add_position(self, symbol: str, side: str, amount: float, entry_price: float) -> None:
        """添加持仓"""
        position = Position(
            symbol=symbol,
            side=side,
            amount=amount,
            entry_price=entry_price,
            current_price=entry_price,
            entry_time=datetime.now(),
            unrealized_pnl=0.0,
            unrealized_pnl_percent=0.0
        )
        
        self.positions[symbol] = position
        self.daily_trades += 1
    
    def update_position_price(self, symbol: str, current_price: float) -> None:
        """更新持仓价格"""
        if symbol in self.positions:
            position = self.positions[symbol]
            position.current_price = current_price
            
            # 计算未实现盈亏
            if position.side == 'long':
                position.unrealized_pnl = (current_price - position.entry_price) * position.amount
            else:  # short
                position.unrealized_pnl = (position.entry_price - current_price) * position.amount
            
            position.unrealized_pnl_percent = position.unrealized_pnl / (position.entry_price * position.amount)
    
    def remove_position(self, symbol: str) -> Optional[Position]:
        """移除持仓"""
        if symbol in self.positions:
            position = self.positions.pop(symbol)
            
            # 记录交易历史
            self.trade_history.append({
                'symbol': symbol,
                'side': position.side,
                'amount': position.amount,
                'entry_price': position.entry_price,
                'exit_price': position.current_price,
                'entry_time': position.entry_time,
                'exit_time': datetime.now(),
                'pnl': position.unrealized_pnl,
                'pnl_percent': position.unrealized_pnl_percent
            })
            
            # 更新每日盈亏
            self.daily_pnl += position.unrealized_pnl
            
            return position
        
        return None
    
    def should_close_position(self, symbol: str) -> Tuple[bool, str]:
        """判断是否应该平仓"""
        if symbol not in self.positions:
            return False, "持仓不存在"
        
        position = self.positions[symbol]
        
        # 检查止损
        stop_loss = self.config.get("stop_loss", 0.05)
        if position.unrealized_pnl_percent <= -stop_loss:
            return True, f"触发止损: {position.unrealized_pnl_percent * 100:.2f}%"
        
        # 检查止盈
        profit_target = self.config.get("profit_target", 0.05)
        if position.unrealized_pnl_percent >= profit_target:
            return True, f"达到止盈目标: {position.unrealized_pnl_percent * 100:.2f}%"
        
        return False, "持仓正常"
    
    def get_available_balance(self) -> float:
        """获取可用余额（模拟）"""
        # 这里应该从交易所获取实际余额
        # 为了演示，使用配置中的最大持仓金额
        return self.config.get("max_position_size", 1000)
    
    def calculate_risk_metrics(self) -> RiskMetrics:
        """计算风险指标"""
        self.reset_daily_metrics()
        
        total_balance = self.get_available_balance()
        available_balance = total_balance
        
        # 计算总敞口
        total_exposure = sum(pos.amount * pos.current_price for pos in self.positions.values())
        
        # 计算最大回撤
        current_balance = total_balance + sum(pos.unrealized_pnl for pos in self.positions.values())
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
        
        drawdown = (self.peak_balance - current_balance) / self.peak_balance if self.peak_balance > 0 else 0
        self.max_drawdown = max(self.max_drawdown, drawdown)
        
        # 计算胜率
        if self.trade_history:
            winning_trades = sum(1 for trade in self.trade_history if trade['pnl'] > 0)
            win_rate = winning_trades / len(self.trade_history)
        else:
            win_rate = 0.0
        
        # 计算夏普比率（简化版）
        if self.trade_history and len(self.trade_history) > 1:
            returns = [trade['pnl_percent'] for trade in self.trade_history]
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0.0
        
        # 确定风险等级
        risk_level = self._determine_risk_level(drawdown, self.daily_trades, win_rate)
        
        return RiskMetrics(
            total_balance=total_balance,
            available_balance=available_balance,
            total_exposure=total_exposure,
            max_drawdown=self.max_drawdown,
            daily_pnl=self.daily_pnl,
            daily_trades=self.daily_trades,
            win_rate=win_rate,
            sharpe_ratio=sharpe_ratio,
            risk_level=risk_level
        )
    
    def _determine_risk_level(self, drawdown: float, daily_trades: int, win_rate: float) -> RiskLevel:
        """确定风险等级"""
        if drawdown > 0.15 or daily_trades > 40 or win_rate < 0.3:
            return RiskLevel.CRITICAL
        elif drawdown > 0.1 or daily_trades > 30 or win_rate < 0.4:
            return RiskLevel.HIGH
        elif drawdown > 0.05 or daily_trades > 20 or win_rate < 0.5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def get_positions(self) -> Dict[str, Position]:
        """获取所有持仓"""
        return self.positions.copy()
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取指定持仓"""
        return self.positions.get(symbol)
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """获取交易历史"""
        return self.trade_history.copy()
