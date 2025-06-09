"""
内容分析器

分析面试回答的内容，包括相关性、逻辑性、专业性等
"""

import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FilterResult:
    """过滤结果数据类"""
    filtered_text: str
    has_sensitive_content: bool
    sensitive_word_count: int
    sensitive_categories: List[str]
    highest_severity: str

class ContentFilterServiceWrapper:
    """内容过滤服务包装器，避免循环导入"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = ContentFilterServiceWrapper()
        return cls._instance
    
    def __init__(self):
        """初始化内容过滤服务"""
        self.sensitive_words = [
            "敏感词1", "敏感词2", "敏感词3"
        ]
        logger.info("内容过滤服务初始化完成")
    
    def filter_text(self, text: str) -> FilterResult:
        """过滤文本内容"""
        if not text:
            return FilterResult(
                filtered_text="",
                has_sensitive_content=False,
                sensitive_word_count=0,
                sensitive_categories=[],
                highest_severity="low"
            )
        
        # 检查敏感词
        sensitive_words_found = []
        for word in self.sensitive_words:
            if word in text:
                sensitive_words_found.append(word)
                text = text.replace(word, "***")
        
        # 构建结果
        return FilterResult(
            filtered_text=text,
            has_sensitive_content=len(sensitive_words_found) > 0,
            sensitive_word_count=len(sensitive_words_found),
            sensitive_categories=["敏感类别"] if sensitive_words_found else [],
            highest_severity="high" if len(sensitive_words_found) > 2 else "medium" if sensitive_words_found else "low"
        )


class ContentAnalyzer:
    """内容分析器"""
    
    def __init__(self, config=None):
        """初始化内容分析器"""
        self.config = config or {}
        self.content_filter = None
        
        try:
            # 初始化内容过滤服务
            self.content_filter = ContentFilterServiceWrapper.get_instance()
            logger.info("内容分析器初始化完成，已加载内容过滤服务")
        except Exception as e:
            logger.error(f"初始化内容过滤服务失败: {str(e)}")
    
    def extract_features(self, transcript, job_position=None):
        """提取内容特征
        
        Args:
            transcript: 回答文本
            job_position: 职位信息
            
        Returns:
            Dict[str, Any]: 提取的特征
        """
        # 处理None或空字符串
        if transcript is None:
            return {}
        
        try:
            # 内容过滤
            filter_result = self.content_filter.filter_text(transcript)
            filtered_text = filter_result.filtered_text
            
            # 提取基本特征
            words = filtered_text.split()
            sentences = filtered_text.split('。')
            sentences = [s for s in sentences if s.strip()]  # 过滤空句子
            
            # 计算基本指标
            word_count = len(words)
            sentence_count = max(len(sentences), 1)  # 确保不会除以零
            avg_sentence_length = word_count / sentence_count
            
            # 提取关键词
            keywords = self._extract_keywords(filtered_text)
            
            # 构建特征字典
            features = {
                "text": filtered_text,
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_sentence_length": avg_sentence_length,
                "keywords": keywords,
                "filter_result": {
                    "has_sensitive_content": filter_result.has_sensitive_content,
                    "sensitive_word_count": filter_result.sensitive_word_count,
                    "sensitive_categories": filter_result.sensitive_categories,
                    "highest_severity": filter_result.highest_severity
                }
            }
            
            # 如果提供了职位信息，计算相关性
            if job_position:
                features["job_position"] = job_position
                features["job_title"] = job_position.get("title", "")
                features["job_requirements"] = job_position.get("requirements", [])
                features["relevance_score"] = self._calculate_relevance(filtered_text, job_position)
            
            return features
        except Exception as e:
            logger.error(f"提取内容特征失败: {str(e)}")
            return {
                "text": transcript or "",
                "word_count": 0,
                "sentence_count": 0,
                "avg_sentence_length": 0,
                "keywords": [],
                "filter_result": {
                    "has_sensitive_content": False,
                    "sensitive_word_count": 0,
                    "sensitive_categories": [],
                    "highest_severity": "low"
                }
            }
    
    def _extract_keywords(self, text):
        """提取关键词
        
        Args:
            text: 文本内容
            
        Returns:
            List[str]: 关键词列表
        """
        # 这里应该使用NLP技术提取关键词
        # 简单实现，使用预定义的关键词列表
        keywords = []
        
        # 技术关键词
        tech_keywords = ["Python", "Java", "C++", "JavaScript", "SQL", "机器学习", 
                        "人工智能", "大数据", "云计算", "开发", "测试", "架构", 
                        "算法", "数据库", "前端", "后端", "全栈"]
        
        # 软技能关键词
        soft_keywords = ["团队", "协作", "沟通", "领导", "管理", "解决问题", 
                        "项目管理", "创新", "时间管理", "适应性", "学习能力"]
        
        # 检查文本中是否包含这些关键词
        for keyword in tech_keywords:
            if keyword.lower() in text.lower():
                keywords.append(keyword)
        
        for keyword in soft_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        return keywords
    
    def _calculate_relevance(self, text, job_position):
        """计算文本与职位的相关性
        
        Args:
            text: 文本内容
            job_position: 职位信息
            
        Returns:
            float: 相关性评分(0-1)
        """
        if not job_position:
            return 0.5  # 默认中等相关性
        
        job_title = job_position.get("title", "").lower()
        job_requirements = job_position.get("requirements", [])
        
        # 基础相关性分数
        relevance_score = 0.5
        
        # 基于职位名称计算相关性
        if job_title:
            # 软件开发相关职位
            if any(term in job_title for term in ["软件", "开发", "程序员", "工程师"]):
                for term in ["开发", "编程", "代码", "软件", "工程", "系统", "设计", "架构"]:
                    if term in text:
                        relevance_score += 0.05
            
            # 数据相关职位
            if any(term in job_title for term in ["数据", "分析", "算法", "机器学习"]):
                for term in ["数据", "分析", "模型", "算法", "机器学习", "预测", "统计"]:
                    if term in text:
                        relevance_score += 0.05
            
            # 管理相关职位
            if any(term in job_title for term in ["经理", "主管", "总监", "管理"]):
                for term in ["管理", "团队", "领导", "战略", "决策", "规划", "执行"]:
                    if term in text:
                        relevance_score += 0.05
        
        # 基于职位要求计算相关性
        for requirement in job_requirements:
            if isinstance(requirement, str) and requirement in text:
                relevance_score += 0.1
        
        # 确保相关性分数在0-1之间
        return min(1.0, max(0.0, relevance_score))
    
    def analyze(self, features, params=None):
        """分析内容
        
        Args:
            features: 提取的特征
            params: 分析参数，如职位信息等
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            # 确保即使特征为空也能返回一个基本的分析结果
            if not features:
                return {
                    "relevance": {"score": 60, "feedback": "无法分析相关性，缺少输入数据"},
                    "completeness": {"score": 60, "feedback": "无法分析完整性，缺少输入数据"},
                    "structure": {"score": 60, "feedback": "无法分析结构，缺少输入数据"},
                    "overall_score": 60
                }
            
            # 分析各个维度
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
            logger.error(f"分析内容失败: {str(e)}")
            return {
                "error": str(e),
                "relevance": {"score": 60, "feedback": "分析失败"},
                "completeness": {"score": 60, "feedback": "分析失败"},
                "structure": {"score": 60, "feedback": "分析失败"},
                "overall_score": 60
            }
    
    def analyze_relevance(self, features):
        """分析相关性
        
        Args:
            features: 提取的特征
            
        Returns:
            Dict[str, Any]: 相关性分析结果
        """
        relevance_score = features.get("relevance_score", 0.5)
        keywords = features.get("keywords", [])
        job_title = features.get("job_title", "")
        
        # 基于相关性分数评分
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
        
        # 基于关键词数量调整分数
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
    
    def analyze_completeness(self, features):
        """分析完整性
        
        Args:
            features: 提取的特征
            
        Returns:
            Dict[str, Any]: 完整性分析结果
        """
        word_count = features.get("word_count", 0)
        sentence_count = features.get("sentence_count", 0)
        
        # 基于字数和句子数评分
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
    
    def analyze_structure(self, features):
        """分析结构
        
        Args:
            features: 提取的特征
            
        Returns:
            Dict[str, Any]: 结构分析结果
        """
        sentence_count = features.get("sentence_count", 0)
        avg_sentence_length = features.get("avg_sentence_length", 0)
        
        # 基于句子长度和句子数评分
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
        
        # 基于句子数量调整分数
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