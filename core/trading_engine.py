import time
import os
import json
from utils.logger import enhanced_logger
from utils.helpers import calculate_pnl, format_price
from api.exchange_client import OKXClient

class TradingEngine:
    """
    交易引擎核心类
    负责处理交易信号、执行交易、管理仓位等核心逻辑
    """
    def __init__(self, exchange_client, trade_config):
        """
        初始化交易引擎
        
        参数:
            exchange_client: 交易所客户端
            trade_config: 交易配置
        """
        self.exchange = exchange_client
        self.config = trade_config
        self.trade_history = []
        self.signal_history = []
        
        # 确保data目录存在
        os.makedirs('data', exist_ok=True)
        
        # 加载历史记录
        self._load_history()
        
    def _load_history(self):
        """
        加载历史交易记录和信号历史
        """
        try:
            # 加载交易历史
            if os.path.exists('data/trade_history.json'):
                with open('data/trade_history.json', 'r', encoding='utf-8') as f:
                    self.trade_history = json.load(f)
                enhanced_logger.log_info(f"加载交易历史记录: {len(self.trade_history)}条", "trading_engine")
            
            # 加载信号历史
            if os.path.exists('data/signal_history.json'):
                with open('data/signal_history.json', 'r', encoding='utf-8') as f:
                    self.signal_history = json.load(f)
                enhanced_logger.log_info(f"加载信号历史记录: {len(self.signal_history)}条", "trading_engine")
                
        except Exception as e:
            enhanced_logger.log_error("加载历史记录失败", "trading_engine", e)
    
    def _save_history(self):
        """
        保存历史交易记录和信号历史
        """
        try:
            # 保存交易历史
            with open('data/trade_history.json', 'w', encoding='utf-8') as f:
                json.dump(self.trade_history, f, ensure_ascii=False, indent=2)
            
            # 保存信号历史（只保留最近100条）
            recent_signals = self.signal_history[-100:] if len(self.signal_history) > 100 else self.signal_history
            with open('data/signal_history.json', 'w', encoding='utf-8') as f:
                json.dump(recent_signals, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            enhanced_logger.log_error("保存历史记录失败", "trading_engine", e)
    
    def get_current_position(self):
        """
        获取当前持仓
        
        返回:
            持仓信息或None
        """
        try:
            position = self.exchange.get_position()
            if position and position['size'] > 0:
                enhanced_logger.log_info(f"当前持仓: {position['side']} {position['size']} 入场价: {position['entry_price']:.2f} 盈亏: {position['unrealized_pnl']:.2f} USDT", "trading_engine")
            else:
                enhanced_logger.log_info("当前无持仓", "trading_engine")
            return position
        except Exception as e:
            enhanced_logger.log_error("获取持仓信息失败", "trading_engine", e)
            return None
    
    def calculate_position_size(self, signal_data, current_position):
        """
        智能计算仓位大小
        
        参数:
            signal_data: 信号数据
            current_position: 当前持仓
        
        返回:
            计算后的仓位大小
        """
        try:
            # 获取账户余额
            balance = self.exchange.get_balance()
            equity = float(balance.get('totalEq', 0)) if balance else 0
            
            if equity <= 0:
                enhanced_logger.log_warning("账户余额为0，无法计算仓位", "trading_engine")
                return 0
            
            # 获取当前价格
            current_price = self.exchange.get_market_price()
            if current_price <= 0:
                enhanced_logger.log_warning("无法获取当前价格", "trading_engine")
                return 0
            
            # 基础仓位大小 (账户权益 * 风险系数 * 杠杆)
            base_size = (equity * self.config['risk_percent'] / 100) * self.config['leverage'] / current_price
            
            # 根据信号信心调整仓位
            confidence_multiplier = {
                'HIGH': 1.0,
                'MEDIUM': 0.7,
                'LOW': 0.5
            }
            
            confidence = signal_data.get('confidence', 'MEDIUM')
            adjusted_size = base_size * confidence_multiplier.get(confidence, 0.7)
            
            # 最小交易量限制
            min_size = self.config['min_order_size']
            if adjusted_size < min_size:
                adjusted_size = min_size
            
            # 根据趋势强度进一步调整
            trend_strength = self._calculate_trend_strength(signal_data)
            trend_multiplier = 0.8 + (trend_strength * 0.4)  # 0.8 到 1.2 的范围
            final_size = adjusted_size * trend_multiplier
            
            # 最大交易量限制
            max_size = self.config['max_order_size']
            if final_size > max_size:
                final_size = max_size
            
            # 保留4位小数
            final_size = round(final_size, 4)
            
            # 检查是否需要加仓或减仓
            if current_position and current_position['size'] > 0:
                position_side = current_position['side']
                signal_side = 'long' if signal_data['signal'] == 'BUY' else 'short' if signal_data['signal'] == 'SELL' else None
                
                # 同向信号 - 加仓
                if position_side == signal_side:
                    total_size = current_position['size'] + final_size
                    # 检查是否超过最大持仓
                    if total_size > self.config['max_position_size']:
                        final_size = self.config['max_position_size'] - current_position['size']
                        if final_size <= 0:
                            enhanced_logger.log_info("已达到最大持仓限制，不执行加仓", "trading_engine")
                            return 0
                    enhanced_logger.log_info(f"加仓: {final_size} {self.config['symbol']}", "trading_engine")
                
            enhanced_logger.log_info(f"计算仓位: {final_size} {self.config['symbol']} (信心: {confidence}, 趋势强度: {trend_strength:.2f})", "trading_engine")
            return final_size
            
        except Exception as e:
            enhanced_logger.log_error("计算仓位失败", "trading_engine", e)
            return self.config['min_order_size']
    
    def _calculate_trend_strength(self, signal_data):
        """
        计算趋势强度
        
        参数:
            signal_data: 信号数据
        
        返回:
            趋势强度 (0-1之间)
        """
        # 这里可以根据信号中的更多信息来计算趋势强度
        # 简化版本：根据信心级别和理由中关键词判断
        confidence = signal_data.get('confidence', 'MEDIUM')
        reason = signal_data.get('reason', '')
        
        # 基础强度
        base_strength = {
            'HIGH': 0.8,
            'MEDIUM': 0.5,
            'LOW': 0.3
        }.get(confidence, 0.5)
        
        # 关键词增强
        strength_boost = 0
        if any(keyword in reason for keyword in ['强势', '突破', '明确', '明显']):
            strength_boost += 0.2
        if any(keyword in reason for keyword in ['反转', '改变', '转向']):
            strength_boost += 0.1
            
        # 确保不超过1.0
        total_strength = min(base_strength + strength_boost, 1.0)
        return total_strength
    
    def check_signal_reversal(self, new_signal, current_position):
        """
        检查信号是否发生反转
        
        参数:
            new_signal: 新信号
            current_position: 当前持仓
        
        返回:
            是否需要反转
        """
        if not current_position or current_position['size'] == 0:
            return False
        
        position_side = current_position['side']
        
        # 检查是否需要反转
        if (position_side == 'long' and new_signal['signal'] == 'SELL') or \
           (position_side == 'short' and new_signal['signal'] == 'BUY'):
            
            # 计算当前盈亏
            pnl_percent = current_position['unrealized_pnl'] / (current_position['size'] * current_position['entry_price']) * 100
            
            # 亏损超过阈值时立即反转
            if pnl_percent < -self.config['max_loss_percent']:
                enhanced_logger.log_warning(f"亏损超过阈值 {self.config['max_loss_percent']}%，执行反转交易", "trading_engine")
                return True
            
            # 盈利达到目标时反转
            if pnl_percent > self.config['target_profit_percent']:
                enhanced_logger.log_info(f"盈利达到目标 {self.config['target_profit_percent']}%，执行反转交易", "trading_engine")
                return True
            
            # 根据信号信心决定是否反转
            confidence = new_signal.get('confidence', 'MEDIUM')
            if confidence == 'HIGH':
                enhanced_logger.log_info(f"高信心信号，执行反转交易", "trading_engine")
                return True
            
            # 中等信心需要额外确认
            if confidence == 'MEDIUM':
                # 检查是否有多个技术指标支持反转
                reason = new_signal.get('reason', '')
                if any(keyword in reason for keyword in ['突破', '反转', '确认']):
                    enhanced_logger.log_info(f"中等信心信号但有反转确认，执行反转交易", "trading_engine")
                    return True
        
        return False
    
    def execute_intelligent_trade(self, signal_data):
        """
        执行智能交易
        
        参数:
            signal_data: 信号数据
        
        返回:
            交易结果
        """
        try:
            enhanced_logger.log_info(f"执行智能交易，信号: {signal_data['signal']}, 信心: {signal_data['confidence']}", "trading_engine")
            
            # 获取当前持仓
            current_position = self.get_current_position()
            
            # 记录信号历史
            self.signal_history.append(signal_data)
            
            # HOLD信号处理
            if signal_data['signal'] == 'HOLD':
                enhanced_logger.log_info(f"收到HOLD信号，保持当前状态", "trading_engine")
                return {'status': 'hold', 'message': '保持当前状态'}
            
            # 检查信号反转
            reversal_needed = self.check_signal_reversal(signal_data, current_position)
            
            # 计算仓位大小
            position_size = self.calculate_position_size(signal_data, current_position)
            if position_size <= 0:
                return {'status': 'failed', 'message': '无效的仓位大小'}
            
            # 交易执行
            if signal_data['signal'] == 'BUY':
                result = self._execute_buy_signal(current_position, position_size, reversal_needed)
            elif signal_data['signal'] == 'SELL':
                result = self._execute_sell_signal(current_position, position_size, reversal_needed)
            else:
                result = {'status': 'failed', 'message': '未知信号类型'}
            
            # 保存历史记录
            if result['status'] in ['success', 'partial']:
                self._save_history()
            
            return result
            
        except Exception as e:
            enhanced_logger.log_error("执行智能交易失败", "trading_engine", e)
            return {'status': 'error', 'message': str(e)}
    
    def _execute_buy_signal(self, current_position, position_size, reversal_needed):
        """
        执行买入信号
        """
        if reversal_needed and current_position:
            # 平空仓并开多仓
            enhanced_logger.log_info("执行反转交易：平空仓并开多仓", "trading_engine")
            
            # 平仓
            close_result = self.exchange.close_position()
            if not close_result:
                enhanced_logger.log_error("平仓失败，取消交易", "trading_engine")
                return {'status': 'failed', 'message': '平仓失败'}
            
            # 等待平仓完成
            time.sleep(1)
            
            # 开多仓
            order_id = self.exchange.place_order(side='buy', size=position_size, ord_type='market')
            if order_id:
                self._record_trade('BUY', position_size, 'market', 'reversal')
                return {'status': 'success', 'order_id': order_id, 'action': 'reversal'}
            else:
                enhanced_logger.log_error("开多仓失败", "trading_engine")
                return {'status': 'failed', 'message': '开多仓失败'}
        
        if current_position and current_position['side'] == 'long':
            # 已有多仓，加仓
            enhanced_logger.log_info("执行加仓：多仓加仓", "trading_engine")
            order_id = self.exchange.place_order(side='buy', size=position_size, ord_type='market')
            if order_id:
                self._record_trade('BUY', position_size, 'market', 'add')
                return {'status': 'success', 'order_id': order_id, 'action': 'add'}
            else:
                enhanced_logger.log_error("加仓失败", "trading_engine")
                return {'status': 'failed', 'message': '加仓失败'}
        
        if current_position and current_position['side'] == 'short':
            # 已有空仓，但不需要反转，忽略信号
            enhanced_logger.log_info("收到买入信号，但已有空仓且不需要反转，忽略信号", "trading_engine")
            return {'status': 'ignored', 'message': '已有空仓且不需要反转'}
        
        # 无持仓，新开多仓
        enhanced_logger.log_info("执行开仓：新开多仓", "trading_engine")
        order_id = self.exchange.place_order(side='buy', size=position_size, ord_type='market')
        if order_id:
            self._record_trade('BUY', position_size, 'market', 'open')
            return {'status': 'success', 'order_id': order_id, 'action': 'open'}
        else:
            enhanced_logger.log_error("开仓失败", "trading_engine")
            return {'status': 'failed', 'message': '开仓失败'}
    
    def _execute_sell_signal(self, current_position, position_size, reversal_needed):
        """
        执行卖出信号
        """
        if reversal_needed and current_position:
            # 平多仓并开空仓
            enhanced_logger.log_info("执行反转交易：平多仓并开空仓", "trading_engine")
            
            # 平仓
            close_result = self.exchange.close_position()
            if not close_result:
                enhanced_logger.log_error("平仓失败，取消交易", "trading_engine")
                return {'status': 'failed', 'message': '平仓失败'}
            
            # 等待平仓完成
            time.sleep(1)
            
            # 开空仓
            order_id = self.exchange.place_order(side='sell', size=position_size, ord_type='market')
            if order_id:
                self._record_trade('SELL', position_size, 'market', 'reversal')
                return {'status': 'success', 'order_id': order_id, 'action': 'reversal'}
            else:
                enhanced_logger.log_error("开空仓失败", "trading_engine")
                return {'status': 'failed', 'message': '开空仓失败'}
        
        if current_position and current_position['side'] == 'short':
            # 已有空仓，加仓
            enhanced_logger.log_info("执行加仓：空仓加仓", "trading_engine")
            order_id = self.exchange.place_order(side='sell', size=position_size, ord_type='market')
            if order_id:
                self._record_trade('SELL', position_size, 'market', 'add')
                return {'status': 'success', 'order_id': order_id, 'action': 'add'}
            else:
                enhanced_logger.log_error("加仓失败", "trading_engine")
                return {'status': 'failed', 'message': '加仓失败'}
        
        if current_position and current_position['side'] == 'long':
            # 已有多仓，但不需要反转，忽略信号
            enhanced_logger.log_info("收到卖出信号，但已有多仓且不需要反转，忽略信号", "trading_engine")
            return {'status': 'ignored', 'message': '已有多仓且不需要反转'}
        
        # 无持仓，新开空仓
        enhanced_logger.log_info("执行开仓：新开空仓", "trading_engine")
        order_id = self.exchange.place_order(side='sell', size=position_size, ord_type='market')
        if order_id:
            self._record_trade('SELL', position_size, 'market', 'open')
            return {'status': 'success', 'order_id': order_id, 'action': 'open'}
        else:
            enhanced_logger.log_error("开仓失败", "trading_engine")
            return {'status': 'failed', 'message': '开仓失败'}
    
    def _record_trade(self, side, size, order_type, action):
        """
        记录交易
        """
        trade_record = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'side': side,
            'size': size,
            'order_type': order_type,
            'action': action,
            'symbol': self.config['symbol']
        }
        
        self.trade_history.append(trade_record)
        enhanced_logger.log_trade(f"{action} {side} {size} {self.config['symbol']}", "trading_engine")
        
        # 只保留最近1000条交易记录
        if len(self.trade_history) > 1000:
            self.trade_history = self.trade_history[-1000:]
    
    def get_trade_summary(self):
        """
        获取交易汇总信息
        
        返回:
            交易汇总数据
        """
        # 获取当前状态
        current_position = self.get_current_position()
        current_price = self.exchange.get_market_price()
        
        # 计算统计信息
        total_trades = len(self.trade_history)
        buy_trades = len([t for t in self.trade_history if t['side'] == 'BUY'])
        sell_trades = len([t for t in self.trade_history if t['side'] == 'SELL'])
        
        # 最近信号
        last_signal = self.signal_history[-1] if self.signal_history else None
        
        return {
            'current_price': current_price,
            'current_position': current_position,
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'last_signal': last_signal,
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def clear_history(self):
        """
        清空历史记录
        """
        self.trade_history = []
        self.signal_history = []
        self._save_history()
        enhanced_logger.log_info("历史记录已清空", "trading_engine")