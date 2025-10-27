#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版Web监控面板测试脚本
用于验证Web监控面板的基本功能
"""

import os
import sys

# 添加项目路径到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_monitor_structure():
    """测试监控面板文件结构"""
    print("测试监控面板文件结构...")
    
    # 检查必要的文件是否存在
    required_files = [
        "monitor/web_app.py",
        "monitor/templates/monitor.html"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"✗ 缺少文件: {', '.join(missing_files)}")
        return False
    else:
        print("✓ 所有必需文件存在")
        return True

def test_web_app_import():
    """测试Web应用导入"""
    print("测试Web应用导入...")
    try:
        # 检查是否能导入基本类
        from monitor.web_app import EnhancedWebMonitor
        print("✓ EnhancedWebMonitor类导入成功")
        
        # 创建模拟的交易引擎
        class MockTradingEngine:
            def __init__(self):
                self.trade_history = []
                self.signal_history = []
            
            def get_trade_summary(self):
                return {
                    'current_price': 50000.0,
                    'current_position': {},
                    'total_trades': 0,
                    'last_signal': {},
                    'last_updated': '2024-01-01 00:00:00'
                }
            
            @property
            def exchange(self):
                class MockExchange:
                    def get_balance(self):
                        return {'totalEq': 1000.0}
                return MockExchange()
        
        # 测试监控面板初始化
        mock_engine = MockTradingEngine()
        monitor = EnhancedWebMonitor(mock_engine)
        print("✓ Web监控面板初始化成功")
        
        return True
    except Exception as e:
        print(f"✗ Web应用导入失败: {e}")
        return False

def test_template_content():
    """测试模板文件内容"""
    print("测试模板文件内容...")
    try:
        # 读取模板文件
        template_path = "monitor/templates/monitor.html"
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键元素
        required_elements = [
            '<title>',
            '<div class="container">',
            'DeepSeek AI',
            '交易机器人'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"✗ 模板缺少元素: {', '.join(missing_elements)}")
            return False
        else:
            print("✓ 模板文件内容完整")
            return True
            
    except Exception as e:
        print(f"✗ 模板文件读取失败: {e}")
        return False

def test_api_endpoints():
    """测试API端点定义"""
    print("测试API端点定义...")
    try:
        # 读取web_app.py文件
        web_app_path = "monitor/web_app.py"
        with open(web_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键API端点
        required_endpoints = [
            '@self.app.route(\'/api/status\')',
            '@self.app.route(\'/api/history\')',
            '@self.app.route(\'/api/config\')',
            '@self.app.route(\'/api/logs\')'
        ]
        
        missing_endpoints = []
        for endpoint in required_endpoints:
            if endpoint not in content:
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            print(f"✗ 缺少API端点: {', '.join(missing_endpoints)}")
            return False
        else:
            print("✓ 所有API端点定义完整")
            return True
            
    except Exception as e:
        print(f"✗ API端点检查失败: {e}")
        return False

def test_monitor_features():
    """测试监控面板功能特性"""
    print("测试监控面板功能特性...")
    try:
        # 检查web_app.py中的功能
        web_app_path = "monitor/web_app.py"
        with open(web_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键功能
        required_features = [
            'class EnhancedWebMonitor',
            'def _setup_routes',
            'def start',
            'def stop',
            '实时监控',
            '交易历史',
            '配置管理'
        ]
        
        missing_features = []
        for feature in required_features:
            if feature not in content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"✗ 缺少功能特性: {', '.join(missing_features)}")
            return False
        else:
            print("✓ 监控面板功能特性完整")
            return True
            
    except Exception as e:
        print(f"✗ 功能特性检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("     DeepSeek AI 交易机器人 - Web监控面板测试")
    print("=" * 60)
    print()
    
    tests = [
        ("文件结构", test_monitor_structure),
        ("应用导入", test_web_app_import),
        ("模板内容", test_template_content),
        ("API端点", test_api_endpoints),
        ("功能特性", test_monitor_features)
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
        print("✓ 所有测试通过！Web监控面板结构完整")
        print("\nWeb监控面板功能包括:")
        print("• 实时交易状态监控")
        print("• 交易历史查看")
        print("• 配置参数管理")
        print("• 日志查看和清理")
        print("• Token使用量监控")
        print("• 响应式Web界面")
        print("\n启动命令: python main.py (需要安装Flask依赖)")
    else:
        print("✗ 部分测试失败，需要修复问题")
    
    print("=" * 60)

if __name__ == "__main__":
    main()