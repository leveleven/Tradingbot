#!/usr/bin/env python3
"""
交易机器人测试脚本
Trading Bot Test Script
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from system_init import initialize_system
from exchange_manager import ExchangeManager
from strategy_manager import StrategyManager
from risk_manager import RiskManager
from config_manager import config
from loguru import logger

async def test_exchange_connection():
    """测试交易所连接"""
    logger.info("测试交易所连接...")
    
    exchange_manager = ExchangeManager()
    
    try:
        if await exchange_manager.initialize_exchanges():
            exchange = exchange_manager.get_active_exchange()
            if exchange:
                logger.info(f"成功连接到 {exchange.get_exchange_name()}")
                
                # 测试获取行情
                try:
                    ticker = await exchange.get_ticker("BTC/USDT")
                    logger.info(f"BTC/USDT 当前价格: {ticker.last}")
                except Exception as e:
                    logger.warning(f"获取行情失败: {e}")
                
                # 测试获取余额
                try:
                    balance = await exchange.get_balance("USDT")
                    if "USDT" in balance:
                        logger.info(f"USDT余额: {balance['USDT'].free}")
                    else:
                        logger.info("未找到USDT余额")
                except Exception as e:
                    logger.warning(f"获取余额失败: {e}")
                
                await exchange_manager.close_all_exchanges()
                return True
            else:
                logger.error("未找到活跃的交易所")
                return False
        else:
            logger.error("交易所初始化失败")
            return False
            
    except Exception as e:
        logger.error(f"测试交易所连接失败: {e}")
        return False

def test_strategy():
    """测试交易策略"""
    logger.info("测试交易策略...")
    
    try:
        strategy_manager = StrategyManager()
        
        if strategy_manager.initialize_strategies():
            strategy = strategy_manager.get_active_strategy()
            if strategy:
                logger.info(f"成功初始化策略: {strategy.get_strategy_name()}")
                return True
            else:
                logger.error("未找到活跃的策略")
                return False
        else:
            logger.error("策略初始化失败")
            return False
            
    except Exception as e:
        logger.error(f"测试策略失败: {e}")
        return False

def test_risk_manager():
    """测试风险管理"""
    logger.info("测试风险管理...")
    
    try:
        risk_config = config.get("risk_management", {})
        risk_manager = RiskManager(risk_config)
        
        # 测试风险指标计算
        metrics = risk_manager.calculate_risk_metrics()
        logger.info(f"风险等级: {metrics.risk_level.value}")
        logger.info(f"最大回撤: {metrics.max_drawdown*100:.2f}%")
        
        # 测试仓位大小计算
        position_size = risk_manager.calculate_position_size("BTC/USDT", 50000, 0.8)
        logger.info(f"建议仓位大小: {position_size:.6f} BTC")
        
        return True
        
    except Exception as e:
        logger.error(f"测试风险管理失败: {e}")
        return False

async def test_full_system():
    """测试完整系统"""
    logger.info("=" * 50)
    logger.info("开始系统测试")
    logger.info("=" * 50)
    
    tests = [
        ("交易所连接", test_exchange_connection),
        ("交易策略", test_strategy),
        ("风险管理", test_risk_manager),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- 测试 {test_name} ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name} 测试通过")
            else:
                logger.error(f"❌ {test_name} 测试失败")
                
        except Exception as e:
            logger.error(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    logger.info("\n" + "=" * 50)
    logger.info("测试结果汇总")
    logger.info("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        logger.info("🎉 所有测试通过！系统可以正常运行")
        return True
    else:
        logger.warning("⚠️ 部分测试失败，请检查配置")
        return False

async def main():
    """主函数"""
    # 初始化系统
    if not initialize_system():
        logger.error("系统初始化失败")
        return 1
    
    # 运行测试
    success = await test_full_system()
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"测试程序异常退出: {e}")
        sys.exit(1)
