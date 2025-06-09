# -*- coding: utf-8 -*-
"""
内容分析器模块

分析面试回答内容
"""

import logging
from typing import Dict, Any, Optional, List

from ...core.system.config import AgentConfig
from ...services.content_filter_service import ContentFilterService

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    """内容分析器"""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化内容分析器
        
        Args:
            config: 配置对象
        """
        self.config = config or AgentConfig()
        logger.info("内容分析器初始化完成")
    
    def analyze(self, features: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """分析内容
        
        Args:
            features: 提取的特征
            params: 分析参数，如职位信息等
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            # 获取职位信息
            job_position = params.get("job_position") if params else None
            
            # 分析特征
            relevance_result = self.analyze_relevance(features)
            completeness_result = self.analyze_completeness(features)
            structure_result = self.analyze_structure(features)
            
            # 计算总体评分(加权平均)
            relevance_weight = 0.4
            completeness_weight = 0.4
            structure_weight = 0.2
            
            overall_score = (
                relevance_result["score"] * relevance_weight +
                completeness_result["score"] * completeness_weight +
                structure_result["score"] * structure_weight
            )
            
            # 汇总结果
            result = {
                "relevance": relevance_result,
                "completeness": completeness_result,
                "structure": structure_result,
                "overall_score": round(overall_score)
            }
            
            return result
        except Exception as e:
            logger.exception(f"内容分析失败: {str(e)}")
            return {
                "error": str(e),
                "relevance": {"score": 0, "feedback": "分析失败"},
                "completeness": {"score": 0, "feedback": "分析失败"},
                "structure": {"score": 0, "feedback": "分析失败"},
                "overall_score": 0
            }
    
    def extract_features(self, transcript: str, job_position: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """提取特征
        
        Args:
            transcript: 文本内容
            job_position: 职位信息
            
        Returns:
            Dict[str, Any]: 提取的特征
        """
        # 内容过滤
        filter_service = ContentFilterService.get_instance()
        filter_result = filter_service.filter_text(transcript)
        filtered_text = filter_result.filtered_text
        
        # 提取基本特征
        words = filtered_text.split()
        sentences = filtered_text.split('。')
        
        # 计算基本指标
        word_count = len(words)
        sentence_count = len(sentences)
        avg_sentence_length = word_count / max(1, sentence_count)
        
        # 简单实现，返回模拟特征
        features = {
            "text": filtered_text,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": avg_sentence_length,
            "keywords": self._extract_keywords(filtered_text)
        }
        
        # 如果提供了职位信息，计算相关性
        if job_position:
            features["job_position"] = job_position
            features["job_title"] = job_position.get("title", "")
            features["relevance_score"] = self._calculate_relevance(filtered_text, job_position)
        
        return features
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词
        
        Args:
            text: 文本内容
            
        Returns:
            List[str]: 关键词列表
        """
        # 简单实现，仅为演示目的
        keywords = []
        
        # 技术关键词
        tech_keywords = ["Python", "Java", "SQL", "机器学习", "人工智能", "开发", "测试", "架构"]
        for keyword in tech_keywords:
            if keyword.lower() in text.lower():
                keywords.append(keyword)
        
        # 软技能关键词
        soft_keywords = ["团队", "协作", "沟通", "领导", "解决问题", "项目管理", "创新"]
        for keyword in soft_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        return keywords
    
    def _calculate_relevance(self, text: str, job_position: Dict[str, Any]) -> float:
        """计算相关性
        
        Args:
            text: 文本内容
            job_position: 职位信息
            
        Returns:
            float: 相关性分数
        """
        # 简单实现，仅为演示目的
        job_title = job_position.get("title", "").lower()
        
        relevance_score = 0.5  # 基础分数
        
        # 根据职位关键词增加分数
        if "软件" in job_title or "开发" in job_title:
            for keyword in ["代码", "开发", "软件", "编程", "算法"]:
                if keyword in text:
                    relevance_score += 0.1
        
        if "数据" in job_title:
            for keyword in ["数据", "分析", "统计", "模型"]:
                if keyword in text:
                    relevance_score += 0.1
        
        if "管理" in job_title:
            for keyword in ["管理", "团队", "领导", "规划"]:
                if keyword in text:
                    relevance_score += 0.1
        
        return min(1.0, relevance_score)
    
    def analyze_relevance(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """分析相关性
        
        Args:
            features: 提取的特征
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        relevance_score = features.get("relevance_score", 0.5)
        keywords = features.get("keywords", [])
        job_title = features.get("job_title", "")
        
        if relevance_score > 0.8:
            score = 90
            feedback = f"回答与{job_title}职位高度相关，提到了多个重要关键词"
        elif relevance_score > 0.6:
            score = 80
            feedback = f"回答与{job_title}职位相关，但可以更加突出专业技能"
        elif relevance_score > 0.4:
            score = 70
            feedback = f"回答基本相关，建议更加针对{job_title}职位需求"
        else:
            score = 60
            feedback = f"回答与{job_title}职位相关性不足，建议更加具体地突出相关经验和技能"
        
        if len(keywords) > 5:
            score += 5
            feedback += "，关键词覆盖全面"
        elif len(keywords) < 2:
            score -= 5
            feedback += "，缺少关键技术词汇"
        
        return {
            "score": score,
            "feedback": feedback
        }
    
    def analyze_completeness(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """分析完整性
        
        Args:
            features: 提取的特征
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        word_count = features.get("word_count", 0)
        sentence_count = features.get("sentence_count", 0)
        
        if word_count > 100 and sentence_count > 5:
            score = 90
            feedback = "回答非常全面，内容充实"
        elif word_count > 50 and sentence_count > 3:
            score = 80
            feedback = "回答较为全面，但可以补充更多细节"
        elif word_count > 30:
            score = 70
            feedback = "回答基本完整，但缺乏深度"
        else:
            score = 60
            feedback = "回答过于简短，建议提供更多细节和例子"
        
        return {
            "score": score,
            "feedback": feedback
        }
    
    def analyze_structure(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """分析结构
        
        Args:
            features: 提取的特征
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        sentence_count = features.get("sentence_count", 0)
        avg_sentence_length = features.get("avg_sentence_length", 0)
        
        if avg_sentence_length > 30:
            score = 70
            feedback = "句子过长，建议精简表达，增加可读性"
        elif avg_sentence_length < 5 and sentence_count > 1:
            score = 75
            feedback = "句子过短，建议适当增加连贯性"
        elif 10 <= avg_sentence_length <= 20:
            score = 85
            feedback = "语句结构良好，表达清晰"
        else:
            score = 80
            feedback = "语句结构基本合理"
        
        if sentence_count < 2:
            score -= 10
            feedback += "，回答结构过于简单"
        elif sentence_count > 10:
            score += 5
            feedback += "，层次分明"
        
        return {
            "score": score,
            "feedback": feedback
        }