# -*- coding: utf-8 -*-
"""
工作流模块

定义工作流程，用于连接各个节点
"""

import logging
from typing import Dict, Any, Optional, List, Union

from .workflow.state import GraphState, TaskType, TaskStatus
from ..nodes.task_parser import TaskParser
from ..nodes.strategy_decider import StrategyDecider
from ..nodes.task_planner import TaskPlanner
from ..nodes.analyzer_executor import AnalyzerExecutor
from ..nodes.result_integrator import ResultIntegrator
from ..nodes.feedback_generator import FeedbackGenerator

logger = logging.getLogger(__name__)

class InterviewAnalysisWorkflow:
    """面试分析工作流
    
    该类整合了面试分析的完整流程，包括：
    1. 任务解析
    2. 策略决策
    3. 任务规划
    4. 分析执行
    5. 结果整合
    6. 反馈生成
    """
    
    def __init__(self, notification_service=None):
        """初始化工作流
        
        Args:
            notification_service: 通知服务，用于向用户发送通知
        """
        self.task_parser = TaskParser()
        self.strategy_decider = StrategyDecider()
        self.task_planner = TaskPlanner()
        self.analyzer_executor = AnalyzerExecutor()
        self.result_integrator = ResultIntegrator()
        self.feedback_generator = FeedbackGenerator()
        
        self.notification_service = notification_service
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流
        
        Args:
            input_data: 输入数据
                - interview_data: 面试数据
                    - audio: 音频文件路径
                    - video: 视频文件路径
                    - text: 文本内容
                - user_id: 用户ID
                - session_id: 会话ID
                
        Returns:
            Dict[str, Any]: 执行结果
                - feedback: 反馈内容
                - error: 错误信息（如果有）
        """
        try:
            # 创建初始状态
            state = GraphState()
            
            # 设置用户上下文
            if "user_id" in input_data:
                state.user_context.user_id = input_data["user_id"]
            if "session_id" in input_data:
                state.user_context.session_id = input_data["session_id"]
                
            # 设置输入数据
            state.input = input_data
            
            # 如果有面试数据，设置到用户上下文
            if "interview_data" in input_data:
                state.user_context.interview_data = input_data["interview_data"]
            
            # 设置任务类型
            state.task_type = TaskType.INTERVIEW_ANALYSIS
            
            # 验证输入数据
            if not self._validate_input(input_data):
                state.set_error("输入数据不完整或无效")
                return self._prepare_output(state)
            
            # 1. 任务解析
            self._send_progress("正在解析任务...", 10)
            state = self.task_parser.execute(state)
            
            # 检查错误
            if state.error:
                logger.error(f"任务解析失败: {state.error}")
                return self._prepare_output(state)
            
            # 2. 策略决策
            self._send_progress("正在制定策略...", 20)
            state = self.strategy_decider.execute(state)
            
            # 检查错误
            if state.error:
                logger.error(f"策略决策失败: {state.error}")
                return self._prepare_output(state)
            
            # 3. 任务规划
            self._send_progress("正在规划任务...", 30)
            state = self.task_planner.execute(state)
            
            # 检查错误
            if state.error:
                logger.error(f"任务规划失败: {state.error}")
                return self._prepare_output(state)
            
            # 4. 分析执行
            self._send_progress("正在执行分析...", 40)
            state = self.analyzer_executor.execute(state)
            
            # 检查错误
            if state.error:
                logger.error(f"分析执行失败: {state.error}")
                return self._prepare_output(state)
            
            # 5. 结果整合
            self._send_progress("正在整合结果...", 70)
            state = self.result_integrator.execute(state)
            
            # 检查错误
            if state.error:
                logger.error(f"结果整合失败: {state.error}")
                return self._prepare_output(state)
            
            # 6. 反馈生成
            self._send_progress("正在生成反馈...", 90)
            state = self.feedback_generator.execute(state)
            
            # 完成
            self._send_progress("已完成", 100)
            
            return self._prepare_output(state)
        except Exception as e:
            logger.exception(f"工作流执行出错: {str(e)}")
            state = GraphState()
            state.set_error(f"工作流执行出错: {str(e)}")
            return self._prepare_output(state)
    
    def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据
        
        Args:
            input_data: 输入数据
            
        Returns:
            bool: 输入数据是否有效
        """
        # 检查是否有面试数据
        if "interview_data" not in input_data:
            logger.error("缺少面试数据")
            return False
            
        interview_data = input_data["interview_data"]
        
        # 检查是否至少有一种数据
        has_audio = interview_data.get("audio") is not None
        has_video = interview_data.get("video") is not None
        has_text = interview_data.get("text") is not None and interview_data.get("text") != ""
        
        if not (has_audio or has_video or has_text):
            logger.error("面试数据为空")
            return False
            
        return True
    
    def _prepare_output(self, state: GraphState) -> Dict[str, Any]:
        """准备输出结果
        
        Args:
            state: 当前状态
            
        Returns:
            Dict[str, Any]: 输出结果
        """
        output = {}
        
        # 如果有错误，添加到输出
        if state.error:
            output["error"] = state.error
            
        # 如果有反馈，添加到输出
        feedback = state.get_feedback()
        if feedback:
            output["feedback"] = feedback
            
        # 如果有分析结果，添加到输出
        result = state.get_result()
        if result:
            output["analysis"] = result
            
        return output
    
    def _send_progress(self, message: str, percent: int) -> None:
        """发送进度通知
        
        Args:
            message: 进度消息
            percent: 进度百分比
        """
        if self.notification_service:
            try:
                self.notification_service.send_progress(message, percent)
            except Exception as e:
                logger.warning(f"发送进度通知失败: {str(e)}")
        else:
            logger.debug(f"进度: {percent}% - {message}") 