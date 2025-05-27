"""分析器适配器模块（重构版）

将旧的分析器适配到新的LangGraph框架中，支持多模态分析。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type
import logging
import os
import sys
from pathlib import Path

# 添加analyzers目录到系统路径，以便导入旧的分析器
sys.path.append(str(Path(__file__).parent.parent))

from .state import Task, AnalysisResult


class AnalyzerAdapter(ABC):
    """分析器适配器抽象基类
    
    将旧的分析器接口适配到新的框架中
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化分析器适配器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.analyzer = None
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化分析器
        
        Returns:
            bool: 是否初始化成功
        """
        pass
    
    @abstractmethod
    def analyze(self, task: Task, data: Any) -> Dict[str, Any]:
        """执行分析
        
        Args:
            task: 任务对象
            data: 分析数据
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        pass
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """获取分析器信息
        
        Returns:
            Dict[str, Any]: 分析器信息
        """
        return {
            'name': self.__class__.__name__,
            'type': 'unknown',
            'initialized': self.analyzer is not None
        }


class SpeechAnalyzerAdapter(AnalyzerAdapter):
    """语音分析器适配器
    
    适配旧的语音分析器到新框架
    """
    
    def initialize(self) -> bool:
        """初始化语音分析器
        
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 导入旧的语音分析器
            from analyzers.speech_analyzer_refactored import SpeechAnalyzer
            from core.config import AgentConfig
            
            # 创建配置对象
            agent_config = AgentConfig(self.config)
            
            # 初始化分析器
            self.analyzer = SpeechAnalyzer(agent_config)
            self.logger.info("语音分析器初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"语音分析器初始化失败: {e}")
            return False
    
    def analyze(self, task: Task, data: Any) -> Dict[str, Any]:
        """执行语音分析
        
        Args:
            task: 任务对象
            data: 音频文件路径或音频数据
            
        Returns:
            Dict[str, Any]: 语音分析结果
        """
        try:
            if self.analyzer is None:
                if not self.initialize():
                    return {'error': '语音分析器未初始化'}
            
            # 检查数据类型
            if isinstance(data, str) and os.path.exists(data):
                # 文件路径
                features = self.analyzer.extract_features(data)
                analysis_result = self.analyzer.analyze(features)
                return analysis_result
            else:
                return {'error': '无效的音频数据'}
                
        except Exception as e:
            self.logger.error(f"语音分析失败: {e}")
            return {'error': str(e)}
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """获取分析器信息
        
        Returns:
            Dict[str, Any]: 分析器信息
        """
        info = super().get_analyzer_info()
        info['type'] = 'speech'
        return info


class VisualAnalyzerAdapter(AnalyzerAdapter):
    """视觉分析器适配器
    
    适配旧的视觉分析器到新框架
    """
    
    def initialize(self) -> bool:
        """初始化视觉分析器
        
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 导入旧的视觉分析器
            from analyzers.visual_analyzer import VisualAnalyzer
            from core.config import AgentConfig
            
            # 创建配置对象
            agent_config = AgentConfig(self.config)
            
            # 初始化分析器
            self.analyzer = VisualAnalyzer(agent_config)
            self.logger.info("视觉分析器初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"视觉分析器初始化失败: {e}")
            return False
    
    def analyze(self, task: Task, data: Any) -> Dict[str, Any]:
        """执行视觉分析
        
        Args:
            task: 任务对象
            data: 视频文件路径或图像数据
            
        Returns:
            Dict[str, Any]: 视觉分析结果
        """
        try:
            if self.analyzer is None:
                if not self.initialize():
                    return {'error': '视觉分析器未初始化'}
            
            # 检查数据类型
            if isinstance(data, str) and os.path.exists(data):
                # 文件路径
                features = self.analyzer.extract_features(data)
                analysis_result = self.analyzer.analyze(features)
                return analysis_result
            else:
                return {'error': '无效的视频/图像数据'}
                
        except Exception as e:
            self.logger.error(f"视觉分析失败: {e}")
            return {'error': str(e)}
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """获取分析器信息
        
        Returns:
            Dict[str, Any]: 分析器信息
        """
        info = super().get_analyzer_info()
        info['type'] = 'visual'
        return info


class ContentAnalyzerAdapter(AnalyzerAdapter):
    """内容分析器适配器
    
    适配旧的内容分析器到新框架
    """
    
    def initialize(self) -> bool:
        """初始化内容分析器
        
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 导入旧的内容分析器
            from analyzers.content_analyzer import ContentAnalyzer
            from core.config import AgentConfig
            
            # 创建配置对象
            agent_config = AgentConfig(self.config)
            
            # 初始化分析器
            self.analyzer = ContentAnalyzer(agent_config)
            self.logger.info("内容分析器初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"内容分析器初始化失败: {e}")
            return False
    
    def analyze(self, task: Task, data: Any) -> Dict[str, Any]:
        """执行内容分析
        
        Args:
            task: 任务对象
            data: 文本内容或文本文件路径
            
        Returns:
            Dict[str, Any]: 内容分析结果
        """
        try:
            if self.analyzer is None:
                if not self.initialize():
                    return {'error': '内容分析器未初始化'}
            
            # 检查数据类型
            if isinstance(data, str):
                if os.path.exists(data):
                    # 文件路径，读取文件内容
                    with open(data, 'r', encoding='utf-8') as f:
                        content = f.read()
                else:
                    # 直接是文本内容
                    content = data
                
                features = self.analyzer.extract_features(content)
                analysis_result = self.analyzer.analyze(features)
                return analysis_result
            else:
                return {'error': '无效的文本数据'}
                
        except Exception as e:
            self.logger.error(f"内容分析失败: {e}")
            return {'error': str(e)}
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """获取分析器信息
        
        Returns:
            Dict[str, Any]: 分析器信息
        """
        info = super().get_analyzer_info()
        info['type'] = 'content'
        return info


class OverallAnalyzerAdapter(AnalyzerAdapter):
    """综合分析器适配器
    
    适配旧的综合分析器到新框架
    """
    
    def initialize(self) -> bool:
        """初始化综合分析器
        
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 导入旧的综合分析器
            from analyzers.overall_analyzer import OverallAnalyzer
            from core.config import AgentConfig
            
            # 创建配置对象
            agent_config = AgentConfig(self.config)
            
            # 初始化分析器
            self.analyzer = OverallAnalyzer(agent_config)
            self.logger.info("综合分析器初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"综合分析器初始化失败: {e}")
            return False
    
    def analyze(self, task: Task, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行综合分析
        
        Args:
            task: 任务对象
            data: 各维度分析结果
            
        Returns:
            Dict[str, Any]: 综合分析结果
        """
        try:
            if self.analyzer is None:
                if not self.initialize():
                    return {'error': '综合分析器未初始化'}
            
            # 检查数据类型
            if isinstance(data, dict):
                analysis_result = self.analyzer.analyze(data)
                return analysis_result
            else:
                return {'error': '无效的分析数据'}
                
        except Exception as e:
            self.logger.error(f"综合分析失败: {e}")
            return {'error': str(e)}
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """获取分析器信息
        
        Returns:
            Dict[str, Any]: 分析器信息
        """
        info = super().get_analyzer_info()
        info['type'] = 'overall'
        return info


class AnalyzerFactory:
    """分析器工厂
    
    创建和管理分析器适配器实例
    """
    
    _adapters: Dict[str, Type[AnalyzerAdapter]] = {
        'speech': SpeechAnalyzerAdapter,
        'visual': VisualAnalyzerAdapter,
        'content': ContentAnalyzerAdapter,
        'overall': OverallAnalyzerAdapter
    }
    
    @classmethod
    def create_analyzer(cls, analyzer_type: str, config: Dict[str, Any] = None) -> Optional[AnalyzerAdapter]:
        """创建分析器适配器
        
        Args:
            analyzer_type: 分析器类型
            config: 配置参数
            
        Returns:
            Optional[AnalyzerAdapter]: 分析器适配器实例，如果类型无效则返回None
        """
        if analyzer_type not in cls._adapters:
            logging.error(f"无效的分析器类型: {analyzer_type}")
            return None
        
        adapter_class = cls._adapters[analyzer_type]
        adapter = adapter_class(config)
        
        # 初始化分析器
        if not adapter.initialize():
            logging.warning(f"分析器初始化失败: {analyzer_type}")
        
        return adapter
    
    @classmethod
    def get_available_analyzers(cls) -> List[str]:
        """获取可用的分析器类型
        
        Returns:
            List[str]: 可用的分析器类型列表
        """
        return list(cls._adapters.keys())
    
    @classmethod
    def register_analyzer(cls, analyzer_type: str, adapter_class: Type[AnalyzerAdapter]) -> None:
        """注册新的分析器适配器
        
        Args:
            analyzer_type: 分析器类型
            adapter_class: 适配器类
        """
        cls._adapters[analyzer_type] = adapter_class
        logging.info(f"注册分析器适配器: {analyzer_type}")