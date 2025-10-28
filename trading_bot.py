import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from loguru import logger
import schedule
import time

from exchange_manager import ExchangeManager
from strategy_manager import StrategyManager
from risk_manager import RiskManager
from exchange_interface import OrderSide, OrderType, OrderStatus
from trading_strategies import Signal
from config_manager import config

class TradingBot:
    """自动交易机器人主控制器"""
    
    def __init__(self):
        self.exchange_manager = ExchangeManager()
        self.strategy_manager = StrategyManager()
        self.risk_manager = RiskManager(config.get("risk_management", {}))
        self.is_running = False
        self.symbols = config.get("symbols", ["BTC/USDT"])
        self.trading_enabled = config.get("trading.enabled", True)
        self.trading_frequency = config.get("trading.trading_frequency", 300)  # 5分钟
        
    async def initialize(self) -> bool:
        """初始化交易机器人"""
        try:
            logger.info("正在初始化交易机器人...")
            
            # 初始化交易所
            if not await self.exchange_manager.initialize_exchanges():
                logger.error("交易所初始化失败")
                return False
            
            # 初始化策略
            if not self.strategy_manager.initialize_strategies():
                logger.error("策略初始化失败")
                return False
            
            logger.info("交易机器人初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
    
    async def start(self) -> None:
        """启动交易机器人"""
        if not await self.initialize():
            logger.error("无法启动交易机器人")
            return
        
        self.is_running = True
        logger.info("交易机器人已启动")
        
        # 设置定时任务
        schedule.every(self.trading_frequency).seconds.do(self._run_trading_cycle)
        
        # 主循环
        while self.is_running:
            try:
                schedule.run_pending()
                await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("收到停止信号")
                break
            except Exception as e:
                logger.error(f"运行错误: {e}")
                await asyncio.sleep(5)
        
        await self.stop()
    
    async def stop(self) -> None:
        """停止交易机器人"""
        logger.info("正在停止交易机器人...")
        self.is_running = False
        
        # 关闭所有持仓
        await self._close_all_positions()
        
        # 断开交易所连接
        await self.exchange_manager.close_all_exchanges()
        
        logger.info("交易机器人已停止")
    
    def _run_trading_cycle(self) -> None:
        """运行交易周期"""
        asyncio.create_task(self._execute_trading_cycle())
    
    async def _execute_trading_cycle(self) -> None:
        """执行交易周期"""
        try:
            logger.info("开始交易周期")
            
            # 更新持仓价格
            await self._update_positions()
            
            # 检查是否需要平仓
            await self._check_exit_signals()
            
            # 检查是否有新的交易信号
            if self.trading_enabled:
                await self._check_entry_signals()
            
            # 输出状态信息
            self._log_status()
            
        except Exception as e:
            logger.error(f"交易周期执行错误: {e}")
    
    async def _update_positions(self) -> None:
        """更新持仓价格"""
        exchange = self.exchange_manager.get_active_exchange()
        if not exchange:
            return
        
        for symbol in self.risk_manager.get_positions().keys():
            try:
                ticker = await exchange.get_ticker(symbol)
                self.risk_manager.update_position_price(symbol, ticker.last)
            except Exception as e:
                logger.error(f"更新 {symbol} 价格失败: {e}")
    
    async def _check_exit_signals(self) -> None:
        """检查平仓信号"""
        exchange = self.exchange_manager.get_active_exchange()
        if not exchange:
            return
        
        positions = self.risk_manager.get_positions()
        
        for symbol, position in positions.items():
            try:
                should_close, reason = self.risk_manager.should_close_position(symbol)
                
                if should_close:
                    logger.info(f"平仓信号: {symbol} - {reason}")
                    await self._close_position(symbol, reason)
                
            except Exception as e:
                logger.error(f"检查 {symbol} 平仓信号失败: {e}")
    
    async def _check_entry_signals(self) -> None:
        """检查开仓信号"""
        exchange = self.exchange_manager.get_active_exchange()
        strategy = self.strategy_manager.get_active_strategy()
        
        if not exchange or not strategy:
            return
        
        for symbol in self.symbols:
            try:
                # 跳过已有持仓的交易对
                if symbol in self.risk_manager.get_positions():
                    continue
                
                # 获取K线数据
                klines = await exchange.get_klines(symbol, "1h", 100)
                if not klines:
                    continue
                
                # 转换为DataFrame
                df = pd.DataFrame(klines)
                df['symbol'] = symbol
                df.set_index('timestamp', inplace=True)
                
                # 生成交易信号
                signal = strategy.generate_signal(df)
                
                if signal.signal != Signal.HOLD:
                    logger.info(f"交易信号: {symbol} - {signal.signal.value} - {signal.reason}")
                    await self._execute_signal(signal)
                
            except Exception as e:
                logger.error(f"检查 {symbol} 交易信号失败: {e}")
    
    async def _execute_signal(self, signal) -> None:
        """执行交易信号"""
        exchange = self.exchange_manager.get_active_exchange()
        if not exchange:
            return
        
        try:
            # 检查风险限制
            side = "long" if signal.signal == Signal.BUY else "short"
            can_trade, reason = self.risk_manager.check_risk_limits(
                signal.symbol, side, 0, signal.price
            )
            
            if not can_trade:
                logger.warning(f"风险限制: {reason}")
                return
            
            # 计算仓位大小
            position_size = self.risk_manager.calculate_position_size(
                signal.symbol, signal.price, signal.strength
            )
            
            if position_size <= 0:
                logger.warning(f"仓位大小计算失败: {signal.symbol}")
                return
            
            # 创建订单
            order_side = OrderSide.BUY if signal.signal == Signal.BUY else OrderSide.SELL
            order_type = OrderType.LIMIT  # 使用限价单
            
            # 设置限价单价格（稍微偏离市价）
            if signal.signal == Signal.BUY:
                order_price = signal.price * 0.999  # 买入价稍微低一点
            else:
                order_price = signal.price * 1.001  # 卖出价稍微高一点
            
            order = await exchange.create_order(
                symbol=signal.symbol,
                side=order_side,
                order_type=order_type,
                amount=position_size,
                price=order_price
            )
            
            if order.status == OrderStatus.OPEN:
                # 添加持仓
                self.risk_manager.add_position(
                    signal.symbol, side, position_size, order_price
                )
                
                logger.info(f"订单创建成功: {signal.symbol} {order_side.value} {position_size} @ {order_price}")
            else:
                logger.warning(f"订单创建失败: {order.status}")
                
        except Exception as e:
            logger.error(f"执行交易信号失败: {e}")
    
    async def _close_position(self, symbol: str, reason: str) -> None:
        """平仓"""
        exchange = self.exchange_manager.get_active_exchange()
        if not exchange:
            return
        
        try:
            position = self.risk_manager.get_position(symbol)
            if not position:
                return
            
            # 创建平仓订单
            order_side = OrderSide.SELL if position.side == "long" else OrderSide.BUY
            order_type = OrderType.LIMIT
            
            # 设置平仓价格
            ticker = await exchange.get_ticker(symbol)
            if position.side == "long":
                order_price = ticker.ask * 0.999  # 卖出价稍微低一点
            else:
                order_price = ticker.bid * 1.001  # 买入价稍微高一点
            
            order = await exchange.create_order(
                symbol=symbol,
                side=order_side,
                order_type=order_type,
                amount=position.amount,
                price=order_price
            )
            
            if order.status == OrderStatus.OPEN:
                # 移除持仓
                closed_position = self.risk_manager.remove_position(symbol)
                
                logger.info(f"平仓成功: {symbol} - {reason}")
                logger.info(f"盈亏: {closed_position.unrealized_pnl:.2f} USDT ({closed_position.unrealized_pnl_percent*100:.2f}%)")
            else:
                logger.warning(f"平仓订单创建失败: {order.status}")
                
        except Exception as e:
            logger.error(f"平仓失败: {e}")
    
    async def _close_all_positions(self) -> None:
        """关闭所有持仓"""
        positions = self.risk_manager.get_positions()
        
        for symbol in positions.keys():
            try:
                await self._close_position(symbol, "机器人停止")
            except Exception as e:
                logger.error(f"强制平仓 {symbol} 失败: {e}")
    
    def _log_status(self) -> None:
        """输出状态信息"""
        risk_metrics = self.risk_manager.calculate_risk_metrics()
        positions = self.risk_manager.get_positions()
        
        logger.info("=== 交易状态 ===")
        logger.info(f"风险等级: {risk_metrics.risk_level.value}")
        logger.info(f"最大回撤: {risk_metrics.max_drawdown*100:.2f}%")
        logger.info(f"今日交易次数: {risk_metrics.daily_trades}")
        logger.info(f"今日盈亏: {risk_metrics.daily_pnl:.2f} USDT")
        logger.info(f"胜率: {risk_metrics.win_rate*100:.2f}%")
        logger.info(f"持仓数量: {len(positions)}")
        
        for symbol, position in positions.items():
            logger.info(f"  {symbol}: {position.side} {position.amount:.4f} @ {position.entry_price:.2f} "
                       f"(当前: {position.current_price:.2f}, 盈亏: {position.unrealized_pnl_percent*100:.2f}%)")
    
    async def manual_trade(self, symbol: str, side: str, amount: float, price: float = None) -> bool:
        """手动交易"""
        try:
            exchange = self.exchange_manager.get_active_exchange()
            if not exchange:
                return False
            
            # 检查风险限制
            can_trade, reason = self.risk_manager.check_risk_limits(symbol, side, amount, price or 0)
            if not can_trade:
                logger.warning(f"手动交易被风险控制阻止: {reason}")
                return False
            
            # 创建订单
            order_side = OrderSide.BUY if side == "long" else OrderSide.SELL
            order_type = OrderType.MARKET if price is None else OrderType.LIMIT
            
            order = await exchange.create_order(
                symbol=symbol,
                side=order_side,
                order_type=order_type,
                amount=amount,
                price=price
            )
            
            if order.status == OrderStatus.OPEN:
                # 添加持仓
                self.risk_manager.add_position(symbol, side, amount, price or order.price)
                logger.info(f"手动交易成功: {symbol} {side} {amount} @ {price or order.price}")
                return True
            else:
                logger.warning(f"手动交易失败: {order.status}")
                return False
                
        except Exception as e:
            logger.error(f"手动交易失败: {e}")
            return False

# 全局交易机器人实例
trading_bot = TradingBot()
