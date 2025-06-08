from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class FeedbackGenerator:
    """反馈生成器，负责生成结构化的反馈"""
    
    def __init__(self):
        """初始化反馈生成器"""
        pass
    
    def generate_feedback(
        self, 
        content_analysis: Dict[str, Any],
        cognitive_analysis: Dict[str, Any],
        speech_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成反馈
        
        Args:
            content_analysis: 内容分析结果
            cognitive_analysis: 思维能力分析结果
            speech_analysis: 语音分析结果（可选）
            
        Returns:
            Dict[str, Any]: 结构化反馈
        """
        try:
            # 生成优势列表
            strengths = self._generate_strengths(content_analysis, cognitive_analysis, speech_analysis)
            
            # 生成需要改进的地方
            growth_areas = self._generate_growth_areas(content_analysis, cognitive_analysis, speech_analysis)
            
            # 计算各模块得分
            content_quality_score = self._calculate_content_quality_score(content_analysis)
            cognitive_skills_score = self._calculate_cognitive_skills_score(cognitive_analysis)
            communication_skills_score = self._calculate_communication_skills_score(speech_analysis) if speech_analysis else 0
            
            # 计算总分
            weights = [0.4, 0.3, 0.3] if speech_analysis else [0.6, 0.4, 0]
            overall_score = (
                content_quality_score * weights[0] + 
                cognitive_skills_score * weights[1] + 
                communication_skills_score * weights[2]
            )
            
            return {
                "strengths": strengths,
                "growth_areas": growth_areas,
                "content_quality_score": content_quality_score,
                "cognitive_skills_score": cognitive_skills_score,
                "communication_skills_score": communication_skills_score,
                "overall_score": overall_score
            }
            
        except Exception as e:
            logger.error(f"Error generating feedback: {str(e)}")
            return {
                "strengths": [],
                "growth_areas": [],
                "content_quality_score": 60.0,
                "cognitive_skills_score": 60.0,
                "communication_skills_score": 60.0,
                "overall_score": 60.0
            }
    
    def _generate_strengths(
        self, 
        content_analysis: Dict[str, Any],
        cognitive_analysis: Dict[str, Any],
        speech_analysis: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """生成优势列表
        
        Args:
            content_analysis: 内容分析结果
            cognitive_analysis: 思维能力分析结果
            speech_analysis: 语音分析结果（可选）
            
        Returns:
            List[Dict[str, Any]]: 优势列表
        """
        strengths = []
        
        # 内容质量优势
        if content_analysis.get("relevance", 0) >= 7.0:
            strengths.append({
                "category": "content_quality",
                "item": "relevance",
                "description": "回答的相关性极高，你的回答紧扣问题核心，展现了良好的理解能力。"
            })
        
        if content_analysis.get("depth_and_detail", 0) >= 7.0:
            strengths.append({
                "category": "content_quality",
                "item": "depth_and_detail",
                "description": "回答内容丰富，提供了充足的细节和深度，使回答更有说服力。"
            })
        
        if content_analysis.get("professionalism", 0) >= 7.0:
            strengths.append({
                "category": "content_quality",
                "item": "professionalism",
                "description": "展现了良好的专业素养，使用了恰当的专业术语，增强了回答的可信度。"
            })
        
        # 思维能力优势
        if cognitive_analysis.get("logical_structure", 0) >= 7.0:
            strengths.append({
                "category": "cognitive_skills",
                "item": "logical_structure",
                "description": "回答结构清晰，逻辑性强，思路展开有条理，便于面试官理解。"
            })
        
        if cognitive_analysis.get("clarity_of_thought", 0) >= 7.0:
            strengths.append({
                "category": "cognitive_skills",
                "item": "clarity_of_thought",
                "description": "思维清晰，能够有条理地表达复杂概念，展示了良好的分析能力。"
            })
        
        # 沟通技巧优势（如果有语音分析）
        if speech_analysis:
            if speech_analysis.get("fluency", 0) >= 7.0:
                strengths.append({
                    "category": "communication_skills",
                    "item": "fluency",
                    "description": "语言表达流畅，很少使用填充词，展现了良好的口头表达能力。"
                })
            
            if speech_analysis.get("speech_rate", 0) >= 7.0:
                strengths.append({
                    "category": "communication_skills",
                    "item": "speech_rate",
                    "description": "语速适中，既不过快也不过慢，便于听者理解。"
                })
            
            if speech_analysis.get("vocal_energy", 0) >= 7.0:
                strengths.append({
                    "category": "communication_skills",
                    "item": "vocal_energy",
                    "description": "声音富有表现力，语调抑扬顿挫，有效传达了信息和情感。"
                })
            
            if speech_analysis.get("conciseness", 0) >= 7.0:
                strengths.append({
                    "category": "communication_skills",
                    "item": "conciseness",
                    "description": "表达简洁有力，直击要点，没有不必要的冗余。"
                })
        
        # 最多返回3个优势
        return strengths[:3]
    
    def _generate_growth_areas(
        self, 
        content_analysis: Dict[str, Any],
        cognitive_analysis: Dict[str, Any],
        speech_analysis: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """生成需要改进的地方
        
        Args:
            content_analysis: 内容分析结果
            cognitive_analysis: 思维能力分析结果
            speech_analysis: 语音分析结果（可选）
            
        Returns:
            List[Dict[str, Any]]: 需要改进的地方列表
        """
        growth_areas = []
        
        # 内容质量改进点
        if content_analysis.get("relevance", 10) < 6.0:
            growth_areas.append({
                "category": "content_quality",
                "item": "relevance",
                "description": "回答与问题的相关性不足，没有直接回应问题的核心要点。",
                "action_suggestion": "使用STAR法则回答问题，确保开头直接点明你对问题的理解和立场。"
            })
        
        if content_analysis.get("depth_and_detail", 10) < 6.0:
            growth_areas.append({
                "category": "content_quality",
                "item": "depth_and_detail",
                "description": "回答缺乏具体的细节和深度，显得过于表面。",
                "action_suggestion": "准备2-3个具体的例子，包含数据、时间、结果等细节，增强回答的说服力。"
            })
        
        if content_analysis.get("professionalism", 10) < 6.0:
            growth_areas.append({
                "category": "content_quality",
                "item": "professionalism",
                "description": "回答缺乏专业术语和行业知识的展示。",
                "action_suggestion": "整理该领域的核心术语和概念，在回答中自然融入3-5个专业术语。"
            })
        
        # 思维能力改进点
        if cognitive_analysis.get("logical_structure", 10) < 6.0:
            growth_areas.append({
                "category": "cognitive_skills",
                "item": "logical_structure",
                "description": "回答结构不清晰，缺乏明确的逻辑线索。",
                "action_suggestion": "采用总分总结构，先概述主要观点，再分点展开，最后总结。"
            })
        
        if cognitive_analysis.get("clarity_of_thought", 10) < 6.0:
            growth_areas.append({
                "category": "cognitive_skills",
                "item": "clarity_of_thought",
                "description": "思维表达不够清晰，存在自相矛盾或模糊的观点。",
                "action_suggestion": "练习将复杂想法分解为简单的要点，确保每个要点都有明确的支持论据。"
            })
        
        # 沟通技巧改进点（如果有语音分析）
        if speech_analysis:
            if speech_analysis.get("fluency", 10) < 6.0:
                filler_count = speech_analysis.get("fluency_details", {}).get("filler_words_count", 0)
                growth_areas.append({
                    "category": "communication_skills",
                    "item": "fluency",
                    "description": f"语言流畅度不足，检测到{filler_count}次填充词（如'嗯'、'这个'等）。",
                    "action_suggestion": "用有意的停顿代替填充词，增强表达的专业性。录音练习时标记出所有填充词。"
                })
            
            if speech_analysis.get("speech_rate", 10) < 6.0:
                wpm = speech_analysis.get("speech_rate_details", {}).get("words_per_minute", 0)
                if wpm < 120:
                    growth_areas.append({
                        "category": "communication_skills",
                        "item": "speech_rate",
                        "description": f"语速过慢（{wpm}字/分钟），可能会让面试官感到拖沓。",
                        "action_suggestion": "练习提高语速至140-180字/分钟，可以通过朗读计时训练。"
                    })
                elif wpm > 200:
                    growth_areas.append({
                        "category": "communication_skills",
                        "item": "speech_rate",
                        "description": f"语速过快（{wpm}字/分钟），可能影响清晰度和理解。",
                        "action_suggestion": "有意识地放慢语速，在关键点处适当停顿，目标是140-180字/分钟。"
                    })
            
            if speech_analysis.get("vocal_energy", 10) < 6.0:
                growth_areas.append({
                    "category": "communication_skills",
                    "item": "vocal_energy",
                    "description": "声音缺乏表现力，语调过于平稳，不足以吸引听众。",
                    "action_suggestion": "练习有意识地在关键词和重点处强调语调，增加声音的抑扬顿挫。"
                })
        
        # 按分数升序排序（分数越低，越需要改进）
        all_scores = {
            "content_quality.relevance": content_analysis.get("relevance", 10),
            "content_quality.depth_and_detail": content_analysis.get("depth_and_detail", 10),
            "content_quality.professionalism": content_analysis.get("professionalism", 10),
            "cognitive_skills.logical_structure": cognitive_analysis.get("logical_structure", 10),
            "cognitive_skills.clarity_of_thought": cognitive_analysis.get("clarity_of_thought", 10)
        }
        
        if speech_analysis:
            all_scores.update({
                "communication_skills.fluency": speech_analysis.get("fluency", 10),
                "communication_skills.speech_rate": speech_analysis.get("speech_rate", 10),
                "communication_skills.vocal_energy": speech_analysis.get("vocal_energy", 10),
                "communication_skills.conciseness": speech_analysis.get("conciseness", 10)
            })
        
        # 按照改进需求的紧迫性排序
        growth_areas.sort(key=lambda x: all_scores.get(f"{x['category']}.{x['item']}", 10))
        
        # 最多返回3个改进点
        return growth_areas[:3]
    
    def _calculate_content_quality_score(self, content_analysis: Dict[str, Any]) -> float:
        """计算内容质量得分
        
        Args:
            content_analysis: 内容分析结果
            
        Returns:
            float: 内容质量得分（0-100）
        """
        try:
            relevance = content_analysis.get("relevance", 5.0)
            depth = content_analysis.get("depth_and_detail", 5.0)
            professionalism = content_analysis.get("professionalism", 5.0)
            
            # 加权平均（相关性权重最高）
            weighted_avg = (relevance * 0.4 + depth * 0.3 + professionalism * 0.3)
            
            # 转换为0-100分制
            return weighted_avg * 10
            
        except Exception as e:
            logger.error(f"Error calculating content quality score: {str(e)}")
            return 60.0
    
    def _calculate_cognitive_skills_score(self, cognitive_analysis: Dict[str, Any]) -> float:
        """计算思维能力得分
        
        Args:
            cognitive_analysis: 思维能力分析结果
            
        Returns:
            float: 思维能力得分（0-100）
        """
        try:
            logical_structure = cognitive_analysis.get("logical_structure", 5.0)
            clarity_of_thought = cognitive_analysis.get("clarity_of_thought", 5.0)
            
            # 简单平均
            avg = (logical_structure + clarity_of_thought) / 2
            
            # 转换为0-100分制
            return avg * 10
            
        except Exception as e:
            logger.error(f"Error calculating cognitive skills score: {str(e)}")
            return 60.0
    
    def _calculate_communication_skills_score(self, speech_analysis: Dict[str, Any]) -> float:
        """计算沟通技巧得分
        
        Args:
            speech_analysis: 语音分析结果
            
        Returns:
            float: 沟通技巧得分（0-100）
        """
        try:
            if not speech_analysis:
                return 0.0
                
            fluency = speech_analysis.get("fluency", 5.0)
            speech_rate = speech_analysis.get("speech_rate", 5.0)
            vocal_energy = speech_analysis.get("vocal_energy", 5.0)
            conciseness = speech_analysis.get("conciseness", 5.0)
            
            # 加权平均
            weighted_avg = (
                fluency * 0.3 + 
                speech_rate * 0.3 + 
                vocal_energy * 0.2 + 
                conciseness * 0.2
            )
            
            # 转换为0-100分制
            return weighted_avg * 10
            
        except Exception as e:
            logger.error(f"Error calculating communication skills score: {str(e)}")
            return 60.0