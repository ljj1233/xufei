# ai_agent/core/graph.py

"""
工作流图定义模块

该模块定义了LangGraph工作流的节点和边，以及条件分支逻辑。
工作流图包含以下节点：
- 任务解析（task_parser）
- 策略决策（strategy_decider）
- 任务规划（task_planner）
- 分析执行（analyzer_executor）
- 结果整合（result_integrator）
- 反馈生成（feedback_generator）
"""

from typing import Dict, Any, List, Tuple, Annotated, TypedDict, Literal
import logging

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_langgraph.graph import StateGraph, END

from ai_agent.core.state import GraphState
from ai_agent.core.nodes import (
    TaskParser,
    StrategyDecider,
    TaskPlanner,
    AnalyzerExecutor,
    ResultIntegrator,
    FeedbackGenerator,
)

# 配置日志
logger = logging.getLogger(__name__)


def create_interview_agent_graph() -> StateGraph:
    """创建面试智能体工作流图
    
    Returns:
        工作流图
    """
    # 创建工作流图
    workflow = StateGraph(GraphState)
    
    # 添加节点
    workflow.add_node("task_parser", TaskParser())
    workflow.add_node("strategy_decider", StrategyDecider())
    workflow.add_node("task_planner", TaskPlanner())
    workflow.add_node("analyzer_executor", AnalyzerExecutor())
    workflow.add_node("result_integrator", ResultIntegrator())
    workflow.add_node("feedback_generator", FeedbackGenerator())
    
    # 定义边
    # 从任务解析到策略决策
    workflow.add_edge("task_parser", "strategy_decider")
    
    # 从策略决策到任务规划
    workflow.add_edge("strategy_decider", "task_planner")
    
    # 从任务规划到分析执行
    workflow.add_edge("task_planner", "analyzer_executor")
    
    # 分析执行可能循环执行多次，直到所有任务完成
    workflow.add_conditional_edges(
        "analyzer_executor",
        lambda state: state.next_node,
        {
            "analyzer_executor": "analyzer_executor",
            "result_integrator": "result_integrator",
        }
    )
    
    # 从结果整合到反馈生成
    workflow.add_edge("result_integrator", "feedback_generator")
    
    # 反馈生成是最后一个节点，工作流结束
    workflow.add_edge("feedback_generator", END)
    
    # 设置入口节点
    workflow.set_entry_point("task_parser")
    
    return workflow


def get_or_create_interview_agent_graph() -> StateGraph:
    """获取或创建面试智能体工作流图
    
    如果工作流图已经创建，则返回已有的图；否则创建新的图。
    这个函数可以用于缓存工作流图，避免重复创建。
    
    Returns:
        工作流图
    """
    # 在实际实现中，这里可能会使用缓存机制
    # 目前简单返回新创建的图
    return create_interview_agent_graph()