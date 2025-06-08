from typing import Dict, Any, List, Optional
import numpy as np
import logging
from app.services.audio_feature_extractor import AudioFeatureExtractor

logger = logging.getLogger(__name__)

class SpeechAnalyzer:
    """语音分析器，负责分析语音的流畅度、语速和声音能量"""
    
    def __init__(self, feature_extractor=None):
        """初始化语音分析器
        
        Args:
            feature_extractor: 音频特征提取器实例
        """
        self.feature_extractor = feature_extractor or AudioFeatureExtractor()
    
    async def analyze_speech(self, audio_data: bytes) -> Dict[str, Any]:
        """分析语音
        
        Args:
            audio_data: 音频数据
            
        Returns:
            Dict[str, Any]: 语音分析结果
        """
        try:
            if audio_data is None or len(audio_data) == 0:
                logger.warning("No audio data provided for speech analysis")
                return self._get_empty_analysis_result()
            
            # 提取音频特征
            features = self.feature_extractor.extract_features(audio_data)
            
            if not features:
                logger.warning("Failed to extract audio features")
                return self._get_empty_analysis_result()
            
            # 分析流畅度
            fluency_score, fluency_details = self._analyze_fluency(features)
            
            # 分析语速
            speech_rate_score, speech_rate_details = self._analyze_speech_rate(features)
            
            # 分析声音能量
            vocal_energy_score, vocal_energy_details = self._analyze_vocal_energy(features)
            
            # 分析语言简洁性
            conciseness_score = self._analyze_conciseness(features)
            
            return {
                "fluency": fluency_score,
                "fluency_details": fluency_details,
                "speech_rate": speech_rate_score,
                "speech_rate_details": speech_rate_details,
                "vocal_energy": vocal_energy_score,
                "vocal_energy_details": vocal_energy_details,
                "conciseness": conciseness_score,
                "conciseness_review": self._get_conciseness_review(conciseness_score)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing speech: {str(e)}")
            return self._get_empty_analysis_result()
    
    def _analyze_fluency(self, features: Dict[str, Any]) -> tuple:
        """分析语言流畅度
        
        Args:
            features: 音频特征
            
        Returns:
            tuple: (流畅度评分, 流畅度详情)
        """
        try:
            # 获取填充词统计和不自然停顿
            filler_words_count = features.get("filler_words_count", 0)
            unnatural_pauses_count = features.get("unnatural_pauses_count", 0)
            
            # 基于填充词和不自然停顿计算流畅度评分
            # 填充词越多，评分越低
            filler_penalty = min(3.0, filler_words_count * 0.5)
            
            # 不自然停顿越多，评分越低
            pause_penalty = min(3.0, unnatural_pauses_count * 0.7)
            
            # 基础分10分，减去填充词和不自然停顿的惩罚
            fluency_score = max(1.0, 10.0 - filler_penalty - pause_penalty)
            
            fluency_details = {
                "filler_words_count": filler_words_count,
                "unnatural_pauses_count": unnatural_pauses_count
            }
            
            return fluency_score, fluency_details
            
        except Exception as e:
            logger.error(f"Error analyzing fluency: {str(e)}")
            return 5.0, {"filler_words_count": 0, "unnatural_pauses_count": 0}
    
    def _analyze_speech_rate(self, features: Dict[str, Any]) -> tuple:
        """分析语速
        
        Args:
            features: 音频特征
            
        Returns:
            tuple: (语速评分, 语速详情)
        """
        try:
            # 获取每分钟字数
            words_per_minute = features.get("words_per_minute", 150)
            
            # 理想语速范围：140-180 WPM
            if 140 <= words_per_minute <= 180:
                speech_rate_score = 9.0
                pace_category = "适中"
            elif 120 <= words_per_minute < 140 or 180 < words_per_minute <= 200:
                speech_rate_score = 7.0
                pace_category = "尚可"
            elif words_per_minute < 120:
                speech_rate_score = max(3.0, 7.0 - (120 - words_per_minute) / 20)
                pace_category = "偏慢"
            else:  # words_per_minute > 200
                speech_rate_score = max(3.0, 7.0 - (words_per_minute - 200) / 20)
                pace_category = "偏快"
            
            speech_rate_details = {
                "words_per_minute": words_per_minute,
                "pace_category": pace_category
            }
            
            return speech_rate_score, speech_rate_details
            
        except Exception as e:
            logger.error(f"Error analyzing speech rate: {str(e)}")
            return 5.0, {"words_per_minute": 150, "pace_category": "未知"}
    
    def _analyze_vocal_energy(self, features: Dict[str, Any]) -> tuple:
        """分析声音能量
        
        Args:
            features: 音频特征
            
        Returns:
            tuple: (声音能量评分, 声音能量详情)
        """
        try:
            # 获取音高标准差
            pitch_std_dev = features.get("pitch_std_dev", 10.0)
            
            # 音高变化适中（有抑扬顿挫）：10-25
            if 10.0 <= pitch_std_dev <= 25.0:
                vocal_energy_score = 8.0
                pitch_category = "平稳有变化"
            elif 5.0 <= pitch_std_dev < 10.0 or 25.0 < pitch_std_dev <= 35.0:
                vocal_energy_score = 6.0
                pitch_category = "变化适中"
            elif pitch_std_dev < 5.0:
                vocal_energy_score = 4.0
                pitch_category = "过于平稳"
            else:  # pitch_std_dev > 35.0
                vocal_energy_score = 5.0
                pitch_category = "变化过大"
            
            # 获取音量信息
            volume_avg = features.get("volume_avg", 0.5)
            
            # 音量评分（0.3-0.7是适中范围）
            if 0.3 <= volume_avg <= 0.7:
                volume_score = 8.0
            elif 0.2 <= volume_avg < 0.3 or 0.7 < volume_avg <= 0.8:
                volume_score = 6.0
            else:
                volume_score = 4.0
            
            # 综合评分
            vocal_energy_score = (vocal_energy_score * 0.7 + volume_score * 0.3)
            
            vocal_energy_details = {
                "pitch_std_dev": pitch_std_dev,
                "pitch_category": pitch_category,
                "volume_avg": volume_avg
            }
            
            return vocal_energy_score, vocal_energy_details
            
        except Exception as e:
            logger.error(f"Error analyzing vocal energy: {str(e)}")
            return 5.0, {"pitch_std_dev": 10.0, "pitch_category": "未知", "volume_avg": 0.5}
    
    def _analyze_conciseness(self, features: Dict[str, Any]) -> float:
        """分析语言简洁性
        
        Args:
            features: 音频特征
            
        Returns:
            float: 简洁性评分
        """
        try:
            # 获取语音时长和字数
            duration_seconds = features.get("duration_seconds", 60)
            word_count = features.get("word_count", 150)
            
            # 计算每秒字数
            words_per_second = word_count / max(1, duration_seconds)
            
            # 理想的简洁表达：2.5-3.0 字/秒
            if 2.5 <= words_per_second <= 3.0:
                return 9.0
            elif 2.0 <= words_per_second < 2.5 or 3.0 < words_per_second <= 3.5:
                return 7.0
            elif words_per_second < 2.0:
                return max(4.0, 7.0 - (2.0 - words_per_second) * 2)
            else:  # words_per_second > 3.5
                return max(4.0, 7.0 - (words_per_second - 3.5) * 2)
                
        except Exception as e:
            logger.error(f"Error analyzing conciseness: {str(e)}")
            return 5.0
    
    def _get_conciseness_review(self, score: float) -> str:
        """根据简洁性评分生成评价
        
        Args:
            score: 简洁性评分
            
        Returns:
            str: 简洁性评价
        """
        if score >= 8.0:
            return "表达简洁有力，没有冗余内容"
        elif score >= 6.0:
            return "表达较为简洁，有少量冗余"
        elif score >= 4.0:
            return "表达有些冗长，可以更加精简"
        else:
            return "表达过于冗长或过于简略，需要调整"
    
    def _get_empty_analysis_result(self) -> Dict[str, Any]:
        """获取空的分析结果
        
        Returns:
            Dict[str, Any]: 空的分析结果
        """
        return {
            "fluency": 5.0,
            "fluency_details": {
                "filler_words_count": 0,
                "unnatural_pauses_count": 0
            },
            "speech_rate": 5.0,
            "speech_rate_details": {
                "words_per_minute": 150,
                "pace_category": "未知"
            },
            "vocal_energy": 5.0,
            "vocal_energy_details": {
                "pitch_std_dev": 10.0,
                "pitch_category": "未知",
                "volume_avg": 0.5
            },
            "conciseness": 5.0,
            "conciseness_review": "无法评估语言简洁性"
        }