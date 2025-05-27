# ai_agent/analyzers/overall_analyzer.py

from typing import Dict, Any, Optional, List

from ..core.analyzer import Analyzer
from ..core.config import AgentConfig
from ..core.utils import normalize_score, weighted_average


class OverallAnalyzer(Analyzer):
    """综合分析器
    
    负责整合各个维度的分析结果，生成综合评估和建议
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化综合分析器
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        super().__init__(name="overall_analyzer", analyzer_type="overall", config=config)
    
    def extract_features(self, data: Any) -> Dict[str, Any]:
        """提取特征
        
        综合分析器不需要提取特征，直接返回输入数据
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 输入数据
        """
        return data
    
    def analyze(self, results: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """综合分析
        
        整合各个维度的分析结果，生成综合评估
        
        Args:
            results: 各个维度的分析结果
            params: 分析参数，如果为None则使用默认参数
            
        Returns:
            Dict[str, Any]: 综合分析结果
        """
        # 获取各个维度的分析结果
        speech_results = results.get("speech", {})
        visual_results = results.get("visual", {})
        content_results = results.get("content", {})
        
        # 获取权重配置
        speech_weight = self.get_config("speech_weight", 0.3)
        visual_weight = self.get_config("visual_weight", 0.3)
        content_weight = self.get_config("content_weight", 0.4)
        
        # 如果提供了参数，覆盖默认权重
        if params:
            speech_weight = params.get("speech_weight", speech_weight)
            visual_weight = params.get("visual_weight", visual_weight)
            content_weight = params.get("content_weight", content_weight)
        
        # 获取各个维度的总分
        speech_score = speech_results.get("overall_score", 5.0)
        visual_score = visual_results.get("overall_score", 5.0)
        content_score = content_results.get("overall_score", 5.0)
        
        # 计算综合评分
        overall_score = weighted_average(
            {
                "speech": speech_score,
                "visual": visual_score,
                "content": content_score
            },
            {
                "speech": speech_weight,
                "visual": visual_weight,
                "content": content_weight
            }
        )
        
        # 识别优势
        strengths = self._identify_strengths(results, params)
        
        # 识别劣势
        weaknesses = self._identify_weaknesses(results, params)
        
        # 生成建议
        suggestions = self._generate_suggestions(results, weaknesses, params)
        
        return {
            "score": overall_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "suggestions": suggestions
        }
    
    def _identify_strengths(self, results: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> List[str]:
        """识别优势
        
        根据分析结果识别面试者的优势
        
        Args:
            results: 各个维度的分析结果
            params: 分析参数
            
        Returns:
            List[str]: 优势列表
        """
        strengths = []
        
        # 获取配置的优势数量
        strengths_count = self.get_config("strengths_count", 3)
        if params and "strengths_count" in params:
            strengths_count = params.get("strengths_count")
        
        # 语音表现优势
        speech_results = results.get("speech", {})
        if speech_results.get("clarity", 0) >= 8.0:
            strengths.append("语音清晰度高，表达清楚")
        if speech_results.get("pace", 0) >= 7.0 and speech_results.get("pace", 0) <= 8.0:
            strengths.append("语速适中，节奏感好")
        if speech_results.get("emotion", "") in ["积极", "高兴"] and speech_results.get("emotion_score", 0) >= 7.0:
            strengths.append("情感表达积极自信")
        
        # 视觉表现优势
        visual_results = results.get("visual", {})
        if visual_results.get("eye_contact", 0) >= 7.0:
            strengths.append("眼神交流自然，展现自信")
        if visual_results.get("expression_score", 0) >= 7.0:
            strengths.append("面部表情丰富，亲和力强")
        if visual_results.get("posture_score", 0) >= 7.0:
            strengths.append("肢体语言自然得体")
        
        # 内容表现优势
        content_results = results.get("content", {})
        if content_results.get("relevance", 0) >= 7.0:
            strengths.append("回答内容与问题高度相关")
        if content_results.get("structure", 0) >= 7.0:
            strengths.append("回答结构清晰，逻辑性强")
        if content_results.get("key_points_score", 0) >= 7.0:
            strengths.append("关键点突出，论据充分")
        
        # 如果STAR结构完整
        star_completeness = results.get("content", {}).get("star_completeness", 0)
        if star_completeness >= 0.75:
            strengths.append("回答采用STAR结构，条理清晰")
        
        # 限制优势数量
        return strengths[:strengths_count]
    
    def _identify_weaknesses(self, results: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> List[str]:
        """识别劣势
        
        根据分析结果识别面试者的劣势
        
        Args:
            results: 各个维度的分析结果
            params: 分析参数
            
        Returns:
            List[str]: 劣势列表
        """
        weaknesses = []
        
        # 获取配置的劣势数量
        weaknesses_count = self.get_config("weaknesses_count", 3)
        if params and "weaknesses_count" in params:
            weaknesses_count = params.get("weaknesses_count")
        
        # 语音表现劣势
        speech_results = results.get("speech", {})
        if speech_results.get("clarity", 0) < 5.0:
            weaknesses.append("语音清晰度不足，表达不够清楚")
        if speech_results.get("pace", 0) < 4.0:
            weaknesses.append("语速过慢，影响表达效果")
        elif speech_results.get("pace", 0) > 8.0:
            weaknesses.append("语速过快，不易理解")
        if speech_results.get("emotion", "") in ["消极", "悲伤", "愤怒"] or speech_results.get("emotion_score", 0) < 5.0:
            weaknesses.append("情感表达不够积极")
        
        # 视觉表现劣势
        visual_results = results.get("visual", {})
        if visual_results.get("eye_contact", 0) < 5.0:
            weaknesses.append("眼神交流不足，缺乏自信")
        if visual_results.get("expression_score", 0) < 5.0:
            weaknesses.append("面部表情单一，缺乏亲和力")
        if visual_results.get("posture_score", 0) < 5.0:
            weaknesses.append("肢体语言僵硬或过于紧张")
        
        # 内容表现劣势
        content_results = results.get("content", {})
        if content_results.get("relevance", 0) < 5.0:
            weaknesses.append("回答内容与问题相关性不足")
        if content_results.get("structure", 0) < 5.0:
            weaknesses.append("回答结构不清晰，逻辑性弱")
        if content_results.get("key_points_score", 0) < 5.0:
            weaknesses.append("关键点不突出，论据不充分")
        
        # 如果STAR结构不完整
        star_completeness = results.get("content", {}).get("star_completeness", 0)
        if star_completeness < 0.5:
            weaknesses.append("回答缺乏STAR结构，条理性不足")
        
        # 限制劣势数量
        return weaknesses[:weaknesses_count]
    
    def _generate_suggestions(self, results: Dict[str, Any], weaknesses: List[str], params: Optional[Dict[str, Any]] = None) -> List[str]:
        """生成建议
        
        根据分析结果和识别的劣势生成改进建议
        
        Args:
            results: 各个维度的分析结果
            weaknesses: 识别的劣势
            params: 分析参数
            
        Returns:
            List[str]: 建议列表
        """
        suggestions = []
        
        # 获取配置的建议数量
        suggestions_count = self.get_config("suggestions_count", 5)
        if params and "suggestions_count" in params:
            suggestions_count = params.get("suggestions_count")
        
        # 根据劣势生成针对性建议
        for weakness in weaknesses:
            if "语音清晰度不足" in weakness:
                suggestions.append("练习发音和咬字，可以通过朗读文章或参加演讲训练来提高语音清晰度")
            elif "语速过慢" in weakness:
                suggestions.append("适当加快语速，可以通过定时朗读练习来调整语速")
            elif "语速过快" in weakness:
                suggestions.append("放慢语速，注意在关键点停顿，给听者理解的时间")
            elif "情感表达不够积极" in weakness:
                suggestions.append("在回答问题时保持积极的态度，适当展示热情和自信")
            elif "眼神交流不足" in weakness:
                suggestions.append("增加眼神交流，面试时注视面试官，展示自信和专注")
            elif "面部表情单一" in weakness:
                suggestions.append("丰富面部表情，适当微笑，展示亲和力和热情")
            elif "肢体语言僵硬" in weakness:
                suggestions.append("放松身体，保持自然的姿态，适当使用手势辅助表达")
            elif "回答内容与问题相关性不足" in weakness:
                suggestions.append("仔细聆听问题，确保回答紧扣问题核心，避免偏题")
            elif "回答结构不清晰" in weakness:
                suggestions.append("使用清晰的结构组织回答，可以先概述要点，再逐一展开")
            elif "关键点不突出" in weakness:
                suggestions.append("在回答中突出关键点，使用具体的例子和数据支持观点")
            elif "缺乏STAR结构" in weakness:
                suggestions.append("使用STAR结构（情境、任务、行动、结果）组织回答，使回答更有条理和说服力")
        
        # 通用建议
        general_suggestions = [
            "面试前进行充分的准备，包括研究公司背景和职位要求",
            "准备一些常见面试问题的回答，但避免背诵，保持自然",
            "面试前进行模拟面试练习，可以录制视频回看自己的表现",
            "注意仪表整洁，着装得体，给面试官留下良好的第一印象",
            "面试结束时，表达对这次面试机会的感谢，展示你的热情和礼貌"
        ]
        
        # 如果针对性建议不足，添加通用建议
        while len(suggestions) < suggestions_count and general_suggestions:
            suggestion = general_suggestions.pop(0)
            if suggestion not in suggestions:
                suggestions.append(suggestion)
        
        # 限制建议数量
        return suggestions[:suggestions_count]