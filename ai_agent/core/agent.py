# ai_agent/core/agent.py

from typing import Dict, Any, Optional, List, Callable, AsyncGenerator
import os
import json
import asyncio
import time
from datetime import datetime

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
    
    负责协调各个分析器，支持实时面试分析和流式反馈
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
        
        # 实时分析状态
        self.is_analyzing = False
        self.session_start_time = None
        self.current_session_id = None
        self.feedback_callbacks = []
    
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
    
    async def start_real_time_analysis(self, session_id: str, scenario: str = "technical", 
                                      feedback_callback: Optional[Callable] = None) -> bool:
        """开始实时分析
        
        Args:
            session_id: 面试会话ID
            scenario: 面试场景
            feedback_callback: 反馈回调函数
            
        Returns:
            bool: 是否成功开始
        """
        if self.is_analyzing:
            return False
            
        self.is_analyzing = True
        self.current_session_id = session_id
        self.session_start_time = time.time()
        
        if feedback_callback:
            self.feedback_callbacks.append(feedback_callback)
            
        return True
    
    async def stop_real_time_analysis(self, session_id: str) -> bool:
        """停止实时分析
        
        Args:
            session_id: 面试会话ID
            
        Returns:
            bool: 是否成功停止
        """
        if self.current_session_id == session_id:
            self.is_analyzing = False
            self.current_session_id = None
            self.session_start_time = None
            self.feedback_callbacks.clear()
            return True
        return False
    
    async def analyze_audio_stream(self, session_id: str, audio_data: bytes, 
                                  timestamp: float = None) -> Dict[str, Any]:
        """分析音频流数据
        
        Args:
            session_id: 会话ID
            audio_data: 音频数据
            timestamp: 时间戳
            
        Returns:
            Dict[str, Any]: 实时分析结果
        """
        if not self.is_analyzing or self.current_session_id != session_id:
            return {}
            
        try:
            # 提取音频特征
            features = self.speech_analyzer.extract_stream_features(audio_data)
            
            # 进行实时语音分析
            speech_result = self.speech_analyzer.analyze_stream(features)
            
            # 计算会话时间
            session_time = time.time() - self.session_start_time if self.session_start_time else 0
            
            # 构建反馈结果
            feedback = {
                "session_id": self.current_session_id,
                "timestamp": timestamp or time.time(),
                "session_time": session_time,
                "feedback_type": "speech",
                "analysis": speech_result,
                "suggestions": self._generate_real_time_suggestions(speech_result)
            }
            
            # 触发回调
            for callback in self.feedback_callbacks:
                try:
                    await callback(session_id, feedback)
                except Exception as e:
                    print(f"回调函数执行失败: {e}")
            
            return speech_result
            
        except Exception as e:
            print(f"音频流分析失败: {e}")
            return {}
    
    async def analyze_video_frame(self, session_id: str, frame_data: bytes, 
                                 timestamp: float = None) -> Dict[str, Any]:
        """分析视频帧数据
        
        Args:
            session_id: 会话ID
            frame_data: 视频帧数据
            timestamp: 时间戳
            
        Returns:
            Dict[str, Any]: 实时分析结果
        """
        if not self.is_analyzing or self.current_session_id != session_id:
            return {}
            
        try:
            # 提取视觉特征
            features = self.visual_analyzer.extract_frame_features(frame_data)
            
            # 进行实时视觉分析
            visual_result = self.visual_analyzer.analyze_frame(features)
            
            # 计算会话时间
            session_time = time.time() - self.session_start_time if self.session_start_time else 0
            
            # 构建反馈结果
            feedback = {
                "session_id": self.current_session_id,
                "timestamp": timestamp or time.time(),
                "session_time": session_time,
                "feedback_type": "visual",
                "analysis": visual_result,
                "suggestions": self._generate_real_time_suggestions(visual_result)
            }
            
            # 触发回调
            for callback in self.feedback_callbacks:
                try:
                    await callback(session_id, feedback)
                except Exception as e:
                    print(f"回调函数执行失败: {e}")
            
            return visual_result
            
        except Exception as e:
            print(f"视频帧分析失败: {e}")
            return {}
    
    async def analyze_question_answer(self, session_id: str, question_id: int, answer_text: str, 
                                     audio_features: Dict[str, Any] = None,
                                     visual_features: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析问题回答
        
        Args:
            question_id: 问题ID
            answer_text: 回答文本
            audio_features: 音频特征
            visual_features: 视觉特征
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        result = {
            "question_id": question_id,
            "content_analysis": {},
            "speech_analysis": {},
            "visual_analysis": {},
            "overall_scores": {}
        }
        
        try:
            # 内容分析
            result["content_analysis"] = self.content_analyzer.analyze(answer_text)
            
            # 语音分析（如果有音频特征）
            if audio_features:
                result["speech_analysis"] = self.speech_analyzer.analyze(audio_features)
            
            # 视觉分析（如果有视觉特征）
            if visual_features:
                result["visual_analysis"] = self.visual_analyzer.analyze(visual_features)
            
            # 综合评分
            result["overall_scores"] = self.overall_analyzer.analyze_question(result)
            
        except Exception as e:
            print(f"问题回答分析失败: {e}")
        
        return result
    
    def _generate_real_time_suggestions(self, analysis_result: Dict[str, Any]) -> List[str]:
        """生成实时建议
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            List[str]: 建议列表
        """
        suggestions = []
        
        try:
            # 根据分析结果生成建议
            if "clarity" in analysis_result:
                clarity = analysis_result["clarity"]
                if clarity < 6.0:
                    suggestions.append("请尽量清晰地表达，注意发音")
            
            if "pace" in analysis_result:
                pace = analysis_result["pace"]
                if pace < 5.0:
                    suggestions.append("语速偏慢，可以适当加快")
                elif pace > 8.0:
                    suggestions.append("语速偏快，建议放慢一些")
            
            if "eye_contact" in analysis_result:
                eye_contact = analysis_result["eye_contact"]
                if eye_contact < 6.0:
                    suggestions.append("增加与摄像头的眼神接触")
            
            if "confidence" in analysis_result:
                confidence = analysis_result["confidence"]
                if confidence < 6.0:
                    suggestions.append("保持自信，放松心态")
                    
        except Exception as e:
            print(f"生成实时建议失败: {e}")
        
        return suggestions