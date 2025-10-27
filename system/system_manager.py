"""
系统管理模块 - 统一管理所有功能
"""
import os
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List

from utils.data_manager import data_manager
from utils.logger import enhanced_logger
from config.config_manager import config_manager
from utils.token_monitor import token_monitor


class SystemManager:
    """系统管理器 - 统一管理所有功能模块"""
    
    def __init__(self):
        self.version = "1.0.0"
        self.start_time = time.time()
        self.modules = {
            'data_manager': data_manager,
            'logger': enhanced_logger,
            'config': config_manager,
            'token_monitor': token_monitor
        }
        
        # 初始化系统日志
        enhanced_logger.log_info("系统管理器初始化完成", "system_manager")
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            # 获取进程信息
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # 获取磁盘使用情况
            disk_usage = psutil.disk_usage('.')
            
            # 计算运行时长
            uptime_seconds = time.time() - self.start_time
            uptime_str = str(timedelta(seconds=int(uptime_seconds)))
            
            # 获取数据统计
            data_stats = self._get_data_statistics()
            
            system_info = {
                'version': self.version,
                'uptime': uptime_str,
                'memory_usage': f"{memory_info.rss / 1024 / 1024:.2f} MB",
                'cpu_usage': f"{psutil.cpu_percent(interval=1):.1f}%",
                'disk_usage_percent': round((disk_usage.used / disk_usage.total) * 100, 1),
                'disk_usage': f"{disk_usage.used / 1024 / 1024 / 1024:.2f} GB / {disk_usage.total / 1024 / 1024 / 1024:.2f} GB",
                'data_file_size': data_stats['data_file_size'],
                'trade_count': data_stats['trade_count'],
                'config_count': data_stats['config_count'],
                'token_record_count': data_stats['token_record_count'],
                'log_file_count': data_stats['log_file_count']
            }
            
            enhanced_logger.log_info("系统信息获取成功", "system_manager")
            return system_info
            
        except Exception as e:
            enhanced_logger.log_error(f"获取系统信息失败: {str(e)}", "system_manager")
            return {
                'version': self.version,
                'uptime': 'N/A',
                'memory_usage': 'N/A',
                'cpu_usage': 'N/A',
                'disk_usage_percent': 0,
                'disk_usage': 'N/A',
                'data_file_size': 'N/A',
                'trade_count': 'N/A',
                'config_count': 'N/A',
                'token_record_count': 'N/A',
                'log_file_count': 'N/A'
            }
    
    def _get_data_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        try:
            # 获取数据文件大小
            data_file_size = '0 KB'
            if os.path.exists('data/system_data.json'):
                size = os.path.getsize('data/system_data.json')
                if size < 1024:
                    data_file_size = f"{size} B"
                elif size < 1024 * 1024:
                    data_file_size = f"{size / 1024:.2f} KB"
                else:
                    data_file_size = f"{size / 1024 / 1024:.2f} MB"
            
            # 获取交易记录数量
            trades = data_manager.load_data('trades', [])
            trade_count = len(trades)
            
            # 获取配置数量
            configs = data_manager.load_data('configs', [])
            config_count = len(configs)
            
            # 获取Token记录数量
            token_records = data_manager.load_data('token_usage', [])
            token_record_count = len(token_records)
            
            # 获取日志文件数量
            log_file_count = 0
            if os.path.exists('logs'):
                for file in os.listdir('logs'):
                    if file.endswith('.log'):
                        log_file_count += 1
            
            return {
                'data_file_size': data_file_size,
                'trade_count': trade_count,
                'config_count': config_count,
                'token_record_count': token_record_count,
                'log_file_count': log_file_count
            }
            
        except Exception as e:
            enhanced_logger.log_error(f"获取数据统计失败: {str(e)}", "system_manager")
            return {
                'data_file_size': 'N/A',
                'trade_count': 'N/A',
                'config_count': 'N/A',
                'token_record_count': 'N/A',
                'log_file_count': 'N/A'
            }
    
    def get_module_status(self) -> Dict[str, Dict[str, Any]]:
        """获取各模块状态"""
        module_status = {}
        
        try:
            # 数据管理器状态
            module_status['data_manager'] = {
                'status': 'running',
                'last_update': data_manager.get_last_update_time(),
                'data_files': len([f for f in os.listdir('data') if f.endswith('.json')])
            }
            
            # 日志系统状态
            module_status['logger'] = {
                'status': 'running',
                'log_level': enhanced_logger.get_log_level(),
                'log_files': len([f for f in os.listdir('logs') if f.endswith('.log')]) if os.path.exists('logs') else 0
            }
            
            # 配置管理器状态
            module_status['config'] = {
                'status': 'running',
                'current_mode': config_manager.get_current_mode(),
                'config_count': len(config_manager.get_all_configs())
            }
            
            # Token监控状态
            module_status['token_monitor'] = {
                'status': 'running',
                'today_usage': token_monitor.get_today_usage(),
                'month_usage': token_monitor.get_month_usage()
            }
            
            enhanced_logger.log_info("模块状态获取成功", "system_manager")
            
        except Exception as e:
            enhanced_logger.log_error(f"获取模块状态失败: {str(e)}", "system_manager")
            
        return module_status
    
    def cleanup_old_data(self, days: int = 30) -> Dict[str, Any]:
        """清理指定天数前的旧数据"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            cutoff_timestamp = cutoff_time.timestamp()
            
            cleaned_count = 0
            
            # 清理交易记录
            trades = data_manager.load_data('trades', [])
            original_count = len(trades)
            trades = [trade for trade in trades if trade.get('timestamp', 0) >= cutoff_timestamp]
            data_manager.save_data('trades', trades)
            cleaned_count += (original_count - len(trades))
            
            # 清理Token使用记录
            token_records = data_manager.load_data('token_usage', [])
            original_count = len(token_records)
            token_records = [record for record in token_records if record.get('timestamp', 0) >= cutoff_timestamp]
            data_manager.save_data('token_usage', token_records)
            cleaned_count += (original_count - len(token_records))
            
            # 清理日志索引
            log_index = data_manager.load_data('log_index', [])
            original_count = len(log_index)
            log_index = [entry for entry in log_index if entry.get('timestamp', 0) >= cutoff_timestamp]
            data_manager.save_data('log_index', log_index)
            cleaned_count += (original_count - len(log_index))
            
            enhanced_logger.log_info(f"数据清理完成，清理了{cleaned_count}条记录", "system_manager")
            
            return {
                'success': True,
                'message': f"成功清理了{cleaned_count}条{days}天前的旧数据",
                'cleaned_count': cleaned_count
            }
            
        except Exception as e:
            enhanced_logger.log_error(f"数据清理失败: {str(e)}", "system_manager")
            return {
                'success': False,
                'message': f"数据清理失败: {str(e)}",
                'cleaned_count': 0
            }
    
    def backup_system_data(self, backup_path: str = None) -> Dict[str, Any]:
        """备份系统数据"""
        try:
            if backup_path is None:
                backup_path = f"backup/system_backup_{int(time.time())}.json"
            
            # 确保备份目录存在
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # 收集所有数据
            backup_data = {
                'backup_time': time.time(),
                'backup_version': self.version,
                'configs': data_manager.load_data('configs', {}),
                'trades': data_manager.load_data('trades', []),
                'token_usage': data_manager.load_data('token_usage', []),
                'system_state': data_manager.load_data('system_state', {}),
                'log_index': data_manager.load_data('log_index', [])
            }
            
            # 保存备份文件
            import json
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            enhanced_logger.log_info(f"系统数据备份完成: {backup_path}", "system_manager")
            
            return {
                'success': True,
                'message': f"系统数据备份成功: {backup_path}",
                'backup_path': backup_path
            }
            
        except Exception as e:
            enhanced_logger.log_error(f"系统数据备份失败: {str(e)}", "system_manager")
            return {
                'success': False,
                'message': f"系统数据备份失败: {str(e)}",
                'backup_path': None
            }
    
    def restore_system_data(self, backup_path: str) -> Dict[str, Any]:
        """恢复系统数据"""
        try:
            if not os.path.exists(backup_path):
                return {
                    'success': False,
                    'message': f"备份文件不存在: {backup_path}"
                }
            
            # 读取备份数据
            import json
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # 恢复数据
            if 'configs' in backup_data:
                data_manager.save_data('configs', backup_data['configs'])
            if 'trades' in backup_data:
                data_manager.save_data('trades', backup_data['trades'])
            if 'token_usage' in backup_data:
                data_manager.save_data('token_usage', backup_data['token_usage'])
            if 'system_state' in backup_data:
                data_manager.save_data('system_state', backup_data['system_state'])
            if 'log_index' in backup_data:
                data_manager.save_data('log_index', backup_data['log_index'])
            
            enhanced_logger.log_info(f"系统数据恢复完成: {backup_path}", "system_manager")
            
            return {
                'success': True,
                'message': f"系统数据恢复成功: {backup_path}"
            }
            
        except Exception as e:
            enhanced_logger.log_error(f"系统数据恢复失败: {str(e)}", "system_manager")
            return {
                'success': False,
                'message': f"系统数据恢复失败: {str(e)}"
            }
    
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        try:
            health_status = {
                'overall': 'healthy',
                'details': {},
                'warnings': [],
                'errors': []
            }
            
            # 检查磁盘空间
            disk_usage = psutil.disk_usage('.')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            if disk_percent > 90:
                health_status['overall'] = 'warning'
                health_status['warnings'].append('磁盘空间不足')
            
            # 检查内存使用
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 85:
                health_status['overall'] = 'warning'
                health_status['warnings'].append('内存使用率过高')
            
            # 检查数据文件
            if not os.path.exists('data/system_data.json'):
                health_status['overall'] = 'error'
                health_status['errors'].append('数据文件不存在')
            
            # 检查日志目录
            if not os.path.exists('logs'):
                health_status['overall'] = 'warning'
                health_status['warnings'].append('日志目录不存在')
            
            health_status['details'] = {
                'disk_usage_percent': round(disk_percent, 1),
                'memory_usage_percent': round(memory_percent, 1),
                'data_file_exists': os.path.exists('data/system_data.json'),
                'log_dir_exists': os.path.exists('logs'),
                'module_count': len(self.modules)
            }
            
            enhanced_logger.log_info("系统健康状态检查完成", "system_manager")
            
            return health_status
            
        except Exception as e:
            enhanced_logger.log_error(f"系统健康状态检查失败: {str(e)}", "system_manager")
            return {
                'overall': 'error',
                'details': {},
                'warnings': [],
                'errors': [f'健康检查失败: {str(e)}']
            }
    
    def shutdown_system(self) -> Dict[str, Any]:
        """安全关闭系统"""
        try:
            enhanced_logger.log_info("系统正在安全关闭...", "system_manager")
            
            # 备份当前数据
            self.backup_system_data()
            
            # 记录关闭信息
            enhanced_logger.log_info("系统安全关闭完成", "system_manager")
            
            return {
                'success': True,
                'message': '系统安全关闭完成'
            }
            
        except Exception as e:
            enhanced_logger.log_error(f"系统关闭失败: {str(e)}", "system_manager")
            return {
                'success': False,
                'message': f'系统关闭失败: {str(e)}'
            }


# 创建全局系统管理器实例
system_manager = SystemManager()