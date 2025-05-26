"""适应管理器模块

实现面试智能体的模型适应功能，包括参数调整、阈值优化和性能监控。
与LangGraph框架集成，支持状态管理和工作流集成。
使用基于规则的决策树方法而非训练模型，通过JSON存储适应历史和参数。
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from pathlib import Path
import logging
from enum import Enum, auto
from collections import deque

from ..state import Task, AnalysisResult, GraphState


class AdaptationType(Enum):
    """适应类型枚举"""
    PARAMETER_TUNING = auto()  # 参数调整
    THRESHOLD_ADJUSTMENT = auto()  # 阈值调整
    WEIGHT_REBALANCING = auto()  # 权重重平衡
    FEATURE_SELECTION = auto()  # 特征选择
    MODEL_SWITCHING = auto()  # 模型切换


@dataclass
class AdaptationRule:
    """适应规则"""
    name: str
    condition: str  # 触发条件
    action: str  # 执行动作
    parameters: Dict[str, Any] = field(default_factory=dict)  # 参数
    priority: int = 0  # 优先级
    enabled: bool = True  # 是否启用
    created_at: datetime = None  # 创建时间
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class AdaptationEvent:
    """适应事件"""
    event_id: str
    adaptation_type: AdaptationType
    trigger_condition: str
    action_taken: str
    parameters_before: Dict[str, Any]
    parameters_after: Dict[str, Any]
    performance_before: Dict[str, Any]
    performance_after: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, window_size: int = 100):
        """初始化性能监控器
        
        Args:
            window_size: 滑动窗口大小
        """
        self.window_size = window_size
        self.metrics_history = deque(maxlen=window_size)
        self.performance_trends = {
            'overall_score': 0.0,
            'confidence': 0.0,
            'feedback_score': 0.0,
            'speech_score': 0.0,
            'visual_score': 0.0,
            'content_score': 0.0
        }
    
    def add_metrics(self, metrics: Dict[str, float]) -> None:
        """添加性能指标
        
        Args:
            metrics: 性能指标字典
        """
        self.metrics_history.append(metrics)
        self._update_trends()
    
    def get_current_performance(self) -> Dict[str, float]:
        """获取当前性能
        
        Returns:
            Dict[str, float]: 当前性能指标
        """
        if not self.metrics_history:
            return {}
        
        return self.metrics_history[-1].copy()
    
    def get_average_performance(self, window: int = None) -> Dict[str, float]:
        """获取平均性能
        
        Args:
            window: 窗口大小，如果为None则使用所有历史数据
            
        Returns:
            Dict[str, float]: 平均性能指标
        """
        if not self.metrics_history:
            return {}
        
        if window is None or window > len(self.metrics_history):
            window = len(self.metrics_history)
        
        recent_metrics = list(self.metrics_history)[-window:]
        
        avg_metrics = {}
        for key in recent_metrics[0].keys():
            values = [m.get(key, 0) for m in recent_metrics if key in m]
            if values:
                avg_metrics[key] = sum(values) / len(values)
        
        return avg_metrics
    
    def is_performance_declining(self, threshold: float = 0.05, window: int = 10) -> bool:
        """检查性能是否下降
        
        Args:
            threshold: 下降阈值
            window: 窗口大小
            
        Returns:
            bool: 是否下降
        """
        if len(self.metrics_history) < window:
            return False
        
        # 获取窗口内的平均性能
        recent_avg = self.get_average_performance(window)
        previous_avg = self.get_average_performance(window * 2) if len(self.metrics_history) >= window * 2 else recent_avg
        
        # 检查关键指标是否下降
        for key in ['overall_score', 'confidence', 'feedback_score']:
            if key in recent_avg and key in previous_avg:
                if previous_avg[key] - recent_avg[key] > threshold:
                    return True
        
        return False
    
    def _update_trends(self) -> None:
        """更新性能趋势"""
        if len(self.metrics_history) < 2:
            return
        
        # 计算最近10个样本的趋势
        window = min(10, len(self.metrics_history))
        recent = list(self.metrics_history)[-window:]
        
        for key in self.performance_trends.keys():
            values = [m.get(key, None) for m in recent if key in m]
            values = [v for v in values if v is not None]
            
            if len(values) >= 2:
                # 简单线性回归计算趋势
                x = np.arange(len(values))
                y = np.array(values)
                A = np.vstack([x, np.ones(len(x))]).T
                m, c = np.linalg.lstsq(A, y, rcond=None)[0]
                
                self.performance_trends[key] = m  # 斜率作为趋势指标


class DecisionTreeOptimizer:
    """决策树参数优化器
    
    使用简单决策树规则而非训练模型来优化参数
    """
    
    def __init__(self):
        """初始化决策树优化器"""
        self.optimization_history = []
        self.decision_rules = {
            'speech_threshold': self._optimize_speech_threshold,
            'visual_threshold': self._optimize_visual_threshold,
            'content_threshold': self._optimize_content_threshold,
            'confidence_threshold': self._optimize_confidence_threshold,
            'adaptation_sensitivity': self._optimize_sensitivity
        }
    
    def optimize_parameters(self, 
                           current_params: Dict[str, Any], 
                           performance_metrics: Dict[str, float],
                           target_metric: str = 'overall_score') -> Dict[str, Any]:
        """优化参数
        
        Args:
            current_params: 当前参数
            performance_metrics: 性能指标
            target_metric: 目标指标
            
        Returns:
            Dict[str, Any]: 优化后的参数
        """
        # 记录优化历史
        self.optimization_history.append({
            'params': current_params.copy(),
            'metrics': performance_metrics.copy(),
            'timestamp': datetime.now()
        })
        
        # 应用决策树规则优化参数
        optimized_params = current_params.copy()
        
        for param_name, optimizer_func in self.decision_rules.items():
            if param_name in current_params:
                optimized_params[param_name] = optimizer_func(
                    current_params[param_name],
                    performance_metrics
                )
        
        return optimized_params
    
    def _optimize_speech_threshold(self, current_value: float, metrics: Dict[str, float]) -> float:
        """优化语音阈值"""
        speech_score = metrics.get('speech_score', 0.5)
        
        # 决策树规则
        if speech_score < 0.3:  # 语音分数很低
            return max(0.5, current_value - 0.1)  # 降低阈值，提高通过率
        elif speech_score > 0.8:  # 语音分数很高
            return min(0.9, current_value + 0.05)  # 提高阈值，提高标准
        elif 0.4 <= speech_score <= 0.6:  # 语音分数一般
            return current_value  # 保持不变
        else:
            # 微调
            adjustment = (speech_score - 0.5) * 0.1
            return max(0.5, min(0.9, current_value + adjustment))
    
    def _optimize_visual_threshold(self, current_value: float, metrics: Dict[str, float]) -> float:
        """优化视觉阈值"""
        visual_score = metrics.get('visual_score', 0.5)
        
        # 决策树规则
        if visual_score < 0.3:  # 视觉分数很低
            return max(0.4, current_value - 0.1)  # 降低阈值
        elif visual_score > 0.8:  # 视觉分数很高
            return min(0.8, current_value + 0.05)  # 提高阈值
        elif 0.4 <= visual_score <= 0.6:  # 视觉分数一般
            return current_value  # 保持不变
        else:
            # 微调
            adjustment = (visual_score - 0.5) * 0.1
            return max(0.4, min(0.8, current_value + adjustment))
    
    def _optimize_content_threshold(self, current_value: float, metrics: Dict[str, float]) -> float:
        """优化内容阈值"""
        content_score = metrics.get('content_score', 0.5)
        
        # 决策树规则
        if content_score < 0.4:  # 内容分数较低
            return max(0.6, current_value - 0.1)  # 降低阈值
        elif content_score > 0.85:  # 内容分数很高
            return min(0.95, current_value + 0.05)  # 提高阈值
        elif 0.5 <= content_score <= 0.7:  # 内容分数一般
            return current_value  # 保持不变
        else:
            # 微调
            adjustment = (content_score - 0.6) * 0.15
            return max(0.6, min(0.95, current_value + adjustment))
    
    def _optimize_confidence_threshold(self, current_value: float, metrics: Dict[str, float]) -> float:
        """优化置信度阈值"""
        confidence = metrics.get('confidence', 0.5)
        feedback_score = metrics.get('feedback_score', 0.5)
        
        # 结合置信度和反馈分数
        if confidence < 0.4 and feedback_score < 0.4:  # 置信度和反馈都低
            return max(0.6, current_value - 0.15)  # 大幅降低阈值
        elif confidence > 0.8 and feedback_score > 0.7:  # 置信度和反馈都高
            return min(0.9, current_value + 0.05)  # 提高阈值
        elif abs(confidence - feedback_score) > 0.3:  # 置信度和反馈差异大
            # 向反馈分数方向调整
            return current_value + (feedback_score - confidence) * 0.1
        else:
            return current_value  # 保持不变
    
    def _optimize_sensitivity(self, current_value: float, metrics: Dict[str, float]) -> float:
        """优化适应灵敏度"""
        feedback_score = metrics.get('feedback_score', 0.5)
        
        # 根据反馈调整灵敏度
        if feedback_score < 0.3:  # 反馈很差
            return min(0.2, current_value + 0.05)  # 提高灵敏度
        elif feedback_score > 0.8:  # 反馈很好
            return max(0.05, current_value - 0.02)  # 降低灵敏度
        else:
            return current_value  # 保持不变


class AdaptationManager:
    """适应管理器主类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.performance_monitor = PerformanceMonitor(
            window_size=self.config.get('monitor_window_size', 100)
        )
        self.parameter_optimizer = DecisionTreeOptimizer()
        
        # 适应规则和事件
        self.adaptation_rules = []
        self.adaptation_events = []
        
        # 当前参数
        self.current_parameters = {
            'speech_threshold': 0.7,
            'visual_threshold': 0.6,
            'content_threshold': 0.8,
            'confidence_threshold': 0.75,
            'adaptation_sensitivity': 0.1
        }
        
        # 加载默认适应规则
        self._load_default_rules()
        
        # 保存路径
        self.save_path = Path(self.config.get('adaptation_save_path', 'models/adaptation'))
        self.save_path.mkdir(parents=True, exist_ok=True)
        
        # 加载历史数据
        self._load_adaptation_data()
    
    def adapt(self, 
             state: GraphState) -> Dict[str, Any]:
        """执行适应性调整
        
        Args:
            state: 图状态对象
            
        Returns:
            Dict[str, Any]: 适应结果
        """
        try:
            # 从状态中提取任务和分析结果
            task = state.task_state.current_task
            analysis_result = state.analysis_state.result
            feedback_score = state.feedback_state.feedback_score if state.feedback_state else 0.5
            
            # 更新性能监控
            performance_metrics = self._extract_performance_metrics(analysis_result, feedback_score)
            self.performance_monitor.add_metrics(performance_metrics)
            
            # 检查是否需要适应
            adaptation_needed = self._check_adaptation_needed()
            
            if adaptation_needed:
                # 执行适应
                adaptation_result = self._execute_adaptation(task, analysis_result, feedback_score)
                
                # 记录适应事件
                self._record_adaptation_event(adaptation_result)
                
                # 保存数据
                self._save_adaptation_data()
                
                return adaptation_result
            
            return {'adapted': False, 'reason': 'No adaptation needed'}
            
        except Exception as e:
            self.logger.error(f"适应性调整失败: {e}")
            return {'adapted': False, 'error': str(e)}
    
    def add_adaptation_rule(self, rule: AdaptationRule) -> None:
        """添加适应规则
        
        Args:
            rule: 适应规则
        """
        self.adaptation_rules.append(rule)
        self.adaptation_rules.sort(key=lambda x: x.priority, reverse=True)
        self.logger.info(f"添加适应规则: {rule.name}")
    
    def get_adaptation_status(self) -> Dict[str, Any]:
        """获取适应状态
        
        Returns:
            Dict[str, Any]: 适应状态
        """
        return {
            'current_parameters': self.current_parameters.copy(),
            'performance_trends': self.performance_monitor.performance_trends.copy(),
            'recent_events': [asdict(event) for event in self.adaptation_events[-10:]],
            'adaptation_rules_count': len(self.adaptation_rules),
            'total_adaptations': len(self.adaptation_events)
        }
    
    def reset_adaptation(self) -> None:
        """重置适应状态"""
        self.adaptation_events.clear()
        self.performance_monitor = PerformanceMonitor(
            window_size=self.config.get('monitor_window_size', 100)
        )
        self.parameter_optimizer = DecisionTreeOptimizer()
        
        # 重置参数为默认值
        self.current_parameters = {
            'speech_threshold': 0.7,
            'visual_threshold': 0.6,
            'content_threshold': 0.8,
            'confidence_threshold': 0.75,
            'adaptation_sensitivity': 0.1
        }
        
        self.logger.info("适应状态已重置")
    
    def _extract_performance_metrics(self, 
                                   analysis_result: AnalysisResult, 
                                   feedback_score: float) -> Dict[str, float]:
        """提取性能指标
        
        Args:
            analysis_result: 分析结果
            feedback_score: 反馈分数
            
        Returns:
            Dict[str, float]: 性能指标
        """
        metrics = {
            'overall_score': analysis_result.overall_score,
            'confidence': analysis_result.confidence,
            'feedback_score': feedback_score
        }
        
        # 添加各维度分数
        if analysis_result.speech_features:
            metrics['speech_score'] = analysis_result.speech_features.get('overall_score', 0.5)
        
        if analysis_result.visual_features:
            metrics['visual_score'] = analysis_result.visual_features.get('overall_score', 0.5)
        
        if analysis_result.content_features:
            metrics['content_score'] = analysis_result.content_features.get('overall_score', 0.5)
        
        return metrics
    
    def _check_adaptation_needed(self) -> bool:
        """检查是否需要适应
        
        Returns:
            bool: 是否需要适应
        """
        # 检查性能下降
        if self.performance_monitor.is_performance_declining():
            return True
        
        # 检查适应规则
        for rule in self.adaptation_rules:
            if rule.enabled and self._evaluate_rule_condition(rule):
                return True
        
        return False
    
    def _evaluate_rule_condition(self, rule: AdaptationRule) -> bool:
        """评估规则条件
        
        Args:
            rule: 适应规则
            
        Returns:
            bool: 条件是否满足
        """
        try:
            # 简化的条件评估
            current_performance = self.performance_monitor.get_current_performance()
            
            if rule.condition == 'accuracy_below_threshold':
                threshold = rule.parameters.get('threshold', 0.7)
                return current_performance.get('overall_score', 1.0) < threshold
            
            elif rule.condition == 'confidence_low':
                threshold = rule.parameters.get('threshold', 0.6)
                return current_performance.get('confidence', 1.0) < threshold
            
            elif rule.condition == 'feedback_negative':
                threshold = rule.parameters.get('threshold', 0.5)
                return current_performance.get('feedback_score', 1.0) < threshold
            
            return False
            
        except Exception as e:
            self.logger.error(f"评估规则条件失败: {e}")
            return False
    
    def _execute_adaptation(self, 
                          task: Task, 
                          analysis_result: AnalysisResult, 
                          feedback_score: float) -> Dict[str, Any]:
        """执行适应
        
        Args:
            task: 任务
            analysis_result: 分析结果
            feedback_score: 反馈分数
            
        Returns:
            Dict[str, Any]: 适应结果
        """
        parameters_before = self.current_parameters.copy()
        performance_before = self.performance_monitor.get_current_performance()
        
        # 参数优化
        optimized_params = self.parameter_optimizer.optimize_parameters(
            self.current_parameters,
            performance_before,
            target_metric='overall_score'
        )
        
        # 应用优化后的参数
        self.current_parameters.update(optimized_params)
        
        return {
            'adapted': True,
            'adaptation_type': AdaptationType.PARAMETER_TUNING,
            'parameters_before': parameters_before,
            'parameters_after': self.current_parameters.copy(),
            'performance_before': performance_before,
            'trigger': 'performance_optimization'
        }
    
    def _record_adaptation_event(self, adaptation_result: Dict[str, Any]) -> None:
        """记录适应事件
        
        Args:
            adaptation_result: 适应结果
        """
        event = AdaptationEvent(
            event_id=f"adapt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.adaptation_events)}",
            adaptation_type=adaptation_result.get('adaptation_type', AdaptationType.PARAMETER_TUNING),
            trigger_condition=adaptation_result.get('trigger', 'unknown'),
            action_taken='parameter_optimization',
            parameters_before=adaptation_result.get('parameters_before', {}),
            parameters_after=adaptation_result.get('parameters_after', {}),
            performance_before=adaptation_result.get('performance_before', {}),
            performance_after={},  # 将在下次评估时更新
            success=adaptation_result.get('adapted', False)
        )
        
        self.adaptation_events.append(event)
        
        # 保持事件历史大小
        if len(self.adaptation_events) > 1000:
            self.adaptation_events = self.adaptation_events[-1000:]
    
    def _load_default_rules(self) -> None:
        """加载默认适应规则"""
        default_rules = [
            AdaptationRule(
                name="accuracy_threshold",
                condition="accuracy_below_threshold",
                action="optimize_parameters",
                parameters={"threshold": 0.7},
                priority=3
            ),
            AdaptationRule(
                name="confidence_threshold",
                condition="confidence_low",
                action="adjust_thresholds",
                parameters={"threshold": 0.6},
                priority=2
            ),
            AdaptationRule(
                name="feedback_threshold",
                condition="feedback_negative",
                action="rebalance_weights",
                parameters={"threshold": 0.5},
                priority=1
            )
        ]
        
        self.adaptation_rules.extend(default_rules)
        self.logger.info(f"加载了{len(default_rules)}个默认适应规则")
    
    def _save_adaptation_data(self) -> None:
        """保存适应数据"""
        try:
            # 保存适应事件
            events_file = self.save_path / "adaptation_events.json"
            with open(events_file, 'w', encoding='utf-8') as f:
                events_data = []
                for event in self.adaptation_events[-100:]:  # 只保存最近100个事件
                    event_dict = asdict(event)
                    event_dict['timestamp'] = event.timestamp.isoformat()
                    event_dict['adaptation_type'] = event.adaptation_type.name
                    events_data.append(event_dict)
                
                json.dump(events_data, f, ensure_ascii=False, indent=2)
            
            # 保存当前参数
            params_file = self.save_path / "current_parameters.json"
            with open(params_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_parameters, f, ensure_ascii=False, indent=2)
            
            # 保存性能历史
            metrics_file = self.save_path / "performance_metrics.json"
            with open(metrics_file, 'w', encoding='utf-8') as f:
                metrics_data = {
                    'recent_metrics': list(self.performance_monitor.metrics_history)[-50:],
                    'trends': self.performance_monitor.performance_trends
                }
                json.dump(metrics_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info("适应数据保存成功")
            
        except Exception as e:
            self.logger.error(f"保存适应数据失败: {e}")
    
    def _load_adaptation_data(self) -> None:
        """加载适应数据"""
        try:
            # 加载当前参数
            params_file = self.save_path / "current_parameters.json"
            if params_file.exists():
                with open(params_file, 'r', encoding='utf-8') as f:
                    saved_params = json.load(f)
                    self.current_parameters.update(saved_params)
            
            # 加载性能历史
            metrics_file = self.save_path / "performance_metrics.json"
            if metrics_file.exists():
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    metrics_data = json.load(f)
                    for metric in metrics_data.get('recent_metrics', []):
                        self.performance_monitor.add_metrics(metric)
            
            # 加载适应事件（仅用于统计）
            events_file = self.save_path / "adaptation_events.json"
            if events_file.exists():
                with open(events_file, 'r', encoding='utf-8') as f:
                    events_data = json.load(f)
                    # 这里只加载事件数量，不加载完整事件以节省内存
                    self.logger.info(f"历史适应事件数量: {len(events_data)}")
            
            self.logger.info("适应数据加载成功")
            
        except Exception as e:
            self.logger.error(f"加载适应数据失败: {e}")