from typing import Dict, Any, List, Optional
import numpy as np
import io
import logging
import re
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

logger = logging.getLogger(__name__)

class AudioFeatureExtractor:
    """音频特征提取器，负责从音频数据中提取各种特征"""
    
    def __init__(self):
        """初始化音频特征提取器"""
        # 填充词列表（中英文）
        self.filler_words = [
            "嗯", "呃", "啊", "那个", "就是", "这个", "然后", "所以", "其实", "怎么说",
            "um", "uh", "ah", "like", "you know", "so", "well", "I mean"
        ]
        
        # 填充词正则表达式
        self.filler_pattern = re.compile(r'\b(' + '|'.join(self.filler_words) + r')\b', re.IGNORECASE)
    
    def extract_features(self, audio_data: bytes) -> Dict[str, Any]:
        """从音频数据中提取特征
        
        Args:
            audio_data: 音频数据
            
        Returns:
            Dict[str, Any]: 提取的特征
        """
        try:
            # 加载音频
            audio = self._load_audio(audio_data)
            
            if audio is None:
                logger.warning("Failed to load audio data")
                return {}
            
            # 提取基本特征
            duration_seconds = len(audio) / 1000.0  # 毫秒转秒
            
            # 提取音量特征
            volume_features = self._extract_volume_features(audio)
            
            # 提取音高特征
            pitch_features = self._extract_pitch_features(audio)
            
            # 检测停顿
            pause_features = self._detect_pauses(audio)
            
            # 估算语速（每分钟字数）
            words_per_minute = self._estimate_speech_rate(audio, duration_seconds)
            
            # 统计填充词（模拟，实际应该基于语音识别结果）
            filler_words_count = self._count_filler_words("这个 嗯 我认为 那个 项目是 嗯 非常成功的")
            
            # 合并所有特征
            features = {
                "duration_seconds": duration_seconds,
                "volume_avg": volume_features.get("average", 0.5),
                "volume_std": volume_features.get("std_dev", 0.1),
                "pitch_avg": pitch_features.get("average", 120.0),
                "pitch_std_dev": pitch_features.get("std_dev", 15.0),
                "pause_count": pause_features.get("count", 0),
                "pause_avg_duration": pause_features.get("avg_duration", 0.0),
                "unnatural_pauses_count": pause_features.get("unnatural_count", 0),
                "words_per_minute": words_per_minute,
                "filler_words_count": filler_words_count,
                "word_count": int(words_per_minute * duration_seconds / 60)
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting audio features: {str(e)}")
            return {}
    
    def _load_audio(self, audio_data: bytes) -> Optional[AudioSegment]:
        """加载音频数据
        
        Args:
            audio_data: 音频数据
            
        Returns:
            Optional[AudioSegment]: 加载的音频，如果失败则返回None
        """
        try:
            # 尝试加载为WAV
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format="wav")
            return audio
        except Exception as e1:
            try:
                # 尝试加载为MP3
                audio = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
                return audio
            except Exception as e2:
                logger.error(f"Failed to load audio: {str(e1)}, {str(e2)}")
                return None
    
    def _extract_volume_features(self, audio: AudioSegment) -> Dict[str, float]:
        """提取音量特征
        
        Args:
            audio: 音频数据
            
        Returns:
            Dict[str, float]: 音量特征
        """
        try:
            # 将音频转换为numpy数组
            samples = np.array(audio.get_array_of_samples())
            
            # 归一化
            samples = samples / np.max(np.abs(samples))
            
            # 计算音量特征
            volume_avg = np.mean(np.abs(samples))
            volume_std = np.std(np.abs(samples))
            
            return {
                "average": float(volume_avg),
                "std_dev": float(volume_std),
                "max": float(np.max(np.abs(samples))),
                "min": float(np.min(np.abs(samples)))
            }
            
        except Exception as e:
            logger.error(f"Error extracting volume features: {str(e)}")
            return {"average": 0.5, "std_dev": 0.1, "max": 1.0, "min": 0.0}
    
    def _extract_pitch_features(self, audio: AudioSegment) -> Dict[str, float]:
        """提取音高特征
        
        Args:
            audio: 音频数据
            
        Returns:
            Dict[str, float]: 音高特征
        """
        try:
            # 在实际应用中，这里应该使用专门的音高提取算法
            # 这里使用随机值模拟
            
            # 模拟平均音高（Hz）
            pitch_avg = 120.0 + np.random.normal(0, 10.0)
            
            # 模拟音高标准差
            pitch_std = 15.0 + np.random.normal(0, 5.0)
            
            return {
                "average": float(pitch_avg),
                "std_dev": float(pitch_std),
                "max": float(pitch_avg + 2 * pitch_std),
                "min": float(max(0, pitch_avg - 2 * pitch_std))
            }
            
        except Exception as e:
            logger.error(f"Error extracting pitch features: {str(e)}")
            return {"average": 120.0, "std_dev": 15.0, "max": 150.0, "min": 90.0}
    
    def _detect_pauses(self, audio: AudioSegment) -> Dict[str, Any]:
        """检测音频中的停顿
        
        Args:
            audio: 音频数据
            
        Returns:
            Dict[str, Any]: 停顿特征
        """
        try:
            # 检测非静音段
            non_silent_ranges = detect_nonsilent(
                audio, 
                min_silence_len=500,  # 最小静音长度（毫秒）
                silence_thresh=-40  # 静音阈值（dB）
            )
            
            if not non_silent_ranges:
                return {
                    "count": 0,
                    "avg_duration": 0.0,
                    "unnatural_count": 0,
                    "pauses": []
                }
            
            # 计算停顿
            pauses = []
            for i in range(len(non_silent_ranges) - 1):
                pause_start = non_silent_ranges[i][1]
                pause_end = non_silent_ranges[i + 1][0]
                pause_duration = (pause_end - pause_start) / 1000.0  # 转换为秒
                
                if pause_duration >= 0.5:  # 只考虑0.5秒以上的停顿
                    pauses.append({
                        "start": pause_start / 1000.0,
                        "end": pause_end / 1000.0,
                        "duration": pause_duration
                    })
            
            # 计算不自然停顿数量（这里简单地将超过2秒的停顿视为不自然）
            unnatural_pauses = [p for p in pauses if p["duration"] > 2.0]
            
            return {
                "count": len(pauses),
                "avg_duration": np.mean([p["duration"] for p in pauses]) if pauses else 0.0,
                "unnatural_count": len(unnatural_pauses),
                "pauses": pauses
            }
            
        except Exception as e:
            logger.error(f"Error detecting pauses: {str(e)}")
            return {"count": 0, "avg_duration": 0.0, "unnatural_count": 0, "pauses": []}
    
    def _estimate_speech_rate(self, audio: AudioSegment, duration_seconds: float) -> float:
        """估算语速（每分钟字数）
        
        Args:
            audio: 音频数据
            duration_seconds: 音频时长（秒）
            
        Returns:
            float: 估算的每分钟字数
        """
        try:
            # 在实际应用中，这里应该基于语音识别结果计算实际字数
            # 这里使用启发式方法估算
            
            # 假设平均每秒2.5个字
            estimated_word_count = 2.5 * duration_seconds
            
            # 转换为每分钟字数
            words_per_minute = estimated_word_count * 60 / duration_seconds
            
            # 添加一些随机变化
            words_per_minute += np.random.normal(0, 10.0)
            
            return max(80.0, min(250.0, words_per_minute))
            
        except Exception as e:
            logger.error(f"Error estimating speech rate: {str(e)}")
            return 150.0  # 默认值
    
    def _count_filler_words(self, text: str) -> int:
        """统计填充词数量
        
        Args:
            text: 文本
            
        Returns:
            int: 填充词数量
        """
        try:
            matches = self.filler_pattern.findall(text)
            return len(matches)
        except Exception as e:
            logger.error(f"Error counting filler words: {str(e)}")
            return 0