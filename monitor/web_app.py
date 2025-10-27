"""
增强版Web监控面板模块
集成参数修改、模式切换、日志查看、Token监控等功能
"""
from flask import Flask, render_template, jsonify, request
import threading
import time
from datetime import datetime
import json
from utils.logger import enhanced_logger
from config.config_manager import config_manager
from utils.data_manager import data_manager
from utils.token_monitor import token_monitor
from system.system_manager import system_manager


class EnhancedWebMonitor:
    """增强版Web监控面板"""
    
    def __init__(self, trading_engine, host='0.0.0.0', port=5000):
        """
        初始化增强版Web监控面板
        
        参数:
            trading_engine: 交易引擎实例
            host: 监听主机
            port: 监听端口
        """
        self.engine = trading_engine
        self.host = host
        self.port = port
        self.app = Flask(__name__, template_folder='templates')
        self.server_thread = None
        self.running = False
        
        self.status = {
            'running': False,
            'last_update': datetime.now().isoformat(),
            'trading_status': 'stopped',
            'current_price': 0.0,
            'position': {},
            'signals': [],
            'errors': [],
            'system_info': {},
            'token_usage': {},
            'log_stats': {}
        }
        
        # 配置路由
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.route('/')
        def index():
            return render_template('monitor.html')
        
        @self.app.route('/api/status')
        def api_status():
            """获取系统状态"""
            try:
                # 更新实时数据
                self._update_real_time_data()
                
                # 获取交易汇总信息
                summary = self.engine.get_trade_summary()
                
                # 获取账户信息
                balance = self.engine.exchange.get_balance()
                equity = float(balance.get('totalEq', 0)) if balance else 0
                
                # 构建响应数据
                status_data = {
                    'trading_status': 'running',
                    'current_price': summary['current_price'],
                    'position': summary['current_position'],
                    'account_equity': equity,
                    'total_trades': summary['total_trades'],
                    'last_signal': summary['last_signal'],
                    'last_updated': summary['last_updated']
                }
                
                # 合并增强状态数据
                status_data.update(self.status)
                
                return jsonify({'status': 'success', 'data': status_data})
                
            except Exception as e:
                enhanced_logger.log_error("获取状态信息失败", e, "web_monitor")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/history')
        def api_history():
            """获取交易历史"""
            try:
                # 获取最近20条交易记录
                recent_trades = self.engine.trade_history[-20:][::-1]  # 倒序，最新的在前
                
                # 获取最近10个信号
                recent_signals = self.engine.signal_history[-10:][::-1]
                
                return jsonify({
                    'status': 'success',
                    'data': {
                        'trades': recent_trades,
                        'signals': recent_signals
                    }
                })
                
            except Exception as e:
                enhanced_logger.log_error("获取历史数据失败", e, "web_monitor")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/config', methods=['GET', 'POST'])
        def api_config():
            """配置管理API"""
            if request.method == 'GET':
                return jsonify({
                    'success': True,
                    'config': config_manager.get_config_for_ui()
                })
            else:
                # POST请求 - 更新配置
                try:
                    config_updates = request.get_json()
                    if config_updates and config_manager.update_config(config_updates):
                        enhanced_logger.log_info(f"配置已更新: {list(config_updates.keys())}", "web_monitor")
                        return jsonify({'success': True, 'message': '配置更新成功'})
                    else:
                        return jsonify({'success': False, 'message': '配置更新失败'})
                except Exception as e:
                    enhanced_logger.log_error(f"配置更新失败: {e}", "web_monitor")
                    return jsonify({'success': False, 'message': str(e)})
        
        @self.app.route('/api/switch_mode', methods=['POST'])
        def api_switch_mode():
            """切换交易模式"""
            try:
                mode = request.get_json().get('mode')
                if mode in ['test', 'production']:
                    if config_manager.switch_trading_mode(mode):
                        enhanced_logger.log_info(f"交易模式已切换为: {mode}", "web_monitor")
                        return jsonify({'success': True, 'message': f'已切换到{mode}模式'})
                    else:
                        return jsonify({'success': False, 'message': '模式切换失败'})
                else:
                    return jsonify({'success': False, 'message': '无效的模式'})
            except Exception as e:
                enhanced_logger.log_error(f"模式切换失败: {e}", "web_monitor")
                return jsonify({'success': False, 'message': str(e)})
        
        @self.app.route('/api/token_usage')
        def api_token_usage():
            """获取Token使用量"""
            try:
                period = request.args.get('period', 'all')
                stats = token_monitor.get_usage_stats(period)
                limits = token_monitor.check_usage_limits()
                cost = token_monitor.get_cost_estimation()
                
                return jsonify({
                    'success': True,
                    'stats': stats,
                    'limits': limits,
                    'cost': cost
                })
            except Exception as e:
                enhanced_logger.log_error(f"获取Token使用量失败: {e}", "web_monitor")
                return jsonify({'success': False, 'message': str(e)})
        
        @self.app.route('/api/logs')
        def api_logs():
            """获取日志"""
            try:
                limit = int(request.args.get('limit', 100))
                log_type = request.args.get('type')
                logs = enhanced_logger.get_recent_logs(limit, log_type)
                stats = enhanced_logger.get_log_statistics()
                
                return jsonify({
                    'success': True,
                    'logs': logs,
                    'stats': stats
                })
            except Exception as e:
                enhanced_logger.log_error(f"获取日志失败: {e}", "web_monitor")
                return jsonify({'success': False, 'message': str(e)})
        
        @self.app.route('/api/cleanup_logs', methods=['POST'])
        def api_cleanup_logs():
            """清理日志"""
            try:
                if enhanced_logger.cleanup_old_logs():
                    enhanced_logger.log_info("日志清理完成", "web_monitor")
                    return jsonify({'success': True, 'message': '日志清理成功'})
                else:
                    return jsonify({'success': False, 'message': '日志清理失败'})
            except Exception as e:
                enhanced_logger.log_error(f"日志清理失败: {e}", "web_monitor")
                return jsonify({'success': False, 'message': str(e)})
        
        @self.app.route('/api/trades')
        def api_trades():
            """获取交易记录"""
            try:
                limit = int(request.args.get('limit', 50))
                trades = data_manager.get_trade_history(limit)
                
                return jsonify({
                    'success': True,
                    'trades': trades
                })
            except Exception as e:
                enhanced_logger.log_error(f"获取交易记录失败: {e}", "web_monitor")
                return jsonify({'success': False, 'message': str(e)})
        
        @self.app.route('/api/system_info')
        def api_system_info():
            """获取系统信息"""
            try:
                system_info = system_manager.get_system_info()
                
                return jsonify({
                    'success': True,
                    'system_info': system_info
                })
            except Exception as e:
                enhanced_logger.log_error(f"获取系统信息失败: {e}", "web_monitor")
                return jsonify({'success': False, 'message': str(e)})
        
        @self.app.route('/api/cleanup_data', methods=['POST'])
        def api_cleanup_data():
            """清理数据"""
            try:
                days_to_keep = request.get_json().get('days', 30)
                if data_manager.cleanup_old_data(days_to_keep):
                    enhanced_logger.log_info(f"数据清理完成，保留最近{days_to_keep}天数据", "web_monitor")
                    return jsonify({'success': True, 'message': '数据清理成功'})
                else:
                    return jsonify({'success': False, 'message': '数据清理失败'})
            except Exception as e:
                enhanced_logger.log_error(f"数据清理失败: {e}", "web_monitor")
                return jsonify({'success': False, 'message': str(e)})
        
        @self.app.route('/api/system_health', methods=['GET'])
        def api_system_health():
            """获取系统健康状态"""
            try:
                health_status = system_manager.get_system_health()
                
                return jsonify({
                    'success': True,
                    'health_status': health_status
                })
                
            except Exception as e:
                enhanced_logger.log_error(f"获取系统健康状态失败: {e}", "web_monitor")
                return jsonify({
                    'success': False,
                    'message': f'获取系统健康状态失败: {str(e)}'
                })
        
        @self.app.route('/api/backup_system', methods=['POST'])
        def api_backup_system():
            """备份系统数据"""
            try:
                result = system_manager.backup_system_data()
                
                return jsonify(result)
                
            except Exception as e:
                enhanced_logger.log_error(f"备份系统数据失败: {e}", "web_monitor")
                return jsonify({
                    'success': False,
                    'message': f'备份系统数据失败: {str(e)}'
                })
        
        @self.app.route('/api/shutdown', methods=['POST'])
        def api_shutdown():
            """安全关闭系统"""
            try:
                result = system_manager.shutdown_system()
                
                return jsonify(result)
                
            except Exception as e:
                enhanced_logger.log_error(f"关闭系统失败: {e}", "web_monitor")
                return jsonify({
                    'success': False,
                    'message': f'关闭系统失败: {str(e)}'
                })
    
    def _update_real_time_data(self):
        """更新实时数据"""
        try:
            # 更新Token使用量
            self.status['token_usage'] = token_monitor.get_usage_stats()
            
            # 更新日志统计
            self.status['log_stats'] = enhanced_logger.get_log_statistics()
            
            # 更新系统信息
            self.status['system_info'] = system_manager.get_system_info()
            
            # 更新配置状态
            self.status['config'] = config_manager.get_config_for_ui()
            
        except Exception as e:
            enhanced_logger.log_error(f"更新实时数据失败: {e}", "web_monitor")
    
    def update_monitor_state(self, state_data):
        """
        更新监控状态（预留接口，可用于实时数据更新）
        
        参数:
            state_data: 状态数据
        """
        self.status.update(state_data)
        self.status['last_update'] = datetime.now().isoformat()
    
    def _run_server(self):
        """
        在后台线程中运行Flask服务器
        """
        try:
            enhanced_logger.log_info(f"启动Web监控面板: http://{self.host}:{self.port}", "web_monitor")
            self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
        except Exception as e:
            enhanced_logger.log_error("Web服务器运行失败", e, "web_monitor")
    
    def start(self, daemon=True):
        """
        启动Web监控面板
        
        参数:
            daemon: 是否使用守护线程，默认为True
        """
        if not self.running:
            self.running = True
            self.server_thread = threading.Thread(target=self._run_server, daemon=daemon)
            self.server_thread.start()
            enhanced_logger.log_info(f"Web监控面板已启动，访问地址: http://localhost:{self.port}", "web_monitor")
        else:
            enhanced_logger.log_info("Web监控面板已经在运行中", "web_monitor")
    
    def stop(self):
        """
        停止Web监控面板
        """
        if self.running:
            self.running = False
            # Flask不提供优雅停止的方式，这里简单记录
            enhanced_logger.log_info("Web监控面板已停止", "web_monitor")
            # 注意：实际生产环境中可能需要更复杂的停止机制