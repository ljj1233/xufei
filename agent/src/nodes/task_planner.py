# -*- coding: utf-8 -*-
"""
任务规划器模块

负责根据策略规划执行任务
"""

import logging
from typing import Dict, Any, List

from ..core.workflow.state import GraphState, TaskType, TaskStatus

logger = logging.getLogger(__name__)

class TaskPlanner:
    """任务规划器
    
    根据策略规划执行任务
    """
    
    def __init__(self):
        """初始化任务规划器"""
        logger.info("任务规划器初始化完成")
    
    def execute(self, state: GraphState) -> GraphState:
        """执行任务规划
        
        这是对 plan 方法的封装，用于提供统一的接口
        
        Args:
            state: 当前状态
            
        Returns:
            GraphState: 更新后的状态
        """
        # 调用 plan 方法
        return self.plan(state)
    
    def plan(self, state: GraphState) -> GraphState:
        """规划任务
        
        Args:
            state: 当前状态
            
        Returns:
            GraphState: 更新后的状态
        """
        # 获取策略
        strategies = state.get_strategies()
        
        # 创建任务列表
        tasks = []
        
        # 根据策略创建任务
        for strategy in strategies:
            if strategy == "speech_analysis":
                tasks.append({
                    "id": f"task_speech_{len(tasks) + 1}",
                    "type": "speech_analysis",
                    "resources": ["audio_file"],
                    "analyzer": "speech_analyzer"
                })
            elif strategy == "visual_analysis":
                tasks.append({
                    "id": f"task_visual_{len(tasks) + 1}",
                    "type": "visual_analysis",
                    "resources": ["video_file"],
                    "analyzer": "visual_analyzer"
                })
            elif strategy == "content_analysis":
                tasks.append({
                    "id": f"task_content_{len(tasks) + 1}",
                    "type": "content_analysis",
                    "resources": ["transcript", "job_position"],
                    "analyzer": "content_analyzer"
                })
            elif strategy == "skill_gap_analysis":
                tasks.append({
                    "id": f"task_skill_{len(tasks) + 1}",
                    "type": "skill_gap_analysis",
                    "resources": ["skills", "career_goal"],
                    "analyzer": "skill_gap_analyzer"
                })
            elif strategy == "resource_retrieval":
                tasks.append({
                    "id": f"task_resource_{len(tasks) + 1}",
                    "type": "resource_retrieval",
                    "resources": ["skills", "career_goal"],
                    "analyzer": "resource_retriever"
                })
            elif strategy == "path_generation":
                tasks.append({
                    "id": f"task_path_{len(tasks) + 1}",
                    "type": "path_generation",
                    "resources": ["skills", "career_goal", "time_constraint"],
                    "analyzer": "path_generator"
                })
            else:
                logger.warning(f"未知策略: {strategy}")
        
        # 设置任务
        state.set_tasks(tasks)
        
        # 更新任务状态
        state.task_status = TaskStatus.PLANNED
        
        return state 