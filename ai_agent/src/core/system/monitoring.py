#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控与日志系统

提供全面的系统监控功能，包括：
1. 性能监控
2. 资源监控
3. 错误追踪
4. 实时指标收集
5. 告警机制
"""

import time
import psutil
import threading
import logging
import json
import os
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: float = field(default_factory=time.time)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_io: Dict[str, int] = field(default_factory=dict)
    task_count: int = 0
    active_sessions: int = 0
    response_time: float = 0.0
    error_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    metric: str
    threshold: float
    operator: str  # '>', '<', '>=', '<=', '==', '!='
    duration: int  # 持续时间（秒）
    enabled: bool = True
    last_triggered: Optional[float] = None
    
    def check(self, value: float) -> bool:
        """检查是否触发告警"""
        if not self.enabled:
            return False
            
        if self.operator == '>':
            return value > self.threshold
        elif self.operator == '<':
            return value < self.threshold
        elif self.operator == '>=':
            return value >= self.threshold
        elif self.operator == '<=':
            return value <= self.threshold
        elif self.operator == '==':
            return value == self.threshold
        elif self.operator == '!=':
            return value != self.threshold
        return False


class SystemMonitor:
    """系统监控器"""
    
    def __init__(self, monitor_interval: int = 30, metrics_retention: int = 1000):
        """
        初始化系统监控器
        
        Args:
            monitor_interval: 监控间隔（秒）
            metrics_retention: 指标保留数量
        """
        self.monitor_interval = monitor_interval
        self.metrics_retention = metrics_retention
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 指标存储
        self.metrics_history: deque = deque(maxlen=metrics_retention)
        self.current_metrics = PerformanceMetrics()
        
        # 监控状态
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # 告警规则
        self.alert_rules: List[AlertRule] = []
        self.alert_callbacks: List[Callable] = []
        
        # 统计数据
        self.stats = {
            'total_alerts': 0,
            'monitoring_start_time': None,
            'last_update': None
        }
        
        # 初始化默认告警规则
        self._init_default_alert_rules()
    
    def _init_default_alert_rules(self):
        """初始化默认告警规则"""
        default_rules = [
            AlertRule("高CPU使用率", "cpu_usage", 80.0, ">", 60),
            AlertRule("高内存使用率", "memory_usage", 85.0, ">", 60),
            AlertRule("高磁盘使用率", "disk_usage", 90.0, ">", 300),
            AlertRule("高错误率", "error_count", 10, ">", 30),
            AlertRule("响应时间过长", "response_time", 5.0, ">", 60)
        ]
        self.alert_rules.extend(default_rules)
    
    def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            self.logger.warning("监控已在运行中")
            return
        
        self.is_monitoring = True
        self.stats['monitoring_start_time'] = time.time()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("系统监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("系统监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集系统指标
                metrics = self._collect_system_metrics()
                
                # 更新当前指标
                self.current_metrics = metrics
                self.metrics_history.append(metrics)
                
                # 检查告警
                self._check_alerts(metrics)
                
                # 更新统计
                self.stats['last_update'] = time.time()
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                time.sleep(self.monitor_interval)
    
    def _collect_system_metrics(self) -> PerformanceMetrics:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # 网络IO
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            return PerformanceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io
            )
            
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")
            return PerformanceMetrics()
    
    def _check_alerts(self, metrics: PerformanceMetrics):
        """检查告警"""
        current_time = time.time()
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            # 获取指标值
            metric_value = getattr(metrics, rule.metric, None)
            if metric_value is None:
                continue
            
            # 检查是否触发
            if rule.check(metric_value):
                # 检查是否在冷却期内
                if (rule.last_triggered and 
                    current_time - rule.last_triggered < rule.duration):
                    continue
                
                # 触发告警
                self._trigger_alert(rule, metric_value, metrics)
                rule.last_triggered = current_time
    
    def _trigger_alert(self, rule: AlertRule, value: float, metrics: PerformanceMetrics):
        """触发告警"""
        alert_data = {
            'rule_name': rule.name,
            'metric': rule.metric,
            'value': value,
            'threshold': rule.threshold,
            'timestamp': time.time(),
            'metrics': metrics.to_dict()
        }
        
        self.stats['total_alerts'] += 1
        
        # 记录告警日志
        self.logger.warning(f"告警触发: {rule.name} - {rule.metric}={value} {rule.operator} {rule.threshold}")
        
        # 调用告警回调
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                self.logger.error(f"告警回调执行失败: {e}")
    
    def add_alert_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.alert_rules.append(rule)
        self.logger.info(f"添加告警规则: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str) -> bool:
        """移除告警规则"""
        for i, rule in enumerate(self.alert_rules):
            if rule.name == rule_name:
                del self.alert_rules[i]
                self.logger.info(f"移除告警规则: {rule_name}")
                return True
        return False
    
    def add_alert_callback(self, callback: Callable):
        """添加告警回调"""
        self.alert_callbacks.append(callback)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        return self.current_metrics.to_dict()
    
    def get_metrics_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取指标历史"""
        history = list(self.metrics_history)
        if limit:
            history = history[-limit:]
        return [m.to_dict() for m in history]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        stats['is_monitoring'] = self.is_monitoring
        stats['metrics_count'] = len(self.metrics_history)
        stats['alert_rules_count'] = len(self.alert_rules)
        return stats


class ErrorTracker:
    """错误追踪器"""
    
    def __init__(self, max_errors: int = 1000):
        """
        初始化错误追踪器
        
        Args:
            max_errors: 最大错误记录数
        """
        self.max_errors = max_errors
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 错误存储
        self.errors: deque = deque(maxlen=max_errors)
        self.error_counts = defaultdict(int)
        self.error_stats = {
            'total_errors': 0,
            'last_error_time': None,
            'error_rate': 0.0
        }
        
        # 错误分类
        self.error_categories = {
            'system': 0,
            'network': 0,
            'analysis': 0,
            'validation': 0,
            'unknown': 0
        }
    
    def track_error(self, error: Exception, context: Optional[Dict[str, Any]] = None,
                   category: str = 'unknown'):
        """追踪错误"""
        error_data = {
            'timestamp': time.time(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'category': category,
            'context': context or {},
            'traceback': None
        }
        
        # 获取堆栈跟踪
        import traceback
        error_data['traceback'] = traceback.format_exc()
        
        # 存储错误
        self.errors.append(error_data)
        
        # 更新统计
        self.error_counts[error_data['error_type']] += 1
        self.error_categories[category] += 1
        self.error_stats['total_errors'] += 1
        self.error_stats['last_error_time'] = time.time()
        
        # 计算错误率（最近1小时）
        self._calculate_error_rate()
        
        # 记录日志
        self.logger.error(f"错误追踪: {category} - {error_data['error_type']}: {error_data['error_message']}")
    
    def _calculate_error_rate(self):
        """计算错误率"""
        current_time = time.time()
        hour_ago = current_time - 3600
        
        recent_errors = [e for e in self.errors if e['timestamp'] > hour_ago]
        self.error_stats['error_rate'] = len(recent_errors) / 3600  # 每秒错误数
    
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        return {
            'stats': self.error_stats.copy(),
            'categories': dict(self.error_categories),
            'top_errors': dict(sorted(self.error_counts.items(), 
                                    key=lambda x: x[1], reverse=True)[:10])
        }
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近错误"""
        return list(self.errors)[-limit:]
    
    def clear_errors(self):
        """清空错误记录"""
        self.errors.clear()
        self.error_counts.clear()
        self.error_categories = {k: 0 for k in self.error_categories}
        self.error_stats = {
            'total_errors': 0,
            'last_error_time': None,
            'error_rate': 0.0
        }
        self.logger.info("错误记录已清空")


class MonitoringManager:
    """监控管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化监控管理器
        
        Args:
            config: 监控配置
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化组件
        self.system_monitor = SystemMonitor(
            monitor_interval=self.config.get('monitor_interval', 30),
            metrics_retention=self.config.get('metrics_retention', 1000)
        )
        
        self.error_tracker = ErrorTracker(
            max_errors=self.config.get('max_errors', 1000)
        )
        
        # 任务监控
        self.task_metrics = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'average_duration': 0.0,
            'active_tasks': 0
        }
        
        # 会话监控
        self.session_metrics = {
            'total_sessions': 0,
            'active_sessions': 0,
            'average_session_duration': 0.0
        }
        
        # 设置告警回调
        self.system_monitor.add_alert_callback(self._handle_alert)
    
    def start(self):
        """启动监控"""
        self.system_monitor.start_monitoring()
        self.logger.info("监控管理器已启动")
    
    def stop(self):
        """停止监控"""
        self.system_monitor.stop_monitoring()
        self.logger.info("监控管理器已停止")
    
    def _handle_alert(self, alert_data: Dict[str, Any]):
        """处理告警"""
        # 这里可以实现告警通知逻辑
        # 例如：发送邮件、短信、Webhook等
        self.logger.critical(f"系统告警: {alert_data['rule_name']} - {alert_data['metric']}={alert_data['value']}")
    
    def record_task_start(self, task_id: str):
        """记录任务开始"""
        self.task_metrics['total_tasks'] += 1
        self.task_metrics['active_tasks'] += 1
    
    def record_task_complete(self, task_id: str, duration: float, success: bool = True):
        """记录任务完成"""
        self.task_metrics['active_tasks'] = max(0, self.task_metrics['active_tasks'] - 1)
        
        if success:
            self.task_metrics['completed_tasks'] += 1
        else:
            self.task_metrics['failed_tasks'] += 1
        
        # 更新平均持续时间
        total_completed = self.task_metrics['completed_tasks'] + self.task_metrics['failed_tasks']
        if total_completed > 0:
            current_avg = self.task_metrics['average_duration']
            self.task_metrics['average_duration'] = (
                (current_avg * (total_completed - 1) + duration) / total_completed
            )
    
    def record_session_start(self, session_id: str):
        """记录会话开始"""
        self.session_metrics['total_sessions'] += 1
        self.session_metrics['active_sessions'] += 1
    
    def record_session_end(self, session_id: str, duration: float):
        """记录会话结束"""
        self.session_metrics['active_sessions'] = max(0, self.session_metrics['active_sessions'] - 1)
        
        # 更新平均会话持续时间
        total_sessions = self.session_metrics['total_sessions']
        if total_sessions > 0:
            current_avg = self.session_metrics['average_session_duration']
            self.session_metrics['average_session_duration'] = (
                (current_avg * (total_sessions - 1) + duration) / total_sessions
            )
    
    def track_error(self, error: Exception, context: Optional[Dict[str, Any]] = None,
                   category: str = 'unknown'):
        """追踪错误"""
        self.error_tracker.track_error(error, context, category)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取监控面板数据"""
        return {
            'system_metrics': self.system_monitor.get_current_metrics(),
            'system_stats': self.system_monitor.get_stats(),
            'task_metrics': self.task_metrics.copy(),
            'session_metrics': self.session_metrics.copy(),
            'error_summary': self.error_tracker.get_error_summary(),
            'timestamp': time.time()
        }
    
    def export_metrics(self, filepath: str):
        """导出指标数据"""
        try:
            data = {
                'export_time': time.time(),
                'system_metrics_history': self.system_monitor.get_metrics_history(),
                'task_metrics': self.task_metrics,
                'session_metrics': self.session_metrics,
                'error_summary': self.error_tracker.get_error_summary(),
                'recent_errors': self.error_tracker.get_recent_errors(100)
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"指标数据已导出到: {filepath}")
            
        except Exception as e:
            self.logger.error(f"导出指标数据失败: {e}")


# 全局监控实例
_monitoring_manager: Optional[MonitoringManager] = None


def get_monitoring_manager() -> MonitoringManager:
    """获取全局监控管理器实例"""
    global _monitoring_manager
    if _monitoring_manager is None:
        _monitoring_manager = MonitoringManager()
    return _monitoring_manager


def init_monitoring(config: Optional[Dict[str, Any]] = None) -> MonitoringManager:
    """初始化监控系统"""
    global _monitoring_manager
    _monitoring_manager = MonitoringManager(config)
    _monitoring_manager.start()
    return _monitoring_manager