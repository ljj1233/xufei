# ai_agent/analyzers/speech_analyzer.py

from typing import Dict, Any, Optional
import os
import librosa
import numpy as np

from ..core.analyzer import Analyzer
from ..core.config import AgentConfig
from ..services.xunfei_service import XunFeiService
from ..core.utils import normalize_score, weighted_average


class SpeechAnalyzer(Analyzer):
    """语音分析器
    
    负责提取和分析语音特征，包括清晰度、语速和情感等
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化语音分析器
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        super().__init__(name="speech_analyzer", analyzer_type="speech", config=config)
        
        # 初始化讯飞服务
        self.use_xunfei = self.get_config("use_xunfei", True)
        if self.use_xunfei:
            self.xunfei_service = XunFeiService(self.config)
    
    def extract_features(self, file_path: str) -> Dict[str, Any]:
        """提取语音特征
        
        从音频文件中提取语音特征
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            Dict[str, Any]: 提取的语音特征
        """
        try:
            # 读取音频文件
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            features = {}
            
            # 如果启用讯飞服务，调用讯飞API
            if self.use_xunfei:
                # 调用讯飞语音评测服务
                xunfei_assessment = self.xunfei_service.speech_assessment(audio_data)
                features["xunfei_assessment"] = xunfei_assessment
                
                # 调用讯飞情感分析服务
                xunfei_emotion = self.xunfei_service.emotion_analysis(audio_data)
                features["xunfei_emotion"] = xunfei_emotion
            
            # 同时保留一些基本的音频特征分析作为补充
            y, sr = librosa.load(file_path, sr=None)
            
            # 提取基本音频特征
            features.update({
                # 基本音频特征
                "mfcc": librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1).tolist(),
                "spectral_centroid": float(librosa.feature.spectral_centroid(y=y, sr=sr).mean()),
                "zero_crossing_rate": float(librosa.feature.zero_crossing_rate(y).mean()),
                "tempo": float(librosa.beat.tempo(y=y, sr=sr)[0]),
                "rms": float(librosa.feature.rms(y=y).mean()),
            })
            
            return features
        
        except Exception as e:
            print(f"提取语音特征失败: {e}")
            return {}
    
    def analyze(self, features: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """分析语音特征
        
        根据提取的语音特征进行分析
        
        Args:
            features: 提取的语音特征
            params: 分析参数，如果为None则使用默认参数
            
        Returns:
            Dict[str, Any]: 语音分析结果
        """
        if not features:
            return {
                "clarity": 5.0,
                "pace": 5.0,
                "emotion": "中性",
                "overall_score": 5.0
            }
        
        # 获取权重配置
        clarity_weight = self.get_config("clarity_weight", 0.3)
        pace_weight = self.get_config("pace_weight", 0.3)
        emotion_weight = self.get_config("emotion_weight", 0.4)
        
        # 如果提供了参数，覆盖默认权重
        if params:
            clarity_weight = params.get("clarity_weight", clarity_weight)
            pace_weight = params.get("pace_weight", pace_weight)
            emotion_weight = params.get("emotion_weight", emotion_weight)
        
        # 分析清晰度
        clarity = self._analyze_clarity(features)
        
        # 分析语速
        pace = self._analyze_pace(features)
        
        # 分析情感
        emotion, emotion_score = self._analyze_emotion(features)
        
        # 计算总分
        overall_score = weighted_average(
            {
                "clarity": clarity,
                "pace": pace,
                "emotion": emotion_score
            },
            {
                "clarity": clarity_weight,
                "pace": pace_weight,
                "emotion": emotion_weight
            }
        )
        
        return {
            "clarity": clarity,
            "pace": pace,
            "emotion": emotion,
            "emotion_score": emotion_score,
            "overall_score": overall_score
        }
    
    def _analyze_clarity(self, features: Dict[str, Any]) -> float:
        """分析清晰度
        
        Args:
            features: 语音特征
            
        Returns:
            float: 清晰度评分（0-10）
        """
        # 获取讯飞API评测结果
        xunfei_assessment = features.get("xunfei_assessment", {})
        
        # 使用讯飞评测结果计算清晰度（如果有）
        if xunfei_assessment and "clarity" in xunfei_assessment:
            # 讯飞评测结果通常是百分制，转换为10分制
            clarity = min(10.0, max(0.0, xunfei_assessment.get("clarity", 50) / 10))
        else:
            # 使用备选方法计算清晰度
            spectral_centroid = features.get("spectral_centroid", 1000)
            rms = features.get("rms", 0.1)
            
            # 简单算法：根据频谱质心和RMS能量估计清晰度
            # 频谱质心越高，通常表示声音越清晰
            # RMS能量越高，通常表示声音越响亮
            clarity = min(10.0, max(0.0, 5.0 + spectral_centroid / 2000 + rms * 10))
        
        return normalize_score(clarity)
    
    def _analyze_pace(self, features: Dict[str, Any]) -> float:
        """分析语速
        
        Args:
            features: 语音特征
            
        Returns:
            float: 语速评分（0-10，5分为最佳）
        """
        # 获取讯飞API评测结果
        xunfei_assessment = features.get("xunfei_assessment", {})
        
        # 使用讯飞评测结果计算语速（如果有）
        if xunfei_assessment and "speed" in xunfei_assessment:
            # 讯飞语速评分，转换为10分制
            # 假设讯飞返回的语速是一个0-100的分数，其中50表示标准语速
            xunfei_speed = xunfei_assessment.get("speed", 50)
            # 将语速转换为10分制评分，5分表示标准语速
            if xunfei_speed < 50:
                # 语速过慢，分数越低
                pace = 5.0 * (xunfei_speed / 50)
            elif xunfei_speed > 50:
                # 语速过快，分数越低
                pace = 10.0 - 5.0 * ((xunfei_speed - 50) / 50)
            else:
                pace = 5.0
        else:
            # 使用备选方法计算语速
            tempo = features.get("tempo", 120)
            zcr = features.get("zero_crossing_rate", 0.1)
            
            # 简单算法：根据节奏和过零率估计语速
            # 标准语速约为120-130 BPM
            if tempo < 100:
                # 语速过慢
                pace = 5.0 * (tempo / 100)
            elif tempo > 140:
                # 语速过快
                pace = 10.0 - 5.0 * ((tempo - 140) / 60)
            else:
                # 语速适中，给予高分
                pace = 7.5 + 2.5 * (1 - abs(tempo - 120) / 20)
        
        return normalize_score(pace)
    
    def _analyze_emotion(self, features: Dict[str, Any]) -> tuple:
        """分析情感
        
        Args:
            features: 语音特征
            
        Returns:
            tuple: (情感类型, 情感评分)
        """
        # 获取讯飞API情感分析结果
        xunfei_emotion = features.get("xunfei_emotion", {})
        
        # 使用讯飞情感分析结果（如果有）
        if xunfei_emotion and "emotion" in xunfei_emotion:
            emotion = xunfei_emotion.get("emotion", "中性")
            confidence = xunfei_emotion.get("confidence", 0.5)
            
            # 根据情感类型和置信度计算评分
            if emotion in ["平静", "中性"]:
                # 平静/中性情感适合面试，给予高分
                emotion_score = 7.0 + 3.0 * confidence
            elif emotion in ["高兴", "积极"]:
                # 积极情感也适合面试，但过于兴奋可能不适合
                emotion_score = 6.0 + 4.0 * confidence
            elif emotion in ["紧张", "焦虑"]:
                # 紧张情感在面试中常见，但不宜过度
                emotion_score = 5.0 + 2.0 * confidence
            else:
                # 其他情感（如愤怒、悲伤等）通常不适合面试
                emotion_score = 3.0 + 2.0 * confidence
        else:
            # 使用备选方法估计情感
            # 这里使用简单的启发式方法，实际应用中应使用更复杂的情感识别模型
            mfcc = features.get("mfcc", [])
            rms = features.get("rms", 0.1)
            zcr = features.get("zero_crossing_rate", 0.1)
            
            # 简单估计：高能量、高过零率可能表示积极情感
            if rms > 0.2 and zcr > 0.15:
                emotion = "积极"
                emotion_score = 8.0
            elif rms < 0.05 and zcr < 0.05:
                emotion = "消极"
                emotion_score = 4.0
            else:
                emotion = "中性"
                emotion_score = 6.0
        
        return emotion, normalize_score(emotion_score)
    
    def speech_to_text(self, file_path: str) -> str:
        """语音转文本
        
        将语音文件转换为文本
        
        Args:
            file_path: 语音文件路径
            
        Returns:
            str: 转换后的文本
        """
        try:
            # 读取音频文件
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            # 如果启用讯飞服务，调用讯飞语音识别API
            if self.use_xunfei and hasattr(self, 'xunfei_service'):
                text = self.xunfei_service.speech_recognition(audio_data)
                return text
            else:
                # 如果未启用讯飞服务，返回空文本
                # 实际应用中，可以集成其他语音识别服务
                return ""
        
        except Exception as e:
            print(f"语音转文本失败: {e}")
            return ""