import os
import sys
from pathlib import Path
from loguru import logger
from config_manager import config

def setup_logging():
    """设置日志系统"""
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 获取日志配置
    log_config = config.get("logging", {})
    log_level = log_config.get("level", "INFO")
    log_file = log_config.get("file", "logs/trading_bot.log")
    max_size = log_config.get("max_size", "10MB")
    backup_count = log_config.get("backup_count", 5)
    
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 添加文件输出
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=max_size,
        retention=f"{backup_count} files",
        compression="zip",
        encoding="utf-8"
    )
    
    # 添加错误日志文件
    logger.add(
        "logs/error.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )
    
    logger.info("日志系统初始化完成")

def create_env_template():
    """创建环境变量模板文件"""
    env_template = """# 交易机器人环境变量配置
# Trading Bot Environment Variables Configuration

# 币安交易所API配置
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# OKX交易所API配置
OKX_API_KEY=your_okx_api_key_here
OKX_API_SECRET=your_okx_api_secret_here
OKX_PASSPHRASE=your_okx_passphrase_here

# 其他配置
TRADING_ENABLED=true
SANDBOX_MODE=true
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_template)
        logger.info("已创建 .env 模板文件，请填入您的API密钥")

def load_env_variables():
    """加载环境变量"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # 更新配置中的API密钥
        if os.getenv("BINANCE_API_KEY"):
            config.update("exchanges.binance.api_key", os.getenv("BINANCE_API_KEY"))
        if os.getenv("BINANCE_API_SECRET"):
            config.update("exchanges.binance.api_secret", os.getenv("BINANCE_API_SECRET"))
        
        if os.getenv("OKX_API_KEY"):
            config.update("exchanges.okx.api_key", os.getenv("OKX_API_KEY"))
        if os.getenv("OKX_API_SECRET"):
            config.update("exchanges.okx.api_secret", os.getenv("OKX_API_SECRET"))
        if os.getenv("OKX_PASSPHRASE"):
            config.update("exchanges.okx.passphrase", os.getenv("OKX_PASSPHRASE"))
        
        if os.getenv("TRADING_ENABLED"):
            config.update("trading.enabled", os.getenv("TRADING_ENABLED").lower() == "true")
        if os.getenv("SANDBOX_MODE"):
            config.update("exchanges.binance.sandbox", os.getenv("SANDBOX_MODE").lower() == "true")
            config.update("exchanges.okx.sandbox", os.getenv("SANDBOX_MODE").lower() == "true")
        
        logger.info("环境变量加载完成")
        
    except ImportError:
        logger.warning("未安装 python-dotenv，跳过环境变量加载")
    except Exception as e:
        logger.error(f"加载环境变量失败: {e}")

def check_dependencies():
    """检查依赖项"""
    required_packages = [
        "ccxt", "pandas", "numpy", "loguru", "schedule", "pyyaml"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"缺少依赖包: {', '.join(missing_packages)}")
        logger.error("请运行: pip install -r requirements.txt")
        return False
    
    return True

def initialize_system():
    """初始化系统"""
    logger.info("正在初始化交易机器人系统...")
    
    # 检查依赖项
    if not check_dependencies():
        return False
    
    # 设置日志
    setup_logging()
    
    # 创建环境变量模板
    create_env_template()
    
    # 加载环境变量
    load_env_variables()
    
    logger.info("系统初始化完成")
    return True
