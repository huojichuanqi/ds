"""
JSON数据持久化管理模块
实现参数配置、交易记录、token使用量等数据的存储
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import threading
from .logger import enhanced_logger


class DataManager:
    """JSON数据管理器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.lock = threading.Lock()
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 数据文件路径
        self.config_file = os.path.join(data_dir, "config.json")
        self.trades_file = os.path.join(data_dir, "trades.json")
        self.tokens_file = os.path.join(data_dir, "tokens.json")
        self.system_file = os.path.join(data_dir, "system.json")
        
        # 初始化数据文件
        self._init_data_files()
    
    def _init_data_files(self):
        """初始化数据文件"""
        with self.lock:
            # 配置数据
            if not os.path.exists(self.config_file):
                self._save_json(self.config_file, {
                    "trading_mode": "test",  # test/production
                    "symbol": "BTC-USDT-SWAP",
                    "leverage": 10,
                    "timeframe": "1m",
                    "ma_periods": [5, 10, 20, 60],
                    "position_size": 0.1,
                    "max_position_size": 0.5,
                    "stop_loss": 0.02,
                    "take_profit": 0.05,
                    "ai_confidence_threshold": 0.7,
                    "last_modified": datetime.now().isoformat()
                })
            
            # 交易记录
            if not os.path.exists(self.trades_file):
                self._save_json(self.trades_file, {
                    "trades": [],
                    "total_trades": 0,
                    "winning_trades": 0,
                    "total_profit": 0.0,
                    "last_updated": datetime.now().isoformat()
                })
            
            # Token使用量
            if not os.path.exists(self.tokens_file):
                self._save_json(self.tokens_file, {
                    "daily_usage": {},
                    "monthly_usage": {},
                    "total_tokens": 0,
                    "last_reset": datetime.now().isoformat()
                })
            
            # 系统状态
            if not os.path.exists(self.system_file):
                self._save_json(self.system_file, {
                    "startup_time": datetime.now().isoformat(),
                    "last_heartbeat": datetime.now().isoformat(),
                    "system_status": "running",
                    "error_count": 0,
                    "performance_stats": {}
                })
    
    def _save_json(self, file_path: str, data: Dict[str, Any]):
        """保存JSON数据"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            enhanced_logger.log_error(f"保存JSON文件失败 {file_path}: {e}", "data_manager")
    
    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """加载JSON数据"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            enhanced_logger.log_error(f"加载JSON文件失败 {file_path}: {e}", "data_manager")
            return {}
    
    # 配置管理方法
    def get_config(self) -> Dict[str, Any]:
        """获取交易配置"""
        with self.lock:
            return self._load_json(self.config_file)
    
    def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """更新交易配置"""
        with self.lock:
            try:
                config = self._load_json(self.config_file)
                config.update(config_updates)
                config["last_modified"] = datetime.now().isoformat()
                self._save_json(self.config_file, config)
                enhanced_logger.log_info(f"配置已更新: {list(config_updates.keys())}", "data_manager")
                return True
            except Exception as e:
                enhanced_logger.log_error(f"更新配置失败: {e}", "data_manager")
                return False
    
    def switch_trading_mode(self, mode: str) -> bool:
        """切换交易模式"""
        if mode not in ["test", "production"]:
            enhanced_logger.log_error(f"无效的交易模式: {mode}", "data_manager")
            return False
        
        return self.update_config({"trading_mode": mode})
    
    # 交易记录管理
    def save_trade(self, trade_data: Dict[str, Any]) -> bool:
        """保存交易记录"""
        with self.lock:
            try:
                data = self._load_json(self.trades_file)
                trade_data["id"] = len(data.get("trades", [])) + 1
                trade_data["timestamp"] = datetime.now().isoformat()
                
                if "trades" not in data:
                    data["trades"] = []
                data["trades"].append(trade_data)
                
                # 更新统计信息
                data["total_trades"] = len(data["trades"])
                if trade_data.get("profit", 0) > 0:
                    data["winning_trades"] = data.get("winning_trades", 0) + 1
                data["total_profit"] = data.get("total_profit", 0) + trade_data.get("profit", 0)
                data["last_updated"] = datetime.now().isoformat()
                
                # 限制交易记录数量（保留最近1000条）
                if len(data["trades"]) > 1000:
                    data["trades"] = data["trades"][-1000:]
                
                self._save_json(self.trades_file, data)
                enhanced_logger.log_info(f"交易记录已保存: {trade_data.get('symbol', 'N/A')}", "data_manager")
                return True
            except Exception as e:
                enhanced_logger.log_error(f"保存交易记录失败: {e}", "data_manager")
                return False
    
    def get_trade_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取交易历史"""
        with self.lock:
            data = self._load_json(self.trades_file)
            trades = data.get("trades", [])
            return trades[-limit:] if limit > 0 else trades
    
    # Token使用量管理
    def record_token_usage(self, model: str, prompt_tokens: int, completion_tokens: int) -> bool:
        """记录Token使用量"""
        with self.lock:
            try:
                data = self._load_json(self.tokens_file)
                today = datetime.now().strftime("%Y-%m-%d")
                month = datetime.now().strftime("%Y-%m")
                
                # 更新日使用量
                if today not in data["daily_usage"]:
                    data["daily_usage"][today] = {}
                
                if model not in data["daily_usage"][today]:
                    data["daily_usage"][today][model] = {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                
                data["daily_usage"][today][model]["prompt_tokens"] += prompt_tokens
                data["daily_usage"][today][model]["completion_tokens"] += completion_tokens
                data["daily_usage"][today][model]["total_tokens"] += prompt_tokens + completion_tokens
                
                # 更新月使用量
                if month not in data["monthly_usage"]:
                    data["monthly_usage"][month] = {}
                
                if model not in data["monthly_usage"][month]:
                    data["monthly_usage"][month][model] = {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                
                data["monthly_usage"][month][model]["prompt_tokens"] += prompt_tokens
                data["monthly_usage"][month][model]["completion_tokens"] += completion_tokens
                data["monthly_usage"][month][model]["total_tokens"] += prompt_tokens + completion_tokens
                
                # 更新总量
                data["total_tokens"] += prompt_tokens + completion_tokens
                
                self._save_json(self.tokens_file, data)
                return True
            except Exception as e:
                enhanced_logger.log_error(f"记录Token使用量失败: {e}", "data_manager")
                return False
    
    def get_token_usage(self, period: str = "daily") -> Dict[str, Any]:
        """获取Token使用量统计"""
        with self.lock:
            data = self._load_json(self.tokens_file)
            
            if period == "daily":
                today = datetime.now().strftime("%Y-%m-%d")
                return data.get("daily_usage", {}).get(today, {})
            elif period == "monthly":
                month = datetime.now().strftime("%Y-%m")
                return data.get("monthly_usage", {}).get(month, {})
            else:
                return {
                    "daily_usage": data.get("daily_usage", {}),
                    "monthly_usage": data.get("monthly_usage", {}),
                    "total_tokens": data.get("total_tokens", 0)
                }
    
    # 系统状态管理
    def update_system_status(self, status_updates: Dict[str, Any]) -> bool:
        """更新系统状态"""
        with self.lock:
            try:
                data = self._load_json(self.system_file)
                data.update(status_updates)
                data["last_heartbeat"] = datetime.now().isoformat()
                self._save_json(self.system_file, data)
                return True
            except Exception as e:
                enhanced_logger.log_error(f"更新系统状态失败: {e}", "data_manager")
                return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        with self.lock:
            return self._load_json(self.system_file)
    
    # 数据清理方法
    def cleanup_old_data(self, days_to_keep: int = 30) -> bool:
        """清理旧数据"""
        with self.lock:
            try:
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                
                # 清理交易记录
                trades_data = self._load_json(self.trades_file)
                if "trades" in trades_data:
                    trades_data["trades"] = [
                        trade for trade in trades_data["trades"]
                        if datetime.fromisoformat(trade["timestamp"]) > cutoff_date
                    ]
                    self._save_json(self.trades_file, trades_data)
                
                # 清理Token使用量
                tokens_data = self._load_json(self.tokens_file)
                if "daily_usage" in tokens_data:
                    tokens_data["daily_usage"] = {
                        date: usage for date, usage in tokens_data["daily_usage"].items()
                        if datetime.strptime(date, "%Y-%m-%d") > cutoff_date
                    }
                    self._save_json(self.tokens_file, tokens_data)
                
                enhanced_logger.log_info(f"已清理 {days_to_keep} 天前的数据", "data_manager")
                return True
            except Exception as e:
                enhanced_logger.log_error(f"数据清理失败: {e}", "data_manager")
                return False


# 全局数据管理器实例
data_manager = DataManager()