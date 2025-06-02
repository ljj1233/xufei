# ai_agent/analyzers/audio_feature_extractor.py

from typing import Dict, Any, Tuple
import logging
import numpy as np
import librosa

# 获取日志记录器
logger = logging.getLogger("ai_agent.audio_feature_extractor")


class AudioFeatureExtractor:
    """音频特征提取器
    
    负责从音频文件中提取基本音频特征，作为语音分析的基础
    """
    
    @staticmethod
    def load_audio(file_path: str) -> Tuple[np.ndarray, int]:
        """加载音频文件
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            Tuple[np.ndarray, int]: 音频数据和采样率
        """
        try:
            y, sr = librosa.load(file_path, sr=None)
            return y, sr
        except Exception as e:
            logger.error(f"加载音频文件失败: {e}")
            raise
    
    @staticmethod
    def read_audio_bytes(file_path: str) -> bytes:
        """读取音频文件为字节数据
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            bytes: 音频字节数据
        """
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取音频文件失败: {file_path}, 错误: {e}")
            raise
    
    @staticmethod
    def extract_mfcc(y: np.ndarray, sr: int, n_mfcc: int = 13) -> np.ndarray:
        """提取MFCC特征
        
        Args:
            y: 音频数据
            sr: 采样率
            n_mfcc: MFCC系数数量
            
        Returns:
            np.ndarray: MFCC特征
        """
        try:
            return librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc).mean(axis=1)
        except Exception as e:
            logger.error(f"提取MFCC特征失败: {e}")
            return np.zeros(n_mfcc)
    
    @staticmethod
    def extract_spectral_centroid(y: np.ndarray, sr: int) -> float:
        """提取频谱质心特征
        
        Args:
            y: 音频数据
            sr: 采样率
            
        Returns:
            float: 频谱质心
        """
        try:
            return float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
        except Exception as e:
            logger.error(f"提取频谱质心特征失败: {e}")
            return 1000.0  # 默认值
    
    @staticmethod
    def extract_zero_crossing_rate(y: np.ndarray) -> float:
        """提取过零率特征
        
        Args:
            y: 音频数据
            
        Returns:
            float: 过零率
        """
        try:
            return float(librosa.feature.zero_crossing_rate(y).mean())
        except Exception as e:
            logger.error(f"提取过零率特征失败: {e}")
            return 0.1  # 默认值
    
    @staticmethod
    def extract_tempo(y: np.ndarray, sr: int) -> float:
        """提取节奏特征
        
        Args:
            y: 音频数据
            sr: 采样率
            
        Returns:
            float: 节奏（BPM）
        """
        try:
            return float(librosa.beat.tempo(y=y, sr=sr)[0])
        except Exception as e:
            logger.error(f"提取节奏特征失败: {e}")
            return 120.0  # 默认值
    
    @staticmethod
    def extract_rms(y: np.ndarray) -> float:
        """提取RMS能量特征
        
        Args:
            y: 音频数据
            
        Returns:
            float: RMS能量
        """
        try:
            return float(librosa.feature.rms(y=y).mean())
        except Exception as e:
            logger.error(f"提取RMS能量特征失败: {e}")
            return 0.1  # 默认值
    
    @classmethod
    def extract_all_features(cls, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """提取所有基本音频特征
        
        Args:
            y: 音频数据
            sr: 采样率
            
        Returns:
            Dict[str, Any]: 所有基本音频特征
        """
        try:
            features = {
                "mfcc": cls.extract_mfcc(y, sr).tolist(),
                "spectral_centroid": cls.extract_spectral_centroid(y, sr),
                "zero_crossing_rate": cls.extract_zero_crossing_rate(y),
                "tempo": cls.extract_tempo(y, sr),
                "rms": cls.extract_rms(y),
            }
            return features
        except Exception as e:
            logger.error(f"提取所有基本音频特征失败: {e}")
            return {}
    
    @classmethod
    def extract_from_file(cls, file_path: str) -> Dict[str, Any]:
        """从文件中提取所有基本音频特征
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            Dict[str, Any]: 所有基本音频特征
        """
        try:
            y, sr = cls.load_audio(file_path)
            return cls.extract_all_features(y, sr)
        except Exception as e:
            logger.error(f"从文件中提取所有基本音频特征失败: {file_path}, 错误: {e}")
            return {}