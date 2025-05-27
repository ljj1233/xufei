# ai_agent/core/state.py

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


class TaskType(Enum):
    """任务类型枚举"""
    SPEECH_ANALYSIS = auto()  # 语音分析
    VISION_ANALYSIS = auto()  # 视觉分析
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


@dataclass
class AnalysisState:
    """分析状态数据类"""
    in_progress: Dict[str, TaskType] = field(default_factory=dict)  # 进行中的分析，键为任务ID
    results: Dict[str, AnalysisResult] = field(default_factory=dict)  # 分析结果，键为任务ID


@dataclass
class UserContext:
    """用户上下文数据类"""
    user_id: str  # 用户ID
    session_id: str  # 会话ID
    preferences: Dict[str, Any] = field(default_factory=dict)  # 用户偏好
    history: List[Dict[str, Any]] = field(default_factory=list)  # 历史记录
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


@dataclass
class FeedbackState:
    """反馈状态数据类"""
    pending_feedback: List[Dict[str, Any]] = field(default_factory=list)  # 待发送的反馈
    sent_feedback: List[Dict[str, Any]] = field(default_factory=list)  # 已发送的反馈


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