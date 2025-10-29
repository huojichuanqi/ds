#### 个人喜欢玩黑箱文化，你们不一样，别上头。




## 单向持仓  单向持仓 单向持仓  


## 配置内容

### 配置文件建在策略根目录

### 文件名字    .env

####  DEEPSEEK_API_KEY= 你的deepseek  api密钥

####  BINANCE_API_KEY=

####  BINANCE_SECRET=

####  OKX_API_KEY=

####  OKX_SECRET=

#### OKX_PASSWORD=

###  视频教程：https://www.youtube.com/watch?v=Yv-AMVaWUVg


### 准备一台ubuntu服务器 推荐阿里云 香港或者新加坡 轻云服务器


#### wget https://repo.anaconda.com/archive/Anaconda3-2024.10-1-Linux-x86_64.sh

#### bash Anaconda3-2024.10-1-Linux-x86_64.sh


#### source /root/anaconda3/etc/profile.d/conda.sh 
#### echo ". /root/anaconda3/etc/profile.d/conda.sh" >> ~/.bashrc




#### conda create -n ds python=3.10

#### conda activate ds

#### pip install -r requirements.txt



#### apt-get update 更新镜像源


#### apt-get upgrade 必要库的一个升级


#### apt install npm 安装npm


#### npm install pm2 -g 使用npm安装pm2

#### conda create -n trail3 python=4.10

###### 打赏地址（TRC20）：TUunBuqQ1ZDYt9WrA3ZarndFPQgefXqZAM


## plus_log_server 使用说明

该服务用于每分钟扫描 `plus.out.log`，解析每次“交易建议”并在网页端以可折叠列表展示。

### 依赖安装

- 已在 `requirements.txt` 中加入 `flask`，执行一次：

```
pip install -r requirements.txt
```

### 启动服务
plus服务启动：
```
nohup python -u deepseek_ok_带指标plus版本.py > plus.out.log 2>&1 &
```



- 默认读取当前目录下的 `plus.out.log`：

```
python plus_log_server.py
```

- 自定义日志路径与扫描间隔（秒）：

Windows PowerShell 示例：

```
$env:PLUS_LOG_PATH = "C:\\Users\\donnie\\projects\\python\\ds\\plus.out.log"
$env:PLUS_LOG_SCAN_INTERVAL = "60"
$env:PORT = "5000"
python plus_log_server.py
```

Linux/macOS Bash 示例：

```
export PLUS_LOG_PATH="/path/to/plus.out.log"
export PLUS_LOG_SCAN_INTERVAL=60
export PORT=5000
python plus_log_server.py
```

- 访问地址：

```
http://localhost:5000/
```

### 接口与页面

- `/`：前端页面（支持“展开全部 / 折叠全部 / 刷新”）。
- `/api/records`：返回已解析记录的 JSON（包含最后一次解析错误信息）。
- `/healthz`：健康检查返回 `ok`。

### 后台常驻（可选）

如果已安装 pm2，可用下述方式常驻（需已安装 Node.js 与 pm2）：

```
pm2 start plus_log_server.py --name plus-log-server --interpreter python
pm2 logs plus-log-server
```

### 日志格式要求

- 每条记录以一行 `执行时间: YYYY-MM-DD HH:MM:SS` 开始。
- 记录之间用一行 `============================================================` 分隔。
- 解析的主要字段包括：`ETH当前价格`、`数据周期`、`价格变化`、`DeepSeek原始回复`、`信号统计`、`交易信号`、`信心程度`、`理由`、`止损`、`止盈`、`当前持仓`、以及最终“建议/动作”行。
