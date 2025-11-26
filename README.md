# Crypto Trading Bot

An AI-powered cryptocurrency trading system integrating OKX exchange APIs with advanced machine learning decision-making capabilities.

## 📋 项目概述

本项目是一个智能加密货币交易机器人，它能够：

- 自动收集市场数据（K线、技术指标等）
- 使用AI大模型分析市场并生成交易决策
- 通过OKX API执行实际交易操作
- 支持现货(spot)和合约(swap)交易模式
- 记录每次交易决策和执行结果

## 🏗️ 技术架构

```
TradingBot (trade_bot.py)
│
├── OKX接口层 (okx_trade.py)
│   ├── 账户管理
│   ├── 订单执行
│   └── 行情数据获取
│
├── 数据收集层 (data_collector.py)
│   ├── K线数据获取
│   ├── 账户信息获取
│   └── 技术指标计算
│
├── 提示词生成器 (prompt_generator.py)
│   └── 构建AI决策所需的数据提示
│
└── AI决策模型 (model.py)
    └── 调用大语言模型进行交易决策
```

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

创建 `.env` 文件并配置以下参数：

```env
# OKX API Keys (实盘)
OKX_API_KEY1=your_api_key
OKX_SECRET_KEY1=your_secret_key
OKX_PASSPHRASE1=your_passphrase

# OKX API Keys (模拟盘)
OKX_API_KEY_SIMU=your_simulation_api_key
OKX_SECRET_KEY_SIMU=your_simulation_secret_key
OKX_PASSPHRASE=your_simulation_passphrase

# AI模型API (阿里云百炼)
DASHSCOPE_API_KEY=your_dashscope_api_key
```

### 运行交易机器人

```python
from trade_bot import TradingBot

# 创建实盘交易机器人
bot = TradingBot(is_simulated=False, coin_list=["BTC-USDT"])

# 执行单次交易周期
bot.run_single_cycle()

# 或者启动持续交易循环(默认5分钟间隔)
bot.trading_cycle()
```

## 📁 项目结构

```
.
├── data_collector.py      # 数据收集模块
├── main.py               # 主程序入口
├── model.py              # AI模型接口
├── okx_trade.py          # OKX交易接口
├── prompt_generator.py   # 提示词生成器
├── trade_bot.py          # 交易机器人主类
└── trading_record/       # 交易记录存储目录
```

## ⚙️ 核心组件说明

### TradingBot (trade_bot.py)
交易机器人的主控制器，协调各个组件工作：
- 初始化所有必要组件
- 控制交易循环
- 保存交易记录

### OKX接口 (okx_trade.py)
与OKX交易所交互的核心模块：
- 账户信息查询
- 下单执行
- 持仓管理
- K线数据获取

### 数据收集器 (data_collector.py)
负责收集和整理市场及账户数据：
- K线数据分析
- 技术指标计算(EMA, MACD, RSI, ATR等)
- 账户余额和持仓信息

### 提示词生成器 (prompt_generator.py)
构建提供给AI模型的完整市场数据提示：
- 整合多时间框架数据
- 格式化技术指标序列
- 包含账户状态信息

### AI决策模型 (model.py)
调用大语言模型进行交易决策：
- 当前使用阿里云Qwen模型
- 根据市场数据生成买卖信号
- 输出标准化JSON格式决策

## 📊 支持的技术指标

- **EMA** (指数移动平均)
- **MACD** (异同移动平均线)
- **RSI** (相对强弱指数)
- **ATR** (平均真实波幅)

支持多个时间框架分析：3分钟、4小时等。

## 🧠 AI决策逻辑

AI模型接收完整的市场数据和账户信息，包括：
- 当前价格和历史价格序列
- 多种技术指标数据
- 账户余额和持仓情况
- 合约资金费率和持仓量(针对合约交易)

输出标准化的交易决策JSON，包含：
- 交易信号(buy/sell/hold/close)
- 交易数量
- 止损价位
- 目标价位
- 置信度评分
- 交易理由

## 📝 交易记录

每次交易都会自动生成详细记录并保存为JSON文件：
- 时间戳
- AI原始响应
- 解析后的决策数据
- 执行结果状态

## ⚠️ 免责声明

本项目仅供学习和研究使用：
1. 加密货币交易存在高风险，可能导致重大资金损失
2. 使用此代码进行实盘交易需自行承担全部风险
3. 作者不对任何交易损失负责
4. 建议先在模拟环境中充分测试后再考虑实盘使用

## 🛠️ 开发计划

- [ ] 添加更多技术指标支持
- [ ] 实现风险管理模块
- [ ] 增加回测功能
- [ ] 支持更多交易所
- [ ] 优化AI决策逻辑
- [ ] 添加Web监控界面

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。