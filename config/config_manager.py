"""
配置管理系统
支持Web界面动态修改参数和测试/生产模式切换
"""
import os
from typing import Dict, Any, Optional
from utils.data_manager import data_manager
from utils.logger import enhanced_logger


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self._config_cache = None
        self._last_update_time = None
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            self._config_cache = data_manager.get_config()
            self._last_update_time = self._config_cache.get("last_modified")
            enhanced_logger.log_info("配置已加载", "config_manager")
            return self._config_cache
        except Exception as e:
            enhanced_logger.log_error(f"加载配置失败: {e}", "config_manager")
            return {}
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        if self._config_cache is None:
            self.load_config()
        return self._config_cache.copy() if self._config_cache else {}
    
    def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            # 验证配置参数
            if not self._validate_config(config_updates):
                return False
            
            # 更新配置
            success = data_manager.update_config(config_updates)
            if success:
                self._config_cache = None  # 清除缓存
                self.load_config()  # 重新加载
                enhanced_logger.log_info(f"配置已更新: {list(config_updates.keys())}", "config_manager")
            
            return success
        except Exception as e:
            enhanced_logger.log_error(f"更新配置失败: {e}", "config_manager")
            return False
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置参数"""
        try:
            # 交易模式验证
            if "trading_mode" in config:
                if config["trading_mode"] not in ["test", "production"]:
                    enhanced_logger.log_error("无效的交易模式", "config_manager")
                    return False
            
            # 杠杆倍数验证
            if "leverage" in config:
                leverage = config["leverage"]
                if not isinstance(leverage, (int, float)) or leverage <= 0 or leverage > 100:
                    enhanced_logger.log_error("杠杆倍数必须在1-100之间", "config_manager")
                    return False
            
            # 仓位大小验证
            if "position_size" in config:
                size = config["position_size"]
                if not isinstance(size, (int, float)) or size <= 0 or size > 1:
                    enhanced_logger.log_error("仓位大小必须在0-1之间", "config_manager")
                    return False
            
            # 止损止盈验证
            if "stop_loss" in config:
                sl = config["stop_loss"]
                if not isinstance(sl, (int, float)) or sl <= 0 or sl > 0.5:
                    enhanced_logger.log_error("止损比例必须在0-0.5之间", "config_manager")
                    return False
            
            if "take_profit" in config:
                tp = config["take_profit"]
                if not isinstance(tp, (int, float)) or tp <= 0 or tp > 1:
                    enhanced_logger.log_error("止盈比例必须在0-1之间", "config_manager")
                    return False
            
            # AI置信度验证
            if "ai_confidence_threshold" in config:
                conf = config["ai_confidence_threshold"]
                if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
                    enhanced_logger.log_error("AI置信度必须在0-1之间", "config_manager")
                    return False
            
            return True
        except Exception as e:
            enhanced_logger.log_error(f"配置验证失败: {e}", "config_manager")
            return False
    
    def switch_trading_mode(self, mode: str) -> bool:
        """切换交易模式"""
        return data_manager.switch_trading_mode(mode)
    
    def is_test_mode(self) -> bool:
        """检查是否为测试模式"""
        config = self.get_config()
        return config.get("trading_mode", "test") == "test"
    
    def is_production_mode(self) -> bool:
        """检查是否为生产模式"""
        config = self.get_config()
        return config.get("trading_mode", "test") == "production"
    
    def get_trading_params(self) -> Dict[str, Any]:
        """获取交易参数"""
        config = self.get_config()
        return {
            "symbol": config.get("symbol", "BTC-USDT-SWAP"),
            "leverage": config.get("leverage", 10),
            "timeframe": config.get("timeframe", "1m"),
            "position_size": config.get("position_size", 0.1),
            "max_position_size": config.get("max_position_size", 0.5),
            "stop_loss": config.get("stop_loss", 0.02),
            "take_profit": config.get("take_profit", 0.05),
            "ai_confidence_threshold": config.get("ai_confidence_threshold", 0.7)
        }
    
    def get_ma_periods(self) -> list:
        """获取均线周期"""
        config = self.get_config()
        return config.get("ma_periods", [5, 10, 20, 60])
    
    def get_config_for_ui(self) -> Dict[str, Any]:
        """获取用于UI显示的配置"""
        config = self.get_config()
        return {
            "trading_mode": config.get("trading_mode", "test"),
            "symbol": config.get("symbol", "BTC-USDT-SWAP"),
            "leverage": config.get("leverage", 10),
            "timeframe": config.get("timeframe", "1m"),
            "position_size": config.get("position_size", 0.1),
            "max_position_size": config.get("max_position_size", 0.5),
            "stop_loss": config.get("stop_loss", 0.02),
            "take_profit": config.get("take_profit", 0.05),
            "ai_confidence_threshold": config.get("ai_confidence_threshold", 0.7),
            "ma_periods": config.get("ma_periods", [5, 10, 20, 60]),
            "last_modified": config.get("last_modified", "")
        }


# 全局配置管理器实例
config_manager = ConfigManager()