# agent/core/nodes/task_planner.py

"""
任务规划节点

该节点负责根据策略决策的结果规划具体的分析任务，包括：
- 任务分解：将复杂任务分解为多个子任务
- 依赖关系：确定子任务之间的依赖关系
- 执行顺序：确定子任务的执行顺序
"""

import uuid
from typing import Dict, Any, List, Set, Tuple
from datetime import datetime
from copy import deepcopy
import logging

from ...core.workflow.state import GraphState, Task, TaskType, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)

class TaskPlanner:
    """任务规划器节点"""
    
    def __init__(self):
        """初始化任务规划器"""
        pass
    
    def _decompose_task(self, task: Task) -> List[Task]:
        """将任务分解为子任务
        
        Args:
            task: 原始任务
            
        Returns:
            子任务列表
        """
        # 获取任务数据
        analyzers = task.data.get("analyzers", [])
        analyzer_params = task.data.get("analyzer_params", {})
        
        # 如果没有分析器，则返回空列表
        if not analyzers:
            return []
        
        # 创建子任务列表
        subtasks = []
        
        # 为每个分析器创建一个子任务
        for analyzer in analyzers:
            # 生成子任务ID
            subtask_id = str(uuid.uuid4())
            
            # 确定子任务类型
            if analyzer == "speech_analyzer":
                subtask_type = TaskType.SPEECH_ANALYSIS
            elif analyzer == "vision_analyzer":
                subtask_type = TaskType.VISION_ANALYSIS
            elif analyzer == "content_analyzer":
                subtask_type = TaskType.CONTENT_ANALYSIS
            else:
                subtask_type = TaskType.CUSTOM
            
            # 创建子任务数据
            subtask_data = deepcopy(task.data)
            subtask_data["parent_task_id"] = task.id
            subtask_data["analyzer"] = analyzer
            subtask_data["params"] = analyzer_params.get(analyzer, {})
            
            # 创建子任务
            subtask = Task(
                id=subtask_id,
                type=subtask_type,
                priority=task.priority,  # 继承父任务的优先级
                status=TaskStatus.PENDING,
                data=subtask_data,
                created_at=datetime.now(),
                dependencies=[],  # 初始没有依赖
            )
            
            # 添加到子任务列表
            subtasks.append(subtask)
        
        return subtasks
    
    def _determine_dependencies(self, subtasks: List[Task]) -> List[Task]:
        """确定子任务之间的依赖关系
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            更新了依赖关系的子任务列表
        """
        # 创建分析器到任务ID的映射
        analyzer_to_task_id = {}
        for task in subtasks:
            analyzer = task.data.get("analyzer")
            if analyzer:
                analyzer_to_task_id[analyzer] = task.id
        
        # 定义依赖关系
        # 在这个简化的示例中，我们假设内容分析依赖于语音分析和视觉分析
        dependencies = {
            "content_analyzer": ["speech_analyzer", "vision_analyzer"],
        }
        
        # 更新子任务的依赖关系
        for task in subtasks:
            analyzer = task.data.get("analyzer")
            if analyzer in dependencies:
                for dep_analyzer in dependencies[analyzer]:
                    if dep_analyzer in analyzer_to_task_id:
                        task.dependencies.append(analyzer_to_task_id[dep_analyzer])
        
        return subtasks
    
    def _sort_tasks(self, subtasks: List[Task]) -> List[Task]:
        """根据依赖关系和优先级对任务进行排序
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            排序后的子任务列表
        """
        # 创建任务ID到任务的映射
        task_map = {task.id: task for task in subtasks}
        
        # 创建任务ID到依赖它的任务ID集合的映射
        dependents = {task.id: set() for task in subtasks}
        for task in subtasks:
            for dep_id in task.dependencies:
                dependents[dep_id].add(task.id)
        
        # 创建入度映射（每个任务依赖的任务数量）
        in_degree = {task.id: len(task.dependencies) for task in subtasks}
        
        # 创建优先级映射
        priority_value = {
            TaskPriority.CRITICAL: 3,
            TaskPriority.HIGH: 2,
            TaskPriority.MEDIUM: 1,
            TaskPriority.LOW: 0,
        }
        
        # 拓扑排序
        result = []
        queue = [task.id for task in subtasks if not task.dependencies]  # 没有依赖的任务
        
        # 按优先级排序队列
        queue.sort(key=lambda task_id: priority_value.get(task_map[task_id].priority, 0), reverse=True)
        
        while queue:
            task_id = queue.pop(0)
            result.append(task_id)
            
            # 更新依赖于当前任务的任务的入度
            for dependent_id in dependents[task_id]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)
            
            # 重新按优先级排序队列
            queue.sort(key=lambda task_id: priority_value.get(task_map[task_id].priority, 0), reverse=True)
        
        # 检查是否有环
        if len(result) != len(subtasks):
            # 有环，按优先级排序
            return sorted(subtasks, key=lambda task: priority_value.get(task.priority, 0), reverse=True)
        
        # 返回排序后的任务列表
        return [task_map[task_id] for task_id in result]
    
    def plan(self, state: GraphState) -> GraphState:
        logger.info(f"任务规划节点开始，输入状态: {state}")
        try:
            # 确保有当前任务
            if not state.task_state.current_task:
                state.error = "No current task"
                return state
            
            # 获取当前任务
            current_task = state.task_state.current_task
            
            # 分解任务
            subtasks = self._decompose_task(current_task)
            
            # 确定依赖关系
            subtasks = self._determine_dependencies(subtasks)
            
            # 排序任务
            sorted_tasks = self._sort_tasks(subtasks)
            
            # 更新任务队列
            state.task_state.task_queue = sorted_tasks
            
            # 如果任务队列不为空，则设置当前任务为队列中的第一个任务
            if sorted_tasks:
                state.task_state.current_task = sorted_tasks[0]
                state.task_state.task_queue = sorted_tasks[1:]
            else:
                # 如果没有子任务，则将当前任务标记为已完成
                current_task.status = TaskStatus.COMPLETED
                current_task.completed_at = datetime.now()
                state.task_state.completed_tasks.append(current_task)
                state.task_state.current_task = None
            
            # 更新状态
            state.next_node = "analyzer_executor"  # 设置下一个节点
            
            # 假设有任务规划主流程
            plan = self._plan_tasks(state)
            logger.info(f"任务规划完成，结果: {plan}")
            state.task_state.plan = plan
            return state
        except Exception as e:
            logger.error(f"任务规划异常: {e}")
            state.error = str(e)
            return state