# ai_agent/core/agent.py

from typing import Dict, Any, Optional, List
import os
import json

from .config import AgentConfig
from ..analyzers.speech_analyzer import SpeechAnalyzer
from ..analyzers.visual_analyzer import VisualAnalyzer
from ..analyzers.content_analyzer import ContentAnalyzer
from ..analyzers.overall_analyzer import OverallAnalyzer


class AnalysisResult:
    """分析结果类，封装所有分析结果并提供便捷的访问方法"""
    
    def __init__(self, raw_result: Dict[str, Any]):
        self.raw_result = raw_result
    
    def get_full_analysis(self) -> Dict[str, Any]:
        """获取完整分析结果"""
        return self.raw_result
    
    def get_speech_analysis(self) -> Dict[str, Any]:
        """获取语音分析结果"""
        return self.raw_result.get("speech", {})
    
    def get_visual_analysis(self) -> Dict[str, Any]:
        """获取视觉分析结果"""
        return self.raw_result.get("visual", {})
    
    def get_content_analysis(self) -> Dict[str, Any]:
        """获取内容分析结果"""
        return self.raw_result.get("content", {})
    
    def get_overall_score(self) -> float:
        """获取综合评分"""
        return self.raw_result.get("overall", {}).get("score", 0.0)
    
    def get_strengths(self) -> List[str]:
        """获取优势列表"""
        return self.raw_result.get("overall", {}).get("strengths", [])
    
    def get_weaknesses(self) -> List[str]:
        """获取劣势列表"""
        return self.raw_result.get("overall", {}).get("weaknesses", [])
    
    def get_suggestions(self) -> List[str]:
        """获取建议列表"""
        return self.raw_result.get("overall", {}).get("suggestions", [])


class InterviewAgent:
    """面试评测智能体主类
    
    负责协调各个分析器，根据场景选择合适的分析策略，并整合分析结果
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化面试评测智能体
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        # 加载配置
        self.config = AgentConfig(config_path)
        
        # 初始化分析器
        self.speech_analyzer = SpeechAnalyzer(self.config)
        self.visual_analyzer = VisualAnalyzer(self.config)
        self.content_analyzer = ContentAnalyzer(self.config)
        self.overall_analyzer = OverallAnalyzer(self.config)
        
        # 初始化场景注册表
        self.scenarios = {}
        self._load_default_scenarios()
    
    def _load_default_scenarios(self):
        """加载默认场景"""
        # 导入并注册默认场景
        from ..scenarios.tech_interview import TechInterviewScenario
        
        # 创建场景实例并注册
        tech_interview = TechInterviewScenario()
        self.register_scenario(tech_interview)
    
    def register_scenario(self, scenario):
        """注册新场景
        
        Args:
            scenario: 场景实例
        """
        self.scenarios[scenario.name] = scenario
    
    def register_analyzer(self, analyzer):
        """注册新分析器
        
        Args:
            analyzer: 分析器实例
        """
        # 根据分析器类型注册到相应位置
        if analyzer.type == "speech":
            self.speech_analyzer = analyzer
        elif analyzer.type == "visual":
            self.visual_analyzer = analyzer
        elif analyzer.type == "content":
            self.content_analyzer = analyzer
        elif analyzer.type == "overall":
            self.overall_analyzer = analyzer
    
    def _detect_scenario(self, file_path: str, file_type: str) -> str:
        """检测面试场景
        
        根据文件内容自动检测面试场景类型
        
        Args:
            file_path: 文件路径
            file_type: 文件类型（video或audio）
            
        Returns:
            str: 场景名称
        """
        # 提取基本特征用于场景识别
        # 这里简化处理，实际实现需要更复杂的特征提取和场景识别逻辑
        
        # 默认返回通用场景
        return "general_interview"
    
    def analyze(self, file_path: str, file_type: Optional[str] = None, 
                scenario: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """分析面试
        
        对面试文件进行多模态分析
        
        Args:
            file_path: 文件路径
            file_type: 文件类型（video或audio），如果为None则自动检测
            scenario: 场景名称，如果为None则自动检测
            params: 分析参数，如果为None则使用场景默认参数
            
        Returns:
            AnalysisResult: 分析结果
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 自动检测文件类型（如果未指定）
        if file_type is None:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in [".mp4", ".avi", ".mov", ".wmv"]:
                file_type = "video"
            elif ext in [".mp3", ".wav", ".ogg", ".flac"]:
                file_type = "audio"
            else:
                raise ValueError(f"无法识别的文件类型: {ext}")
        
        # 自动检测场景（如果未指定）
        if scenario is None:
            scenario = self._detect_scenario(file_path, file_type)
        
        # 获取场景特定的分析参数
        scenario_params = {}
        if scenario in self.scenarios:
            scenario_params = self.scenarios[scenario].get_analysis_params()
        
        # 合并用户提供的参数（优先级更高）
        if params:
            scenario_params.update(params)
        
        # 初始化结果
        result = {
            "speech": {},
            "visual": {},
            "content": {},
            "overall": {}
        }
        
        # 提取语音特征并分析
        speech_features = self.speech_analyzer.extract_features(file_path)
        result["speech"] = self.speech_analyzer.analyze(speech_features, scenario_params)
        
        # 如果是视频，提取视觉特征并分析
        if file_type == "video":
            visual_features = self.visual_analyzer.extract_features(file_path)
            result["visual"] = self.visual_analyzer.analyze(visual_features, scenario_params)
        
        # 提取文本内容并分析
        text_content = self.speech_analyzer.speech_to_text(file_path)
        result["content"] = self.content_analyzer.analyze(text_content, scenario_params)
        
        # 综合分析
        result["overall"] = self.overall_analyzer.analyze(result, scenario_params)
        
        return AnalysisResult(result)