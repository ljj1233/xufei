# -*- coding: utf-8 -*-
"""
结果整合器模块

负责整合分析结果
"""

import logging
from typing import Dict, Any, List

from ..core.workflow.state import GraphState, TaskStatus

logger = logging.getLogger(__name__)

class ResultIntegrator:
    """结果整合器
    
    整合分析结果
    """
    
    def __init__(self):
        """初始化结果整合器"""
        logger.info("结果整合器初始化完成")
    
    def execute(self, state: GraphState) -> GraphState:
        """执行结果整合
        
        这是对 integrate 方法的封装，用于提供统一的接口
        
        Args:
            state: 当前状态
            
        Returns:
            GraphState: 更新后的状态
        """
        # 调用 integrate 方法
        return self.integrate(state)
    
    def integrate(self, state: GraphState) -> GraphState:
        """整合结果
        
        Args:
            state: 当前状态
            
        Returns:
            GraphState: 更新后的状态
        """
        # 获取结果
        results = state.get_results()
        
        # 如果没有结果，返回当前状态
        if not results:
            logger.warning("没有结果可整合")
            return state
        
        # 整合结果
        if state.task_type.value == "interview_analysis":
            integrated_result = self._integrate_interview_results(results)
        elif state.task_type.value == "learning_path_generation":
            integrated_result = self._integrate_learning_path_results(results)
        else:
            logger.warning(f"未知任务类型: {state.task_type}")
            integrated_result = {
                "error": f"未知任务类型: {state.task_type}"
            }
        
        # 设置整合结果
        state.set_result(integrated_result)
        
        # 更新任务状态
        state.task_status = TaskStatus.INTEGRATED
        
        return state
    
    def _integrate_interview_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """整合面试分析结果
        
        Args:
            results: 分析结果列表
            
        Returns:
            Dict[str, Any]: 整合结果
        """
        # 初始化整合结果
        integrated_result = {
            "speech_analysis": {},
            "visual_analysis": {},
            "content_analysis": {},
            "overall_score": 0.0
        }
        
        # 计算权重
        weights = {
            "speech_analysis": 0.3,
            "visual_analysis": 0.3,
            "content_analysis": 0.4
        }
        
        # 整合各项分析结果
        scores = {}
        for result in results:
            if "task_id" not in result or "result" not in result:
                continue
                
            task_id = result["task_id"]
            if "speech" in task_id:
                integrated_result["speech_analysis"] = result["result"]
                scores["speech_analysis"] = self._calculate_average_score(result["result"])
            elif "visual" in task_id:
                integrated_result["visual_analysis"] = result["result"]
                scores["visual_analysis"] = self._calculate_average_score(result["result"])
            elif "content" in task_id:
                integrated_result["content_analysis"] = result["result"]
                scores["content_analysis"] = self._calculate_average_score(result["result"])
        
        # 计算总分
        if scores:
            total_score = 0.0
            total_weight = 0.0
            for analysis_type, score in scores.items():
                if analysis_type in weights:
                    total_score += score * weights[analysis_type]
                    total_weight += weights[analysis_type]
                    
            if total_weight > 0:
                integrated_result["overall_score"] = total_score / total_weight
        
        return integrated_result
    
    def _integrate_learning_path_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """整合学习路径生成结果
        
        Args:
            results: 分析结果列表
            
        Returns:
            Dict[str, Any]: 整合结果
        """
        # 初始化整合结果
        integrated_result = {
            "skill_gap_analysis": {},
            "resources": [],
            "learning_path": []
        }
        
        # 整合各项分析结果
        for result in results:
            if "task_id" not in result or "result" not in result:
                continue
                
            task_id = result["task_id"]
            if "skill" in task_id:
                integrated_result["skill_gap_analysis"] = result["result"]
            elif "resource" in task_id:
                integrated_result["resources"] = result["result"].get("resources", [])
            elif "path" in task_id:
                integrated_result["learning_path"] = result["result"].get("learning_path", [])
        
        return integrated_result
    
    def _calculate_average_score(self, result: Dict[str, Any]) -> float:
        """计算平均分数
        
        Args:
            result: 分析结果
            
        Returns:
            float: 平均分数
        """
        # 提取分数
        scores = []
        for key, value in result.items():
            if isinstance(value, dict) and "score" in value:
                scores.append(value["score"])
            elif isinstance(value, (int, float)):
                scores.append(value)
        
        # 计算平均分
        if scores:
            return sum(scores) / len(scores)
        else:
            return 0.0 