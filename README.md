# 🤖 BTC/USDT AI 量化交易系统

## 📝 项目简介

这是一个基于大模型的加密货币量化交易系统，利用DeepSeek和通义千问等先进AI模型进行市场分析和交易决策。系统采用单向持仓模式，支持实时行情分析和自动化交易执行。

## ⚙️ 系统要求

### 服务器配置
- 推荐使用阿里云香港/新加坡轻量服务器
- 操作系统：Ubuntu
- Python 3.10+
- Node.js（用于PM2进程管理）

### API密钥配置
在项目根目录创建 `.env` 文件：
```bash
DEEPSEEK_API_KEY=你的DeepSeek API密钥
QWEN_API_KEY=你的通义千问 API密钥

OKX_API_KEY=你的OKX API密钥
OKX_SECRET=你的OKX Secret密钥
OKX_PASSWORD=你的OKX API密码
```

## 🚀 部署步骤

### 1. 环境配置
```bash
# 安装Anaconda
wget https://repo.anaconda.com/archive/Anaconda3-2024.10-1-Linux-x86_64.sh
bash Anaconda3-2024.10-1-Linux-x86_64.sh

# 配置Anaconda环境
source /root/anaconda3/etc/profile.d/conda.sh
echo ". /root/anaconda3/etc/profile.d/conda.sh" >> ~/.bashrc

# 创建并激活Python环境
conda create -n LLM python=3.10
conda activate LLM

# 安装项目依赖
pip install -r requirements.txt
```

### 2. 系统依赖安装
```bash
# 更新系统包
apt-get update
apt-get upgrade

# 安装Node.js和PM2
apt install npm
npm install pm2 -g

conda create -n trail3 python=4.10
```

## 💡 关键特性

- 多AI模型支持（DeepSeek/通义千问）
- 实时市场数据分析
- 自动化交易执行
- 单向持仓
- PM2进程管理
- 完整的日志记录

## 🔧 运行管理

使用PM2启动服务：
```bash
pm2 start LLM_ok.py --name btc_trader
```

常用PM2命令：
```bash
pm2 list            # 查看运行状态
pm2 logs btc_trader # 查看日志
pm2 stop btc_trader # 停止服务
pm2 restart btc_trader # 重启服务
```

## ⚠️ 风险提示

1. 本系统仅供学习研究使用
2. 建议先使用测试环境进行充分测试
3. 实盘交易请严格控制仓位和风险
4. 定期检查系统运行状态和交易日志


## 📌 注意事项

1. 确保服务器网络稳定
2. 定期检查API额度使用情况
3. 做好异常处理和自动重试机制
4. 保持充足的账户保证金
