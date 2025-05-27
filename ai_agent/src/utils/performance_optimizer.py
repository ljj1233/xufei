#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化器

提供系统性能优化功能，包括：
1. 算法优化
2. 资源管理
3. 内存优化
4. 并发处理优化
5. 数据库查询优化
6. 网络请求优化
7. 性能监控和分析
"""

import time
import psutil
import threading
import asyncio
import gc
import sys
import os
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps, lru_cache
import logging
import weakref
import multiprocessing
from pathlib import Path
import json


@dataclass
class PerformanceMetrics:
    """性能指标"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_io: Dict[str, float] = field(default_factory=dict)
    network_io: Dict[str, float] = field(default_factory=dict)
    response_time: float = 0.0
    throughput: float = 0.0
    error_rate: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_io': self.disk_io,
            'network_io': self.network_io,
            'response_time': self.response_time,
            'throughput': self.throughput,
            'error_rate': self.error_rate,
            'timestamp': self.timestamp
        }


class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self, interval: float = 1.0, history_size: int = 1000):
        """
        初始化资源监控器
        
        Args:
            interval: 监控间隔（秒）
            history_size: 历史记录大小
        """
        self.interval = interval
        self.history_size = history_size
        self.metrics_history = deque(maxlen=history_size)
        
        self._monitoring = False
        self._monitor_thread = None
        self._lock = threading.Lock()
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def start_monitoring(self):
        """开始监控"""
        with self._lock:
            if not self._monitoring:
                self._monitoring = True
                self._monitor_thread = threading.Thread(
                    target=self._monitor_loop,
                    daemon=True
                )
                self._monitor_thread.start()
                self.logger.info("资源监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        with self._lock:
            self._monitoring = False
            if self._monitor_thread:
                self._monitor_thread.join(timeout=5)
                self._monitor_thread = None
            self.logger.info("资源监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self._monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f"监控过程中发生错误: {e}")
                time.sleep(self.interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        # CPU使用率
        cpu_usage = psutil.cpu_percent(interval=None)
        
        # 内存使用率
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # 磁盘IO
        disk_io = psutil.disk_io_counters()
        disk_metrics = {
            'read_bytes': disk_io.read_bytes if disk_io else 0,
            'write_bytes': disk_io.write_bytes if disk_io else 0,
            'read_count': disk_io.read_count if disk_io else 0,
            'write_count': disk_io.write_count if disk_io else 0
        }
        
        # 网络IO
        network_io = psutil.net_io_counters()
        network_metrics = {
            'bytes_sent': network_io.bytes_sent if network_io else 0,
            'bytes_recv': network_io.bytes_recv if network_io else 0,
            'packets_sent': network_io.packets_sent if network_io else 0,
            'packets_recv': network_io.packets_recv if network_io else 0
        }
        
        return PerformanceMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_io=disk_metrics,
            network_io=network_metrics
        )
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前性能指标"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_average_metrics(self, duration: int = 60) -> Optional[PerformanceMetrics]:
        """获取平均性能指标"""
        if not self.metrics_history:
            return None
        
        # 获取指定时间内的指标
        current_time = time.time()
        recent_metrics = [
            m for m in self.metrics_history
            if current_time - m.timestamp <= duration
        ]
        
        if not recent_metrics:
            return None
        
        # 计算平均值
        avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
        avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
        
        return PerformanceMetrics(
            cpu_usage=avg_cpu,
            memory_usage=avg_memory,
            response_time=avg_response_time
        )


class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._weak_refs = weakref.WeakSet()
    
    def optimize_memory(self):
        """优化内存使用"""
        # 强制垃圾回收
        collected = gc.collect()
        self.logger.info(f"垃圾回收释放了 {collected} 个对象")
        
        # 获取内存使用情况
        memory_info = psutil.Process().memory_info()
        self.logger.info(f"当前内存使用: {memory_info.rss / 1024 / 1024:.2f} MB")
        
        return {
            'collected_objects': collected,
            'memory_usage_mb': memory_info.rss / 1024 / 1024
        }
    
    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': memory_percent,
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    
    def register_for_cleanup(self, obj):
        """注册对象以便清理"""
        self._weak_refs.add(obj)
    
    def cleanup_registered_objects(self):
        """清理注册的对象"""
        # WeakSet会自动清理已被垃圾回收的对象
        remaining = len(self._weak_refs)
        self.logger.info(f"剩余注册对象: {remaining}")
        return remaining


class ConcurrencyOptimizer:
    """并发优化器"""
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        初始化并发优化器
        
        Args:
            max_workers: 最大工作线程数
        """
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=min(4, os.cpu_count() or 1))
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 任务统计
        self.task_stats = {
            'submitted': 0,
            'completed': 0,
            'failed': 0,
            'total_time': 0.0
        }
    
    def submit_task(self, func: Callable, *args, use_process: bool = False, **kwargs):
        """提交任务"""
        self.task_stats['submitted'] += 1
        
        if use_process:
            future = self.process_pool.submit(func, *args, **kwargs)
        else:
            future = self.thread_pool.submit(func, *args, **kwargs)
        
        # 添加回调来更新统计
        future.add_done_callback(self._task_done_callback)
        
        return future
    
    def _task_done_callback(self, future):
        """任务完成回调"""
        try:
            future.result()  # 这会抛出异常（如果有的话）
            self.task_stats['completed'] += 1
        except Exception as e:
            self.task_stats['failed'] += 1
            self.logger.error(f"任务执行失败: {e}")
    
    def batch_execute(self, func: Callable, items: List[Any], 
                     batch_size: int = 10, use_process: bool = False) -> List[Any]:
        """批量执行任务"""
        results = []
        futures = []
        
        # 分批提交任务
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            future = self.submit_task(func, batch, use_process=use_process)
            futures.append(future)
        
        # 收集结果
        for future in futures:
            try:
                result = future.result(timeout=30)
                if isinstance(result, list):
                    results.extend(result)
                else:
                    results.append(result)
            except Exception as e:
                self.logger.error(f"批量任务执行失败: {e}")
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = 0.0
        if self.task_stats['submitted'] > 0:
            success_rate = self.task_stats['completed'] / self.task_stats['submitted']
        
        return {
            **self.task_stats,
            'success_rate': success_rate,
            'max_workers': self.max_workers
        }
    
    def shutdown(self, wait: bool = True):
        """关闭线程池"""
        self.thread_pool.shutdown(wait=wait)
        self.process_pool.shutdown(wait=wait)


class AlgorithmOptimizer:
    """算法优化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._cache = {}
    
    def memoize(self, func: Callable) -> Callable:
        """记忆化装饰器"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 创建缓存键
            key = str(args) + str(sorted(kwargs.items()))
            
            if key in self._cache:
                return self._cache[key]
            
            result = func(*args, **kwargs)
            self._cache[key] = result
            return result
        
        return wrapper
    
    def time_function(self, func: Callable) -> Callable:
        """函数计时装饰器"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                self.logger.info(f"函数 {func.__name__} 执行时间: {execution_time:.4f}秒")
        
        return wrapper
    
    def optimize_data_structure(self, data: List[Any], 
                              operation: str = 'search') -> Union[List, Dict, set]:
        """优化数据结构"""
        if operation == 'search':
            # 对于搜索操作，使用集合
            return set(data)
        elif operation == 'lookup':
            # 对于查找操作，使用字典
            if isinstance(data[0], (tuple, list)) and len(data[0]) >= 2:
                return {item[0]: item[1] for item in data}
            else:
                return {i: item for i, item in enumerate(data)}
        else:
            # 默认返回列表
            return list(data)
    
    def batch_process(self, items: List[Any], func: Callable, 
                     batch_size: int = 100) -> List[Any]:
        """批量处理"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = func(batch)
            
            if isinstance(batch_results, list):
                results.extend(batch_results)
            else:
                results.append(batch_results)
        
        return results
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        self.logger.info("算法缓存已清空")


class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.query_cache = {}
        self.query_stats = defaultdict(lambda: {'count': 0, 'total_time': 0.0})
    
    def cache_query_result(self, query: str, result: Any, ttl: int = 300):
        """缓存查询结果"""
        cache_key = hash(query)
        self.query_cache[cache_key] = {
            'result': result,
            'timestamp': time.time(),
            'ttl': ttl
        }
    
    def get_cached_result(self, query: str) -> Optional[Any]:
        """获取缓存的查询结果"""
        cache_key = hash(query)
        
        if cache_key in self.query_cache:
            cached = self.query_cache[cache_key]
            
            # 检查是否过期
            if time.time() - cached['timestamp'] <= cached['ttl']:
                return cached['result']
            else:
                # 删除过期缓存
                del self.query_cache[cache_key]
        
        return None
    
    def record_query_stats(self, query: str, execution_time: float):
        """记录查询统计"""
        self.query_stats[query]['count'] += 1
        self.query_stats[query]['total_time'] += execution_time
    
    def get_slow_queries(self, threshold: float = 1.0) -> List[Tuple[str, Dict]]:
        """获取慢查询"""
        slow_queries = []
        
        for query, stats in self.query_stats.items():
            avg_time = stats['total_time'] / stats['count']
            if avg_time > threshold:
                slow_queries.append((query, {
                    'avg_time': avg_time,
                    'count': stats['count'],
                    'total_time': stats['total_time']
                }))
        
        # 按平均执行时间排序
        slow_queries.sort(key=lambda x: x[1]['avg_time'], reverse=True)
        
        return slow_queries
    
    def optimize_query(self, query: str) -> str:
        """优化查询语句"""
        # 这里可以实现查询优化逻辑
        # 例如：添加索引建议、重写查询等
        optimized = query.strip()
        
        # 简单的优化示例
        if 'SELECT *' in optimized:
            self.logger.warning("建议避免使用 SELECT *，明确指定需要的列")
        
        return optimized


class PerformanceOptimizer:
    """性能优化器主类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化性能优化器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化各个优化器
        self.resource_monitor = ResourceMonitor(
            interval=self.config.get('monitor_interval', 1.0),
            history_size=self.config.get('history_size', 1000)
        )
        
        self.memory_optimizer = MemoryOptimizer()
        
        self.concurrency_optimizer = ConcurrencyOptimizer(
            max_workers=self.config.get('max_workers')
        )
        
        self.algorithm_optimizer = AlgorithmOptimizer()
        self.database_optimizer = DatabaseOptimizer()
        
        # 优化统计
        self.optimization_stats = {
            'memory_optimizations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_optimizations': 0
        }
    
    def start_monitoring(self):
        """开始性能监控"""
        self.resource_monitor.start_monitoring()
        self.logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.resource_monitor.stop_monitoring()
        self.logger.info("性能监控已停止")
    
    def optimize_system(self) -> Dict[str, Any]:
        """优化系统性能"""
        results = {}
        
        # 内存优化
        memory_result = self.memory_optimizer.optimize_memory()
        results['memory'] = memory_result
        self.optimization_stats['memory_optimizations'] += 1
        
        # 清理算法缓存
        self.algorithm_optimizer.clear_cache()
        results['algorithm_cache_cleared'] = True
        
        # 获取当前性能指标
        current_metrics = self.resource_monitor.get_current_metrics()
        if current_metrics:
            results['current_metrics'] = current_metrics.to_dict()
        
        self.optimization_stats['total_optimizations'] += 1
        
        self.logger.info(f"系统优化完成: {results}")
        return results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'current_metrics': None,
            'average_metrics': None,
            'memory_usage': self.memory_optimizer.get_memory_usage(),
            'concurrency_stats': self.concurrency_optimizer.get_stats(),
            'optimization_stats': self.optimization_stats,
            'slow_queries': self.database_optimizer.get_slow_queries()
        }
        
        # 获取性能指标
        current_metrics = self.resource_monitor.get_current_metrics()
        if current_metrics:
            report['current_metrics'] = current_metrics.to_dict()
        
        average_metrics = self.resource_monitor.get_average_metrics()
        if average_metrics:
            report['average_metrics'] = average_metrics.to_dict()
        
        return report
    
    def export_performance_data(self, file_path: str):
        """导出性能数据"""
        report = self.get_performance_report()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"性能数据已导出到: {file_path}")
    
    def shutdown(self):
        """关闭优化器"""
        self.stop_monitoring()
        self.concurrency_optimizer.shutdown()
        self.logger.info("性能优化器已关闭")


# 全局性能优化器实例
_performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """获取全局性能优化器实例"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer


def init_performance_optimizer(config: Optional[Dict[str, Any]] = None) -> PerformanceOptimizer:
    """初始化性能优化器"""
    global _performance_optimizer
    _performance_optimizer = PerformanceOptimizer(config)
    return _performance_optimizer