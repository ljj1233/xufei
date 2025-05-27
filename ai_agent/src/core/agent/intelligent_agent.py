# ai_agent/core/intelligent_agent.py

"""
智能面试代理模块

该模块实现了智能面试评测代理，具备自主决策、任务规划、状态管理、学习适应和并发处理等核心特性。
基于LangGraph框架重构，提供更灵活的工作流和更强的智能性。
"""

from typing import Dict, Any, List, Optional, Union, Callable
from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json

from ai_agent.core.langgraph_agent import LangGraphAgent
from ai_agent.core.state import TaskType, TaskPriority

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AgentState(Enum):
    """智能体状态枚举"""
    IDLE = auto()  # 空闲状态
    ANALYZING = auto()  # 分析中
    WAITING = auto()  # 等待中
    ERROR = auto()  # 错误状态


@dataclass
class AnalysisTask:
    """分析任务数据类"""
    id: str  # 任务ID
    type: str  # 任务类型
    data: Dict[str, Any]  # 任务数据
    priority: str = "MEDIUM"  # 任务优先级
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间


@dataclass
class AnalysisResult:
    """分析结果数据类"""
    task_id: str  # 关联的任务ID
    type: str  # 分析类型
    score: Optional[float] = None  # 分析得分
    details: Dict[str, Any] = field(default_factory=dict)  # 详细结果
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间


class IntelligentInterviewAgent:
    """智能面试评测代理
    
    基于LangGraph框架实现的智能面试评测代理，具备自主决策、任务规划、状态管理、学习适应和并发处理等核心特性。
    """
    
    def __init__(self, user_id: str = None, session_id: str = None, config: Dict[str, Any] = None):
        """初始化智能面试评测代理
        
        Args:
            user_id: 用户ID，如果不提供则自动生成
            session_id: 会话ID，如果不提供则自动生成
            config: 配置参数
        """
        # 初始化配置
        self.config = config or {}
        
        # 初始化LangGraph智能体
        self.agent = LangGraphAgent(user_id=user_id, session_id=session_id)
        
        # 初始化状态
        self.state = AgentState.IDLE
        
        logger.info(f"智能面试评测代理初始化完成")
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析面试数据
        
        Args:
            data: 面试数据，可能包含音频、视频、文本等多模态数据
            
        Returns:
            分析结果
        """
        try:
            # 更新状态
            self.state = AgentState.ANALYZING
            
            # 处理输入数据
            result = self.agent.process(data)
            
            # 更新状态
            self.state = AgentState.IDLE
            
            return result
            
        except Exception as e:
            # 更新状态
            self.state = AgentState.ERROR
            
            error_msg = f"分析面试数据时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # 返回错误信息
            return {"error": error_msg}
    
    def analyze_stream(self, data: Dict[str, Any], callback: Callable[[Dict[str, Any]], None] = None) -> Dict[str, Any]:
        """流式分析面试数据
        
        Args:
            data: 面试数据，可能包含音频、视频、文本等多模态数据
            callback: 回调函数，用于接收中间结果
            
        Returns:
            最终分析结果
        """
        try:
            # 更新状态
            self.state = AgentState.ANALYZING
            
            # 流式处理输入数据
            result = self.agent.process_stream(data, callback)
            
            # 更新状态
            self.state = AgentState.IDLE
            
            return result
            
        except Exception as e:
            # 更新状态
            self.state = AgentState.ERROR
            
            error_msg = f"流式分析面试数据时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # 返回错误信息
            return {"error": error_msg}
    
    def create_task(self, task_type: str, data: Dict[str, Any], priority: str = "MEDIUM") -> str:
        """创建分析任务
        
        Args:
            task_type: 任务类型，可以是'SPEECH_ANALYSIS'、'VISION_ANALYSIS'、'CONTENT_ANALYSIS'或'COMPREHENSIVE_ANALYSIS'
            data: 任务数据
            priority: 任务优先级，可以是'LOW'、'MEDIUM'、'HIGH'或'CRITICAL'
            
        Returns:
            任务ID
        """
        # 创建任务
        task = AnalysisTask(
            id=f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(data)}",
            type=task_type,
            data=data,
            priority=priority,
            created_at=datetime.now(),
        )
        
        # 转换为输入数据格式
        input_data = {
            "text": f"执行{task_type}分析，优先级{priority}",
            "task": {
                "id": task.id,
                "type": task.type,
                "priority": task.priority,
            },
            **data,
        }
        
        # 提交任务
        self.agent.process(input_data)
        
        return task.id
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态
        
        Returns:
            当前状态的字典表示
        """
        # 获取智能体状态
        agent_state = self.agent.get_state()
        
        # 合并状态
        return {
            "agent_state": self.state.name,
            **agent_state,
        }
    
    def reset(self) -> None:
        """重置智能体状态"""
        # 重置LangGraph智能体
        self.agent.reset()
        
        # 重置状态
        self.state = AgentState.IDLE
        
        logger.info("智能面试评测代理状态已重置")