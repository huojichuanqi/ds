# 交易参数配置

TRADE_CONFIG = {
    # 基础配置
    'symbol': 'BTC/USDT:USDT',    # OKX的合约符号格式
    'margin_mode': 'cross',       # 保证金模式：'cross'（全仓）或 'isolated'（逐仓）
    'leverage': 10,               # 杠杆倍数，只影响保证金不影响下单价值
    'timeframe': '15m',           # 使用15分钟K线
    'test_mode': True,            # 测试模式（True不执行真实交易）
    'data_points': 96,            # 24小时数据（96根15分钟K线）
    
    # 均线周期配置
    'analysis_periods': {
        'short_term': 20,         # 短期均线
        'medium_term': 50,        # 中期均线
        'long_term': 96           # 长期趋势
    },
    
    # 智能仓位管理参数
    'position_management': {
        'base_usdt_amount': 5,    # USDT投入下单基数
        'high_confidence_multiplier': 1.2,  # 高信心倍数
        'medium_confidence_multiplier': 1.0,  # 中信心倍数
        'low_confidence_multiplier': 0.5,    # 低信心倍数
        'max_position_ratio': 2,  # 单次最大仓位比例（总资金的20%）
        'trend_strength_multiplier': 1.1    # 趋势强度倍数
    }
}

def get_trading_config():
    """
    获取交易配置
    
    返回:
        交易配置字典
    """
    return TRADE_CONFIG.copy()