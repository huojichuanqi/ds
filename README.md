# 🤖 BTC/USDT 自动交易机器人

基于DeepSeek AI的智能加密货币交易机器人，支持OKX交易所，提供完整的Web监控面板和先进的交易策略。

## ✨ 核心特性

- 🤖 **AI驱动分析**：使用DeepSeek AI进行市场分析和交易信号生成
- 📊 **技术指标集成**：MACD、RSI、布林带、移动平均线等多种技术指标
- 📈 **市场情绪分析**：集成外部市场情绪API，提供情绪辅助决策
- 💰 **智能仓位管理**：根据信号信心、趋势强度动态调整仓位大小
- 📱 **Web监控面板**：实时查看交易状态、价格、持仓和信号历史
- 🛡️ **完善风险控制**：自动止损止盈、仓位限制、异常处理
- ⚙️ **灵活配置选项**：支持测试模式和实盘模式，可根据资金规模调整参数

## 📁 项目结构

```
d:\OPEN\ds\
├── config/                 # 配置文件目录
│   └── trading_config.py   # 交易参数配置
├── core/                   # 核心功能模块
│   ├── analysis.py         # 市场分析模块
│   ├── execution.py        # 交易执行模块
│   └── position.py         # 仓位管理模块
├── api/                    # API交互模块
│   ├── deepseek_client.py  # DeepSeek AI客户端
│   ├── okx_client.py       # OKX交易所客户端
│   └── sentiment_api.py    # 情绪分析API
├── monitor/                # 监控相关
│   ├── web_server.py       # Web监控服务器
│   └── templates/          # HTML模板目录
│       └── monitor.html    # 监控面板模板
├── utils/                  # 工具函数
│   ├── indicators.py       # 技术指标计算
│   ├── logger.py           # 日志工具
│   └── helpers.py          # 辅助函数
├── main.py                 # 主程序入口
├── monitor.py              # 独立监控脚本
├── requirements.txt        # 项目依赖
├── .env                    # 环境变量配置
└── README.md               # 项目说明文档
```

## 🚀 快速开始

### 1. 环境准备

确保已安装Python 3.7+，然后安装项目依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

编辑 `.env` 文件，填入您的API密钥：

```env
# DeepSeek AI配置
DEEPSEEK_API_KEY=你的deepseek密钥

# OKX交易所配置
OKX_API_KEY=你的OKX_API_KEY
OKX_SECRET=你的OKX_SECRET
OKX_PASSWORD=你的OKX_PASSWORD
```

### 3. 配置交易参数

编辑 `config/trading_config.py`，根据您的需求调整交易参数：

```python
# 基础配置
TRADE_CONFIG = {
    'symbol': 'BTC/USDT:USDT',    # 交易对
    'leverage': 10,               # 杠杆倍数
    'timeframe': '15m',           # 时间周期
    'test_mode': True,            # 测试模式
    'data_points': 96,            # 数据点数量
    
    # 仓位管理
    'position_management': {
        'base_usdt_amount': 5,    # 基础USDT投入
        'high_confidence_multiplier': 1.2,
        'medium_confidence_multiplier': 1.0,
        'low_confidence_multiplier': 0.5,
        'max_position_ratio': 2,  # 最大仓位比例
        'trend_strength_multiplier': 1.1
    }
}
```

### 4. 启动机器人

**方式1：启动主程序（包含交易和监控）**
```bash
python main.py
```

**方式2：仅启动监控面板**
```bash
python monitor.py
```

访问监控面板：http://localhost:5000

## 🔍 使用说明

### 测试模式

首次使用时，请先设置 `test_mode: True`，这样系统不会执行真实交易，只会模拟交易过程：

```python
'test_mode': True
```

### 实盘交易

确认系统运行正常后，可以切换到实盘模式：

```python
'test_mode': False
```

### 仓位管理

根据您的资金规模调整仓位参数：

- **小额资金（< 200 USDT）**：`base_usdt_amount: 5-20`，`max_position_ratio: 2-3`
- **中等资金（200-1000 USDT）**：`base_usdt_amount: 20-80`，`max_position_ratio: 3-5`
- **大额资金（> 1000 USDT）**：`base_usdt_amount: 80-200`，`max_position_ratio: 5-10`

### 监控面板

监控面板提供以下信息：
- 当前运行状态
- 最新价格和变化
- 账户余额和持仓情况
- 最近交易信号历史
- 技术指标概览

## ⚠️ 风险提示

- 加密货币交易存在高风险，请只投入您能承受损失的资金
- 建议先在测试模式下运行一段时间，熟悉系统表现
- 定期检查API连接状态和交易日志
- 不要过度杠杆，建议保持在10倍以内
- 市场波动剧烈时，系统可能无法及时应对突发情况

## 🛠️ 故障排除

### API连接问题

- 检查API密钥是否正确配置
- 确认API权限是否开启（读取和交易权限）
- 检查网络连接和防火墙设置

### 交易执行失败

- 查看控制台输出的错误信息
- 确保账户有足够的资金
- 检查OKX账户的持仓模式是否为全仓
- 确认没有未平仓的逐仓合约

### 监控面板无法访问

- 检查5000端口是否被占用
- 确认Web服务器是否正常启动
- 检查防火墙设置是否允许该端口访问

## 📊 日志和数据

系统会自动保存以下数据：
- `robot_status.json` - 机器人当前状态
- `signal_history.json` - 交易信号历史记录

## 📈 策略说明

本机器人采用以下策略框架：

1. **技术分析**（60%权重）：基于移动平均线、RSI、MACD等指标判断趋势
2. **市场情绪**（30%权重）：结合外部情绪数据验证技术信号
3. **风险管理**（10%权重）：考虑当前持仓、盈亏和市场状况

系统每15分钟执行一次分析和决策，支持同方向加仓减仓，避免频繁反转交易。

## 📊 监控面板

启动监控面板后可以实时查看：
- 💰 当前BTC价格
- 💵 账户余额和持仓
- 📊 最新交易信号
- 📜 历史交易记录
- ⏱️ 运行状态

访问：http://你的服务器IP:5000

## 🔑 获取API密钥

### DeepSeek API
1. 访问：https://platform.deepseek.com/
2. 注册账号
3. 进入API Keys页面
4. 创建API密钥
5. 复制到 `.env` 文件

### OKX API
1. 访问：https://www.okx.com/
2. 登录账号
3. 设置 → API → 创建API密钥
4. 权限选择：读取+交易（不要选提币）
5. 设置IP白名单
6. 复制API Key、Secret、PassPhrase到 `.env` 文件

## ⚠️ 重要提示

1. **首次使用务必设置测试模式**
   ```python
   'test_mode': True,
   ```

2. **小额测试**：先用200-300 USDT测试

3. **风险管理**：
   - 不要投入超过你资金的50%
   - 设置合理的止损
   - 控制杠杆倍数（建议10倍以内）

4. **定期检查**：
   - 查看监控面板
   - 查看日志文件
   - 观察交易信号是否合理

## 🐛 常见问题

### 无法连接OKX
- 检查网络连接
- 如果是国内服务器，配置代理或使用海外服务器
- 查看：[网络问题修复指南](网络连接问题修复指南.md)

### API密钥错误
- 检查 `.env` 文件配置
- 确认API权限设置
- 验证IP白名单

### 余额不足
- 充值USDT到OKX
- 确保已划转到统一账户
- 查看：[充值教程](OKX充值教程.md)

### 程序运行异常
- 查看日志：`tail -f bot.log`
- 检查错误信息
- 确认所有依赖已安装

## 📖 文件说明

### 核心文件
- `deepseek_ok_带市场情绪+指标版本.py` - 主程序（推荐）
- `monitor.py` - 监控面板服务
- `requirements.txt` - Python依赖
- `.env` - 配置文件（需创建）

### 启动脚本
- `启动监控面板.sh` - 只启动监控面板
- `同时运行机器人和监控面板.sh` - 启动全部服务

### 文档
- `README.md` - 本文件
- `QUICK_START.md` - 快速开始
- `部署指南-CentOS.md` - 部署指南
- `OKX充值教程.md` - 充值教程
- `监控面板使用指南.md` - 监控面板说明
- `网络连接问题修复指南.md` - 网络问题解决

## 🎯 使用流程

1. **配置API密钥** → 创建 `.env` 文件
2. **设置测试模式** → `test_mode: True`
3. **运行程序** → 观察交易信号
4. **查看监控面板** → 确认程序正常
5. **充值到OKX** → 200-500 USDT推荐
6. **开启实盘** → `test_mode: False`
7. **持续监控** → 查看日志和面板

## 📞 获取帮助

- 查看日志：`tail -f bot.log`
- 查看监控：http://localhost:5000
- 查看文档：项目内各.md文件

## ⚖️ 免责声明

加密货币交易存在高风险，可能导致资金损失。本程序仅供学习和研究使用，使用者需自行承担交易风险。

---

**祝您交易顺利！** 📈
