"""学习引擎模块

实现面试智能体的核心学习功能，包括在线学习、模型更新和性能优化。
"""

import json
import pickle
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from abc import ABC, abstractmethod

from agent.src.core.workflow.state import AnalysisResult, Task, TaskStatus


@dataclass
class LearningMetrics:
    """学习指标"""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    learning_rate: float = 0.001
    convergence_rate: float = 0.0
    adaptation_speed: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class LearningData:
    """学习数据"""
    input_features: Dict[str, Any]
    expected_output: Dict[str, Any]
    actual_output: Dict[str, Any]
    feedback_score: float
    context: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class LearningAlgorithm(ABC):
    """学习算法抽象基类"""
    
    @abstractmethod
    def train(self, data: List[LearningData]) -> LearningMetrics:
        """训练模型"""
        pass
    
    @abstractmethod
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """预测"""
        pass
    
    @abstractmethod
    def update(self, data: LearningData) -> None:
        """在线更新"""
        pass
    
    @abstractmethod
    def get_model_state(self) -> Dict[str, Any]:
        """获取模型状态"""
        pass
    
    @abstractmethod
    def load_model_state(self, state: Dict[str, Any]) -> None:
        """加载模型状态"""
        pass


class OnlineLearningAlgorithm(LearningAlgorithm):
    """在线学习算法实现"""
    
    def __init__(self, learning_rate: float = 0.001, decay_rate: float = 0.95):
        self.learning_rate = learning_rate
        self.decay_rate = decay_rate
        self.weights = {}
        self.bias = {}
        self.training_history = []
        self.update_count = 0
        
    def train(self, data: List[LearningData]) -> LearningMetrics:
        """批量训练"""
        total_loss = 0.0
        predictions = []
        actuals = []
        
        for sample in data:
            prediction = self.predict(sample.input_features)
            loss = self._calculate_loss(prediction, sample.expected_output)
            total_loss += loss
            
            predictions.append(prediction)
            actuals.append(sample.expected_output)
            
            # 在线更新
            self.update(sample)
        
        # 计算指标
        metrics = self._calculate_metrics(predictions, actuals)
        metrics.learning_rate = self.learning_rate
        
        return metrics
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """预测"""
        prediction = {}
        
        for key, value in features.items():
            if key in self.weights:
                # 简单的线性预测
                if isinstance(value, (int, float)):
                    pred_value = value * self.weights[key] + self.bias.get(key, 0)
                    prediction[key] = max(0, min(1, pred_value))  # 限制在[0,1]范围
                else:
                    prediction[key] = value
            else:
                prediction[key] = value
        
        return prediction
    
    def update(self, data: LearningData) -> None:
        """在线更新"""
        self.update_count += 1
        
        # 计算梯度并更新权重
        for key in data.input_features:
            if isinstance(data.input_features[key], (int, float)):
                if key not in self.weights:
                    self.weights[key] = np.random.normal(0, 0.1)
                    self.bias[key] = 0.0
                
                # 计算误差
                predicted = self.predict({key: data.input_features[key]})
                if key in data.expected_output:
                    error = data.expected_output[key] - predicted.get(key, 0)
                    
                    # 梯度下降更新
                    self.weights[key] += self.learning_rate * error * data.input_features[key]
                    self.bias[key] += self.learning_rate * error
        
        # 学习率衰减
        if self.update_count % 100 == 0:
            self.learning_rate *= self.decay_rate
        
        # 记录训练历史
        self.training_history.append({
            'timestamp': data.timestamp,
            'feedback_score': data.feedback_score,
            'update_count': self.update_count
        })
    
    def get_model_state(self) -> Dict[str, Any]:
        """获取模型状态"""
        return {
            'weights': self.weights.copy(),
            'bias': self.bias.copy(),
            'learning_rate': self.learning_rate,
            'decay_rate': self.decay_rate,
            'update_count': self.update_count,
            'training_history': self.training_history[-100:]  # 只保留最近100条记录
        }
    
    def load_model_state(self, state: Dict[str, Any]) -> None:
        """加载模型状态"""
        self.weights = state.get('weights', {})
        self.bias = state.get('bias', {})
        self.learning_rate = state.get('learning_rate', 0.001)
        self.decay_rate = state.get('decay_rate', 0.95)
        self.update_count = state.get('update_count', 0)
        self.training_history = state.get('training_history', [])
    
    def _calculate_loss(self, prediction: Dict[str, Any], expected: Dict[str, Any]) -> float:
        """计算损失"""
        total_loss = 0.0
        count = 0
        
        for key in expected:
            if key in prediction and isinstance(expected[key], (int, float)):
                loss = (prediction[key] - expected[key]) ** 2
                total_loss += loss
                count += 1
        
        return total_loss / max(count, 1)
    
    def _calculate_metrics(self, predictions: List[Dict], actuals: List[Dict]) -> LearningMetrics:
        """计算评估指标"""
        if not predictions or not actuals:
            return LearningMetrics()
        
        # 简化的指标计算
        total_accuracy = 0.0
        count = 0
        
        for pred, actual in zip(predictions, actuals):
            for key in actual:
                if key in pred and isinstance(actual[key], (int, float)):
                    accuracy = 1.0 - abs(pred[key] - actual[key])
                    total_accuracy += max(0, accuracy)
                    count += 1
        
        avg_accuracy = total_accuracy / max(count, 1)
        
        return LearningMetrics(
            accuracy=avg_accuracy,
            precision=avg_accuracy * 0.9,  # 简化计算
            recall=avg_accuracy * 0.95,
            f1_score=avg_accuracy * 0.92
        )


class LearningEngine:
    """学习引擎主类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化学习算法
        self.algorithms = {
            'speech': OnlineLearningAlgorithm(
                learning_rate=self.config.get('speech_learning_rate', 0.001)
            ),
            'visual': OnlineLearningAlgorithm(
                learning_rate=self.config.get('visual_learning_rate', 0.001)
            ),
            'content': OnlineLearningAlgorithm(
                learning_rate=self.config.get('content_learning_rate', 0.001)
            )
        }
        
        # 学习数据存储
        self.learning_data = []
        self.metrics_history = []
        
        # 模型保存路径
        self.model_save_path = Path(self.config.get('model_save_path', 'models/learning'))
        self.model_save_path.mkdir(parents=True, exist_ok=True)
        
        # 加载已有模型
        self._load_models()
    
    def add_learning_data(self, 
                         task: Task, 
                         analysis_result: AnalysisResult, 
                         feedback_score: float,
                         expected_result: Dict[str, Any] = None) -> None:
        """添加学习数据"""
        try:
            # 提取特征
            input_features = self._extract_features(task, analysis_result)
            
            # 构建期望输出
            if expected_result is None:
                expected_result = self._generate_expected_output(analysis_result, feedback_score)
            
            # 创建学习数据
            learning_data = LearningData(
                input_features=input_features,
                expected_output=expected_result,
                actual_output=self._extract_actual_output(analysis_result),
                feedback_score=feedback_score,
                context={
                    'task_id': task.task_id,
                    'task_type': task.task_type,
                    'timestamp': datetime.now()
                }
            )
            
            self.learning_data.append(learning_data)
            
            # 在线学习更新
            self._online_update(learning_data)
            
            self.logger.info(f"添加学习数据: task_id={task.task_id}, feedback_score={feedback_score}")
            
        except Exception as e:
            self.logger.error(f"添加学习数据失败: {e}")
    
    def train_models(self, batch_size: int = 100) -> Dict[str, LearningMetrics]:
        """批量训练模型"""
        if len(self.learning_data) < batch_size:
            self.logger.warning(f"学习数据不足，需要至少{batch_size}条数据")
            return {}
        
        # 按类型分组数据
        grouped_data = self._group_learning_data()
        
        metrics = {}
        for algorithm_type, data in grouped_data.items():
            if algorithm_type in self.algorithms and data:
                try:
                    # 训练模型
                    algorithm_metrics = self.algorithms[algorithm_type].train(data[-batch_size:])
                    metrics[algorithm_type] = algorithm_metrics
                    
                    self.logger.info(f"训练{algorithm_type}模型完成，准确率: {algorithm_metrics.accuracy:.3f}")
                    
                except Exception as e:
                    self.logger.error(f"训练{algorithm_type}模型失败: {e}")
        
        # 保存指标历史
        self.metrics_history.append({
            'timestamp': datetime.now(),
            'metrics': metrics
        })
        
        # 保存模型
        self._save_models()
        
        return metrics
    
    def predict(self, task: Task, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """预测优化建议"""
        try:
            features = self._extract_features(task, analysis_result)
            
            predictions = {}
            for algorithm_type, algorithm in self.algorithms.items():
                try:
                    pred = algorithm.predict(features)
                    predictions[algorithm_type] = pred
                except Exception as e:
                    self.logger.error(f"预测{algorithm_type}失败: {e}")
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"预测失败: {e}")
            return {}
    
    def get_learning_metrics(self) -> Dict[str, Any]:
        """获取学习指标"""
        metrics = {
            'total_learning_samples': len(self.learning_data),
            'algorithms': {},
            'recent_performance': []
        }
        
        # 获取各算法状态
        for algorithm_type, algorithm in self.algorithms.items():
            state = algorithm.get_model_state()
            metrics['algorithms'][algorithm_type] = {
                'update_count': state.get('update_count', 0),
                'learning_rate': state.get('learning_rate', 0),
                'weights_count': len(state.get('weights', {}))
            }
        
        # 最近性能
        if self.metrics_history:
            metrics['recent_performance'] = self.metrics_history[-10:]
        
        return metrics
    
    def _extract_features(self, task: Task, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """提取特征"""
        features = {
            'task_type': hash(task.task_type) % 1000 / 1000.0,  # 归一化
            'task_priority': task.priority / 10.0,
        }
        
        # 添加分析结果特征
        if analysis_result.speech_features:
            features.update({
                f'speech_{k}': v for k, v in analysis_result.speech_features.items()
                if isinstance(v, (int, float))
            })
        
        if analysis_result.visual_features:
            features.update({
                f'visual_{k}': v for k, v in analysis_result.visual_features.items()
                if isinstance(v, (int, float))
            })
        
        if analysis_result.content_features:
            features.update({
                f'content_{k}': v for k, v in analysis_result.content_features.items()
                if isinstance(v, (int, float))
            })
        
        return features
    
    def _extract_actual_output(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """提取实际输出"""
        output = {
            'overall_score': analysis_result.overall_score,
            'confidence': analysis_result.confidence
        }
        
        # 添加各维度分数
        if analysis_result.speech_features:
            output['speech_score'] = analysis_result.speech_features.get('overall_score', 0.5)
        
        if analysis_result.visual_features:
            output['visual_score'] = analysis_result.visual_features.get('overall_score', 0.5)
        
        if analysis_result.content_features:
            output['content_score'] = analysis_result.content_features.get('overall_score', 0.5)
        
        return output
    
    def _generate_expected_output(self, analysis_result: AnalysisResult, feedback_score: float) -> Dict[str, Any]:
        """生成期望输出"""
        # 基于反馈分数调整期望输出
        adjustment = (feedback_score - 0.5) * 0.2  # 调整幅度
        
        expected = {
            'overall_score': min(1.0, max(0.0, analysis_result.overall_score + adjustment)),
            'confidence': min(1.0, max(0.0, analysis_result.confidence + adjustment * 0.5))
        }
        
        # 调整各维度分数
        if analysis_result.speech_features:
            current_score = analysis_result.speech_features.get('overall_score', 0.5)
            expected['speech_score'] = min(1.0, max(0.0, current_score + adjustment))
        
        if analysis_result.visual_features:
            current_score = analysis_result.visual_features.get('overall_score', 0.5)
            expected['visual_score'] = min(1.0, max(0.0, current_score + adjustment))
        
        if analysis_result.content_features:
            current_score = analysis_result.content_features.get('overall_score', 0.5)
            expected['content_score'] = min(1.0, max(0.0, current_score + adjustment))
        
        return expected
    
    def _online_update(self, learning_data: LearningData) -> None:
        """在线更新"""
        # 根据数据类型选择算法进行更新
        for algorithm_type, algorithm in self.algorithms.items():
            try:
                algorithm.update(learning_data)
            except Exception as e:
                self.logger.error(f"在线更新{algorithm_type}失败: {e}")
    
    def _group_learning_data(self) -> Dict[str, List[LearningData]]:
        """按类型分组学习数据"""
        grouped = {
            'speech': [],
            'visual': [],
            'content': []
        }
        
        for data in self.learning_data:
            # 根据特征类型分组
            has_speech = any(k.startswith('speech_') for k in data.input_features)
            has_visual = any(k.startswith('visual_') for k in data.input_features)
            has_content = any(k.startswith('content_') for k in data.input_features)
            
            if has_speech:
                grouped['speech'].append(data)
            if has_visual:
                grouped['visual'].append(data)
            if has_content:
                grouped['content'].append(data)
        
        return grouped
    
    def _save_models(self) -> None:
        """保存模型"""
        try:
            for algorithm_type, algorithm in self.algorithms.items():
                model_file = self.model_save_path / f"{algorithm_type}_model.pkl"
                with open(model_file, 'wb') as f:
                    pickle.dump(algorithm.get_model_state(), f)
            
            # 保存学习数据和指标历史
            data_file = self.model_save_path / "learning_data.json"
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'learning_data_count': len(self.learning_data),
                    'metrics_history': [{
                        'timestamp': item['timestamp'].isoformat(),
                        'metrics': {k: asdict(v) for k, v in item['metrics'].items()}
                    } for item in self.metrics_history[-50:]]  # 只保存最近50条
                }, f, ensure_ascii=False, indent=2)
            
            self.logger.info("模型保存成功")
            
        except Exception as e:
            self.logger.error(f"保存模型失败: {e}")
    
    def _load_models(self) -> None:
        """加载模型"""
        try:
            for algorithm_type, algorithm in self.algorithms.items():
                model_file = self.model_save_path / f"{algorithm_type}_model.pkl"
                if model_file.exists():
                    with open(model_file, 'rb') as f:
                        state = pickle.load(f)
                        algorithm.load_model_state(state)
            
            # 加载指标历史
            data_file = self.model_save_path / "learning_data.json"
            if data_file.exists():
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.metrics_history = data.get('metrics_history', [])
            
            self.logger.info("模型加载成功")
            
        except Exception as e:
            self.logger.error(f"加载模型失败: {e}")