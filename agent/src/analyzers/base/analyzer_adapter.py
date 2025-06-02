# -*- coding: utf-8 -*-
"""
分析器适配器模块

将现有的分析器适配到LangGraph工作流中
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import logging

from .state import GraphState, AnalysisResult, TaskType
from ..speech.speech_analyzer import SpeechAnalyzer
from ..visual.visual_analyzer import VisualAnalyzer
from ..content.content_analyzer import ContentAnalyzer

logger = logging.getLogger(__name__)


class AnalyzerAdapter(ABC):
    """分析器适配器基类
    
    将现有分析器适配到LangGraph工作流中
    """
    
    def __init__(self, analyzer_type: str, config: Optional[Dict[str, Any]] = None):
        """初始化适配器
        
        Args:
            analyzer_type: 分析器类型
            config: 配置参数
        """
        self.analyzer_type = analyzer_type
        self.config = config or {}
        self._analyzer = None
    
    @abstractmethod
    def _create_analyzer(self):
        """创建分析器实例"""
        pass
    
    def get_analyzer(self):
        """获取分析器实例（延迟加载）"""
        if self._analyzer is None:
            self._analyzer = self._create_analyzer()
        return self._analyzer
    
    @abstractmethod
    def process(self, state: GraphState, task_data: Dict[str, Any]) -> AnalysisResult:
        """处理分析任务
        
        Args:
            state: 图状态
            task_data: 任务数据
            
        Returns:
            AnalysisResult: 分析结果
        """
        pass
    
    def _create_analysis_result(
        self, 
        task_type: TaskType, 
        score: float, 
        details: Dict[str, Any],
        confidence: float = 0.8
    ) -> AnalysisResult:
        """创建分析结果
        
        Args:
            task_type: 任务类型
            score: 分析得分
            details: 详细信息
            confidence: 置信度
            
        Returns:
            AnalysisResult: 分析结果
        """
        return AnalysisResult(
            task_type=task_type,
            score=score,
            details=details,
            confidence=confidence,
            timestamp=None  # 将在创建时自动设置
        )


class SpeechAnalyzerAdapter(AnalyzerAdapter):
    """语音分析器适配器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("speech", config)
    
    def _create_analyzer(self):
        """创建语音分析器实例"""
        from ...core.system.config import AgentConfig
        agent_config = AgentConfig() if not self.config else AgentConfig(**self.config)
        return SpeechAnalyzer(agent_config)
    
    def process(self, state: GraphState, task_data: Dict[str, Any]) -> AnalysisResult:
        """处理语音分析任务
        
        Args:
            state: 图状态
            task_data: 任务数据
            
        Returns:
            AnalysisResult: 分析结果
        """
        try:
            analyzer = self.get_analyzer()
            
            # 获取音频文件路径或数据
            audio_path = task_data.get("audio_path")
            audio_data = task_data.get("audio_data")
            
            if audio_path:
                # 从文件提取特征
                features = analyzer.extract_features(audio_path)
            elif audio_data:
                # 从音频数据提取特征
                features = analyzer.extract_stream_features(audio_data)
            else:
                logger.warning("未提供音频文件路径或数据")
                features = {}
            
            # 进行分析
            analysis_params = task_data.get("params", {})
            result = analyzer.analyze(features, analysis_params)
            
            # 转换为标准格式
            score = result.get("overall_score", 5.0)
            details = {
                "clarity": result.get("clarity", 5.0),
                "pace": result.get("pace", 5.0),
                "emotion": result.get("emotion", "中性"),
                "emotion_score": result.get("emotion_score", 5.0),
                "features": features
            }
            
            return self._create_analysis_result(
                TaskType.SPEECH_ANALYSIS,
                score,
                details
            )
            
        except Exception as e:
            logger.error(f"语音分析失败: {e}")
            return self._create_analysis_result(
                TaskType.SPEECH_ANALYSIS,
                5.0,
                {"error": str(e)},
                confidence=0.1
            )
    
    def process_stream(self, state: GraphState, audio_data: bytes) -> AnalysisResult:
        """处理流式语音分析
        
        Args:
            state: 图状态
            audio_data: 音频数据
            
        Returns:
            AnalysisResult: 分析结果
        """
        try:
            analyzer = self.get_analyzer()
            
            # 提取流式特征
            features = analyzer.extract_stream_features(audio_data)
            
            # 进行流式分析
            result = analyzer.analyze_stream(features)
            
            if not result:
                # 如果没有分析结果，返回空结果
                return None
            
            # 转换为标准格式
            score = (result.get("clarity", 5.0) + 
                    result.get("pace", 5.0) + 
                    result.get("volume", 5.0) + 
                    result.get("confidence", 5.0)) / 4
            
            details = {
                "clarity": result.get("clarity", 5.0),
                "pace": result.get("pace", 5.0),
                "volume": result.get("volume", 5.0),
                "confidence": result.get("confidence", 5.0),
                "trends": result.get("trends", {}),
                "timestamp": result.get("timestamp")
            }
            
            return self._create_analysis_result(
                TaskType.SPEECH_ANALYSIS,
                score,
                details
            )
            
        except Exception as e:
            logger.error(f"流式语音分析失败: {e}")
            return None


class VisualAnalyzerAdapter(AnalyzerAdapter):
    """视觉分析器适配器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("visual", config)
    
    def _create_analyzer(self):
        """创建视觉分析器实例"""
        from ...core.system.config import AgentConfig
        agent_config = AgentConfig() if not self.config else AgentConfig(**self.config)
        return VisualAnalyzer(agent_config)
    
    def process(self, state: GraphState, task_data: Dict[str, Any]) -> AnalysisResult:
        """处理视觉分析任务
        
        Args:
            state: 图状态
            task_data: 任务数据
            
        Returns:
            AnalysisResult: 分析结果
        """
        try:
            analyzer = self.get_analyzer()
            
            # 获取视频文件路径或帧数据
            video_path = task_data.get("video_path")
            frame_data = task_data.get("frame_data")
            
            if video_path:
                # 从视频文件提取特征
                features = analyzer.extract_features(video_path)
            elif frame_data:
                # 从帧数据提取特征
                features = analyzer.extract_frame_features(frame_data)
            else:
                logger.warning("未提供视频文件路径或帧数据")
                features = {}
            
            # 进行分析
            analysis_params = task_data.get("params", {})
            result = analyzer.analyze(features, analysis_params)
            
            # 转换为标准格式
            score = result.get("overall_score", 5.0)
            details = {
                "eye_contact": result.get("eye_contact", 5.0),
                "expression": result.get("expression", 5.0),
                "posture": result.get("posture", 5.0),
                "engagement": result.get("engagement", 5.0),
                "features": features
            }
            
            return self._create_analysis_result(
                TaskType.VISUAL_ANALYSIS,
                score,
                details
            )
            
        except Exception as e:
            logger.error(f"视觉分析失败: {e}")
            return self._create_analysis_result(
                TaskType.VISUAL_ANALYSIS,
                5.0,
                {"error": str(e)},
                confidence=0.1
            )


class ContentAnalyzerAdapter(AnalyzerAdapter):
    """内容分析器适配器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("content", config)
    
    def _create_analyzer(self):
        """创建内容分析器实例"""
        from ...core.system.config import AgentConfig
        agent_config = AgentConfig() if not self.config else AgentConfig(**self.config)
        return ContentAnalyzer(agent_config)
    
    def process(self, state: GraphState, task_data: Dict[str, Any]) -> AnalysisResult:
        """处理内容分析任务
        
        Args:
            state: 图状态
            task_data: 任务数据
            
        Returns:
            AnalysisResult: 分析结果
        """
        try:
            analyzer = self.get_analyzer()
            
            # 获取文本内容
            text = task_data.get("text", "")
            
            if not text:
                logger.warning("未提供文本内容")
                return self._create_analysis_result(
                    TaskType.CONTENT_ANALYSIS,
                    5.0,
                    {"error": "未提供文本内容"},
                    confidence=0.1
                )
            
            # 提取特征
            features = analyzer.extract_features(text)
            
            # 进行分析
            analysis_params = task_data.get("params", {})
            result = analyzer.analyze(features, analysis_params)
            
            # 转换为标准格式
            score = result.get("overall_score", 5.0)
            details = {
                "relevance": result.get("relevance", 5.0),
                "structure": result.get("structure", 5.0),
                "key_points": result.get("key_points", []),
                "features": features
            }
            
            return self._create_analysis_result(
                TaskType.CONTENT_ANALYSIS,
                score,
                details
            )
            
        except Exception as e:
            logger.error(f"内容分析失败: {e}")
            return self._create_analysis_result(
                TaskType.CONTENT_ANALYSIS,
                5.0,
                {"error": str(e)},
                confidence=0.1
            )


class AnalyzerFactory:
    """分析器工厂类"""
    
    _adapters = {
        "speech": SpeechAnalyzerAdapter,
        "visual": VisualAnalyzerAdapter,
        "content": ContentAnalyzerAdapter
    }
    
    @classmethod
    def create_adapter(cls, analyzer_type: str, config: Optional[Dict[str, Any]] = None) -> AnalyzerAdapter:
        """创建分析器适配器
        
        Args:
            analyzer_type: 分析器类型
            config: 配置参数
            
        Returns:
            AnalyzerAdapter: 分析器适配器
        """
        if analyzer_type not in cls._adapters:
            raise ValueError(f"不支持的分析器类型: {analyzer_type}")
        
        adapter_class = cls._adapters[analyzer_type]
        return adapter_class(config)
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """获取支持的分析器类型
        
        Returns:
            List[str]: 支持的分析器类型列表
        """
        return list(cls._adapters.keys())