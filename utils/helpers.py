import json
import re
import time
from datetime import datetime, timedelta

def safe_json_parse(json_str):
    """
    安全解析JSON，处理格式不规范的情况
    
    参数:
        json_str: JSON字符串
    
    返回:
        解析后的JSON对象或None
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        try:
            # 修复常见的JSON格式问题
            json_str = json_str.replace("'", '"')
            json_str = re.sub(r'(\w+):', r'"\1":', json_str)
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*\]', ']', json_str)
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON解析失败，原始内容: {json_str}")
            print(f"错误详情: {e}")
            return None

def wait_for_next_period():
    """
    等待到下一个15分钟整点
    
    返回:
        需要等待的秒数
    """
    now = datetime.now()
    current_minute = now.minute
    current_second = now.second

    # 计算下一个整点时间（00, 15, 30, 45分钟）
    next_period_minute = ((current_minute // 15) + 1) * 15
    if next_period_minute == 60:
        next_period_minute = 0

    # 计算需要等待的总秒数
    if next_period_minute > current_minute:
        minutes_to_wait = next_period_minute - current_minute
    else:
        minutes_to_wait = 60 - current_minute + next_period_minute

    seconds_to_wait = minutes_to_wait * 60 - current_second

    # 显示友好的等待时间
    display_minutes = minutes_to_wait - 1 if current_second > 0 else minutes_to_wait
    display_seconds = 60 - current_second if current_second > 0 else 0

    if display_minutes > 0:
        print(f"🕒 等待 {display_minutes} 分 {display_seconds} 秒到整点...")
    else:
        print(f"🕒 等待 {display_seconds} 秒到整点...")

    return seconds_to_wait

def format_price(price, symbol='USD'):
    """
    格式化价格显示
    
    参数:
        price: 价格
        symbol: 货币符号
    
    返回:
        格式化后的价格字符串
    """
    if symbol == 'USD':
        return f'${float(price):,.2f}'
    return f'{float(price):.2f} {symbol}'

def calculate_pnl(entry_price, current_price, side, size):
    """
    计算盈亏
    
    参数:
        entry_price: 入场价格
        current_price: 当前价格
        side: 方向 ('long' 或 'short')
        size: 仓位大小
    
    返回:
        盈亏金额
    """
    if side == 'long':
        return (current_price - entry_price) * size
    else:
        return (entry_price - current_price) * size

def create_fallback_signal(price_data):
    """
    创建备用交易信号
    
    参数:
        price_data: 价格数据
    
    返回:
        备用交易信号字典
    """
    return {
        "signal": "HOLD",
        "reason": "因技术分析暂时不可用，采取保守策略",
        "stop_loss": price_data['price'] * 0.98,  # -2%
        "take_profit": price_data['price'] * 1.02,  # +2%
        "confidence": "LOW",
        "is_fallback": True
    }

def validate_api_keys(keys):
    """
    验证API密钥是否有效
    
    参数:
        keys: 包含API密钥的字典
    
    返回:
        验证结果
    """
    for key_name, key_value in keys.items():
        if not key_value or key_value.strip() == "":
            return False, f"{key_name} 未配置"
    return True, "验证通过"

def retry_function(func, max_retries=3, delay=1, *args, **kwargs):
    """
    重试执行函数
    
    参数:
        func: 要执行的函数
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
        *args, **kwargs: 函数参数
    
    返回:
        函数执行结果
    """
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"第{attempt + 1}次尝试失败: {e}，将在{delay}秒后重试...")
            time.sleep(delay)
    return None

def wait_for_next_cycle(timeframe):
    """
    等待到下一个交易周期
    
    参数:
        timeframe: 时间周期（如'15m', '1h'等）
    
    返回:
        需要等待的秒数
    """
    now = datetime.now()
    
    # 解析时间周期
    if timeframe.endswith('m'):
        minutes = int(timeframe[:-1])
        current_minute = now.minute
        
        # 计算下一个周期开始时间
        next_period_minute = ((current_minute // minutes) + 1) * minutes
        if next_period_minute >= 60:
            next_period_minute = 0
            
        # 计算需要等待的总秒数
        if next_period_minute > current_minute:
            minutes_to_wait = next_period_minute - current_minute
        else:
            minutes_to_wait = 60 - current_minute + next_period_minute
            
        seconds_to_wait = minutes_to_wait * 60 - now.second
        
    elif timeframe.endswith('h'):
        hours = int(timeframe[:-1])
        current_hour = now.hour
        
        # 计算下一个周期开始时间
        next_period_hour = ((current_hour // hours) + 1) * hours
        if next_period_hour >= 24:
            next_period_hour = 0
            
        # 计算需要等待的总秒数
        if next_period_hour > current_hour:
            hours_to_wait = next_period_hour - current_hour
        else:
            hours_to_wait = 24 - current_hour + next_period_hour
            
        seconds_to_wait = hours_to_wait * 3600 - now.minute * 60 - now.second
        
    else:
        # 默认使用15分钟周期
        seconds_to_wait = wait_for_next_period()
    
    # 显示友好的等待时间
    hours = seconds_to_wait // 3600
    minutes = (seconds_to_wait % 3600) // 60
    seconds = seconds_to_wait % 60
    
    if hours > 0:
        print(f"🕒 等待 {hours} 小时 {minutes} 分 {seconds} 秒到下一个{timeframe}周期...")
    elif minutes > 0:
        print(f"🕒 等待 {minutes} 分 {seconds} 秒到下一个{timeframe}周期...")
    else:
        print(f"🕒 等待 {seconds} 秒到下一个{timeframe}周期...")
    
    return seconds_to_wait