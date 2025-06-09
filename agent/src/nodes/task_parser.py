# -*- coding: utf-8 -*-
"""
任务解析器模块

负责解析用户输入，提取任务信息
"""

import logging
from typing import Dict, Any, Optional

from ..core.workflow.state import GraphState, TaskType, TaskStatus

logger = logging.getLogger(__name__)

class TaskParser:
    """任务解析器
    
    解析用户输入，提取任务信息
    """
    
    def __init__(self):
        """初始化任务解析器"""
        logger.info("任务解析器初始化完成")
    
    def execute(self, state: GraphState) -> GraphState:
        """执行任务解析
        
        这是对 parse 方法的封装，用于提供统一的接口
        
        Args:
            state: 当前状态
            
        Returns:
            GraphState: 更新后的状态
        """
        # 获取输入数据
        input_data = state.input
        
        # 如果没有输入数据，使用用户上下文中的数据
        if not input_data:
            input_data = {"interview_data": state.user_context.interview_data}
        
        # 调用 parse 方法
        return self.parse(input_data, state)
    
    def parse(self, input_data: Dict[str, Any], state: Optional[GraphState] = None) -> GraphState:
        """解析输入数据
        
        Args:
            input_data: 输入数据
            state: 当前状态，如果为None则创建新状态
            
        Returns:
            GraphState: 更新后的状态
        """
        # 如果没有提供状态，创建新状态
        if state is None:
            state = GraphState()
            
        # 提取任务类型
        task_type = self._determine_task_type(input_data)
        state.task_type = task_type
        
        # 根据任务类型提取信息
        if task_type == TaskType.INTERVIEW_ANALYSIS:
            state = self._parse_interview_analysis(input_data, state)
        elif task_type == TaskType.LEARNING_PATH_GENERATION:
            state = self._parse_learning_path_generation(input_data, state)
        else:
            logger.warning(f"未知任务类型: {task_type}")
            
        # 更新任务状态
        state.task_status = TaskStatus.PARSED
        
        return state
    
    def _determine_task_type(self, input_data: Dict[str, Any]) -> TaskType:
        """确定任务类型
        
        Args:
            input_data: 输入数据
            
        Returns:
            TaskType: 任务类型
        """
        task_type = input_data.get("task_type")
        
        if task_type == "interview_analysis" or "interview" in str(input_data).lower():
            return TaskType.INTERVIEW_ANALYSIS
        elif task_type == "learning_path" or "learning" in str(input_data).lower():
            return TaskType.LEARNING_PATH_GENERATION
        else:
            return TaskType.UNKNOWN
    
    def _parse_interview_analysis(self, input_data: Dict[str, Any], state: GraphState) -> GraphState:
        """解析面试分析任务
        
        Args:
            input_data: 输入数据
            state: 当前状态
            
        Returns:
            GraphState: 更新后的状态
        """
        # 提取面试数据
        interview_data = input_data.get("interview_data", {})
        
        # 提取音频文件路径
        audio_file = interview_data.get("audio")
        if audio_file:
            state.add_resource("audio_file", audio_file)
            
        # 提取视频文件路径
        video_file = interview_data.get("video")
        if video_file:
            state.add_resource("video_file", video_file)
            
        # 提取文本数据
        transcript = interview_data.get("text")
        if transcript:
            state.add_resource("transcript", transcript)
            
        # 提取职位信息
        job_position = interview_data.get("job_position")
        if job_position:
            state.add_resource("job_position", job_position)
            
        return state
    
    def _parse_learning_path_generation(self, input_data: Dict[str, Any], state: GraphState) -> GraphState:
        """解析学习路径生成任务
        
        Args:
            input_data: 输入数据
            state: 当前状态
            
        Returns:
            GraphState: 更新后的状态
        """
        # 提取用户信息
        user_info = input_data.get("user_info", {})
        
        # 提取技能信息
        skills = user_info.get("skills", [])
        if skills:
            state.add_resource("skills", skills)
            
        # 提取职业目标
        career_goal = user_info.get("career_goal")
        if career_goal:
            state.add_resource("career_goal", career_goal)
            
        # 提取时间限制
        time_constraint = input_data.get("time_constraint")
        if time_constraint:
            state.add_resource("time_constraint", time_constraint)
            
        return state 