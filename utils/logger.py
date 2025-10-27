"""
增强版日志工具模块
支持日志分割、自动清理和Web界面查看
"""
import logging
import os
import glob
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json
from typing import List, Dict, Any


class EnhancedLogger:
    """增强版日志管理器"""
    
    def __init__(self, name: str = "trading_bot", log_level: str = "INFO"):
        self.name = name
        self.log_level = log_level.upper()
        self.log_dir = "logs"
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        self.retention_days = 30  # 保留30天日志
        
        # 创建日志目录
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 初始化日志记录器
        self.logger = self._setup_logger()
        
        # 创建日志索引文件
        self._create_log_index()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, self.log_level))
        
        # 清除已有的处理器
        logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 按时间分割的文件处理器（每天）
        time_handler = TimedRotatingFileHandler(
            os.path.join(self.log_dir, "trading.log"),
            when="midnight",
            interval=1,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        time_handler.setLevel(getattr(logging, self.log_level))
        time_handler.setFormatter(formatter)
        
        # 按大小分割的文件处理器
        size_handler = RotatingFileHandler(
            os.path.join(self.log_dir, "trading_current.log"),
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        size_handler.setLevel(getattr(logging, self.log_level))
        size_handler.setFormatter(formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.log_level))
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(time_handler)
        logger.addHandler(size_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _create_log_index(self):
        """创建日志索引文件"""
        index_file = os.path.join(self.log_dir, "log_index.json")
        if not os.path.exists(index_file):
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump({"logs": [], "last_cleanup": datetime.now().isoformat()}, f, indent=2)
    
    def log_trade(self, symbol: str, action: str, price: float, 
                  quantity: float, profit: float = 0.0, notes: str = "") -> None:
        """记录交易信息"""
        self.logger.info(f"TRADE - {symbol} - {action} - Price: {price}, "
                        f"Quantity: {quantity}, Profit: {profit}, Notes: {notes}")
        self._update_log_index("trade", {"symbol": symbol, "action": action, "profit": profit})
    
    def log_error(self, error_msg: str, error_type: str = "", details: str = "") -> None:
        """记录错误信息"""
        self.logger.error(f"ERROR - {error_type} - {error_msg} - Details: {details}")
        self._update_log_index("error", {"type": error_type, "message": error_msg})
    
    def log_info(self, info_msg: str, category: str = "") -> None:
        """记录一般信息"""
        self.logger.info(f"INFO - {category} - {info_msg}")
        self._update_log_index("info", {"category": category, "message": info_msg})
    
    def log_warning(self, warning_msg: str, category: str = "") -> None:
        """记录警告信息"""
        self.logger.warning(f"WARNING - {category} - {warning_msg}")
        self._update_log_index("warning", {"category": category, "message": warning_msg})
    
    def log_token_usage(self, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        """记录Token使用量"""
        total_tokens = prompt_tokens + completion_tokens
        self.logger.info(f"TOKEN_USAGE - {model} - Prompt: {prompt_tokens}, "
                        f"Completion: {completion_tokens}, Total: {total_tokens}")
        self._update_log_index("token_usage", {
            "model": model, 
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        })
    
    def _update_log_index(self, log_type: str, data: Dict[str, Any]):
        """更新日志索引"""
        try:
            index_file = os.path.join(self.log_dir, "log_index.json")
            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                
                # 添加新日志条目
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "type": log_type,
                    "data": data
                }
                index_data["logs"].append(log_entry)
                
                # 限制索引大小（保留最近1000条）
                if len(index_data["logs"]) > 1000:
                    index_data["logs"] = index_data["logs"][-1000:]
                
                with open(index_file, 'w', encoding='utf-8') as f:
                    json.dump(index_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # 如果索引更新失败，不影响主日志记录
            pass
    
    def get_recent_logs(self, limit: int = 100, log_type: str = None) -> List[Dict[str, Any]]:
        """获取最近的日志"""
        try:
            index_file = os.path.join(self.log_dir, "log_index.json")
            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                
                logs = index_data.get("logs", [])
                if log_type:
                    logs = [log for log in logs if log.get("type") == log_type]
                
                return logs[-limit:] if limit > 0 else logs
            return []
        except Exception as e:
            self.logger.error(f"获取日志失败: {e}")
            return []
    
    def cleanup_old_logs(self) -> bool:
        """清理旧日志文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            # 清理日志文件
            log_files = glob.glob(os.path.join(self.log_dir, "*.log*"))
            for log_file in log_files:
                file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                if file_time < cutoff_date:
                    os.remove(log_file)
                    self.logger.info(f"已删除旧日志文件: {os.path.basename(log_file)}")
            
            # 更新索引文件
            index_file = os.path.join(self.log_dir, "log_index.json")
            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                
                # 清理旧日志索引
                index_data["logs"] = [
                    log for log in index_data.get("logs", [])
                    if datetime.fromisoformat(log["timestamp"]) > cutoff_date
                ]
                index_data["last_cleanup"] = datetime.now().isoformat()
                
                with open(index_file, 'w', encoding='utf-8') as f:
                    json.dump(index_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"日志清理完成，保留最近{self.retention_days}天的日志")
            return True
        except Exception as e:
            self.logger.error(f"日志清理失败: {e}")
            return False
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        try:
            index_file = os.path.join(self.log_dir, "log_index.json")
            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                
                logs = index_data.get("logs", [])
                today = datetime.now().strftime("%Y-%m-%d")
                
                stats = {
                    "total_logs": len(logs),
                    "today_logs": len([log for log in logs if log["timestamp"].startswith(today)]),
                    "log_types": {},
                    "last_cleanup": index_data.get("last_cleanup", "")
                }
                
                # 统计各类型日志数量
                for log in logs:
                    log_type = log.get("type", "unknown")
                    stats["log_types"][log_type] = stats["log_types"].get(log_type, 0) + 1
                
                return stats
            return {}
        except Exception as e:
            self.logger.error(f"获取日志统计失败: {e}")
            return {}


# 全局增强日志记录器实例
enhanced_logger = EnhancedLogger()

# 向后兼容的函数
def setup_logger(name: str = "trading_bot", log_level: str = "INFO") -> logging.Logger:
    return enhanced_logger.logger

def log_trade(signal, reason, confidence, position_size, price, logger=None):
    """
    记录交易信息
    
    参数:
        signal: 交易信号
        reason: 交易理由
        confidence: 信心程度
        position_size: 仓位大小
        price: 价格
        logger: 日志记录器
    """
    if logger is None:
        logger = setup_logger()
    
    log_message = f"交易信号: {signal} | 信心: {confidence} | 仓位: {position_size} | 价格: {price} | 理由: {reason}"
    logger.info(log_message)

def log_error(message, error=None, logger=None):
    """
    记录错误信息
    
    参数:
        message: 错误消息
        error: 异常对象
        logger: 日志记录器
    """
    if logger is None:
        logger = setup_logger()
    
    if error:
        logger.error(f"{message}: {str(error)}")
    else:
        logger.error(message)

def log_info(message, logger=None):
    """
    记录一般信息
    
    参数:
        message: 信息内容
        logger: 日志记录器
    """
    if logger is None:
        logger = setup_logger()
    
    logger.info(message)

def log_warning(message, logger=None):
    """
    记录警告信息
    
    参数:
        message: 警告内容
        logger: 日志记录器
    """
    if logger is None:
        logger = setup_logger()
    
    logger.warning(message)

# 创建全局日志记录器实例
global_logger = setup_logger()