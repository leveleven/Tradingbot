#!/usr/bin/env python3
"""
自动交易机器人主程序
Auto Trading Bot Main Program

使用方法:
python main.py [选项]

选项:
  --config FILE    指定配置文件 (默认: config.yaml)
  --symbol SYMBOL  指定交易对 (例如: BTC/USDT)
  --strategy NAME  指定交易策略 (rsi_macd, bollinger, moving_average)
  --dry-run        模拟运行模式
  --help           显示帮助信息
"""

import asyncio
import argparse
import signal
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from system_init import initialize_system
from trading_bot import trading_bot
from config_manager import config
from loguru import logger

class TradingBotCLI:
    """交易机器人命令行界面"""
    
    def __init__(self):
        self.bot = trading_bot
        self.is_running = False
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，正在停止...")
            self.is_running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def parse_arguments(self):
        """解析命令行参数"""
        parser = argparse.ArgumentParser(
            description="自动交易机器人",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=__doc__
        )
        
        parser.add_argument(
            "--config", 
            type=str, 
            default="config.yaml",
            help="指定配置文件 (默认: config.yaml)"
        )
        
        parser.add_argument(
            "--symbol", 
            type=str,
            help="指定交易对 (例如: BTC/USDT)"
        )
        
        parser.add_argument(
            "--strategy", 
            type=str,
            choices=["rsi_macd", "bollinger", "moving_average"],
            help="指定交易策略"
        )
        
        parser.add_argument(
            "--dry-run", 
            action="store_true",
            help="模拟运行模式"
        )
        
        parser.add_argument(
            "--test-connection",
            action="store_true",
            help="测试交易所连接"
        )
        
        return parser.parse_args()
    
    def apply_arguments(self, args):
        """应用命令行参数"""
        # 更新配置文件路径
        if args.config != "config.yaml":
            from config_manager import Config
            global config
            config = Config(args.config)
        
        # 更新交易对
        if args.symbol:
            config.update("symbols", [args.symbol])
            logger.info(f"设置交易对: {args.symbol}")
        
        # 更新策略
        if args.strategy:
            config.update("algorithm.strategy", args.strategy)
            logger.info(f"设置交易策略: {args.strategy}")
        
        # 设置模拟模式
        if args.dry_run:
            config.update("trading.enabled", False)
            logger.info("启用模拟运行模式")
    
    async def test_connections(self):
        """测试交易所连接"""
        logger.info("正在测试交易所连接...")
        
        try:
            if await self.bot.exchange_manager.initialize_exchanges():
                exchange = self.bot.exchange_manager.get_active_exchange()
                if exchange:
                    # 测试获取余额
                    balance = await exchange.get_balance("USDT")
                    logger.info(f"连接测试成功，USDT余额: {balance}")
                    return True
            else:
                logger.error("交易所连接失败")
                return False
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False
    
    async def run(self):
        """运行交易机器人"""
        try:
            self.setup_signal_handlers()
            self.is_running = True
            
            logger.info("=" * 50)
            logger.info("自动交易机器人启动")
            logger.info("=" * 50)
            
            # 显示配置信息
            self.show_config_info()
            
            # 启动机器人
            await self.bot.start()
            
        except KeyboardInterrupt:
            logger.info("用户中断程序")
        except Exception as e:
            logger.error(f"程序运行错误: {e}")
        finally:
            await self.cleanup()
    
    def show_config_info(self):
        """显示配置信息"""
        logger.info("当前配置:")
        logger.info(f"  交易对: {config.get('symbols', [])}")
        logger.info(f"  交易策略: {config.get('algorithm.strategy', 'rsi_macd')}")
        logger.info(f"  交易频率: {config.get('trading.trading_frequency', 300)} 秒")
        logger.info(f"  目标盈利: {config.get('trading.profit_target', 0.05)*100:.1f}%")
        logger.info(f"  止损: {config.get('trading.stop_loss', 0.05)*100:.1f}%")
        logger.info(f"  最大持仓: {config.get('trading.max_position_size', 1000)} USDT")
        logger.info(f"  交易启用: {config.get('trading.enabled', True)}")
    
    async def cleanup(self):
        """清理资源"""
        logger.info("正在清理资源...")
        if hasattr(self.bot, 'stop'):
            await self.bot.stop()
        logger.info("清理完成")

async def main():
    """主函数"""
    # 初始化系统
    if not initialize_system():
        logger.error("系统初始化失败")
        return 1
    
    # 创建CLI实例
    cli = TradingBotCLI()
    
    # 解析命令行参数
    args = cli.parse_arguments()
    
    # 应用参数
    cli.apply_arguments(args)
    
    # 测试连接模式
    if args.test_connection:
        success = await cli.test_connections()
        return 0 if success else 1
    
    # 运行机器人
    await cli.run()
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)
