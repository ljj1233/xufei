# -*- coding: utf-8 -*-
"""
内容分析器模块

分析面试回答内容，使用大语言模型进行多维度评分和分析
"""

import logging
import json
from typing import Dict, Any, Optional, List, Tuple

from ...core.system.config import AgentConfig
from ...services.content_filter_service import ContentFilterService
from ...services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    """内容分析器"""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化内容分析器
        
        Args:
            config: 配置对象
        """
        logger.info("开始初始化内容分析器...")
        self.config = config or AgentConfig()
        self.openai_service = OpenAIService(config)
        self.use_llm = self.config.get("content_analyzer", "use_llm", True)
        logger.info("内容分析器初始化完成，LLM评分模式: %s", str(self.use_llm))
    
    async def analyze_with_llm(self, transcript: str, job_position: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """使用LLM分析内容
        
        Args:
            transcript: 文本内容
            job_position: 职位信息
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        logger.info("开始使用LLM分析内容，文本长度: %d", len(transcript))
        if job_position:
            logger.info("应聘职位: %s", job_position.get("title", "未知职位"))
        
        try:
            # 构建提示词
            logger.debug("正在构建LLM分析提示词...")
            prompt = self._build_analysis_prompt(transcript, job_position)
            logger.debug("提示词构建完成，长度: %d", len(prompt))
            
            # 调用LLM服务
            messages = [
                {"role": "system", "content": "你是一位专业的面试评估专家，负责对面试回答进行分析和评分。"},
                {"role": "user", "content": prompt}
            ]
            
            logger.info("正在调用LLM服务进行内容分析...")
            response = await self.openai_service.chat_completion(
                messages=messages,
                temperature=0.3,  # 低温度以获得更稳定的评分
                max_tokens=2000
            )
            
            # 解析结果
            if response.get("status") == "success":
                content = response.get("content", "")
                logger.info("LLM服务调用成功，响应长度: %d", len(content))
                result = self._parse_llm_response(content)
                logger.info("LLM响应解析成功，总评分: %d", result.get("scores", {}).get("overall_score", 0))
                return result
            else:
                logger.error("LLM服务调用失败: %s", response.get('error', '未知错误'))
                # 如果LLM服务失败，回退到基于规则的评分
                logger.warning("正在回退到基于规则的评分方法")
                return self._fallback_analysis(transcript, job_position)
                
        except Exception as e:
            logger.exception("LLM分析失败: %s", e)
            # 如果出现异常，回退到基于规则的评分
            logger.warning("发生异常，正在回退到基于规则的评分方法")
            return self._fallback_analysis(transcript, job_position)
    
    def _build_analysis_prompt(self, transcript: str, job_position: Optional[Dict[str, Any]] = None) -> str:
        """构建分析提示词
        
        Args:
            transcript: 文本内容
            job_position: 职位信息
            
        Returns:
            str: 构建好的提示词
        """
        logger.debug("开始构建分析提示词")
        position_name = "未知职位"
        position_requirements = []
        
        if job_position:
            position_name = job_position.get("title", "未知职位")
            position_requirements = job_position.get("requirements", [])
            logger.debug("使用职位信息：职位=%s, 要求数量=%d", position_name, len(position_requirements))
        else:
            logger.debug("未提供职位信息，使用默认值")
        
        requirements_text = ', '.join(position_requirements) if position_requirements else '未提供具体要求'
        
        prompt = f"""
        请对以下面试回答进行专业、全面的分析和评分。应聘者正在应聘 {position_name} 职位。

        ## 面试回答内容:
        {transcript}

        ## 职位要求:
        {requirements_text}

        ## 请进行以下九个维度的评分和分析(每个维度0-100分):
        1. 专业技能相关性: 回答与所应聘职位的专业技能相关程度
        2. 问题理解: 对面试问题的理解准确程度
        3. 回答完整度: 回答是否全面、深入
        4. 结构逻辑: 回答的结构是否清晰、逻辑是否严密
        5. 表达流畅度: 语言表达是否流畅、清晰
        6. 深度与细节: 是否展示了深入思考和对细节的关注
        7. 实践经验: 是否能够结合实际工作经验和案例
        8. 创新思维: 解决问题是否展现创新思维
        9. 文化匹配度: 回答是否反映了与企业文化的契合

        ## 回答分析:
        1. 主要优势(列出3-5点)
        2. 改进建议(列出3-5点)

        ## 请以JSON格式返回，格式如下:
        {{
            "scores": {{
                "professional_relevance": 85,
                "question_understanding": 90,
                "completeness": 75,
                "structure_logic": 80,
                "fluency": 85,
                "depth_detail": 70,
                "practical_experience": 75,
                "innovative_thinking": 65,
                "cultural_fit": 80,
                "overall_score": 78
            }},
            "analysis": {{
                "strengths": [
                    "优势1",
                    "优势2",
                    "优势3"
                ],
                "suggestions": [
                    "建议1", 
                    "建议2", 
                    "建议3"
                ]
            }},
            "summary": "一句话总结评价"
        }}

        请确保JSON格式正确，overall_score为所有维度的加权平均分(权重自行判断)。
        """
        
        logger.debug("提示词构建完成，长度为 %d 字符", len(prompt))
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """解析LLM响应
        
        Args:
            response_text: LLM返回的文本
            
        Returns:
            Dict[str, Any]: 解析后的结果
        """
        logger.debug("开始解析LLM响应，响应长度: %d", len(response_text))
        try:
            # 尝试提取JSON
            text = response_text.strip()
            
            # 定位JSON开始和结束的位置
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = text[json_start:json_end]
                logger.debug("成功提取JSON字符串，长度: %d", len(json_str))
                result = json.loads(json_str)
                
                # 确保result包含必要的字段
                if not isinstance(result, dict):
                    logger.error("解析失败：返回结果不是有效的JSON对象")
                    raise ValueError("返回结果不是有效的JSON对象")
                
                # 检查scores字段
                if "scores" not in result or not isinstance(result["scores"], dict):
                    logger.error("解析失败：返回结果中缺少scores字段或格式不正确")
                    raise ValueError("返回结果中缺少scores字段或格式不正确")
                
                # 检查analysis字段
                if "analysis" not in result or not isinstance(result["analysis"], dict):
                    logger.error("解析失败：返回结果中缺少analysis字段或格式不正确")
                    raise ValueError("返回结果中缺少analysis字段或格式不正确")
                
                # 确保overall_score存在
                if "overall_score" not in result["scores"]:
                    logger.warning("返回结果中缺少overall_score字段，将自动计算")
                    # 如果没有overall_score，计算平均分
                    scores = result["scores"]
                    score_values = [v for k, v in scores.items() if k != "overall_score" and isinstance(v, (int, float))]
                    if score_values:
                        result["scores"]["overall_score"] = round(sum(score_values) / len(score_values))
                        logger.info("自动计算的overall_score值为: %d", result["scores"]["overall_score"])
                    else:
                        result["scores"]["overall_score"] = 0
                        logger.warning("无法自动计算overall_score，设置为默认值0")
                
                logger.info("LLM响应解析成功，得分: %s, 优势数量: %d, 改进建议数量: %d", 
                           result["scores"].get("overall_score"),
                           len(result.get("analysis", {}).get("strengths", [])),
                           len(result.get("analysis", {}).get("suggestions", [])))
                return result
            else:
                logger.error("无法从LLM响应中提取JSON, json_start=%d, json_end=%d", json_start, json_end)
                raise ValueError("无法从LLM响应中提取JSON")
        
        except Exception as e:
            logger.exception("解析LLM响应失败: %s", e)
            # 返回一个基本结构以确保API兼容性
            logger.warning("返回默认的解析失败结构")
            return {
                "scores": {
                    "professional_relevance": 0,
                    "question_understanding": 0,
                    "completeness": 0,
                    "structure_logic": 0,
                    "fluency": 0,
                    "depth_detail": 0,
                    "practical_experience": 0,
                    "innovative_thinking": 0,
                    "cultural_fit": 0,
                    "overall_score": 0
                },
                "analysis": {
                    "strengths": ["解析失败"],
                    "suggestions": ["解析失败"]
                },
                "summary": "解析LLM响应失败",
                "error": str(e)
            }
    
    async def analyze_async(self, transcript: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """异步分析内容
        
        Args:
            transcript: 文本内容
            params: 分析参数，如职位信息等
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        logger.info("开始异步分析内容，文本长度: %d", len(transcript) if transcript else 0)
        try:
            # 内容过滤
            filter_service = ContentFilterService.get_instance()
            logger.debug("正在进行内容过滤...")
            filter_result = filter_service.filter_text(transcript)
            filtered_text = filter_result.filtered_text
            logger.debug("内容过滤完成，过滤前长度: %d, 过滤后长度: %d", 
                        len(transcript) if transcript else 0, 
                        len(filtered_text) if filtered_text else 0)
            
            # 获取职位信息
            job_position = params.get("job_position") if params else None
            if job_position:
                logger.info("提供了职位信息: %s", job_position.get("title", "未指定"))
            else:
                logger.info("未提供职位信息")
            
            # 如果使用LLM进行评分
            if self.use_llm:
                logger.info("使用LLM进行内容评分分析...")
                try:
                    result = await self.analyze_with_llm(filtered_text, job_position)
                    
                    # 如果LLM评分成功，返回结果
                    if "scores" in result and "analysis" in result:
                        logger.info("LLM评分成功，转换为兼容旧API的格式")
                        # 兼容旧API返回格式，保留旧字段
                        legacy_result = {
                            "relevance": {
                                "score": result["scores"].get("professional_relevance", 0),
                                "feedback": "请参考详细分析"
                            },
                            "completeness": {
                                "score": result["scores"].get("completeness", 0),
                                "feedback": "请参考详细分析"
                            },
                            "structure": {
                                "score": result["scores"].get("structure_logic", 0),
                                "feedback": "请参考详细分析"
                            },
                            "overall_score": result["scores"].get("overall_score", 0),
                            "detailed_scores": result["scores"],
                            "analysis": result["analysis"],
                            "summary": result.get("summary", "")
                        }
                        logger.debug("返回结果: %s", legacy_result)
                        return legacy_result
                except Exception as e:
                    # LLM调用失败，记录日志但不返回错误，继续使用基于规则的评分
                    logger.exception("LLM分析失败: %s", str(e))
                    logger.warning("回退到基于规则的评分方法")
            else:
                logger.info("未启用LLM评分，将使用基于规则的评分方法")
            
            # 如果不使用LLM或LLM失败，使用基于规则的评分
            logger.info("开始使用基于规则的评分方法...")
            result = self._fallback_analysis(filtered_text, job_position)
            logger.info("基于规则的评分完成，总分: %d", result.get("overall_score", 0))
            return result
            
        except Exception as e:
            logger.exception("内容分析失败: %s", str(e))
            # 即使在完全失败的情况下，也尝试调用_fallback_analysis
            try:
                logger.warning("尝试使用_fallback_analysis作为最后的备选方案")
                return self._fallback_analysis(transcript, params.get("job_position") if params else None)
            except Exception as fallback_error:
                logger.exception("_fallback_analysis也失败: %s", str(fallback_error))
                # 如果_fallback_analysis也失败，返回最基本的错误响应
                error_response = {
                    "error": str(e),
                    "relevance": {"score": 0, "feedback": "分析失败"},
                    "completeness": {"score": 0, "feedback": "分析失败"},
                    "structure": {"score": 0, "feedback": "分析失败"},
                    "overall_score": 0
                }
                logger.debug("返回基本错误响应: %s", error_response)
                return error_response
    
    def analyze(self, features: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """兼容旧API的同步分析方法
        
        Args:
            features: 提取的特征
            params: 分析参数，如职位信息等
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        logger.info("使用旧版同步API进行内容分析")
        try:
            # 获取职位信息
            job_position = params.get("job_position") if params else None
            if job_position:
                logger.info("提供了职位信息: %s", job_position.get("title", "未指定"))
            else:
                logger.info("未提供职位信息")
            
            # 分析特征
            logger.debug("分析相关性...")
            relevance_result = self.analyze_relevance(features)
            logger.debug("分析完整性...")
            completeness_result = self.analyze_completeness(features)
            logger.debug("分析结构...")
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
            
            logger.info("内容分析完成，总分: %d", round(overall_score))
            return result
        except Exception as e:
            logger.exception("内容分析失败: %s", str(e))
            return {
                "error": str(e),
                "relevance": {"score": 0, "feedback": "分析失败"},
                "completeness": {"score": 0, "feedback": "分析失败"},
                "structure": {"score": 0, "feedback": "分析失败"},
                "overall_score": 0
            }
            
    def _fallback_analysis(self, transcript: str, job_position: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """基于规则的回退分析方法
        
        Args:
            transcript: 文本内容
            job_position: 职位信息
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        logger.info("开始使用基于规则的回退分析方法")
        # 提取特征
        logger.debug("提取文本特征...")
        features = self.extract_features(transcript, job_position)
        
        # 分析相关性、完整性和结构
        logger.debug("分析相关性...")
        relevance_result = self.analyze_relevance(features)
        logger.debug("分析完整性...")
        completeness_result = self.analyze_completeness(features)
        logger.debug("分析结构...")
        structure_result = self.analyze_structure(features)
        
        # 计算总体评分
        relevance_weight = 0.4
        completeness_weight = 0.4
        structure_weight = 0.2
        
        overall_score = (
            relevance_result["score"] * relevance_weight +
            completeness_result["score"] * completeness_weight +
            structure_result["score"] * structure_weight
        )
        
        # 确保始终有优势和建议，至少各一个
        strengths = []
        suggestions = []
        
        # 基于规则生成优势和建议
        if relevance_result["score"] >= 80:
            strengths.append("回答与职位要求高度相关")
        else:
            suggestions.append("提高回答与职位要求的相关性")
            
        if completeness_result["score"] >= 80:
            strengths.append("回答内容全面充实")
        else:
            suggestions.append("增加回答的深度和完整性")
            
        if structure_result["score"] >= 80:
            strengths.append("回答结构清晰")
        else:
            suggestions.append("改进回答的结构和逻辑性")
        
        # 确保至少有一个优势和一个建议
        if not strengths:
            strengths = ["表达流畅"]
        if not suggestions:
            suggestions = ["进一步丰富专业术语的使用"]
        
        # 汇总结果，兼容新旧格式
        result = {
            "relevance": relevance_result,
            "completeness": completeness_result,
            "structure": structure_result,
            "overall_score": round(overall_score),
            "detailed_scores": {
                "professional_relevance": relevance_result["score"],
                "completeness": completeness_result["score"],
                "structure_logic": structure_result["score"],
                "fluency": 75,  # 默认值
                "depth_detail": 70,  # 默认值
                "practical_experience": 65,  # 默认值
                "innovative_thinking": 60,  # 默认值
                "cultural_fit": 70,  # 默认值
                "overall_score": round(overall_score)
            },
            "analysis": {
                "strengths": strengths,
                "suggestions": suggestions
            },
            "summary": "基于规则的分析评估"
        }
        
        logger.info("基于规则的回退分析完成，总分: %d", round(overall_score))
        return result
    
    def extract_features(self, transcript: str, job_position: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """提取特征
        
        Args:
            transcript: 文本内容
            job_position: 职位信息
            
        Returns:
            Dict[str, Any]: 提取的特征
        """
        logger.debug("开始提取文本特征...")
        if transcript is None:
            logger.warning("输入的文本内容为None")
            return {}
            
        # 内容过滤
        filter_service = ContentFilterService.get_instance()
        logger.debug("进行内容过滤...")
        filter_result = filter_service.filter_text(transcript)
        filtered_text = filter_result.filtered_text
        logger.debug("内容过滤完成，过滤前长度: %d, 过滤后长度: %d", 
                    len(transcript), 
                    len(filtered_text))
        
        # 提取基本特征
        words = filtered_text.split()
        sentences = filtered_text.split('。')
        
        # 计算基本指标
        word_count = len(words)
        sentence_count = len(sentences)
        avg_sentence_length = word_count / max(1, sentence_count)
        
        logger.debug("基本文本指标: 单词数=%d, 句子数=%d, 平均句长=%.2f", 
                   word_count, sentence_count, avg_sentence_length)
        
        # 提取关键词
        keywords = self._extract_keywords(filtered_text)
        logger.debug("提取到 %d 个关键词: %s", len(keywords), keywords)
        
        # 简单实现，返回模拟特征
        features = {
            "text": filtered_text,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": avg_sentence_length,
            "keywords": keywords
        }
        
        # 如果提供了职位信息，计算相关性
        if job_position:
            features["job_position"] = job_position
            features["job_title"] = job_position.get("title", "")
            logger.debug("计算与职位 %s 的相关性...", features["job_title"])
            features["relevance_score"] = self._calculate_relevance(filtered_text, job_position)
            logger.debug("相关性分数: %.2f", features["relevance_score"])
        
        logger.debug("特征提取完成")
        return features
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词
        
        Args:
            text: 文本内容
            
        Returns:
            List[str]: 关键词列表
        """
        logger.debug("开始提取关键词...")
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
        
        logger.debug("提取到 %d 个关键词", len(keywords))
        return keywords
    
    def _calculate_relevance(self, text: str, job_position: Dict[str, Any]) -> float:
        """计算相关性
        
        Args:
            text: 文本内容
            job_position: 职位信息
            
        Returns:
            float: 相关性分数
        """
        logger.debug("开始计算文本与职位的相关性")
        # 简单实现，仅为演示目的
        job_title = job_position.get("title", "").lower()
        logger.debug("职位名称: %s", job_title)
        
        relevance_score = 0.5  # 基础分数
        
        # 根据职位关键词增加分数
        if "软件" in job_title or "开发" in job_title:
            for keyword in ["代码", "开发", "软件", "编程", "算法"]:
                if keyword in text:
                    relevance_score += 0.1
                    logger.debug("找到软件相关关键词: %s, 相关性 +0.1", keyword)
        
        if "数据" in job_title:
            for keyword in ["数据", "分析", "统计", "模型"]:
                if keyword in text:
                    relevance_score += 0.1
                    logger.debug("找到数据相关关键词: %s, 相关性 +0.1", keyword)
        
        if "管理" in job_title:
            for keyword in ["管理", "团队", "领导", "规划"]:
                if keyword in text:
                    relevance_score += 0.1
                    logger.debug("找到管理相关关键词: %s, 相关性 +0.1", keyword)
        
        final_score = min(1.0, relevance_score)
        logger.debug("最终相关性分数: %.2f", final_score)
        return final_score
    
    def analyze_relevance(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """分析相关性
        
        Args:
            features: 提取的特征
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        logger.debug("开始分析相关性...")
        relevance_score = features.get("relevance_score", 0.5)
        keywords = features.get("keywords", [])
        job_title = features.get("job_title", "")
        
        if relevance_score > 0.8:
            score = 90
            feedback = f"回答与{job_title}职位高度相关，提到了多个重要关键词"
            logger.debug("相关性很高 (>0.8), 评分: %d", score)
        elif relevance_score > 0.6:
            score = 80
            feedback = f"回答与{job_title}职位相关，但可以更加突出专业技能"
            logger.debug("相关性较高 (>0.6), 评分: %d", score)
        elif relevance_score > 0.4:
            score = 70
            feedback = f"回答基本相关，建议更加针对{job_title}职位需求"
            logger.debug("相关性一般 (>0.4), 评分: %d", score)
        else:
            score = 60
            feedback = f"回答与{job_title}职位相关性不足，建议更加具体地突出相关经验和技能"
            logger.debug("相关性较低 (<0.4), 评分: %d", score)
        
        if len(keywords) > 5:
            score += 5
            feedback += "，关键词覆盖全面"
            logger.debug("关键词数量 >5, 评分 +5")
        elif len(keywords) < 2:
            score -= 5
            feedback += "，缺少关键技术词汇"
            logger.debug("关键词数量 <2, 评分 -5")
        
        logger.debug("相关性分析完成，最终评分: %d", score)
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
        logger.debug("开始分析完整性...")
        word_count = features.get("word_count", 0)
        sentence_count = features.get("sentence_count", 0)
        
        if word_count > 100 and sentence_count > 5:
            score = 90
            feedback = "回答非常全面，内容充实"
            logger.debug("回答很全面 (词数>100, 句子>5), 评分: %d", score)
        elif word_count > 50 and sentence_count > 3:
            score = 80
            feedback = "回答较为全面，但可以补充更多细节"
            logger.debug("回答较全面 (词数>50, 句子>3), 评分: %d", score)
        elif word_count > 30:
            score = 70
            feedback = "回答基本完整，但缺乏深度"
            logger.debug("回答基本完整 (词数>30), 评分: %d", score)
        else:
            score = 60
            feedback = "回答过于简短，建议提供更多细节和例子"
            logger.debug("回答过于简短 (词数<30), 评分: %d", score)
        
        logger.debug("完整性分析完成，最终评分: %d", score)
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
        logger.debug("开始分析结构...")
        sentence_count = features.get("sentence_count", 0)
        avg_sentence_length = features.get("avg_sentence_length", 0)
        
        if avg_sentence_length > 30:
            score = 70
            feedback = "句子过长，建议精简表达，增加可读性"
            logger.debug("句子过长 (>30), 评分: %d", score)
        elif avg_sentence_length < 5 and sentence_count > 1:
            score = 75
            feedback = "句子过短，建议适当增加连贯性"
            logger.debug("句子过短 (<5), 评分: %d", score)
        elif 10 <= avg_sentence_length <= 20:
            score = 85
            feedback = "语句结构良好，表达清晰"
            logger.debug("语句结构良好 (10-20), 评分: %d", score)
        else:
            score = 80
            feedback = "语句结构基本合理"
            logger.debug("语句结构一般, 评分: %d", score)
        
        if sentence_count < 2:
            score -= 10
            feedback += "，回答结构过于简单"
            logger.debug("句子数量过少 (<2), 评分 -10")
        elif sentence_count > 10:
            score += 5
            feedback += "，层次分明"
            logger.debug("句子数量充足 (>10), 评分 +5")
        
        logger.debug("结构分析完成，最终评分: %d", score)
        return {
            "score": score,
            "feedback": feedback
        }