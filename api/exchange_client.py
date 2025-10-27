import os
import time
import requests
from utils.logger import enhanced_logger
from utils.helpers import retry_function

class OKXClient:
    """
    OKX交易所客户端
    负责与OKX交易所API交互，处理订单创建、撤销、查询持仓等操作
    """
    def __init__(self, api_key=None, secret_key=None, passphrase=None, testnet=False):
        """
        初始化OKX客户端
        
        参数:
            api_key: OKX API密钥
            secret_key: OKX API密钥
            passphrase: OKX API密钥
            testnet: 是否使用测试网
        """
        # 获取API密钥
        self.api_key = api_key or os.getenv('OKX_API_KEY')
        self.secret_key = secret_key or os.getenv('OKX_SECRET')
        self.passphrase = passphrase or os.getenv('OKX_PASSWORD')
        
        # 设置测试模式
        self.testnet = testnet
        
        # 设置API基础URL
        self.base_url = "https://www.okx.com" if not testnet else "https://www.okx.com"  # 根据实际OKX测试网URL修改
        self.headers = {
            'Content-Type': 'application/json',
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
        }
        
        # 交易配置
        self.symbol = None
        self.inst_id = None
        self.margin_mode = None
        
    def _generate_signature(self, timestamp, method, request_path, body=''):
        """
        生成OKX API签名
        
        参数:
            timestamp: 时间戳
            method: HTTP方法
            request_path: 请求路径
            body: 请求体
        
        返回:
            签名后的字符串
        """
        import hashlib
        import hmac
        
        message = timestamp + method + request_path + body
        mac = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        )
        return mac.hexdigest()
    
    def _request(self, method, endpoint, params=None, data=None):
        """
        发送API请求
        
        参数:
            method: HTTP方法
            endpoint: API端点
            params: 查询参数
            data: 请求体
        
        返回:
            API响应数据
        """
        import json
        
        url = f"{self.base_url}{endpoint}"
        request_path = endpoint
        
        # 生成时间戳
        timestamp = str(time.time())[:13]
        
        # 准备请求体
        body = json.dumps(data) if data else ''
        
        # 生成签名
        signature = self._generate_signature(timestamp, method, request_path, body)
        
        # 更新请求头
        headers = self.headers.copy()
        headers['OK-ACCESS-SIGN'] = signature
        headers['OK-ACCESS-TIMESTAMP'] = timestamp
        
        try:
            # 发送请求
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=30)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 检查API返回状态
            if result.get('code') != '0':
                raise Exception(f"API错误: {result.get('msg')}")
            
            return result.get('data', [])
            
        except requests.exceptions.RequestException as e:
            enhanced_logger.log_error(f"请求失败: {url}", "exchange_client", e)
            raise
    
    def set_trading_symbol(self, symbol, margin_mode='cross'):
        """
        设置交易对
        
        参数:
            symbol: 交易对，如 'BTC-USDT'
            margin_mode: 保证金模式，'cross' 或 'isolated'
        """
        self.symbol = symbol
        self.inst_id = symbol
        self.margin_mode = margin_mode
        enhanced_logger.log_info(f"设置交易对: {symbol}, 保证金模式: {margin_mode}", "exchange_client")
    
    def set_leverage(self, leverage):
        """
        设置杠杆倍数
        
        参数:
            leverage: 杠杆倍数
        """
        if not self.inst_id:
            raise ValueError("请先设置交易对")
        
        # 在测试模式下跳过实际的API调用
        if self.testnet:
            enhanced_logger.log_info(f"测试模式: 模拟设置杠杆: {leverage}x", "exchange_client")
            return {'code': '0', 'msg': '测试模式模拟成功'}
        
        data = {
            'instId': self.inst_id,
            'lever': leverage,
            'mgnMode': self.margin_mode
        }
        
        response = retry_function(lambda: self._request('POST', '/api/v5/account/set-leverage', data=data),
                                 max_retries=3, delay=2)
        enhanced_logger.log_info(f"设置杠杆: {leverage}x 成功", "exchange_client")
        return response
    
    def get_position(self):
        """获取持仓信息"""
        try:
            params = {
                'instId': self.inst_id
            }
            
            position = retry_function(lambda: self._request('GET', '/api/v5/account/positions', params=params),
                                     max_retries=3, delay=2)
            
            if position and len(position) > 0:
                return position[0]
            else:
                enhanced_logger.log_info("当前无持仓", "exchange_client")
                return None
        except Exception as e:
            enhanced_logger.log_error("获取持仓信息失败", "exchange_client", e)
            return None
    
    def get_balance(self):
        """
        获取账户余额
        
        返回:
            余额信息
        """
        try:
            balance = retry_function(lambda: self._request('GET', '/api/v5/account/balance'),
                                   max_retries=3, delay=2)
            
            if balance and len(balance) > 0:
                return balance[0]
            else:
                enhanced_logger.log_warning("获取余额数据为空", "exchange_client")
                return None
        except Exception as e:
            enhanced_logger.log_error("获取余额失败", "exchange_client", e)
            return None
    
    def get_market_price(self):
        """
        获取市场价格

        返回:
            当前价格
        """
        if not self.inst_id:
            raise ValueError("请先设置交易对")
        
        try:
            params = {'instId': self.inst_id}
            ticker = retry_function(lambda: self._request('GET', '/api/v5/market/ticker', params=params),
                                   max_retries=3, delay=2)
            
            if ticker and len(ticker) > 0:
                return float(ticker[0].get('last', 0))
            else:
                enhanced_logger.log_warning("获取市场价格数据为空", "exchange_client")
                return 0
        except Exception as e:
            enhanced_logger.log_error("获取市场价格失败", "exchange_client", e)
            return 0
    
    def get_kline_data(self, timeframe='1m', limit=100):
        """获取K线数据"""
        try:
            # 转换时间周期格式
            okx_timeframe = timeframe.replace('m', '').replace('h', '').replace('d', '')
            if timeframe.endswith('m'):
                okx_timeframe = okx_timeframe + 'M'
            elif timeframe.endswith('h'):
                okx_timeframe = okx_timeframe + 'H'
            elif timeframe.endswith('d'):
                okx_timeframe = okx_timeframe + 'D'
            
            params = {
                'instId': self.inst_id,
                'bar': okx_timeframe,
                'limit': limit
            }
            
            klines = retry_function(lambda: self._request('GET', '/api/v5/market/candles', params=params),
                                   max_retries=3, delay=2)
            
            # 格式化K线数据
            formatted_klines = []
            for kline in klines:
                if len(kline) >= 6:  # 确保数据完整性
                    formatted_klines.append({
                        'timestamp': int(kline[0]),
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5])
                    })
            
            return formatted_klines
        except Exception as e:
            enhanced_logger.log_error("获取K线数据失败", "exchange_client", e)
            return []
    
    def place_order(self, side, size, price=None, ord_type='market'):
        """
        下单
        
        参数:
            side: 交易方向，'buy' 或 'sell'
            size: 交易数量
            price: 价格，市价单不需要
            ord_type: 订单类型，'market' 或 'limit'
        
        返回:
            订单ID
        """
        if not self.inst_id:
            raise ValueError("请先设置交易对")
        
        if size <= 0:
            raise ValueError("交易数量必须大于0")
        
        # 准备订单数据
        data = {
            'instId': self.inst_id,
            'tdMode': self.margin_mode,
            'side': side,
            'ordType': ord_type,
            'sz': str(size),
            'posSide': 'net'
        }
        
        # 限价单添加价格
        if ord_type == 'limit' and price:
            data['px'] = str(price)
        
        try:
            # 下单
            result = retry_function(lambda: self._request('POST', '/api/v5/trade/order', data=data),
                                  max_retries=3, delay=2)
            
            if result:
                order_id = result[0].get('ordId')
                enhanced_logger.log_info(f"下单成功: {side} {size} {self.symbol} @ {price or '市价'} ID: {order_id}", "exchange_client")
                return order_id
            else:
                raise Exception("下单失败: 无返回数据")
                
        except Exception as e:
            enhanced_logger.log_error(f"下单失败: {side} {size} {self.symbol}", "exchange_client", e)
            return None
    
    def close_position(self, size=None):
        """
        平仓
        
        参数:
            size: 平仓数量，None表示平全部
        
        返回:
            订单ID或None
        """
        # 获取当前持仓
        position = self.get_position()
        
        if not position or position['size'] == 0:
            enhanced_logger.log_info("没有持仓可以平", "exchange_client")
            return None
        
        # 确定平仓方向
        side = 'sell' if position['side'] == 'long' else 'buy'
        
        # 确定平仓数量
        close_size = size if size else position['size']
        if close_size > position['size']:
            close_size = position['size']
        
        enhanced_logger.log_info(f"执行平仓: {side} {close_size} {self.symbol}", "exchange_client")
        
        # 下单平仓
        return self.place_order(side=side, size=close_size, ord_type='market')
    
    def cancel_order(self, order_id):
        """
        撤销订单
        
        参数:
            order_id: 订单ID
        
        返回:
            是否成功
        """
        if not self.inst_id:
            raise ValueError("请先设置交易对")
        
        params = {
            'instId': self.inst_id,
            'ordId': order_id
        }
        
        try:
            result = retry_function(lambda: self._request('POST', '/api/v5/trade/cancel-order', params=params),
                                  max_retries=3, delay=2)
            
            if result:
                enhanced_logger.log_info(f"撤销订单成功: {order_id}", "exchange_client")
            return True
        except Exception as e:
            enhanced_logger.log_error(f"撤销订单失败: {order_id}", "exchange_client", e)
            return False