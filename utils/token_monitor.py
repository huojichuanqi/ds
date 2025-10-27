"""
Token使用量监控和统计模块
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from .data_manager import data_manager
from .logger import enhanced_logger


class TokenMonitor:
    """Token使用量监控器"""
    
    def __init__(self):
        self.daily_limit = 1000000  # 每日Token限制
        self.monthly_limit = 30000000  # 每月Token限制
        self.last_reset_check = datetime.now()
        
    def record_usage(self, model: str, prompt_tokens: int, completion_tokens: int, 
                    api_call_type: str = "analysis") -> Dict[str, Any]:
        """记录Token使用量"""
        try:
            # 记录到数据管理器
            success = data_manager.record_token_usage(model, prompt_tokens, completion_tokens)
            
            if success:
                # 记录到日志
                enhanced_logger.log_token_usage(model, prompt_tokens, completion_tokens)
                
                # 检查使用量限制
                usage_stats = self.get_usage_stats()
                daily_usage = usage_stats.get("daily_total", 0)
                monthly_usage = usage_stats.get("monthly_total", 0)
                
                # 检查是否接近限制
                if daily_usage > self.daily_limit * 0.8:
                    enhanced_logger.log_warning(
                        f"每日Token使用量接近限制: {daily_usage}/{self.daily_limit}",
                        "token_limit"
                    )
                
                if monthly_usage > self.monthly_limit * 0.8:
                    enhanced_logger.log_warning(
                        f"每月Token使用量接近限制: {monthly_usage}/{self.monthly_limit}",
                        "token_limit"
                    )
                
                return {
                    "success": True,
                    "daily_usage": daily_usage,
                    "monthly_usage": monthly_usage,
                    "daily_limit": self.daily_limit,
                    "monthly_limit": self.monthly_limit
                }
            else:
                return {"success": False, "error": "记录Token使用量失败"}
                
        except Exception as e:
            enhanced_logger.log_error(f"记录Token使用量失败: {e}", "token_monitor")
            return {"success": False, "error": str(e)}
    
    def get_usage_stats(self, period: str = "all") -> Dict[str, Any]:
        """获取使用量统计"""
        try:
            token_data = data_manager.get_token_usage(period)
            
            if period == "daily":
                today = datetime.now().strftime("%Y-%m-%d")
                daily_usage = token_data.get(today, {})
                return self._calculate_usage_stats(daily_usage)
            
            elif period == "monthly":
                month = datetime.now().strftime("%Y-%m")
                monthly_usage = token_data.get(month, {})
                return self._calculate_usage_stats(monthly_usage)
            
            else:
                # 获取所有统计数据
                daily_usage = data_manager.get_token_usage("daily")
                monthly_usage = data_manager.get_token_usage("monthly")
                total_data = data_manager.get_token_usage("all")
                
                stats = {
                    "daily": self._calculate_usage_stats(daily_usage),
                    "monthly": self._calculate_usage_stats(monthly_usage),
                    "total": {
                        "total_tokens": total_data.get("total_tokens", 0),
                        "daily_limit": self.daily_limit,
                        "monthly_limit": self.monthly_limit
                    }
                }
                
                return stats
                
        except Exception as e:
            enhanced_logger.log_error(f"获取Token使用量统计失败: {e}", "token_monitor")
            return {}
    
    def _calculate_usage_stats(self, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算使用量统计"""
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0
        model_count = 0
        
        for model, usage in usage_data.items():
            if isinstance(usage, dict):
                total_tokens += usage.get("total_tokens", 0)
                prompt_tokens += usage.get("prompt_tokens", 0)
                completion_tokens += usage.get("completion_tokens", 0)
                model_count += 1
        
        return {
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "model_count": model_count,
            "average_tokens": total_tokens // max(model_count, 1)
        }
    
    def get_detailed_usage(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取详细使用量数据"""
        try:
            detailed_usage = []
            today = datetime.now()
            
            for i in range(days):
                date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
                daily_data = data_manager.get_token_usage("daily")
                
                if date in daily_data:
                    day_usage = daily_data[date]
                    day_stats = self._calculate_usage_stats(day_usage)
                    
                    detailed_usage.append({
                        "date": date,
                        "usage": day_stats,
                        "models": day_usage
                    })
                else:
                    detailed_usage.append({
                        "date": date,
                        "usage": {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0},
                        "models": {}
                    })
            
            return detailed_usage
            
        except Exception as e:
            enhanced_logger.log_error(f"获取详细使用量失败: {e}", "token_monitor")
            return []
    
    def check_usage_limits(self) -> Dict[str, Any]:
        """检查使用量限制"""
        try:
            stats = self.get_usage_stats()
            daily_stats = stats.get("daily", {})
            monthly_stats = stats.get("monthly", {})
            
            daily_usage = daily_stats.get("total_tokens", 0)
            monthly_usage = monthly_stats.get("total_tokens", 0)
            
            daily_percentage = (daily_usage / self.daily_limit) * 100 if self.daily_limit > 0 else 0
            monthly_percentage = (monthly_usage / self.monthly_limit) * 100 if self.monthly_limit > 0 else 0
            
            status = "normal"
            if daily_percentage >= 100 or monthly_percentage >= 100:
                status = "exceeded"
            elif daily_percentage >= 80 or monthly_percentage >= 80:
                status = "warning"
            
            return {
                "status": status,
                "daily": {
                    "usage": daily_usage,
                    "limit": self.daily_limit,
                    "percentage": daily_percentage
                },
                "monthly": {
                    "usage": monthly_usage,
                    "limit": self.monthly_limit,
                    "percentage": monthly_percentage
                },
                "recommendation": self._get_usage_recommendation(status, daily_percentage, monthly_percentage)
            }
            
        except Exception as e:
            enhanced_logger.log_error(f"检查使用量限制失败: {e}", "token_monitor")
            return {"status": "error", "error": str(e)}
    
    def _get_usage_recommendation(self, status: str, daily_percentage: float, monthly_percentage: float) -> str:
        """获取使用量建议"""
        if status == "exceeded":
            return "Token使用量已超过限制，建议暂停AI分析功能"
        elif status == "warning":
            if daily_percentage >= 80:
                return "每日Token使用量接近限制，建议减少分析频率"
            elif monthly_percentage >= 80:
                return "每月Token使用量接近限制，建议优化分析策略"
        return "Token使用量正常"
    
    def reset_usage_data(self, period: str = "daily") -> bool:
        """重置使用量数据"""
        try:
            # 目前数据重置由数据管理器自动处理
            # 这里主要记录重置操作
            enhanced_logger.log_info(f"Token使用量数据重置: {period}", "token_monitor")
            return True
        except Exception as e:
            enhanced_logger.log_error(f"重置使用量数据失败: {e}", "token_monitor")
            return False
    
    def get_cost_estimation(self, price_per_1k_tokens: float = 0.002) -> Dict[str, Any]:
        """获取成本估算"""
        try:
            stats = self.get_usage_stats()
            total_tokens = stats.get("total", {}).get("total_tokens", 0)
            daily_tokens = stats.get("daily", {}).get("total_tokens", 0)
            monthly_tokens = stats.get("monthly", {}).get("total_tokens", 0)
            
            total_cost = (total_tokens / 1000) * price_per_1k_tokens
            daily_cost = (daily_tokens / 1000) * price_per_1k_tokens
            monthly_cost = (monthly_tokens / 1000) * price_per_1k_tokens
            
            return {
                "total_cost": round(total_cost, 4),
                "daily_cost": round(daily_cost, 4),
                "monthly_cost": round(monthly_cost, 4),
                "total_tokens": total_tokens,
                "price_per_1k_tokens": price_per_1k_tokens
            }
            
        except Exception as e:
            enhanced_logger.log_error(f"成本估算失败: {e}", "token_monitor")
            return {}


# 全局Token监控器实例
token_monitor = TokenMonitor()