# ai_agent/analyzers/visual_analyzer.py

from typing import Dict, Any, Optional, List
import os
import cv2
import numpy as np
import time
from collections import deque

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
        
        # 流式处理相关属性
        self.frame_buffer = deque(maxlen=30)  # 视频帧缓冲区
        self.analysis_history = deque(maxlen=50)  # 分析历史记录
        self.last_analysis_time = 0
        self.analysis_interval = 0.5  # 分析间隔（秒）
        self.face_tracking = {}  # 人脸跟踪信息
    
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
    
    def extract_frame_features(self, frame_data: bytes) -> Dict[str, Any]:
        """提取视频帧特征
        
        Args:
            frame_data: 视频帧数据
            
        Returns:
            Dict[str, Any]: 提取的特征
        """
        try:
            # 将字节数据转换为numpy数组
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return {}
            
            # 将帧添加到缓冲区
            self.frame_buffer.append({
                "frame": frame,
                "timestamp": time.time()
            })
            
            # 提取帧特征
            features = self._extract_single_frame_features(frame)
            features["timestamp"] = time.time()
            features["buffer_size"] = len(self.frame_buffer)
            
            return features
            
        except Exception as e:
            print(f"提取视频帧特征失败: {e}")
            return {}
    
    def analyze_frame(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """分析视频帧
        
        Args:
            features: 视频帧特征
            
        Returns:
            Dict[str, Any]: 实时分析结果
        """
        current_time = time.time()
        
        # 检查是否需要进行分析（控制分析频率）
        if current_time - self.last_analysis_time < self.analysis_interval:
            return {}
        
        try:
            # 进行实时分析
            result = {
                "timestamp": current_time,
                "eye_contact": self._analyze_frame_eye_contact(features),
                "facial_expression": self._analyze_frame_expression(features),
                "posture": self._analyze_frame_posture(features),
                "attention": self._analyze_frame_attention(features)
            }
            
            # 添加到历史记录
            self.analysis_history.append(result)
            self.last_analysis_time = current_time
            
            # 计算趋势
            result["trends"] = self._calculate_visual_trends()
            
            return result
            
        except Exception as e:
            print(f"视频帧分析失败: {e}")
            return {}
    
    def _extract_single_frame_features(self, frame: np.ndarray) -> Dict[str, Any]:
        """提取单帧特征
        
        Args:
            frame: 视频帧
            
        Returns:
            Dict[str, Any]: 帧特征
        """
        features = {}
        
        try:
            # 加载人脸检测器（如果尚未加载）
            if self._face_detector is None:
                self._load_face_detector()
            
            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 人脸检测
            if self._face_detector is not None:
                faces = self._face_detector.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )
                features["faces"] = faces.tolist() if len(faces) > 0 else []
            else:
                features["faces"] = []
            
            # 图像质量特征
            features["brightness"] = np.mean(gray)
            features["contrast"] = np.std(gray)
            features["frame_shape"] = frame.shape
            
        except Exception as e:
            print(f"提取单帧特征失败: {e}")
        
        return features
    
    def _analyze_frame_eye_contact(self, features: Dict[str, Any]) -> float:
        """分析帧眼神接触
        
        Args:
            features: 帧特征
            
        Returns:
            float: 眼神接触评分
        """
        try:
            faces = features.get("faces", [])
            
            if not faces:
                return 3.0  # 没有检测到人脸，给较低分
            
            # 简单估计：基于人脸位置和大小
            face = faces[0]  # 取第一个人脸
            x, y, w, h = face
            
            # 人脸在画面中央且大小适中，认为眼神接触较好
            frame_shape = features.get("frame_shape", (480, 640, 3))
            frame_height, frame_width = frame_shape[:2]
            
            # 计算人脸中心位置
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            
            # 计算与画面中心的距离
            center_x, center_y = frame_width // 2, frame_height // 2
            distance = np.sqrt((face_center_x - center_x)**2 + (face_center_y - center_y)**2)
            
            # 距离越近，眼神接触越好
            max_distance = np.sqrt(center_x**2 + center_y**2)
            eye_contact_score = max(1.0, 10.0 - (distance / max_distance) * 5)
            
            return normalize_score(eye_contact_score)
            
        except Exception as e:
            print(f"分析帧眼神接触失败: {e}")
            return 5.0
    
    def _analyze_frame_expression(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """分析帧面部表情
        
        Args:
            features: 帧特征
            
        Returns:
            Dict[str, Any]: 表情分析结果
        """
        try:
            faces = features.get("faces", [])
            
            if not faces:
                return {"type": "neutral", "confidence": 0.5, "score": 5.0}
            
            # 简单的表情估计（基于人脸区域的亮度和对比度）
            brightness = features.get("brightness", 128)
            contrast = features.get("contrast", 50)
            
            # 根据亮度和对比度估计表情
            if brightness > 140 and contrast > 60:
                expression_type = "positive"
                confidence = 0.7
                score = 8.0
            elif brightness < 100 or contrast < 30:
                expression_type = "negative"
                confidence = 0.6
                score = 4.0
            else:
                expression_type = "neutral"
                confidence = 0.8
                score = 6.0
            
            return {
                "type": expression_type,
                "confidence": confidence,
                "score": normalize_score(score)
            }
            
        except Exception as e:
            print(f"分析帧面部表情失败: {e}")
            return {"type": "neutral", "confidence": 0.5, "score": 5.0}
    
    def _analyze_frame_posture(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """分析帧姿态
        
        Args:
            features: 帧特征
            
        Returns:
            Dict[str, Any]: 姿态分析结果
        """
        try:
            faces = features.get("faces", [])
            
            if not faces:
                return {"type": "unknown", "confidence": 0.3, "score": 4.0}
            
            # 基于人脸大小和位置估计姿态
            face = faces[0]
            x, y, w, h = face
            
            frame_shape = features.get("frame_shape", (480, 640, 3))
            frame_height, frame_width = frame_shape[:2]
            
            # 人脸大小相对于画面的比例
            face_ratio = (w * h) / (frame_width * frame_height)
            
            if face_ratio > 0.15:  # 人脸较大，可能距离较近
                posture_type = "close"
                confidence = 0.7
                score = 7.0
            elif face_ratio < 0.05:  # 人脸较小，可能距离较远
                posture_type = "far"
                confidence = 0.6
                score = 5.0
            else:
                posture_type = "appropriate"
                confidence = 0.8
                score = 8.0
            
            return {
                "type": posture_type,
                "confidence": confidence,
                "score": normalize_score(score)
            }
            
        except Exception as e:
            print(f"分析帧姿态失败: {e}")
            return {"type": "unknown", "confidence": 0.3, "score": 4.0}
    
    def _analyze_frame_attention(self, features: Dict[str, Any]) -> float:
        """分析帧注意力
        
        Args:
            features: 帧特征
            
        Returns:
            float: 注意力评分
        """
        try:
            faces = features.get("faces", [])
            
            if not faces:
                return 3.0
            
            # 基于人脸稳定性估计注意力
            # 这里简化为基于人脸数量和大小的稳定性
            if len(faces) == 1:  # 单个人脸，注意力集中
                attention_score = 8.0
            elif len(faces) > 1:  # 多个人脸，可能分心
                attention_score = 5.0
            else:
                attention_score = 3.0
            
            return normalize_score(attention_score)
            
        except Exception as e:
            print(f"分析帧注意力失败: {e}")
            return 5.0
    
    def _calculate_visual_trends(self) -> Dict[str, str]:
        """计算视觉分析趋势
        
        Returns:
            Dict[str, str]: 趋势信息
        """
        if len(self.analysis_history) < 3:
            return {}
        
        try:
            # 获取最近的分析结果
            recent = list(self.analysis_history)[-3:]
            
            trends = {}
            
            # 计算眼神接触趋势
            eye_contact_values = [r.get("eye_contact", 5.0) for r in recent]
            trends["eye_contact"] = self._get_trend_direction(eye_contact_values)
            
            # 计算表情趋势
            expression_scores = [r.get("facial_expression", {}).get("score", 5.0) for r in recent]
            trends["expression"] = self._get_trend_direction(expression_scores)
            
            # 计算姿态趋势
            posture_scores = [r.get("posture", {}).get("score", 5.0) for r in recent]
            trends["posture"] = self._get_trend_direction(posture_scores)
            
            # 计算注意力趋势
            attention_values = [r.get("attention", 5.0) for r in recent]
            trends["attention"] = self._get_trend_direction(attention_values)
            
            return trends
            
        except Exception as e:
            print(f"计算视觉趋势失败: {e}")
            return {}
    
    def _get_trend_direction(self, values: List[float]) -> str:
        """获取趋势方向
        
        Args:
            values: 数值列表
            
        Returns:
            str: 趋势方向
        """
        if len(values) < 2:
            return "稳定"
        
        # 计算变化
        diff = values[-1] - values[0]
        
        if diff > 0.5:
            return "上升"
        elif diff < -0.5:
            return "下降"
        else:
            return "稳定"
    
    def clear_stream_data(self):
        """清空流式数据"""
        self.frame_buffer.clear()
        self.analysis_history.clear()
        self.last_analysis_time = 0
        self.face_tracking.clear()