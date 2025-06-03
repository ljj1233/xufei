# agent/core/langgraph_agent.py

"""
LangGraph智能体实现

该模块实现了基于LangGraph的面试智能体，整合了工作流图和状态管理。
"""

from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
import uuid
import logging
import json

from langchain_langgraph.graph import StateGraph

from agent.core.state import GraphState, UserContext
from agent.core.graph import get_or_create_interview_agent_graph

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LangGraphAgent:
    """基于LangGraph的面试智能体"""
    
    def __init__(self, user_id: str = None, session_id: str = None):
        """初始化LangGraph智能体
        
        Args:
            user_id: 用户ID，如果不提供则自动生成
            session_id: 会话ID，如果不提供则自动生成
        """
        # 生成用户ID和会话ID
        self.user_id = user_id or str(uuid.uuid4())
        self.session_id = session_id or str(uuid.uuid4())
        
        # 获取工作流图
        self.graph = get_or_create_interview_agent_graph()
        
        # 创建编译后的图
        self.compiled_graph = self.graph.compile()
        
        # 初始化状态
        self.state = self._create_initial_state()
        
        logger.info(f"LangGraph智能体初始化完成，用户ID: {self.user_id}, 会话ID: {self.session_id}")
    
    def _create_initial_state(self) -> GraphState:
        """创建初始状态
        
        Returns:
            初始状态
        """
        # 创建用户上下文
        user_context = UserContext(
            user_id=self.user_id,
            session_id=self.session_id,
            preferences={},
            history=[],
            metadata={},
        )
        
        # 创建初始状态
        return GraphState(
            user_context=user_context,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据
        
        Args:
            input_data: 输入数据
            
        Returns:
            处理结果
        """
        try:
            # 记录输入
            logger.info(f"处理输入: {json.dumps(input_data, ensure_ascii=False)}")
            
            # 更新状态的输入
            self.state.input = input_data
            
            # 添加到历史记录
            self.state.user_context.history.append({
                "type": "input",
                "data": input_data,
                "timestamp": datetime.now().isoformat(),
            })
            
            # 执行工作流
            self.state = self.compiled_graph.invoke(self.state)
            
            # 获取输出
            output = self.state.output or {"error": "No output generated"}
            
            # 添加到历史记录
            self.state.user_context.history.append({
                "type": "output",
                "data": output,
                "timestamp": datetime.now().isoformat(),
            })
            
            # 记录输出
            logger.info(f"处理完成，输出: {json.dumps(output, ensure_ascii=False)[:200]}...")
            
            return output
            
        except Exception as e:
            error_msg = f"处理输入时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # 返回错误信息
            return {"error": error_msg}
    
    def process_stream(self, input_data: Dict[str, Any], callback: Callable[[Dict[str, Any]], None] = None) -> Dict[str, Any]:
        """流式处理输入数据
        
        Args:
            input_data: 输入数据
            callback: 回调函数，用于接收中间结果
            
        Returns:
            处理结果
        """
        try:
            # 记录输入
            logger.info(f"流式处理输入: {json.dumps(input_data, ensure_ascii=False)}")
            
            # 更新状态的输入
            self.state.input = input_data
            
            # 添加到历史记录
            self.state.user_context.history.append({
                "type": "input",
                "data": input_data,
                "timestamp": datetime.now().isoformat(),
            })
            
            # 执行工作流，获取事件流
            events = self.compiled_graph.stream(self.state)
            
            # 最终输出
            final_output = None
            
            # 处理事件流
            for event in events:
                # 更新状态
                self.state = event.state
                
                # 如果有回调函数，则调用回调函数
                if callback and event.data:
                    callback(event.data)
                
                # 如果是最后一个事件，则获取最终输出
                if event.is_last:
                    final_output = self.state.output or {"error": "No output generated"}
            
            # 添加到历史记录
            self.state.user_context.history.append({
                "type": "output",
                "data": final_output,
                "timestamp": datetime.now().isoformat(),
            })
            
            # 记录输出
            logger.info(f"流式处理完成，输出: {json.dumps(final_output, ensure_ascii=False)[:200]}...")
            
            return final_output
            
        except Exception as e:
            error_msg = f"流式处理输入时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # 返回错误信息
            return {"error": error_msg}
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态
        
        Returns:
            当前状态的字典表示
        """
        # 将状态转换为字典
        # 注意：这里可能需要自定义序列化逻辑，因为GraphState包含复杂对象
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "history_length": len(self.state.user_context.history),
            "last_updated": self.state.updated_at.isoformat(),
        }
    
    def reset(self) -> None:
        """重置智能体状态"""
        # 重新初始化状态
        self.state = self._create_initial_state()
        logger.info(f"智能体状态已重置，用户ID: {self.user_id}, 会话ID: {self.session_id}")