# -*- coding: utf-8 -*-
"""
分析器适配器模块

提供一个统一的接口来连接不同的分析器
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type

logger = logging.getLogger(__name__)

class AnalyzerAdapter(ABC):
    """分析器适配器基类"""
    
    @abstractmethod
    def extract_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取特征
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 提取的特征
        """
        pass
        
    @abstractmethod
    def analyze(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """分析特征
        
        Args:
            features: 提取的特征
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        pass
        
    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """运行分析
        
        Args:
            data: 输入数据
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            # 提取特征
            features = self.extract_features(data)
            
            # 分析特征
            result = self.analyze(features)
            
            return result
        except Exception as e:
            logger.exception(f"分析器运行失败: {str(e)}")
            return {"error": str(e)}


class SpeechAnalyzerAdapter(AnalyzerAdapter):
    """语音分析器适配器"""
    
    def __init__(self, analyzer=None):
        """初始化语音分析器适配器
        
        Args:
            analyzer: 实际的语音分析器
        """
        self.analyzer = analyzer
        
    def extract_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取语音特征
        
        Args:
            data: 输入数据
                - audio_file: 音频文件路径
                
        Returns:
            Dict[str, Any]: 提取的特征
        """
        if self.analyzer and hasattr(self.analyzer, "extract_features"):
            return self.analyzer.extract_features(data)
            
        # 默认实现
        if "audio_file" not in data or not data["audio_file"]:
            raise ValueError("缺少音频文件")
            
        return {
            "audio_file": data["audio_file"]
        }
        
    def analyze(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """分析语音特征
        
        Args:
            features: 提取的特征
                - audio_file: 音频文件路径
                
        Returns:
            Dict[str, Any]: 分析结果
        """
        if self.analyzer and hasattr(self.analyzer, "analyze"):
            return self.analyzer.analyze(features)
            
        # 默认实现（示例结果）
        return {
            "speech_rate": {"score": 80, "feedback": "语速适中"},
            "fluency": {"score": 85, "feedback": "表达流畅"}
        }


class VisualAnalyzerAdapter(AnalyzerAdapter):
    """视觉分析器适配器"""
    
    def __init__(self, analyzer=None):
        """初始化视觉分析器适配器
        
        Args:
            analyzer: 实际的视觉分析器
        """
        self.analyzer = analyzer
        
    def extract_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取视觉特征
        
        Args:
            data: 输入数据
                - video_file: 视频文件路径
                
        Returns:
            Dict[str, Any]: 提取的特征
        """
        if self.analyzer and hasattr(self.analyzer, "extract_features"):
            return self.analyzer.extract_features(data)
            
        # 默认实现
        if "video_file" not in data or not data["video_file"]:
            raise ValueError("缺少视频文件")
            
        return {
            "video_file": data["video_file"]
        }
        
    def analyze(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """分析视觉特征
        
        Args:
            features: 提取的特征
                - video_file: 视频文件路径
                
        Returns:
            Dict[str, Any]: 分析结果
        """
        if self.analyzer and hasattr(self.analyzer, "analyze"):
            return self.analyzer.analyze(features)
            
        # 默认实现（示例结果）
        return {
            "facial_expression": {"score": 80, "feedback": "表情自然"},
            "eye_contact": {"score": 85, "feedback": "目光接触良好"}
        }


class ContentAnalyzerAdapter(AnalyzerAdapter):
    """内容分析器适配器"""
    
    def __init__(self, analyzer=None):
        """初始化内容分析器适配器
        
        Args:
            analyzer: 实际的内容分析器
        """
        self.analyzer = analyzer
        
    def extract_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取内容特征
        
        Args:
            data: 输入数据
                - transcript: 文本内容
                - job_position: 职位信息
                
        Returns:
            Dict[str, Any]: 提取的特征
        """
        if self.analyzer and hasattr(self.analyzer, "extract_features"):
            return self.analyzer.extract_features(data)
            
        # 默认实现
        if "transcript" not in data or not data["transcript"]:
            raise ValueError("缺少文本内容")
            
        features = {
            "text": data["transcript"]
        }
        
        # 添加职位信息
        if "job_position" in data and data["job_position"]:
            features["job_position"] = data["job_position"]
            
        return features
        
    def analyze(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """分析内容特征
        
        Args:
            features: 提取的特征
                - text: 文本内容
                - job_position: 职位信息
                
        Returns:
            Dict[str, Any]: 分析结果
        """
        if self.analyzer and hasattr(self.analyzer, "analyze"):
            return self.analyzer.analyze(features)
            
        # 默认实现（示例结果）
        return {
            "relevance": {"score": 80, "feedback": "回答与问题相关"},
            "completeness": {"score": 85, "feedback": "回答全面"}
        }


class AnalyzerFactory:
    """分析器工厂类
    
    用于创建不同类型的分析器适配器
    """
    
    @staticmethod
    def create(analyzer_type: str, analyzer=None) -> AnalyzerAdapter:
        """创建分析器适配器
        
        Args:
            analyzer_type: 分析器类型
            analyzer: 实际的分析器
            
        Returns:
            AnalyzerAdapter: 分析器适配器实例
        """
        return create_adapter(analyzer_type, analyzer)


def create_adapter(analyzer_type: str, analyzer=None) -> AnalyzerAdapter:
    """创建适配器
    
    Args:
        analyzer_type: 分析器类型
        analyzer: 实际的分析器
        
    Returns:
        AnalyzerAdapter: 适配器实例
    """
    if analyzer_type == "speech":
        return SpeechAnalyzerAdapter(analyzer)
    elif analyzer_type == "visual":
        return VisualAnalyzerAdapter(analyzer)
    elif analyzer_type == "content":
        return ContentAnalyzerAdapter(analyzer)
    else:
        raise ValueError(f"未知的分析器类型: {analyzer_type}") 