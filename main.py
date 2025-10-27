import os
import sys
import time
import json
from datetime import datetime
import dotenv
from config.trading_config import get_trading_config
from api.exchange_client import OKXClient
from api.deepseek_client import init_deepseek_client, analyze_with_deepseek
from core.trading_engine import TradingEngine
from monitor.web_app import EnhancedWebMonitor
from utils.indicators import calculate_technical_indicators, get_support_resistance_levels, get_market_trend
from utils.logger import enhanced_logger
from utils.helpers import wait_for_next_cycle, validate_api_keys, retry_function

# 全局状态
GLOBAL_STATE = {
    'running': True,
    'last_cycle_time': None,
    'current_signal': None,
    'error_count': 0
}

def update_global_state(key, value):
    """
    更新全局状态
    """
    GLOBAL_STATE[key] = value
    save_bot_state()
    
    # 错误计数检查
    if key == 'error_count' and value >= 5:
        enhanced_logger.log_warning(f"连续错误次数达到{value}次，建议检查系统", "main")

def save_bot_state():
    """
    保存机器人状态到文件
    """
    try:
        os.makedirs('data', exist_ok=True)
        state_file = os.path.join('data', 'bot_state.json')
        
        # 添加时间戳
        state_data = GLOBAL_STATE.copy()
        state_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        enhanced_logger.log_error("保存机器人状态失败", "main", e)

def load_bot_state():
    """
    从文件加载机器人状态
    """
    try:
        state_file = os.path.join('data', 'bot_state.json')
        if os.path.exists(state_file):
            with open(state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
                # 移除时间戳，只更新其他状态
                state_data.pop('timestamp', None)
                GLOBAL_STATE.update(state_data)
                enhanced_logger.log_info("机器人状态已加载", "main")
    except Exception as e:
        enhanced_logger.log_error("加载机器人状态失败", "main", e)

def get_market_data(exchange_client, config):
    """
    获取市场数据并进行分析
    
    参数:
        exchange_client: 交易所客户端
        config: 交易配置
    
    返回:
        处理后的市场数据
    """
    try:
        # 获取K线数据
        klines = exchange_client.get_kline_data(config['timeframe'], limit=100)
        if not klines:
            enhanced_logger.log_error("无法获取K线数据", "main")
            return None
        
        # 获取最新价格和K线
        current_price = exchange_client.get_market_price()
        latest_kline = klines[-1] if klines else None
        
        # 计算技术指标
        technical_data = calculate_technical_indicators(klines)
        
        # 获取支撑阻力位
        levels = get_support_resistance_levels(klines)
        
        # 获取趋势分析
        trend_analysis = get_market_trend(klines, technical_data)
        
        # 构建价格数据
        price_data = {
            'price': current_price,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'high': latest_kline['high'] if latest_kline else 0,
            'low': latest_kline['low'] if latest_kline else 0,
            'volume': latest_kline['volume'] if latest_kline else 0,
            'price_change': 0,  # 可以根据需要计算
            'kline_data': klines,
            'technical_data': technical_data,
            'levels_analysis': levels,
            'trend_analysis': trend_analysis
        }
        
        # 计算价格变化
        if len(klines) >= 2:
            prev_close = klines[-2]['close']
            current_close = latest_kline['close']
            price_data['price_change'] = ((current_close - prev_close) / prev_close) * 100
        
        return price_data
        
    except Exception as e:
        enhanced_logger.log_error("获取市场数据失败", "main", e)
        return None

def get_market_sentiment():
    """
    获取市场情绪数据
    这里可以连接到实际的情绪分析API，目前返回模拟数据
    
    返回:
        情绪数据
    """
    try:
        # 模拟市场情绪数据
        # 实际使用时可以连接到情绪分析API
        import random
        sentiment = {
            'positive_ratio': random.uniform(0.4, 0.6),
            'negative_ratio': random.uniform(0.3, 0.5),
            'net_sentiment': random.uniform(-0.2, 0.2)
        }
        # 确保比例合理
        sentiment['positive_ratio'] = min(1.0, sentiment['positive_ratio'])
        sentiment['negative_ratio'] = min(1.0, sentiment['negative_ratio'])
        
        return sentiment
    except Exception as e:
        enhanced_logger.log_error("获取市场情绪数据失败", "main", e)
        return None

def trading_bot(exchange_client, deepseek_client, trading_engine, config):
    """
    主交易机器人逻辑
    """
    try:
        # 记录周期开始时间
        update_global_state('last_cycle_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        enhanced_logger.log_info("-" * 50, "main")
        enhanced_logger.log_info(f"开始新的交易周期: {config['timeframe']}", "main")
        
        # 获取市场数据
        enhanced_logger.log_info("正在获取市场数据...", "main")
        price_data = get_market_data(exchange_client, config)
        if not price_data:
            update_global_state('error_count', GLOBAL_STATE['error_count'] + 1)
            return
        
        # 获取市场情绪
        enhanced_logger.log_info("正在获取市场情绪...", "main")
        sentiment_data = get_market_sentiment()
        
        # 获取当前持仓
        current_position = trading_engine.get_current_position()
        
        # 使用DeepSeek进行分析
        enhanced_logger.log_info("正在进行DeepSeek分析...", "main")
        signal_data = analyze_with_deepseek(
            deepseek_client,
            price_data,
            trading_engine.signal_history,
            sentiment_data,
            current_position,
            config
        )
        
        # 更新全局信号
        update_global_state('current_signal', signal_data)
        
        # 输出信号信息
        enhanced_logger.log_info(f"交易信号: {signal_data['signal']}", "main")
        enhanced_logger.log_info(f"信心级别: {signal_data['confidence']}", "main")
        enhanced_logger.log_info(f"分析理由: {signal_data['reason']}", "main")
        enhanced_logger.log_info(f"止损价格: {signal_data['stop_loss']}", "main")
        enhanced_logger.log_info(f"止盈价格: {signal_data['take_profit']}", "main")
        
        # 执行交易
        enhanced_logger.log_info("正在执行交易...", "main")
        trade_result = trading_engine.execute_intelligent_trade(signal_data)
        
        # 输出交易结果
        enhanced_logger.log_info(f"交易结果: {trade_result.get('status', 'unknown')}", "main")
        if 'message' in trade_result:
            enhanced_logger.log_info(f"交易消息: {trade_result['message']}", "main")
        
        # 重置错误计数
        update_global_state('error_count', 0)
        
        enhanced_logger.log_info(f"交易周期完成", "main")
        enhanced_logger.log_info("-" * 50, "main")
        
    except KeyboardInterrupt:
        raise
    except Exception as e:
        enhanced_logger.log_error("交易周期执行失败", "main", e)
        update_global_state('error_count', GLOBAL_STATE['error_count'] + 1)

def main():
    """
    主函数
    """
    try:
        # 打印启动信息
        print("=" * 60)
        print("     DeepSeek AI 交易机器人 v2.0")
        print("     基于 OKX 交易所和 DeepSeek AI")
        print("=" * 60)
        print()
        
        # 配置日志
        enhanced_logger.log_info("启动交易机器人...", "main")
        
        # 加载环境变量
        dotenv.load_dotenv()
        enhanced_logger.log_info("环境变量加载完成", "main")
        
        # 加载机器人状态
        load_bot_state()
        
        # 获取交易配置
        config = get_trading_config()
        enhanced_logger.log_info(f"交易配置加载完成，交易对: {config['symbol']}", "main")
        
        # 提示模式选择
        print()
        print("请选择运行模式:")
        print("1. 测试模式 (不执行实际交易)")
        print("2. 实盘模式 (执行实际交易)")
        
        mode = input("请输入选择 (1/2，默认1): ").strip()
        test_mode = mode != '2'
        
        enhanced_logger.log_info(f"运行模式: {'测试模式' if test_mode else '实盘模式'}", "main")
        
        # 验证API密钥
        api_keys = {
            'OKX_API_KEY': os.getenv('OKX_API_KEY'),
            'OKX_SECRET': os.getenv('OKX_SECRET'),
            'OKX_PASSWORD': os.getenv('OKX_PASSWORD'),
            'DEEPSEEK_API_KEY': os.getenv('DEEPSEEK_API_KEY')
        }
        validation_result, message = validate_api_keys(api_keys)
        if not validation_result:
            enhanced_logger.log_error(f"API密钥验证失败: {message}，请检查.env文件配置", "main")
            return
        
        # 初始化交易所客户端
        enhanced_logger.log_info("初始化交易所客户端...", "main")
        exchange_client = OKXClient(
            api_key=os.getenv('OKX_API_KEY'),
            secret_key=os.getenv('OKX_SECRET'),
            passphrase=os.getenv('OKX_PASSWORD'),
            testnet=test_mode
        )
        
        # 设置交易对
        exchange_client.set_trading_symbol(config['symbol'], config['margin_mode'])
        
        # 设置杠杆
        enhanced_logger.log_info(f"设置杠杆倍数: {config['leverage']}x", "main")
        exchange_client.set_leverage(config['leverage'])
        
        # 初始化DeepSeek客户端
        enhanced_logger.log_info("初始化DeepSeek AI客户端...", "main")
        deepseek_client = init_deepseek_client(os.getenv('DEEPSEEK_API_KEY'))
        
        # 初始化交易引擎
        enhanced_logger.log_info("初始化交易引擎...", "main")
        trading_engine = TradingEngine(exchange_client, config)
        
        # 启动Web监控面板
        enhanced_logger.log_info("启动Web监控面板...", "main")
        web_monitor = EnhancedWebMonitor(trading_engine, host='0.0.0.0', port=5000)
        web_monitor.start(daemon=False)  # 设置为非守护线程
        
        # 等待Web服务器启动
        time.sleep(2)
        
        print()
        print("交易机器人启动成功！")
        print(f"监控面板地址: http://localhost:5000")
        print(f"按 Ctrl+C 停止机器人")
        print()
        
        # 主交易循环
        while GLOBAL_STATE['running']:
            try:
                # 执行交易周期
                trading_bot(exchange_client, deepseek_client, trading_engine, config)
                
                # 等待下一个周期
                wait_seconds = wait_for_next_cycle(config['timeframe'])
                enhanced_logger.log_info(f"等待下一个{config['timeframe']}周期，{wait_seconds}秒后继续...", "main")
                
                # 等待期间检查是否需要停止
                for _ in range(wait_seconds):
                    if not GLOBAL_STATE['running']:
                        break
                    time.sleep(1)
                
            except KeyboardInterrupt:
                enhanced_logger.log_info("收到停止信号，正在退出...", "main")
                break
            except Exception as e:
                enhanced_logger.log_error("主循环执行失败", "main", e)
                # 出错后等待一段时间再重试
                time.sleep(60)
        
    except KeyboardInterrupt:
        enhanced_logger.log_info("用户中断，程序退出", "main")
    except Exception as e:
        enhanced_logger.log_error("程序启动失败", "main", e)
    finally:
        # 清理资源
        enhanced_logger.log_info("清理资源...", "main")
        update_global_state('running', False)
        save_bot_state()
        print()
        print("交易机器人已停止")

if __name__ == "__main__":
    main()