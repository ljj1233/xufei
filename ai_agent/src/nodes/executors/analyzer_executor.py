# -*- coding: utf-8 -*-
"""
分析执行节点

负责执行具体的分析任务
"""

from typing import Dict, Any, List
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

from ai_agent.src.core.workflow.state import GraphState, TaskStatus, AnalysisResult, TaskType
from ai_agent.src.nodes.analyzer_adapter import AnalyzerFactory

logger = logging.getLogger(__name__)


class AnalyzerExecutor:
    """分析执行节点
    
    负责执行具体的分析任务，调用相应的分析器
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化分析执行节点
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.max_workers = self.config.get("max_workers", 3)
        self.timeout = self.config.get("timeout", 30)
        
        # 初始化分析器适配器
        self.analyzer_adapters = {}
        self._init_analyzers()
    
    def _init_analyzers(self):
        """初始化分析器适配器"""
        try:
            # 创建各类型分析器适配器
            for analyzer_type in AnalyzerFactory.get_supported_types():
                adapter_config = self.config.get(f"{analyzer_type}_config", {})
                self.analyzer_adapters[analyzer_type] = AnalyzerFactory.create_adapter(
                    analyzer_type, adapter_config
                )
            
            logger.info(f"初始化了 {len(self.analyzer_adapters)} 个分析器适配器")
            
        except Exception as e:
            logger.error(f"初始化分析器适配器失败: {e}")
            # 使用模拟分析器作为后备
            self.analyzer_adapters = {
                "speech": None,
                "visual": None,
                "content": None
            }
    
    def execute(self, state: GraphState) -> GraphState:
        logger.info(f"分析执行节点开始，输入状态: {state}")
        start_time = time.time()
        task_times = []
        success_count = 0
        fail_count = 0
        try:
            logger.info("开始执行分析任务")
            
            # 获取待执行的任务
            pending_tasks = [
                task for task in state.task_state.tasks 
                if task.status == TaskStatus.PENDING
            ]
            
            if not pending_tasks:
                logger.info("没有待执行的任务")
                return state
            
            # 执行任务
            if state.task_state.parallel_execution:
                # 并行执行
                results = self._execute_parallel(pending_tasks, state)
            else:
                # 串行执行
                results = self._execute_sequential(pending_tasks, state)
            
            # 更新分析结果
            state.analysis_state.results.extend(results)
            
            # 更新任务状态
            for task, result in zip(pending_tasks, results):
                task.status = TaskStatus.COMPLETED if result else TaskStatus.FAILED
                elapsed = getattr(result, 'elapsed', None)
                if elapsed is not None:
                    task_times.append(elapsed)
                if result:
                    success_count += 1
                else:
                    fail_count += 1
            
            logger.info(f"完成 {len(results)} 个分析任务")
            
            # 假设有分析执行主流程
            result = self._run_analysis(state)
            logger.info(f"分析执行完成，结果: {result}")
            # 更新状态
            state.analysis_state.result = result
            total_time = time.time() - start_time
            avg_time = (sum(task_times) / len(task_times)) if task_times else 0
            logger.info(f"分析执行统计: 总耗时: {total_time:.2f}s, 平均单任务耗时: {avg_time:.2f}s, 成功: {success_count}, 失败: {fail_count}")
            return state
        except Exception as e:
            logger.error(f"分析执行异常: {e}")
            state.error = str(e)
            # 标记任务为失败
            for task in state.task_state.tasks:
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.FAILED
            return state
    
    def _execute_parallel(self, tasks: List, state: GraphState) -> List[AnalysisResult]:
        """并行执行任务
        
        Args:
            tasks: 任务列表
            state: 当前状态
            
        Returns:
            List[AnalysisResult]: 分析结果列表
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            futures = [
                executor.submit(self._execute_single_task, task, state)
                for task in tasks
            ]
            
            # 收集结果
            for future in futures:
                try:
                    result = future.result(timeout=self.timeout)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"任务执行失败: {e}")
        
        return results
    
    def _execute_sequential(self, tasks: List, state: GraphState) -> List[AnalysisResult]:
        """串行执行任务
        
        Args:
            tasks: 任务列表
            state: 当前状态
            
        Returns:
            List[AnalysisResult]: 分析结果列表
        """
        results = []
        
        for task in tasks:
            try:
                result = self._execute_single_task(task, state)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"任务执行失败: {e}")
        
        return results
    
    def _execute_single_task(self, task, state: GraphState) -> AnalysisResult:
        """执行单个任务
        
        Args:
            task: 任务对象
            state: 当前状态
            
        Returns:
            AnalysisResult: 分析结果
        """
        try:
            logger.info(f"执行任务: {task.task_type.value}")
            
            # 根据任务类型选择分析器适配器
            adapter = None
            if task.task_type == TaskType.SPEECH_ANALYSIS:
                adapter = self.analyzer_adapters.get("speech")
            elif task.task_type == TaskType.VISUAL_ANALYSIS:
                adapter = self.analyzer_adapters.get("visual")
            elif task.task_type == TaskType.CONTENT_ANALYSIS:
                adapter = self.analyzer_adapters.get("content")
            
            if adapter is None:
                logger.warning(f"未找到适配器，使用模拟分析器: {task.task_type}")
                return self._mock_analyzer(task, state)
            
            # 执行分析
            result = adapter.process(state, task.data)
            
            logger.info(f"任务执行完成: {task.task_type.value}, 得分: {result.score}")
            
            return result
            
        except Exception as e:
            logger.error(f"执行单个任务失败: {e}")
            # 返回模拟结果作为后备
            return self._mock_analyzer(task, state)
    
    def _mock_analyzer(self, task, state: GraphState) -> AnalysisResult:
        """模拟分析器（后备方案）
        
        Args:
            task: 任务对象
            state: 当前状态
            
        Returns:
            AnalysisResult: 模拟分析结果
        """
        import random
        
        # 根据任务类型生成模拟结果
        if task.task_type == TaskType.SPEECH_ANALYSIS:
            score = random.uniform(6.0, 9.0)
            details = {
                "clarity": random.uniform(6.0, 9.0),
                "pace": random.uniform(6.0, 9.0),
                "emotion": random.choice(["积极", "中性", "紧张"]),
                "confidence": random.uniform(0.7, 0.9),
                "mock": True
            }
        elif task.task_type == TaskType.VISUAL_ANALYSIS:
            score = random.uniform(6.0, 9.0)
            details = {
                "eye_contact": random.uniform(6.0, 9.0),
                "expression": random.uniform(6.0, 9.0),
                "posture": random.uniform(6.0, 9.0),
                "engagement": random.uniform(6.0, 9.0),
                "mock": True
            }
        elif task.task_type == TaskType.CONTENT_ANALYSIS:
            score = random.uniform(6.0, 9.0)
            details = {
                "relevance": random.uniform(6.0, 9.0),
                "structure": random.uniform(6.0, 9.0),
                "key_points": ["技术能力", "沟通能力", "学习能力"],
                "completeness": random.uniform(6.0, 9.0),
                "mock": True
            }
        else:
            score = 5.0
            details = {"error": "未知任务类型", "mock": True}
        
        return AnalysisResult(
            task_type=task.task_type,
            score=score,
            details=details,
            confidence=0.5  # 模拟结果置信度较低
        )
    
    def get_analyzer_status(self) -> Dict[str, bool]:
        """获取分析器状态
        
        Returns:
            Dict[str, bool]: 各分析器的可用状态
        """
        status = {}
        for analyzer_type, adapter in self.analyzer_adapters.items():
            status[analyzer_type] = adapter is not None
        return status