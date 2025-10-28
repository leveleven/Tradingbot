# 项目结构说明
# Project Structure

```
bot/
├── main.py                 # 主程序入口
├── install.py              # 快速安装脚本
├── test_bot.py             # 系统测试脚本
├── requirements.txt        # Python依赖包
├── config.yaml            # 主配置文件
├── .env                   # 环境变量文件（需要创建）
├── README.md              # 项目说明文档
├── setup.sh               # 设置脚本
│
├── config_manager.py      # 配置管理器
├── system_init.py         # 系统初始化
│
├── exchange_interface.py  # 交易所接口抽象层
├── exchange_manager.py    # 交易所管理器
├── exchanges/             # 交易所实现
│   ├── __init__.py
│   ├── binance_exchange.py    # 币安交易所实现
│   └── okx_exchange.py        # OKX交易所实现
│
├── trading_strategies.py  # 交易策略实现
├── strategy_manager.py    # 策略管理器
│
├── risk_manager.py        # 风险管理器
├── trading_bot.py         # 主交易机器人控制器
│
└── logs/                  # 日志目录
    ├── trading_bot.log    # 主日志文件
    └── error.log          # 错误日志文件
```

## 核心模块说明

### 1. 交易所模块 (Exchange)
- **exchange_interface.py**: 定义交易所接口抽象层
- **exchange_manager.py**: 管理多个交易所连接
- **exchanges/**: 具体交易所实现
  - **binance_exchange.py**: 币安交易所实现
  - **okx_exchange.py**: OKX交易所实现

### 2. 策略模块 (Strategy)
- **trading_strategies.py**: 实现多种交易策略
  - RSI + MACD 策略
  - 布林带策略
  - 移动平均线策略
- **strategy_manager.py**: 策略管理器

### 3. 风险管理模块 (Risk Management)
- **risk_manager.py**: 实现风险控制功能
  - 仓位管理
  - 止损止盈
  - 回撤控制
  - 交易频率限制

### 4. 主控制器 (Main Controller)
- **trading_bot.py**: 主交易机器人控制器
  - 协调各个模块
  - 执行交易周期
  - 处理交易信号

### 5. 配置和工具
- **config_manager.py**: 配置管理器
- **system_init.py**: 系统初始化
- **main.py**: 程序入口
- **test_bot.py**: 系统测试

## 数据流

```
配置加载 → 系统初始化 → 交易所连接 → 策略初始化 → 风险管理初始化
    ↓
主循环开始 → 获取市场数据 → 生成交易信号 → 风险检查 → 执行交易
    ↓
更新持仓 → 检查平仓信号 → 记录日志 → 等待下次循环
```

## 关键特性

1. **模块化设计**: 各模块独立，易于扩展和维护
2. **多交易所支持**: 支持币安、OKX等主流交易所
3. **多种策略**: 内置多种技术分析策略
4. **风险控制**: 完善的风险管理机制
5. **配置灵活**: YAML配置文件，支持环境变量
6. **日志完整**: 详细的交易和错误日志
7. **测试友好**: 提供测试脚本和模拟模式
