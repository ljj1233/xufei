# -*- coding: utf-8 -*-
"""
反馈生成器模块

负责生成反馈内容
"""

import logging
from typing import Dict, Any, List

from ..core.workflow.state import GraphState, TaskStatus

logger = logging.getLogger(__name__)

class FeedbackGenerator:
    """反馈生成器
    
    生成反馈内容
    """
    
    def __init__(self):
        """初始化反馈生成器"""
        logger.info("反馈生成器初始化完成")
    
    def execute(self, state: GraphState) -> GraphState:
        """执行反馈生成
        
        这是对 generate 方法的封装，用于提供统一的接口
        
        Args:
            state: 当前状态
            
        Returns:
            GraphState: 更新后的状态
        """
        # 调用 generate 方法
        return self.generate(state)
    
    def generate(self, state: GraphState) -> GraphState:
        """生成反馈
        
        Args:
            state: 当前状态
            
        Returns:
            GraphState: 更新后的状态
        """
        # 获取整合结果
        result = state.get_result()
        
        # 如果没有结果，返回当前状态
        if not result:
            logger.warning("没有结果可生成反馈")
            return state
        
        # 生成反馈
        if state.task_type.value == "interview_analysis":
            feedback = self._generate_interview_feedback(result)
        elif state.task_type.value == "learning_path_generation":
            feedback = self._generate_learning_path_feedback(result)
        else:
            logger.warning(f"未知任务类型: {state.task_type}")
            feedback = {
                "error": f"未知任务类型: {state.task_type}"
            }
        
        # 设置反馈
        state.set_feedback(feedback)
        
        # 更新任务状态
        state.task_status = TaskStatus.FEEDBACK_GENERATED
        
        return state
    
    def _generate_interview_feedback(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """生成面试反馈
        
        Args:
            result: 整合结果
            
        Returns:
            Dict[str, Any]: 反馈内容
        """
        # 初始化反馈
        feedback = {
            "overall_score": result.get("overall_score", 0.0),
            "strengths": [],
            "weaknesses": [],
            "suggestions": []
        }
        
        # 分析语音
        speech_analysis = result.get("speech_analysis", {})
        if speech_analysis:
            # 提取优点
            if "speech_rate" in speech_analysis and speech_analysis["speech_rate"].get("score", 0) >= 75:
                feedback["strengths"].append("语速适中，表达清晰")
            if "fluency" in speech_analysis and speech_analysis["fluency"].get("score", 0) >= 75:
                feedback["strengths"].append("语言流畅，不卡顿")
                
            # 提取缺点
            if "speech_rate" in speech_analysis and speech_analysis["speech_rate"].get("score", 0) < 75:
                feedback["weaknesses"].append("语速需要调整")
                feedback["suggestions"].append("建议控制语速，保持适中的节奏")
            if "fluency" in speech_analysis and speech_analysis["fluency"].get("score", 0) < 75:
                feedback["weaknesses"].append("语言表达不够流畅")
                feedback["suggestions"].append("建议多练习，提高语言表达的流畅度")
        
        # 分析视觉
        visual_analysis = result.get("visual_analysis", {})
        if visual_analysis:
            # 提取优点
            if "facial_expression" in visual_analysis and visual_analysis["facial_expression"].get("score", 0) >= 75:
                feedback["strengths"].append("面部表情自然")
            if "eye_contact" in visual_analysis and visual_analysis["eye_contact"].get("score", 0) >= 75:
                feedback["strengths"].append("目光交流良好")
                
            # 提取缺点
            if "facial_expression" in visual_analysis and visual_analysis["facial_expression"].get("score", 0) < 75:
                feedback["weaknesses"].append("面部表情不够自然")
                feedback["suggestions"].append("建议放松面部肌肉，保持自然表情")
            if "eye_contact" in visual_analysis and visual_analysis["eye_contact"].get("score", 0) < 75:
                feedback["weaknesses"].append("目光交流不足")
                feedback["suggestions"].append("建议增加目光交流，保持与面试官的互动")
        
        # 分析内容
        content_analysis = result.get("content_analysis", {})
        if content_analysis:
            # 提取优点
            if "relevance" in content_analysis and content_analysis["relevance"].get("score", 0) >= 75:
                feedback["strengths"].append("回答与问题相关")
            if "completeness" in content_analysis and content_analysis["completeness"].get("score", 0) >= 75:
                feedback["strengths"].append("回答全面")
                
            # 提取缺点
            if "relevance" in content_analysis and content_analysis["relevance"].get("score", 0) < 75:
                feedback["weaknesses"].append("回答与问题相关性不高")
                feedback["suggestions"].append("建议仔细理解问题，确保回答与问题相关")
            if "completeness" in content_analysis and content_analysis["completeness"].get("score", 0) < 75:
                feedback["weaknesses"].append("回答不够全面")
                feedback["suggestions"].append("建议多角度思考问题，提供更全面的回答")
        
        # 添加默认建议
        if not feedback["suggestions"]:
            feedback["suggestions"].append("继续保持良好的表现")
        
        return feedback
    
    def _generate_learning_path_feedback(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """生成学习路径反馈
        
        Args:
            result: 整合结果
            
        Returns:
            Dict[str, Any]: 反馈内容
        """
        # 初始化反馈
        feedback = {
            "skill_gaps": [],
            "learning_path": result.get("learning_path", []),
            "resources": result.get("resources", []),
            "suggestions": []
        }
        
        # 提取技能差距
        skill_gap_analysis = result.get("skill_gap_analysis", {})
        if skill_gap_analysis and "skill_gaps" in skill_gap_analysis:
            feedback["skill_gaps"] = skill_gap_analysis["skill_gaps"]
            
            # 添加建议
            for skill_gap in skill_gap_analysis["skill_gaps"]:
                skill = skill_gap.get("skill", "")
                level = skill_gap.get("level", "")
                target = skill_gap.get("target", "")
                
                if skill and level and target:
                    feedback["suggestions"].append(f"建议从{level}提升到{target}级别的{skill}技能")
        
        # 添加默认建议
        if not feedback["suggestions"]:
            feedback["suggestions"].append("根据学习路径按部就班地学习")
        
        return feedback 