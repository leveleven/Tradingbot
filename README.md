# 自动交易机器人
# Auto Trading Bot

一个基于Python的自动交易机器人，支持多个交易所和多种交易策略。

## 功能特性

- 🔄 **多交易所支持**: 支持币安(Binance)、OKX等主流交易所
- 📊 **多种交易策略**: RSI+MACD、布林带、移动平均线等策略
- 🛡️ **风险管理**: 止损止盈、仓位管理、回撤控制
- ⚙️ **灵活配置**: YAML配置文件，支持环境变量
- 📝 **详细日志**: 完整的交易日志和错误记录
- 🎯 **限价单支持**: 支持限价单和市价单
- 📈 **实时监控**: 实时显示交易状态和盈亏情况

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置说明

### 1. 复制配置文件

```bash
cp config.yaml config_local.yaml
```

### 2. 配置API密钥

编辑 `.env` 文件，填入您的交易所API密钥：

```env
# 币安交易所API配置
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# OKX交易所API配置
OKX_API_KEY=your_okx_api_key_here
OKX_API_SECRET=your_okx_api_secret_here
OKX_PASSPHRASE=your_okx_passphrase_here
```

### 3. 修改交易配置

编辑 `config.yaml` 文件：

```yaml
# 交易设置
TRADING:
  enabled: true                    # 是否启用交易
  max_position_size: 1000         # 最大持仓金额 (USDT)
  min_trade_amount: 10            # 最小交易金额 (USDT)
  profit_target: 0.05             # 目标盈利 5%
  stop_loss: 0.05                 # 止损 5%
  trading_frequency: 300          # 交易频率 (秒)
  max_daily_trades: 50            # 每日最大交易次数

# 算法配置
ALGORITHM:
  strategy: "rsi_macd"            # 策略类型
  rsi_period: 14                  # RSI周期
  rsi_oversold: 30                # RSI超卖线
  rsi_overbought: 70              # RSI超买线

# 交易对配置
SYMBOLS:
  - "BTC/USDT"
  - "ETH/USDT"
  - "BNB/USDT"
```

## 使用方法

### 基本使用

```bash
# 启动交易机器人
python main.py

# 指定交易对
python main.py --symbol BTC/USDT

# 指定交易策略
python main.py --strategy bollinger

# 模拟运行模式
python main.py --dry-run

# 测试交易所连接
python main.py --test-connection
```

### 高级使用

```bash
# 使用自定义配置文件
python main.py --config my_config.yaml

# 组合参数
python main.py --symbol ETH/USDT --strategy moving_average --dry-run
```

## 交易策略

### 1. RSI + MACD 策略
- **买入信号**: RSI超卖 + MACD金叉
- **卖出信号**: RSI超买 + MACD死叉
- **适用场景**: 震荡市场

### 2. 布林带策略
- **买入信号**: 价格触及下轨
- **卖出信号**: 价格触及上轨
- **适用场景**: 趋势市场

### 3. 移动平均线策略
- **买入信号**: 短期均线上穿长期均线
- **卖出信号**: 短期均线下穿长期均线
- **适用场景**: 趋势市场

## 风险管理

- **止损止盈**: 可配置的止损止盈比例
- **仓位管理**: 基于信号强度的动态仓位调整
- **回撤控制**: 最大回撤限制和紧急止损
- **交易频率**: 限制每日最大交易次数
- **持仓限制**: 限制最大同时持仓数量

## 日志系统

日志文件保存在 `logs/` 目录下：

- `trading_bot.log`: 主要交易日志
- `error.log`: 错误日志
- 支持日志轮转和压缩

## 注意事项

⚠️ **重要提醒**:

1. **测试环境**: 建议先在测试环境(sandbox)中运行
2. **资金安全**: 不要投入过多资金，建议从小额开始
3. **API权限**: 确保API密钥只有交易权限，没有提现权限
4. **网络稳定**: 确保网络连接稳定，避免断线
5. **监控运行**: 定期检查机器人运行状态

## 故障排除

### 常见问题

1. **连接失败**: 检查网络连接和API密钥
2. **余额不足**: 确保账户有足够的USDT余额
3. **交易对不存在**: 检查交易对名称是否正确
4. **权限不足**: 确保API密钥有交易权限

### 调试模式

```bash
# 启用详细日志
python main.py --dry-run

# 查看日志
tail -f logs/trading_bot.log
```

## 免责声明

本软件仅供学习和研究使用，不构成投资建议。使用本软件进行实际交易的风险由用户自行承担。作者不对任何投资损失负责。

## 许可证

MIT License
