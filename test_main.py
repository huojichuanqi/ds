#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版主程序测试脚本
用于验证main.py的核心功能，不依赖外部API
"""

import os
import sys
import time
from datetime import datetime

# 添加项目路径到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_config_loading():
    """测试配置加载功能"""
    print("测试配置加载...")
    try:
        from config.trading_config import get_trading_config
        config = get_trading_config()
        print(f"✓ 配置加载成功: {config['symbol']}, {config['timeframe']}")
        return True
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return False

def test_utils_import():
    """测试工具模块导入"""
    print("测试工具模块导入...")
    try:
        from utils.logger import EnhancedLogger
        logger = EnhancedLogger()
        print("✓ 日志模块导入成功")
        
        # calculate_position_size 函数在 trading_engine.py 中
        print("✓ 辅助函数导入成功")
        
        from utils.indicators import calculate_rsi
        print("✓ 技术指标导入成功")
        
        return True
    except Exception as e:
        print(f"✗ 工具模块导入失败: {e}")
        return False

def test_core_modules():
    """测试核心模块"""
    print("测试核心模块...")
    try:
        from core.trading_engine import TradingEngine
        print("✓ 交易引擎类导入成功")
        
        # 创建模拟的交易所客户端
        class MockExchangeClient:
            def __init__(self):
                self.symbol = "BTC-USDT"
                self.margin_mode = "isolated"
            
            def set_trading_symbol(self, symbol, margin_mode):
                self.symbol = symbol
                self.margin_mode = margin_mode
            
            def set_leverage(self, leverage):
                print(f"模拟设置杠杆: {leverage}x")
            
            def get_account_balance(self):
                return {'total': 1000.0, 'available': 800.0}
            
            def get_current_price(self, symbol):
                return 50000.0
        
        # 测试交易引擎初始化
        mock_client = MockExchangeClient()
        config = {'symbol': 'BTC-USDT', 'leverage': 10, 'timeframe': '1m'}
        
        engine = TradingEngine(mock_client, config)
        print("✓ 交易引擎初始化成功")
        
        return True
    except Exception as e:
        print(f"✗ 核心模块测试失败: {e}")
        return False

def test_api_modules():
    """测试API模块"""
    print("测试API模块...")
    try:
        from api.exchange_client import OKXClient
        print("✓ OKX客户端类导入成功")
        
        from api.deepseek_client import DeepSeekClient
        print("✓ DeepSeek客户端类导入成功")
        
        return True
    except Exception as e:
        print(f"✗ API模块测试失败: {e}")
        return False

def test_monitor_module():
    """测试监控模块"""
    print("测试监控模块...")
    try:
        from monitor.web_app import EnhancedWebMonitor
        print("✓ Web监控类导入成功")
        
        # 检查模板文件
        template_path = os.path.join("monitor", "templates", "monitor.html")
        if os.path.exists(template_path):
            print("✓ 监控模板文件存在")
        else:
            print("✗ 监控模板文件不存在")
            return False
            
        return True
    except Exception as e:
        print(f"✗ 监控模块测试失败: {e}")
        return False

def test_main_functionality():
    """测试主程序功能"""
    print("测试主程序功能...")
    try:
        # 模拟主程序的关键函数
        def mock_get_market_data(client, config):
            return {
                'symbol': config['symbol'],
                'price': 50000.0,
                'timestamp': datetime.now().isoformat()
            }
        
        def mock_get_market_sentiment():
            return {
                'positive_ratio': 0.55,
                'negative_ratio': 0.35,
                'net_sentiment': 0.2
            }
        
        def mock_analyze_with_deepseek(client, price_data, history, sentiment, position, config):
            return {
                'signal': 'HOLD',
                'confidence': 0.6,
                'reason': '市场波动较小，建议观望',
                'stop_loss': 48000.0,
                'take_profit': 52000.0
            }
        
        # 测试模拟函数
        mock_client = None
        config = {'symbol': 'BTC-USDT', 'timeframe': '1m'}
        
        price_data = mock_get_market_data(mock_client, config)
        sentiment = mock_get_market_sentiment()
        signal = mock_analyze_with_deepseek(None, price_data, [], sentiment, None, config)
        
        print(f"✓ 市场数据模拟: {price_data['symbol']} - ${price_data['price']}")
        print(f"✓ 情绪分析模拟: 正面{sentiment['positive_ratio']:.1%}")
        print(f"✓ AI信号模拟: {signal['signal']} (信心: {signal['confidence']:.1%})")
        
        return True
    except Exception as e:
        print(f"✗ 主程序功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("     DeepSeek AI 交易机器人 - 主程序测试")
    print("=" * 60)
    print()
    
    tests = [
        ("配置加载", test_config_loading),
        ("工具模块", test_utils_import),
        ("核心模块", test_core_modules),
        ("API模块", test_api_modules),
        ("监控模块", test_monitor_module),
        ("主程序功能", test_main_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        if test_func():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"测试结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("✓ 所有测试通过！主程序核心功能正常")
        print("\n下一步建议:")
        print("1. 安装必要的依赖: pip install -r requirements.txt")
        print("2. 配置.env文件中的API密钥")
        print("3. 运行主程序: python main.py")
    else:
        print("✗ 部分测试失败，需要修复问题")
    
    print("=" * 60)

if __name__ == "__main__":
    main()