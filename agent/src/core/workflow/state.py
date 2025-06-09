# -*- coding: utf-8 -*-
"""
智能体状态定义模块

该模块定义了LangGraph工作流中使用的状态结构，包括：
- 图状态（GraphState）：工作流的主要状态容器
- 任务状态（TaskState）：当前任务的状态
- 分析状态（AnalysisState）：分析过程的状态
- 结果状态（ResultState）：分析结果的状态
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class TaskType(Enum):
    """任务类型枚举"""
    UNKNOWN = "unknown"  # 未知类型
    INTERVIEW_ANALYSIS = "interview_analysis"  # 面试分析
    LEARNING_PATH_GENERATION = "learning_path_generation"  # 学习路径生成
    SPEECH_ANALYSIS = auto()  # 语音分析
    VISION_ANALYSIS = auto()  # 视觉分析
    VISUAL_ANALYSIS = auto()  # 视觉分析（新版接口）
    CONTENT_ANALYSIS = auto()  # 内容分析
    COMPREHENSIVE_ANALYSIS = auto()  # 综合分析
    CUSTOM = auto()  # 自定义分析


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = auto()  # 等待执行
    PARSED = auto()  # 已解析
    STRATEGY_DECIDED = auto()  # 已决策策略
    PLANNED = auto()  # 已规划
    EXECUTING = auto()  # 执行中
    EXECUTED = auto()  # 已执行
    INTEGRATED = auto()  # 已整合
    FEEDBACK_GENERATED = auto()  # 已生成反馈
    IN_PROGRESS = auto()  # 执行中
    COMPLETED = auto()  # 已完成
    FAILED = auto()  # 执行失败
    CANCELLED = auto()  # 已取消


@dataclass
class Task:
    """任务数据类"""
    id: str  # 任务ID
    type: TaskType  # 任务类型
    priority: TaskPriority = TaskPriority.MEDIUM  # 任务优先级
    status: TaskStatus = TaskStatus.PENDING  # 任务状态
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    started_at: Optional[datetime] = None  # 开始执行时间
    completed_at: Optional[datetime] = None  # 完成时间
    data: Dict[str, Any] = field(default_factory=dict)  # 任务数据
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID列表
    error: Optional[str] = None  # 错误信息


@dataclass
class AnalysisResult:
    """分析结果数据类"""
    task_id: str  # 关联的任务ID
    type: TaskType  # 分析类型
    score: Optional[float] = None  # 分析得分
    details: Dict[str, Any] = field(default_factory=dict)  # 详细结果
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


@dataclass
class TaskState:
    """任务状态数据类"""
    current_task: Optional[Task] = None  # 当前任务
    task_queue: List[Task] = field(default_factory=list)  # 任务队列
    completed_tasks: List[Task] = field(default_factory=list)  # 已完成任务列表
    failed_tasks: List[Task] = field(default_factory=list)  # 失败任务列表
    tasks: List[Dict[str, Any]] = field(default_factory=list)  # 任务列表
    strategies: List[str] = field(default_factory=list)  # 策略列表
    parallel_execution: bool = False  # 是否并行执行
    execution_plan: List[Dict[str, Any]] = field(default_factory=list)  # 执行计划
    priority: Dict[str, int] = field(default_factory=dict)  # 任务优先级
    strategy: Optional[str] = None  # 策略


@dataclass
class AnalysisState:
    """分析状态数据类"""
    in_progress: Dict[str, TaskType] = field(default_factory=dict)  # 进行中的分析，键为任务ID
    results: List[Dict[str, Any]] = field(default_factory=list)  # 分析结果列表
    result: Optional[Dict[str, Any]] = None  # 整合后的结果


@dataclass
class UserContext:
    """用户上下文数据类"""
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # 用户ID，默认生成UUID
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # 会话ID，默认生成UUID
    preferences: Dict[str, Any] = field(default_factory=dict)  # 用户偏好
    history: List[Dict[str, Any]] = field(default_factory=list)  # 历史记录
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    interview_data: Dict[str, Any] = field(default_factory=dict)  # 面试数据
    resources: Dict[str, Any] = field(default_factory=dict)  # 资源数据


@dataclass
class FeedbackState:
    """反馈状态数据类"""
    pending_feedback: List[Dict[str, Any]] = field(default_factory=list)  # 待发送的反馈
    sent_feedback: List[Dict[str, Any]] = field(default_factory=list)  # 已发送的反馈
    feedback: Optional[Dict[str, Any]] = None  # 反馈内容


@dataclass
class GraphState:
    """图状态数据类，作为LangGraph工作流的主要状态容器"""
    # 输入和输出
    input: Optional[Dict[str, Any]] = None  # 用户输入
    output: Optional[Dict[str, Any]] = None  # 最终输出
    
    # 上下文信息
    user_context: UserContext = field(default_factory=UserContext)  # 用户上下文
    
    # 任务管理
    task_state: TaskState = field(default_factory=TaskState)  # 任务状态
    task_type: TaskType = TaskType.UNKNOWN  # 任务类型
    task_status: TaskStatus = TaskStatus.PENDING  # 任务状态
    
    # 分析状态
    analysis_state: AnalysisState = field(default_factory=AnalysisState)  # 分析状态
    
    # 反馈状态
    feedback_state: FeedbackState = field(default_factory=FeedbackState)  # 反馈状态
    
    # 工作流控制
    next_node: Optional[str] = None  # 下一个要执行的节点
    error: Optional[str] = None  # 错误信息
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    updated_at: datetime = field(default_factory=datetime.now)  # 更新时间

    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now()
        
    def add_resource(self, name: str, value: Any) -> None:
        """添加资源
        
        Args:
            name: 资源名称
            value: 资源值
        """
        self.user_context.resources[name] = value
        
    def get_resource(self, name: str) -> Optional[Any]:
        """获取资源
        
        Args:
            name: 资源名称
            
        Returns:
            Any: 资源值
        """
        return self.user_context.resources.get(name)
        
    def get_resources(self) -> Dict[str, Any]:
        """获取所有资源
        
        Returns:
            Dict[str, Any]: 资源字典
        """
        return self.user_context.resources
        
    def set_strategies(self, strategies: List[str]) -> None:
        """设置策略列表
        
        Args:
            strategies: 策略列表
        """
        self.task_state.strategies = strategies
        
    def get_strategies(self) -> List[str]:
        """获取策略列表
        
        Returns:
            List[str]: 策略列表
        """
        return self.task_state.strategies
        
    def set_parallel_execution(self, parallel: bool) -> None:
        """设置是否并行执行
        
        Args:
            parallel: 是否并行执行
        """
        self.task_state.parallel_execution = parallel
        
    def is_parallel_execution(self) -> bool:
        """是否并行执行
        
        Returns:
            bool: 是否并行执行
        """
        return self.task_state.parallel_execution
        
    def set_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """设置任务列表
        
        Args:
            tasks: 任务列表
        """
        self.task_state.tasks = tasks
        
    def get_tasks(self) -> List[Dict[str, Any]]:
        """获取任务列表
        
        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        return self.task_state.tasks
        
    def set_execution_plan(self, plan: List[Dict[str, Any]]) -> None:
        """设置执行计划
        
        Args:
            plan: 执行计划
        """
        self.task_state.execution_plan = plan
        
    def update_task_status(self, task_id: str, status: str) -> None:
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 任务状态
        """
        for task in self.task_state.execution_plan:
            if task["task_id"] == task_id:
                task["status"] = status
                break
                
    def set_results(self, results: List[Dict[str, Any]]) -> None:
        """设置分析结果
        
        Args:
            results: 分析结果列表
        """
        self.analysis_state.results = results
        
    def get_results(self) -> List[Dict[str, Any]]:
        """获取分析结果列表
        
        Returns:
            List[Dict[str, Any]]: 分析结果列表
        """
        return self.analysis_state.results
        
    def set_result(self, result: Dict[str, Any]) -> None:
        """设置整合结果
        
        Args:
            result: 整合结果
        """
        self.analysis_state.result = result
        
    def get_result(self) -> Optional[Dict[str, Any]]:
        """获取整合结果
        
        Returns:
            Optional[Dict[str, Any]]: 整合结果
        """
        return self.analysis_state.result
        
    def set_feedback(self, feedback: Dict[str, Any]) -> None:
        """设置反馈内容
        
        Args:
            feedback: 反馈内容
        """
        self.feedback_state.feedback = feedback
        
    def get_feedback(self) -> Optional[Dict[str, Any]]:
        """获取反馈内容
        
        Returns:
            Optional[Dict[str, Any]]: 反馈内容
        """
        return self.feedback_state.feedback
        
    def set_error(self, error: str) -> None:
        """设置错误信息
        
        Args:
            error: 错误信息
        """
        self.error = error
        
    def to_dict(self) -> Dict[str, Any]:
        """将状态转换为字典
        
        Returns:
            Dict[str, Any]: 状态字典
        """
        return {
            "user_context": self.user_context.__dict__,
            "task_state": self.task_state.__dict__,
            "analysis_state": self.analysis_state.__dict__,
            "feedback_state": self.feedback_state.__dict__,
            "error": self.error
        }