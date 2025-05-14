# ai_agent/analyzers/visual_analyzer.py

from typing import Dict, Any, Optional, List
import os
import cv2
import numpy as np

from ..core.analyzer import Analyzer
from ..core.config import AgentConfig
from ..core.utils import normalize_score, weighted_average


class VisualAnalyzer(Analyzer):
    """视觉分析器
    
    负责提取和分析视频中的视觉特征，包括面部表情、眼神接触和肢体语言等
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化视觉分析器
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        super().__init__(name="visual_analyzer", analyzer_type="visual", config=config)
        
        # 加载模型配置
        self.face_detection_model = self.get_config("face_detection_model", "haarcascade")
        self.frame_sample_rate = self.get_config("frame_sample_rate", 5)  # 每秒采样帧数
        
        # 初始化人脸检测器（延迟加载）
        self._face_detector = None
    
    def _load_face_detector(self):
        """加载人脸检测器"""
        try:
            if self.face_detection_model == "haarcascade":
                # 使用OpenCV内置的Haar级联分类器
                model_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self._face_detector = cv2.CascadeClassifier(model_path)
            else:
                # 默认使用Haar级联分类器
                model_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self._face_detector = cv2.CascadeClassifier(model_path)
        
        except Exception as e:
            print(f"加载人脸检测器失败: {e}")
            self._face_detector = None
    
    def extract_features(self, file_path: str) -> Dict[str, Any]:
        """提取视觉特征
        
        从视频文件中提取视觉特征
        
        Args:
            file_path: 视频文件路径
            
        Returns:
            Dict[str, Any]: 提取的视觉特征
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 打开视频文件
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {file_path}")
            
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            # 计算采样间隔
            sample_interval = int(fps / self.frame_sample_rate) if fps > 0 else 1
            
            # 初始化特征
            features = {
                "video_info": {
                    "fps": fps,
                    "frame_count": frame_count,
                    "duration": duration
                },
                "face_detections": [],
                "eye_contacts": [],
                "expressions": [],
                "postures": []
            }
            
            # 加载人脸检测器（如果尚未加载）
            if self._face_detector is None:
                self._load_face_detector()
            
            # 逐帧处理视频
            frame_idx = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 只处理采样帧
                if frame_idx % sample_interval == 0:
                    # 提取当前帧的特征
                    frame_features = self._extract_frame_features(frame, frame_idx / fps)
                    
                    # 更新特征
                    if "face_detected" in frame_features and frame_features["face_detected"]:
                        features["face_detections"].append({
                            "time": frame_idx / fps,
                            "bbox": frame_features["face_bbox"]
                        })
                    
                    if "eye_contact" in frame_features:
                        features["eye_contacts"].append({
                            "time": frame_idx / fps,
                            "score": frame_features["eye_contact"]
                        })
                    
                    if "expression" in frame_features:
                        features["expressions"].append({
                            "time": frame_idx / fps,
                            "type": frame_features["expression"],
                            "score": frame_features["expression_score"]
                        })
                    
                    if "posture" in frame_features:
                        features["postures"].append({
                            "time": frame_idx / fps,
                            "type": frame_features["posture"],
                            "score": frame_features["posture_score"]
                        })
                
                frame_idx += 1
            
            # 释放视频资源
            cap.release()
            
            # 计算统计特征
            features["stats"] = self._calculate_stats(features)
            
            return features
        
        except Exception as e:
            print(f"提取视觉特征失败: {e}")
            return {
                "video_info": {
                    "fps": 0,
                    "frame_count": 0,
                    "duration": 0
                },
                "face_detections": [],
                "eye_contacts": [],
                "expressions": [],
                "postures": [],
                "stats": {}
            }
    
    def _extract_frame_features(self, frame: np.ndarray, timestamp: float) -> Dict[str, Any]:
        """提取单帧特征
        
        从视频帧中提取视觉特征
        
        Args:
            frame: 视频帧
            timestamp: 时间戳（秒）
            
        Returns:
            Dict[str, Any]: 帧特征
        """
        frame_features = {
            "timestamp": timestamp
        }
        
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 检测人脸
        if self._face_detector is not None:
            faces = self._face_detector.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            if len(faces) > 0:
                # 取最大的人脸（假设是主要人物）
                face = max(faces, key=lambda x: x[2] * x[3])
                x, y, w, h = face
                
                frame_features["face_detected"] = True
                frame_features["face_bbox"] = (int(x), int(y), int(w), int(h))
                
                # 提取人脸区域
                face_roi = gray[y:y+h, x:x+w]
                
                # 分析眼神接触
                frame_features["eye_contact"] = self._analyze_eye_contact(face_roi)
                
                # 分析面部表情
                expression, expression_score = self._analyze_expression(face_roi)
                frame_features["expression"] = expression
                frame_features["expression_score"] = expression_score
            else:
                frame_features["face_detected"] = False
        else:
            frame_features["face_detected"] = False
        
        # 分析肢体语言（简化处理，实际应用中需要更复杂的姿态估计）
        posture, posture_score = self._analyze_posture(frame)
        frame_features["posture"] = posture
        frame_features["posture_score"] = posture_score
        
        return frame_features
    
    def _analyze_eye_contact(self, face_roi: np.ndarray) -> float:
        """分析眼神接触
        
        简化处理，实际应用中需要更复杂的眼睛检测和注视方向估计
        
        Args:
            face_roi: 人脸区域图像
            
        Returns:
            float: 眼神接触评分（0-10）
        """
        # 简化处理：使用启发式方法估计眼神接触
        # 实际应用中，应该使用专门的眼睛检测和注视方向估计模型
        
        # 这里假设人脸检测成功就给一个基础分数
        # 实际应用中需要更精确的分析
        return 7.0
    
    def _analyze_expression(self, face_roi: np.ndarray) -> tuple:
        """分析面部表情
        
        简化处理，实际应用中需要使用表情识别模型
        
        Args:
            face_roi: 人脸区域图像
            
        Returns:
            tuple: (表情类型, 表情评分)
        """
        # 简化处理：随机返回一个表情类型和评分
        # 实际应用中，应该使用专门的表情识别模型
        
        # 这里假设表情为"自然"，评分为7.0
        # 实际应用中需要更精确的分析
        return "自然", 7.0
    
    def _analyze_posture(self, frame: np.ndarray) -> tuple:
        """分析肢体语言
        
        简化处理，实际应用中需要使用姿态估计模型
        
        Args:
            frame: 完整视频帧
            
        Returns:
            tuple: (姿态类型, 姿态评分)
        """
        # 简化处理：随机返回一个姿态类型和评分
        # 实际应用中，应该使用专门的姿态估计模型
        
        # 这里假设姿态为"自然"，评分为7.0
        # 实际应用中需要更精确的分析
        return "自然", 7.0
    
    def _calculate_stats(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """计算统计特征
        
        根据帧级特征计算统计特征
        
        Args:
            features: 帧级特征
            
        Returns:
            Dict[str, Any]: 统计特征
        """
        stats = {}
        
        # 计算人脸检测率
        face_detection_count = len(features["face_detections"])
        total_samples = max(1, int(features["video_info"]["duration"] * self.frame_sample_rate))
        stats["face_detection_rate"] = face_detection_count / total_samples if total_samples > 0 else 0
        
        # 计算平均眼神接触评分
        eye_contact_scores = [item["score"] for item in features["eye_contacts"]]
        stats["avg_eye_contact"] = np.mean(eye_contact_scores) if eye_contact_scores else 5.0
        
        # 计算表情统计
        expression_types = [item["type"] for item in features["expressions"]]
        expression_scores = [item["score"] for item in features["expressions"]]
        
        # 表情类型分布
        expression_counts = {}
        for exp_type in expression_types:
            if exp_type in expression_counts:
                expression_counts[exp_type] += 1
            else:
                expression_counts[exp_type] = 1
        
        stats["expression_distribution"] = expression_counts
        stats["avg_expression_score"] = np.mean(expression_scores) if expression_scores else 5.0
        
        # 计算姿态统计
        posture_types = [item["type"] for item in features["postures"]]
        posture_scores = [item["score"] for item in features["postures"]]
        
        # 姿态类型分布
        posture_counts = {}
        for pos_type in posture_types:
            if pos_type in posture_counts:
                posture_counts[pos_type] += 1
            else:
                posture_counts[pos_type] = 1
        
        stats["posture_distribution"] = posture_counts
        stats["avg_posture_score"] = np.mean(posture_scores) if posture_scores else 5.0
        
        return stats
    
    def analyze(self, features: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """分析视觉特征
        
        根据提取的视觉特征进行分析
        
        Args:
            features: 提取的视觉特征
            params: 分析参数，如果为None则使用默认参数
            
        Returns:
            Dict[str, Any]: 视觉分析结果
        """
        if not features or "stats" not in features:
            return {
                "facial_expressions": {
                    "types": {},
                    "score": 5.0
                },
                "eye_contact": 5.0,
                "body_language": {
                    "types": {},
                    "score": 5.0
                },
                "overall_score": 5.0
            }
        
        # 获取权重配置
        expression_weight = self.get_config("expression_weight", 0.4)
        eye_contact_weight = self.get_config("eye_contact_weight", 0.3)
        body_language_weight = self.get_config("body_language_weight", 0.3)
        
        # 如果提供了参数，覆盖默认权重
        if params:
            expression_weight = params.get("expression_weight", expression_weight)
            eye_contact_weight = params.get("eye_contact_weight", eye_contact_weight)
            body_language_weight = params.get("body_language_weight", body_language_weight)
        
        # 获取统计特征
        stats = features.get("stats", {})
        
        # 分析面部表情
        expression_distribution = stats.get("expression_distribution", {})
        expression_score = stats.get("avg_expression_score", 5.0)
        
        # 分析眼神接触
        eye_contact = stats.get("avg_eye_contact", 5.0)
        
        # 分析肢体语言
        posture_distribution = stats.get("posture_distribution", {})
        posture_score = stats.get("avg_posture_score", 5.0)
        
        # 计算总分
        overall_score = weighted_average(
            {
                "expression": expression_score,
                "eye_contact": eye_contact,
                "posture": posture_score
            },
            {
                "expression": expression_weight,
                "eye_contact": eye_contact_weight,
                "posture": body_language_weight
            }
        )
        
        return {
            "facial_expressions": {
                "types": expression_distribution,
                "score": expression_score
            },
            "eye_contact": eye_contact,
            "body_language": {
                "types": posture_distribution,
                "score": posture_score
            },
            "overall_score": overall_score
        }