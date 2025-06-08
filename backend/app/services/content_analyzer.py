from typing import Dict, Any, List, Optional
import logging
from app.core.config import settings
import json

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    """内容分析器，负责分析回答内容的质量"""
    
    def __init__(self, llm_client=None):
        """初始化内容分析器
        
        Args:
            llm_client: LLM客户端实例，用于调用大语言模型
        """
        self.llm_client = llm_client
    
    async def analyze_content(
        self, 
        answer_text: str, 
        question: str,
        job_description: str = "",
        keywords: List[str] = None
    ) -> Dict[str, Any]:
        """分析回答内容的质量
        
        Args:
            answer_text: 回答文本
            question: 问题文本
            job_description: 职位描述（可选）
            keywords: 关键词列表（可选）
            
        Returns:
            Dict[str, Any]: 内容分析结果
        """
        try:
            # 如果没有LLM客户端，返回模拟结果
            if not self.llm_client:
                return self._mock_content_analysis(answer_text, question)
            
            # 构建LLM提示
            prompt = self._build_content_analysis_prompt(
                answer_text=answer_text,
                question=question,
                job_description=job_description,
                keywords=keywords
            )
            
            # 调用LLM进行分析
            response = await self.llm_client.generate(prompt)
            
            # 解析LLM响应
            analysis_result = self._parse_llm_response(response)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Failed to analyze content: {str(e)}")
            return self._mock_content_analysis(answer_text, question)
    
    def _build_content_analysis_prompt(
        self, 
        answer_text: str, 
        question: str,
        job_description: str = "",
        keywords: List[str] = None
    ) -> str:
        """构建内容分析提示
        
        Args:
            answer_text: 回答文本
            question: 问题文本
            job_description: 职位描述（可选）
            keywords: 关键词列表（可选）
            
        Returns:
            str: LLM提示
        """
        keywords_str = ", ".join(keywords) if keywords else "无特定关键词"
        
        prompt = f"""
        你是一位专业的面试评估专家，现在需要你对以下面试回答进行全面评估。
        
        # 问题
        {question}
        
        # 回答
        {answer_text}
        
        # 职位描述
        {job_description if job_description else "无职位描述"}
        
        # 关键词
        {keywords_str}
        
        请从以下三个维度对回答进行评估，并给出1-10的评分（10分为最高）：
        
        1. 回答相关性：回答与问题的相关程度，是否直接回应了问题
        2. 细节与深度：回答的具体程度，是否提供了足够的细节和深度
        3. 专业性：回答是否体现了专业知识和术语的正确使用
        
        对于每个维度，请提供：
        - 评分（1-10分）
        - 简短评价（一到两句话）
        - 对于专业性，还需列出回答中出现的专业关键词
        
        请以JSON格式输出结果：
        ```json
        {{
            "relevance": 评分,
            "relevance_review": "评价",
            "depth_and_detail": 评分,
            "depth_review": "评价",
            "professionalism": 评分,
            "matched_keywords": ["关键词1", "关键词2", ...],
            "professional_style_review": "评价"
        }}
        ```
        
        只返回JSON格式的结果，不要包含其他内容。
        """
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应
        
        Args:
            response: LLM响应文本
            
        Returns:
            Dict[str, Any]: 解析后的内容分析结果
        """
        try:
            # 尝试提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                
                # 确保所有必要字段存在
                required_fields = [
                    "relevance", "relevance_review", 
                    "depth_and_detail", "depth_review", 
                    "professionalism", "matched_keywords", "professional_style_review"
                ]
                
                for field in required_fields:
                    if field not in result:
                        if field in ["matched_keywords"]:
                            result[field] = []
                        else:
                            result[field] = "无评价" if field.endswith("review") else 5.0
                
                return result
            else:
                logger.warning("Failed to extract JSON from LLM response")
                return self._mock_content_analysis("", "")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            return self._mock_content_analysis("", "")
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return self._mock_content_analysis("", "")
    
    def _mock_content_analysis(self, answer_text: str, question: str) -> Dict[str, Any]:
        """生成模拟的内容分析结果（用于测试或LLM不可用时）
        
        Args:
            answer_text: 回答文本
            question: 问题文本
            
        Returns:
            Dict[str, Any]: 模拟的内容分析结果
        """
        # 基于回答长度简单评估
        answer_length = len(answer_text)
        
        if answer_length < 50:
            depth_score = 3.0
            depth_review = "回答过于简短，缺乏必要的细节和深度"
        elif answer_length < 200:
            depth_score = 5.0
            depth_review = "回答包含一些细节，但深度不足"
        else:
            depth_score = 7.0
            depth_review = "回答包含了适当的细节和一定的深度"
        
        # 简单关键词匹配
        relevance_score = 6.0
        if question.lower() in answer_text.lower():
            relevance_score = 7.0
        
        # 模拟专业性评估
        professionalism_score = 5.0
        tech_keywords = ["算法", "数据结构", "系统设计", "编程", "开发", "框架", "技术", "软件"]
        matched_keywords = [kw for kw in tech_keywords if kw in answer_text]
        
        if len(matched_keywords) > 2:
            professionalism_score = 7.0
            professional_review = "使用了一些专业术语，表现出一定的专业性"
        else:
            professional_review = "专业术语使用较少，专业性有待提高"
        
        return {
            "relevance": relevance_score,
            "relevance_review": "回答与问题有一定相关性，但可以更加直接地回应问题核心",
            "depth_and_detail": depth_score,
            "depth_review": depth_review,
            "professionalism": professionalism_score,
            "matched_keywords": matched_keywords,
            "professional_style_review": professional_review
        }