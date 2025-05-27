#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强日志系统

提供结构化的日志记录功能，包括：
1. 多级别日志记录
2. 结构化日志格式
3. 日志轮转和归档
4. 性能日志记录
5. 错误日志聚合
6. 日志分析和查询
"""

import logging
import logging.handlers
import json
import time
import os
import sys
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import threading
from contextlib import contextmanager


@dataclass
class LogEntry:
    """日志条目数据类"""
    timestamp: float = field(default_factory=time.time)
    level: str = "INFO"
    logger_name: str = ""
    message: str = ""
    module: str = ""
    function: str = ""
    line_number: int = 0
    thread_id: int = 0
    session_id: Optional[str] = None
    task_id: Optional[str] = None
    user_id: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        # 创建日志条目
        log_entry = LogEntry(
            timestamp=record.created,
            level=record.levelname,
            logger_name=record.name,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line_number=record.lineno,
            thread_id=record.thread
        )
        
        # 添加额外数据
        if self.include_extra:
            extra_data = {}
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                              'pathname', 'filename', 'module', 'lineno', 
                              'funcName', 'created', 'msecs', 'relativeCreated',
                              'thread', 'threadName', 'processName', 'process',
                              'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                    extra_data[key] = value
            
            if extra_data:
                log_entry.extra_data = extra_data
        
        # 添加异常信息
        if record.exc_info:
            log_entry.extra_data['exception'] = self.formatException(record.exc_info)
        
        return log_entry.to_json()


class ColoredConsoleFormatter(logging.Formatter):
    """彩色控制台格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'       # 重置
    }
    
    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        if self.use_colors:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
        else:
            color = reset = ''
        
        # 格式化时间
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建日志消息
        message = (
            f"{color}[{timestamp}] {record.levelname:8} "
            f"{record.name}:{record.lineno} - {record.getMessage()}{reset}"
        )
        
        # 添加异常信息
        if record.exc_info:
            message += '\n' + self.formatException(record.exc_info)
        
        return message


class PerformanceLogger:
    """性能日志记录器"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.performance_data = deque(maxlen=1000)
        self.active_timers = {}
    
    @contextmanager
    def timer(self, operation: str, **kwargs):
        """性能计时上下文管理器"""
        start_time = time.time()
        timer_id = f"{operation}_{threading.get_ident()}_{start_time}"
        
        try:
            self.active_timers[timer_id] = {
                'operation': operation,
                'start_time': start_time,
                'metadata': kwargs
            }
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            # 记录性能数据
            perf_data = {
                'operation': operation,
                'duration': duration,
                'start_time': start_time,
                'end_time': end_time,
                'metadata': kwargs
            }
            
            self.performance_data.append(perf_data)
            
            # 记录日志
            self.logger.info(
                f"性能统计: {operation} 耗时 {duration:.3f}s",
                extra={
                    'performance': perf_data,
                    'operation_type': 'performance'
                }
            )
            
            # 清理计时器
            self.active_timers.pop(timer_id, None)
    
    def log_performance(self, operation: str, duration: float, **metadata):
        """直接记录性能数据"""
        perf_data = {
            'operation': operation,
            'duration': duration,
            'timestamp': time.time(),
            'metadata': metadata
        }
        
        self.performance_data.append(perf_data)
        
        self.logger.info(
            f"性能统计: {operation} 耗时 {duration:.3f}s",
            extra={
                'performance': perf_data,
                'operation_type': 'performance'
            }
        )
    
    def get_performance_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """获取性能统计"""
        data = list(self.performance_data)
        
        if operation:
            data = [d for d in data if d['operation'] == operation]
        
        if not data:
            return {}
        
        durations = [d['duration'] for d in data]
        
        return {
            'count': len(data),
            'total_duration': sum(durations),
            'average_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'operations': list(set(d['operation'] for d in data))
        }


class LogAnalyzer:
    """日志分析器"""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def analyze_errors(self, hours: int = 24) -> Dict[str, Any]:
        """分析错误日志"""
        cutoff_time = time.time() - (hours * 3600)
        error_counts = defaultdict(int)
        error_details = []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_data = json.loads(line.strip())
                        
                        if (log_data.get('timestamp', 0) > cutoff_time and 
                            log_data.get('level') in ['ERROR', 'CRITICAL']):
                            
                            error_type = log_data.get('extra_data', {}).get('exception', 'Unknown')
                            if error_type == 'Unknown':
                                error_type = log_data.get('message', 'Unknown Error')
                            
                            error_counts[error_type] += 1
                            error_details.append(log_data)
                    
                    except json.JSONDecodeError:
                        continue
        
        except FileNotFoundError:
            self.logger.warning(f"日志文件不存在: {self.log_file}")
            return {}
        
        return {
            'total_errors': sum(error_counts.values()),
            'error_types': dict(error_counts),
            'top_errors': sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'recent_errors': error_details[-50:]  # 最近50个错误
        }
    
    def analyze_performance(self, hours: int = 24) -> Dict[str, Any]:
        """分析性能日志"""
        cutoff_time = time.time() - (hours * 3600)
        performance_data = []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_data = json.loads(line.strip())
                        
                        if (log_data.get('timestamp', 0) > cutoff_time and 
                            log_data.get('extra_data', {}).get('operation_type') == 'performance'):
                            
                            perf_info = log_data.get('extra_data', {}).get('performance', {})
                            if perf_info:
                                performance_data.append(perf_info)
                    
                    except json.JSONDecodeError:
                        continue
        
        except FileNotFoundError:
            self.logger.warning(f"日志文件不存在: {self.log_file}")
            return {}
        
        if not performance_data:
            return {}
        
        # 按操作分组
        operations = defaultdict(list)
        for data in performance_data:
            operations[data.get('operation', 'unknown')].append(data['duration'])
        
        # 计算统计信息
        stats = {}
        for operation, durations in operations.items():
            stats[operation] = {
                'count': len(durations),
                'total': sum(durations),
                'average': sum(durations) / len(durations),
                'min': min(durations),
                'max': max(durations)
            }
        
        return {
            'total_operations': len(performance_data),
            'operation_stats': stats,
            'slowest_operations': sorted(
                [(op, stat['max']) for op, stat in stats.items()],
                key=lambda x: x[1], reverse=True
            )[:10]
        }


class LoggingSystem:
    """日志系统管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化日志系统
        
        Args:
            config: 日志配置
        """
        self.config = config or {}
        self.loggers = {}
        self.performance_loggers = {}
        self.log_dir = Path(self.config.get('log_dir', './logs'))
        self.log_dir.mkdir(exist_ok=True)
        
        # 默认配置
        self.default_config = {
            'level': 'INFO',
            'format': 'structured',  # 'structured' or 'colored'
            'file_logging': True,
            'console_logging': True,
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5,
            'encoding': 'utf-8'
        }
        
        # 合并配置
        self.config = {**self.default_config, **self.config}
        
        # 设置根日志记录器
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """设置根日志记录器"""
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config['level'].upper()))
        
        # 清除现有处理器
        root_logger.handlers.clear()
        
        # 文件日志处理器
        if self.config['file_logging']:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=self.log_dir / 'app.log',
                maxBytes=self.config['max_file_size'],
                backupCount=self.config['backup_count'],
                encoding=self.config['encoding']
            )
            
            if self.config['format'] == 'structured':
                file_handler.setFormatter(StructuredFormatter())
            else:
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
            
            root_logger.addHandler(file_handler)
        
        # 控制台日志处理器
        if self.config['console_logging']:
            console_handler = logging.StreamHandler()
            
            if self.config['format'] == 'colored':
                console_handler.setFormatter(ColoredConsoleFormatter())
            else:
                console_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
            
            root_logger.addHandler(console_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取日志记录器"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
            
            # 创建性能日志记录器
            self.performance_loggers[name] = PerformanceLogger(logger)
        
        return self.loggers[name]
    
    def get_performance_logger(self, name: str) -> PerformanceLogger:
        """获取性能日志记录器"""
        if name not in self.performance_loggers:
            self.get_logger(name)  # 确保日志记录器存在
        
        return self.performance_loggers[name]
    
    def create_module_logger(self, module_name: str, 
                           session_id: Optional[str] = None,
                           task_id: Optional[str] = None,
                           user_id: Optional[str] = None) -> logging.Logger:
        """创建模块专用日志记录器"""
        logger = self.get_logger(module_name)
        
        # 创建适配器以添加上下文信息
        class ContextAdapter(logging.LoggerAdapter):
            def process(self, msg, kwargs):
                extra = kwargs.get('extra', {})
                if session_id:
                    extra['session_id'] = session_id
                if task_id:
                    extra['task_id'] = task_id
                if user_id:
                    extra['user_id'] = user_id
                kwargs['extra'] = extra
                return msg, kwargs
        
        return ContextAdapter(logger, {})
    
    def setup_error_logging(self):
        """设置错误日志记录"""
        error_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / 'errors.log',
            maxBytes=self.config['max_file_size'],
            backupCount=self.config['backup_count'],
            encoding=self.config['encoding']
        )
        
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        
        # 添加到根日志记录器
        logging.getLogger().addHandler(error_handler)
    
    def setup_performance_logging(self):
        """设置性能日志记录"""
        perf_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / 'performance.log',
            maxBytes=self.config['max_file_size'],
            backupCount=self.config['backup_count'],
            encoding=self.config['encoding']
        )
        
        perf_handler.setFormatter(StructuredFormatter())
        
        # 创建性能日志记录器
        perf_logger = logging.getLogger('performance')
        perf_logger.addHandler(perf_handler)
        perf_logger.setLevel(logging.INFO)
    
    def get_log_analyzer(self, log_type: str = 'app') -> LogAnalyzer:
        """获取日志分析器"""
        log_file = self.log_dir / f'{log_type}.log'
        return LogAnalyzer(str(log_file))
    
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志文件"""
        cutoff_time = time.time() - (days * 24 * 3600)
        
        for log_file in self.log_dir.glob('*.log*'):
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    logging.info(f"删除旧日志文件: {log_file}")
            except Exception as e:
                logging.error(f"删除日志文件失败 {log_file}: {e}")
    
    def get_log_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        stats = {
            'log_dir': str(self.log_dir),
            'config': self.config,
            'loggers_count': len(self.loggers),
            'log_files': []
        }
        
        # 统计日志文件
        for log_file in self.log_dir.glob('*.log'):
            try:
                file_stat = log_file.stat()
                stats['log_files'].append({
                    'name': log_file.name,
                    'size': file_stat.st_size,
                    'modified': file_stat.st_mtime
                })
            except Exception:
                continue
        
        return stats


# 全局日志系统实例
_logging_system: Optional[LoggingSystem] = None


def get_logging_system() -> LoggingSystem:
    """获取全局日志系统实例"""
    global _logging_system
    if _logging_system is None:
        _logging_system = LoggingSystem()
    return _logging_system


def init_logging(config: Optional[Dict[str, Any]] = None) -> LoggingSystem:
    """初始化日志系统"""
    global _logging_system
    _logging_system = LoggingSystem(config)
    _logging_system.setup_error_logging()
    _logging_system.setup_performance_logging()
    return _logging_system


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器的便捷函数"""
    return get_logging_system().get_logger(name)


def get_performance_logger(name: str) -> PerformanceLogger:
    """获取性能日志记录器的便捷函数"""
    return get_logging_system().get_performance_logger(name)