"""
内容分析器

分析面试回答的内容，包括相关性、逻辑性、专业性等
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio

# 引入敏感内容过滤服务
from backend.app.services.content_filter.content_filter_service import ContentFilterService
from backend.app.services.content_filter.content_filter_config import ContentFilterConfig

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """内容分析器"""
    
    def __init__(self):
        """初始化内容分析器"""
        # 初始化敏感内容过滤服务
        self.content_filter = ContentFilterService.get_instance()
        logger.info("内容分析器初始化完成，已加载敏感内容过滤服务")
    
    async def analyze(self, transcript: str, job_position: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析面试回答内容
        
        Args:
            transcript: 回答文本
            job_position: 职位信息
            
        Returns:
            分析结果
        """
        logger.info(f"开始分析内容: {len(transcript)} 字符")
        
        # 1. 敏感内容过滤
        filter_result = self.content_filter.filter_text(transcript)
        filtered_transcript = filter_result.filtered_text
        
        # 记录敏感内容过滤结果
        if filter_result.has_sensitive_content:
            logger.warning(
                f"检测到 {filter_result.sensitive_word_count} 处敏感内容，"
                f"类别: {filter_result.sensitive_categories}"
            )
        
        # 2. 使用过滤后的文本进行后续分析
        
        # 模拟内容分析过程
        await asyncio.sleep(1.5)  # 模拟分析延迟
        
        # 这里是内容分析的实际逻辑
        # TODO: 实现实际的内容分析逻辑
        
        # 返回分析结果
        return {
            "relevance": {
                "score": 85,
                "feedback": "回答与问题高度相关"
            },
            "logic": {
                "score": 90,
                "feedback": "逻辑结构清晰，层次分明"
            },
            "professionalism": {
                "score": 88,
                "feedback": "展现了较高的专业水平"
            },
            "content_quality": {
                "score": 87,
                "feedback": "内容丰富，有深度"
            },
            "sensitive_content": {
                "has_sensitive_content": filter_result.has_sensitive_content,
                "sensitive_word_count": filter_result.sensitive_word_count,
                "sensitive_categories": filter_result.sensitive_categories,
                "highest_severity": filter_result.highest_severity,
                "filtered": filter_result.has_sensitive_content  # 是否进行了过滤
            }
        } 