# -*- coding: utf-8 -*-
"""
策略决策器模块

负责根据任务类型和资源选择分析策略
"""

import logging
from typing import Dict, Any, List

from ..core.workflow.state import GraphState, TaskType, TaskStatus

logger = logging.getLogger(__name__)

class StrategyDecider:
    """策略决策器
    
    根据任务类型和资源选择分析策略
    """
    
    def __init__(self):
        """初始化策略决策器"""
        logger.info("策略决策器初始化完成")
    
    def execute(self, state: GraphState) -> GraphState:
        """执行策略决策
        
        这是对 decide 方法的封装，用于提供统一的接口
        
        Args:
            state: 当前状态
            
        Returns:
            GraphState: 更新后的状态
        """
        # 调用 decide 方法
        return self.decide(state)
    
    def decide(self, state: GraphState) -> GraphState:
        """决定分析策略
        
        Args:
            state: 当前状态
            
        Returns:
            GraphState: 更新后的状态
        """
        # 根据任务类型选择策略
        if state.task_type == TaskType.INTERVIEW_ANALYSIS:
            state = self._decide_interview_strategy(state)
        elif state.task_type == TaskType.LEARNING_PATH_GENERATION:
            state = self._decide_learning_path_strategy(state)
        else:
            logger.warning(f"未知任务类型: {state.task_type}")
            
        # 更新任务状态
        state.task_status = TaskStatus.STRATEGY_DECIDED
        
        return state
    
    def _decide_interview_strategy(self, state: GraphState) -> GraphState:
        """决定面试分析策略

        根据传入的 mode 决定使用哪些分析器。
        "quick" 模式: 使用文本和语音分析。
        "full" 模式: 使用文本、语音和视觉分析。
        
        Args:
            state: 当前状态
            
        Returns:
            GraphState: 更新后的状态
        """
        # 检查可用资源和模式
        resources = state.get_resources()
        # 从输入中获取模式，默认为 "full"
        mode = state.input.get("mode", "full")
        
        logger.info(f"开始决策，模式: {mode}, 可用资源: {list(resources.keys())}")

        # 创建策略列表
        strategies = []
        
        # 内容分析是所有模式的基础
        if "transcript" in resources:
            strategies.append("content_analysis")
            
        # 语音分析在 "quick" 和 "full" 模式下都需要
        if "audio_file" in resources:
            strategies.append("speech_analysis")

        # 视觉分析只在 "full" 模式下使用
        if mode == "full" and "video_file" in resources:
            strategies.append("visual_analysis")
        
        # 如果模式是 "quick"，确保不会意外加入 visual_analysis
        if mode == "quick" and "visual_analysis" in strategies:
            logger.warning("在快速模式下检测到视觉分析策略，将予以移除。")
            strategies.remove("visual_analysis")
            
        logger.info(f"最终选定策略: {strategies}")

        # 设置策略
        state.set_strategies(strategies)
        
        # 如果有多个策略，设置并行执行
        if len(strategies) > 1:
            state.set_parallel_execution(True)
            
        return state
    
    def _decide_learning_path_strategy(self, state: GraphState) -> GraphState:
        """决定学习路径生成策略
        
        Args:
            state: 当前状态
            
        Returns:
            GraphState: 更新后的状态
        """
        # 创建策略列表
        strategies = ["skill_gap_analysis", "resource_retrieval", "path_generation"]
        
        # 设置策略
        state.set_strategies(strategies)
        
        # 设置串行执行
        state.set_parallel_execution(False)
        
        return state 