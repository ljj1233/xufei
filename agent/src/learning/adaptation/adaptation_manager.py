"""适应管理器模块

实现面试智能体的模型适应性调整功能，包括动态参数调整、环境适应和性能优化。
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from enum import Enum, auto

from agent.src.core.workflow.state import AnalysisResult, Task, TaskStatus
from .learning_engine import LearningEngine, LearningMetrics, LearningData


class AdaptationType(Enum):
    """适应类型枚举"""
    PARAMETER_TUNING = auto()  # 参数调优
    THRESHOLD_ADJUSTMENT = auto()  # 阈值调整
    WEIGHT_REBALANCING = auto()  # 权重重平衡
    STRATEGY_SWITCHING = auto()  # 策略切换
    PERFORMANCE_OPTIMIZATION = auto()  # 性能优化


@dataclass
class AdaptationRule:
    """适应规则"""
    name: str
    condition: str  # 触发条件
    action: str  # 执行动作
    parameters: Dict[str, Any]
    priority: int = 1  # 优先级，数字越大优先级越高
    enabled: bool = True
    created_at: datetime = None
    
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
    performance_before: Dict[str, float]
    performance_after: Dict[str, float]
    success: bool
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics_history = []
        self.performance_trends = {}
        
    def add_metrics(self, metrics: Dict[str, float]) -> None:
        """添加性能指标"""
        timestamped_metrics = {
            'timestamp': datetime.now(),
            **metrics
        }
        
        self.metrics_history.append(timestamped_metrics)
        
        # 保持窗口大小
        if len(self.metrics_history) > self.window_size:
            self.metrics_history = self.metrics_history[-self.window_size:]
        
        # 更新趋势
        self._update_trends()
    
    def get_current_performance(self) -> Dict[str, float]:
        """获取当前性能"""
        if not self.metrics_history:
            return {}
        
        return {k: v for k, v in self.metrics_history[-1].items() if k != 'timestamp'}
    
    def get_average_performance(self, window: int = None) -> Dict[str, float]:
        """获取平均性能"""
        if not self.metrics_history:
            return {}
        
        window = window or min(len(self.metrics_history), 10)
        recent_metrics = self.metrics_history[-window:]
        
        avg_metrics = {}
        for key in recent_metrics[0].keys():
            if key != 'timestamp':
                values = [m[key] for m in recent_metrics if key in m]
                avg_metrics[key] = np.mean(values) if values else 0.0
        
        return avg_metrics
    
    def get_performance_trend(self, metric_name: str) -> str:
        """获取性能趋势"""
        return self.performance_trends.get(metric_name, 'stable')
    
    def is_performance_declining(self, threshold: float = 0.05) -> bool:
        """检查性能是否下降"""
        if len(self.metrics_history) < 10:
            return False
        
        recent_avg = self.get_average_performance(5)
        older_avg = self.get_average_performance(10)
        
        for key in recent_avg:
            if key in older_avg:
                decline = (older_avg[key] - recent_avg[key]) / max(older_avg[key], 0.001)
                if decline > threshold:
                    return True
        
        return False
    
    def _update_trends(self) -> None:
        """更新性能趋势"""
        if len(self.metrics_history) < 5:
            return
        
        recent_metrics = self.metrics_history[-5:]
        
        for key in recent_metrics[0].keys():
            if key != 'timestamp':
                values = [m[key] for m in recent_metrics if key in m]
                if len(values) >= 3:
                    # 简单的趋势分析
                    slope = np.polyfit(range(len(values)), values, 1)[0]
                    
                    if slope > 0.01:
                        self.performance_trends[key] = 'improving'
                    elif slope < -0.01:
                        self.performance_trends[key] = 'declining'
                    else:
                        self.performance_trends[key] = 'stable'


class ParameterOptimizer:
    """参数优化器"""
    
    def __init__(self):
        self.parameter_history = []
        self.optimization_results = []
        
    def optimize_parameters(self, 
                          current_params: Dict[str, Any], 
                          performance_metrics: Dict[str, float],
                          target_metric: str = 'accuracy') -> Dict[str, Any]:
        """优化参数"""
        optimized_params = current_params.copy()
        
        # 记录当前参数和性能
        self.parameter_history.append({
            'timestamp': datetime.now(),
            'parameters': current_params.copy(),
            'performance': performance_metrics.copy()
        })
        
        # 基于历史数据进行参数优化
        if len(self.parameter_history) >= 3:
            optimized_params = self._bayesian_optimization(current_params, target_metric)
        else:
            # 初期使用简单的随机搜索
            optimized_params = self._random_search(current_params)
        
        return optimized_params
    
    def _bayesian_optimization(self, current_params: Dict[str, Any], target_metric: str) -> Dict[str, Any]:
        """贝叶斯优化（简化版）"""
        # 找到历史最佳参数
        best_performance = -float('inf')
        best_params = current_params.copy()
        
        for record in self.parameter_history:
            if target_metric in record['performance']:
                performance = record['performance'][target_metric]
                if performance > best_performance:
                    best_performance = performance
                    best_params = record['parameters'].copy()
        
        # 在最佳参数附近进行微调
        optimized_params = {}
        for key, value in best_params.items():
            if isinstance(value, (int, float)):
                # 添加小幅随机扰动
                noise = np.random.normal(0, abs(value) * 0.1)
                optimized_params[key] = max(0, value + noise)
            else:
                optimized_params[key] = value
        
        return optimized_params
    
    def _random_search(self, current_params: Dict[str, Any]) -> Dict[str, Any]:
        """随机搜索"""
        optimized_params = {}
        
        for key, value in current_params.items():
            if isinstance(value, (int, float)):
                # 在当前值附近随机搜索
                scale = abs(value) * 0.2 if value != 0 else 0.1
                optimized_params[key] = max(0, value + np.random.normal(0, scale))
            else:
                optimized_params[key] = value
        
        return optimized_params


class AdaptationManager:
    """适应管理器主类"""
    
    def __init__(self, learning_engine: LearningEngine, config: Dict[str, Any] = None):
        self.learning_engine = learning_engine
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.performance_monitor = PerformanceMonitor(
            window_size=self.config.get('monitor_window_size', 100)
        )
        self.parameter_optimizer = ParameterOptimizer()
        
        # 适应规则和事件
        self.adaptation_rules = []
        self.adaptation_events = []
        
        # 当前参数
        self.current_parameters = {
            'speech_threshold': 0.7,
            'visual_threshold': 0.6,
            'content_threshold': 0.8,
            'confidence_threshold': 0.75,
            'learning_rate': 0.001,
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
             task: Task, 
             analysis_result: AnalysisResult, 
             feedback_score: float) -> Dict[str, Any]:
        """执行适应性调整"""
        try:
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
        """添加适应规则"""
        self.adaptation_rules.append(rule)
        self.adaptation_rules.sort(key=lambda x: x.priority, reverse=True)
        self.logger.info(f"添加适应规则: {rule.name}")
    
    def get_adaptation_status(self) -> Dict[str, Any]:
        """获取适应状态"""
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
        self.parameter_optimizer = ParameterOptimizer()
        
        # 重置参数为默认值
        self.current_parameters = {
            'speech_threshold': 0.7,
            'visual_threshold': 0.6,
            'content_threshold': 0.8,
            'confidence_threshold': 0.75,
            'learning_rate': 0.001,
            'adaptation_sensitivity': 0.1
        }
        
        self.logger.info("适应状态已重置")
    
    def _extract_performance_metrics(self, 
                                   analysis_result: AnalysisResult, 
                                   feedback_score: float) -> Dict[str, float]:
        """提取性能指标"""
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
        """检查是否需要适应"""
        # 检查性能下降
        if self.performance_monitor.is_performance_declining():
            return True
        
        # 检查适应规则
        for rule in self.adaptation_rules:
            if rule.enabled and self._evaluate_rule_condition(rule):
                return True
        
        return False
    
    def _evaluate_rule_condition(self, rule: AdaptationRule) -> bool:
        """评估规则条件"""
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
        """执行适应"""
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
        
        # 更新学习引擎参数
        self._update_learning_engine_parameters()
        
        return {
            'adapted': True,
            'adaptation_type': AdaptationType.PARAMETER_TUNING,
            'parameters_before': parameters_before,
            'parameters_after': self.current_parameters.copy(),
            'performance_before': performance_before,
            'trigger': 'performance_optimization'
        }
    
    def _update_learning_engine_parameters(self) -> None:
        """更新学习引擎参数"""
        try:
            # 更新学习率
            learning_rate = self.current_parameters.get('learning_rate', 0.001)
            
            for algorithm_type, algorithm in self.learning_engine.algorithms.items():
                if hasattr(algorithm, 'learning_rate'):
                    algorithm.learning_rate = learning_rate
            
            self.logger.info(f"更新学习引擎参数: learning_rate={learning_rate}")
            
        except Exception as e:
            self.logger.error(f"更新学习引擎参数失败: {e}")
    
    def _record_adaptation_event(self, adaptation_result: Dict[str, Any]) -> None:
        """记录适应事件"""
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