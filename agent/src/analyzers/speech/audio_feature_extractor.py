# agent/analyzers/audio_feature_extractor.py

from typing import Dict, Any, Tuple, List
import logging
import numpy as np
import librosa

# 获取日志记录器
logger = logging.getLogger("agent.audio_feature_extractor")


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
            
    @staticmethod
    def extract_pitch_std(y: np.ndarray, sr: int) -> float:
        """提取音高标准差特征
        
        Args:
            y: 音频数据
            sr: 采样率
            
        Returns:
            float: 音高标准差
        """
        try:
            # 使用librosa提取音高
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            
            # 获取每一帧的主要音高
            pitch = []
            for i in range(magnitudes.shape[1]):
                index = magnitudes[:, i].argmax()
                pitch.append(pitches[index, i])
            
            # 计算音高标准差
            pitch_std = np.std(pitch)
            return float(pitch_std)
        except Exception as e:
            logger.error(f"提取音高标准差特征失败: {e}")
            return 10.0  # 默认值
    
    @staticmethod
    def detect_pauses(y: np.ndarray, sr: int, min_pause_duration: float = 2.0) -> List[Dict[str, Any]]:
        """检测音频中的停顿
        
        Args:
            y: 音频数据
            sr: 采样率
            min_pause_duration: 最小停顿持续时间（秒）
            
        Returns:
            List[Dict[str, Any]]: 停顿信息列表
        """
        try:
            # 计算短时能量
            hop_length = 512
            frame_length = 2048
            rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            
            # 设置能量阈值（可以根据需要调整）
            threshold = 0.01
            
            # 检测低于阈值的帧
            silence_frames = np.where(rms < threshold)[0]
            
            # 将连续的静音帧分组
            pauses = []
            if len(silence_frames) > 0:
                # 初始化第一个静音区间
                pause_start = silence_frames[0]
                prev_frame = silence_frames[0]
                
                for frame in silence_frames[1:]:
                    # 如果当前帧与前一帧不连续，结束当前静音区间并开始新区间
                    if frame > prev_frame + 1:
                        pause_end = prev_frame
                        pause_duration = (pause_end - pause_start + 1) * hop_length / sr
                        
                        # 只记录超过最小持续时间的停顿
                        if pause_duration >= min_pause_duration:
                            pauses.append({
                                "start": pause_start * hop_length / sr,
                                "end": pause_end * hop_length / sr,
                                "duration": pause_duration
                            })
                        
                        # 开始新的静音区间
                        pause_start = frame
                    
                    prev_frame = frame
                
                # 处理最后一个静音区间
                pause_end = prev_frame
                pause_duration = (pause_end - pause_start + 1) * hop_length / sr
                if pause_duration >= min_pause_duration:
                    pauses.append({
                        "start": pause_start * hop_length / sr,
                        "end": pause_end * hop_length / sr,
                        "duration": pause_duration
                    })
            
            return pauses
        except Exception as e:
            logger.error(f"检测停顿失败: {e}")
            return []
    
    @staticmethod
    def count_filler_words(y: np.ndarray, sr: int, transcript: str = "") -> int:
        """计算填充词数量
        
        如果提供了转录文本，则直接从文本中计算；否则尝试使用音频特征估计
        
        Args:
            y: 音频数据
            sr: 采样率
            transcript: 转录文本
            
        Returns:
            int: 填充词数量
        """
        try:
            if transcript:
                # 从转录文本中计算填充词数量
                filler_words = ["嗯", "啊", "那个", "就是", "这个", "然后", "所以", "其实", "就", "那么"]
                count = sum(transcript.count(word) for word in filler_words)
                return count
            else:
                # 如果没有转录文本，返回一个估计值（实际应用中需要更复杂的算法）
                # 这里简单地基于音频长度返回一个估计值
                audio_duration = len(y) / sr  # 音频长度（秒）
                estimated_fillers = int(audio_duration / 10)  # 假设平均每10秒有一个填充词
                return max(0, estimated_fillers)
        except Exception as e:
            logger.error(f"计算填充词数量失败: {e}")
            return 0
    
    @classmethod
    def extract_all_features(cls, y: np.ndarray, sr: int, transcript: str = "") -> Dict[str, Any]:
        """提取所有基本音频特征
        
        Args:
            y: 音频数据
            sr: 采样率
            transcript: 转录文本
            
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
                "pitch_std_dev": cls.extract_pitch_std(y, sr),
                "pauses": cls.detect_pauses(y, sr),
                "filler_words_count": cls.count_filler_words(y, sr, transcript)
            }
            return features
        except Exception as e:
            logger.error(f"提取所有基本音频特征失败: {e}")
            return {}
    
    @classmethod
    def extract_from_file(cls, file_path: str, transcript: str = "") -> Dict[str, Any]:
        """从文件中提取所有基本音频特征
        
        Args:
            file_path: 音频文件路径
            transcript: 转录文本
            
        Returns:
            Dict[str, Any]: 所有基本音频特征
        """
        try:
            y, sr = cls.load_audio(file_path)
            return cls.extract_all_features(y, sr, transcript)
        except Exception as e:
            logger.error(f"从文件中提取所有基本音频特征失败: {file_path}, 错误: {e}")
            return {}
            
    @classmethod
    def extract_from_bytes(cls, audio_bytes: bytes) -> Dict[str, Any]:
        """从字节数据中提取所有基本音频特征
        
        Args:
            audio_bytes: 音频字节数据
            
        Returns:
            Dict[str, Any]: 所有基本音频特征
        """
        try:
            import io
            import soundfile as sf
            
            # 将字节数据转换为音频数据
            with io.BytesIO(audio_bytes) as buffer:
                y, sr = sf.read(buffer)
                
            return cls.extract_all_features(y, sr)
        except Exception as e:
            logger.error(f"从字节数据中提取所有基本音频特征失败: {e}")
            return {}