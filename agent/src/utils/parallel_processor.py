# -*- coding: utf-8 -*-
"""
并行处理器

实现任务的并行执行、资源管理和负载均衡
"""

import asyncio
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Awaitable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
import logging
from queue import Queue, PriorityQueue
import multiprocessing as mp

from .state import Task, TaskType, TaskPriority, TaskStatus, AnalysisResult


class ProcessorType(Enum):
    """处理器类型"""
    THREAD = "thread"
    PROCESS = "process"
    ASYNC = "async"


@dataclass
class ProcessorConfig:
    """处理器配置"""
    max_workers: int = 4
    processor_type: ProcessorType = ProcessorType.THREAD
    timeout: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0
    enable_load_balancing: bool = True
    resource_limits: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.resource_limits is None:
            self.resource_limits = {
                "memory_limit_mb": 1024,
                "cpu_limit_percent": 80
            }


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    retry_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._monitoring = False
        self._stats = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "active_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0
        }
    
    def start_monitoring(self):
        """开始监控"""
        self._monitoring = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()
    
    def stop_monitoring(self):
        """停止监控"""
        self._monitoring = False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._stats.copy()
    
    def is_resource_available(self, limits: Dict[str, Any]) -> bool:
        """检查资源是否可用"""
        try:
            import psutil
            
            # 检查CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent > limits.get("cpu_limit_percent", 80):
                return False
            
            # 检查内存使用
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024
            if memory_mb > limits.get("memory_limit_mb", 1024):
                return False
            
            return True
            
        except ImportError:
            self.logger.warning("psutil未安装，无法监控资源")
            return True
        except Exception as e:
            self.logger.error(f"资源检查失败: {e}")
            return True
    
    def _monitor_loop(self):
        """监控循环"""
        try:
            import psutil
            
            while self._monitoring:
                try:
                    # 更新CPU使用率
                    self._stats["cpu_usage"] = psutil.cpu_percent(interval=1.0)
                    
                    # 更新内存使用
                    memory = psutil.virtual_memory()
                    self._stats["memory_usage"] = memory.percent
                    
                    time.sleep(5)  # 每5秒更新一次
                    
                except Exception as e:
                    self.logger.error(f"监控更新失败: {e}")
                    time.sleep(10)
                    
        except ImportError:
            self.logger.warning("psutil未安装，资源监控不可用")


class TaskQueue:
    """任务队列"""
    
    def __init__(self, enable_priority: bool = True):
        self.enable_priority = enable_priority
        if enable_priority:
            self._queue = PriorityQueue()
        else:
            self._queue = Queue()
        
        self._task_map = {}  # 任务ID到任务的映射
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def put(self, task: Task):
        """添加任务"""
        if self.enable_priority:
            # 优先级越高，数值越小
            priority = self._get_priority_value(task.priority)
            self._queue.put((priority, time.time(), task))
        else:
            self._queue.put(task)
        
        self._task_map[task.id] = task
        self.logger.debug(f"任务已添加到队列: {task.id}")
    
    def get(self, timeout: Optional[float] = None) -> Optional[Task]:
        """获取任务"""
        try:
            if self.enable_priority:
                _, _, task = self._queue.get(timeout=timeout)
            else:
                task = self._queue.get(timeout=timeout)
            
            return task
            
        except:
            return None
    
    def task_done(self):
        """标记任务完成"""
        self._queue.task_done()
    
    def empty(self) -> bool:
        """检查队列是否为空"""
        return self._queue.empty()
    
    def qsize(self) -> int:
        """获取队列大小"""
        return self._queue.qsize()
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        return self._task_map.get(task_id)
    
    def remove_task(self, task_id: str):
        """移除任务"""
        self._task_map.pop(task_id, None)
    
    def _get_priority_value(self, priority: TaskPriority) -> int:
        """获取优先级数值"""
        priority_map = {
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        return priority_map.get(priority, 2)


class ParallelProcessor:
    """并行处理器
    
    支持多线程、多进程和异步处理
    """
    
    def __init__(self, config: ProcessorConfig = None):
        """初始化并行处理器
        
        Args:
            config: 处理器配置
        """
        self.config = config or ProcessorConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 任务队列
        self.task_queue = TaskQueue(enable_priority=True)
        
        # 执行器
        self._executor = None
        self._async_loop = None
        
        # 资源监控
        self.resource_monitor = ResourceMonitor()
        
        # 状态跟踪
        self._running = False
        self._workers = []
        self._results = {}
        self._task_futures = {}
        
        # 统计信息
        self._stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_execution_time": 0.0,
            "total_execution_time": 0.0
        }
        
        self._initialize_executor()
    
    def _initialize_executor(self):
        """初始化执行器"""
        if self.config.processor_type == ProcessorType.THREAD:
            self._executor = ThreadPoolExecutor(
                max_workers=self.config.max_workers
            )
        elif self.config.processor_type == ProcessorType.PROCESS:
            self._executor = ProcessPoolExecutor(
                max_workers=self.config.max_workers
            )
        elif self.config.processor_type == ProcessorType.ASYNC:
            try:
                self._async_loop = asyncio.new_event_loop()
                threading.Thread(
                    target=self._run_async_loop, 
                    daemon=True
                ).start()
            except Exception as e:
                self.logger.error(f"异步循环初始化失败: {e}")
                # 回退到线程池
                self._executor = ThreadPoolExecutor(
                    max_workers=self.config.max_workers
                )
    
    def start(self):
        """启动处理器"""
        if self._running:
            return
        
        self._running = True
        self.resource_monitor.start_monitoring()
        
        # 启动工作线程
        for i in range(self.config.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"ParallelWorker-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)
        
        self.logger.info(f"并行处理器已启动，工作线程数: {self.config.max_workers}")
    
    def stop(self):
        """停止处理器"""
        if not self._running:
            return
        
        self._running = False
        self.resource_monitor.stop_monitoring()
        
        # 关闭执行器
        if self._executor:
            self._executor.shutdown(wait=True)
        
        if self._async_loop:
            self._async_loop.call_soon_threadsafe(self._async_loop.stop)
        
        self.logger.info("并行处理器已停止")
    
    def submit_task(self, task: Task, 
                   processor_func: Callable[[Task], Any]) -> str:
        """提交任务
        
        Args:
            task: 要执行的任务
            processor_func: 处理函数
            
        Returns:
            str: 任务ID
        """
        # 检查资源
        if (self.config.enable_load_balancing and 
            not self.resource_monitor.is_resource_available(self.config.resource_limits)):
            self.logger.warning(f"资源不足，任务延迟执行: {task.id}")
            time.sleep(1)  # 等待资源释放
        
        # 添加处理函数到任务元数据
        task.metadata["processor_func"] = processor_func
        
        # 添加到队列
        self.task_queue.put(task)
        self._stats["total_tasks"] += 1
        
        self.logger.debug(f"任务已提交: {task.id}")
        return task.id
    
    def submit_async_task(self, task: Task, 
                         async_func: Callable[[Task], Awaitable[Any]]) -> str:
        """提交异步任务
        
        Args:
            task: 要执行的任务
            async_func: 异步处理函数
            
        Returns:
            str: 任务ID
        """
        if not self._async_loop:
            raise RuntimeError("异步循环未初始化")
        
        # 添加异步函数到任务元数据
        task.metadata["async_func"] = async_func
        task.metadata["is_async"] = True
        
        # 添加到队列
        self.task_queue.put(task)
        self._stats["total_tasks"] += 1
        
        self.logger.debug(f"异步任务已提交: {task.id}")
        return task.id
    
    def get_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[TaskResult]:
        """获取任务结果
        
        Args:
            task_id: 任务ID
            timeout: 超时时间
            
        Returns:
            TaskResult: 任务结果
        """
        start_time = time.time()
        
        while True:
            if task_id in self._results:
                return self._results.pop(task_id)
            
            if timeout and (time.time() - start_time) > timeout:
                return None
            
            time.sleep(0.1)
    
    def get_all_results(self) -> Dict[str, TaskResult]:
        """获取所有结果"""
        results = self._results.copy()
        self._results.clear()
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self._stats.copy()
        
        # 计算平均执行时间
        if stats["completed_tasks"] > 0:
            stats["average_execution_time"] = (
                stats["total_execution_time"] / stats["completed_tasks"]
            )
        
        # 添加资源监控信息
        stats.update(self.resource_monitor.get_stats())
        
        # 添加队列信息
        stats["queue_size"] = self.task_queue.qsize()
        stats["pending_results"] = len(self._results)
        
        return stats
    
    def _worker_loop(self):
        """工作线程循环"""
        while self._running:
            try:
                # 获取任务
                task = self.task_queue.get(timeout=1.0)
                if not task:
                    continue
                
                # 执行任务
                result = self._execute_task(task)
                
                # 存储结果
                self._results[task.id] = result
                
                # 更新统计
                if result.success:
                    self._stats["completed_tasks"] += 1
                else:
                    self._stats["failed_tasks"] += 1
                
                self._stats["total_execution_time"] += result.execution_time
                
                # 标记任务完成
                self.task_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"工作线程错误: {e}")
                time.sleep(1)
    
    def _execute_task(self, task: Task) -> TaskResult:
        """执行任务
        
        Args:
            task: 要执行的任务
            
        Returns:
            TaskResult: 执行结果
        """
        start_time = time.time()
        retry_count = 0
        
        while retry_count <= self.config.retry_count:
            try:
                # 更新任务状态
                task.status = TaskStatus.RUNNING
                
                # 获取处理函数
                if task.metadata.get("is_async"):
                    async_func = task.metadata.get("async_func")
                    if not async_func:
                        raise ValueError("异步处理函数未找到")
                    
                    # 在异步循环中执行
                    future = asyncio.run_coroutine_threadsafe(
                        async_func(task), self._async_loop
                    )
                    result = future.result(timeout=self.config.timeout)
                else:
                    processor_func = task.metadata.get("processor_func")
                    if not processor_func:
                        raise ValueError("处理函数未找到")
                    
                    # 同步执行
                    if self._executor:
                        future = self._executor.submit(processor_func, task)
                        result = future.result(timeout=self.config.timeout)
                    else:
                        result = processor_func(task)
                
                # 成功执行
                execution_time = time.time() - start_time
                task.status = TaskStatus.COMPLETED
                
                return TaskResult(
                    task_id=task.id,
                    success=True,
                    result=result,
                    execution_time=execution_time,
                    retry_count=retry_count
                )
                
            except Exception as e:
                retry_count += 1
                
                if retry_count <= self.config.retry_count:
                    self.logger.warning(
                        f"任务执行失败，重试 {retry_count}/{self.config.retry_count}: {task.id}, 错误: {e}"
                    )
                    time.sleep(self.config.retry_delay * retry_count)
                else:
                    # 最终失败
                    execution_time = time.time() - start_time
                    task.status = TaskStatus.FAILED
                    
                    self.logger.error(f"任务执行最终失败: {task.id}, 错误: {e}")
                    
                    return TaskResult(
                        task_id=task.id,
                        success=False,
                        error=e,
                        execution_time=execution_time,
                        retry_count=retry_count - 1
                    )
    
    def _run_async_loop(self):
        """运行异步循环"""
        asyncio.set_event_loop(self._async_loop)
        try:
            self._async_loop.run_forever()
        except Exception as e:
            self.logger.error(f"异步循环错误: {e}")
        finally:
            self._async_loop.close()


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self, processors: List[ParallelProcessor]):
        """初始化负载均衡器
        
        Args:
            processors: 处理器列表
        """
        self.processors = processors
        self.logger = logging.getLogger(self.__class__.__name__)
        self._current_index = 0
    
    def submit_task(self, task: Task, processor_func: Callable[[Task], Any]) -> str:
        """提交任务到最优处理器
        
        Args:
            task: 任务
            processor_func: 处理函数
            
        Returns:
            str: 任务ID
        """
        # 选择最优处理器
        processor = self._select_processor()
        
        # 提交任务
        return processor.submit_task(task, processor_func)
    
    def _select_processor(self) -> ParallelProcessor:
        """选择最优处理器
        
        Returns:
            ParallelProcessor: 选中的处理器
        """
        # 简单的轮询策略
        processor = self.processors[self._current_index]
        self._current_index = (self._current_index + 1) % len(self.processors)
        
        # 可以扩展为基于负载的选择策略
        # min_load_processor = min(self.processors, 
        #                         key=lambda p: p.task_queue.qsize())
        
        return processor
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """获取整体统计信息"""
        overall_stats = {
            "total_processors": len(self.processors),
            "total_tasks": 0,
            "total_completed": 0,
            "total_failed": 0,
            "average_queue_size": 0.0
        }
        
        for processor in self.processors:
            stats = processor.get_stats()
            overall_stats["total_tasks"] += stats.get("total_tasks", 0)
            overall_stats["total_completed"] += stats.get("completed_tasks", 0)
            overall_stats["total_failed"] += stats.get("failed_tasks", 0)
            overall_stats["average_queue_size"] += stats.get("queue_size", 0)
        
        if len(self.processors) > 0:
            overall_stats["average_queue_size"] /= len(self.processors)
        
        return overall_stats