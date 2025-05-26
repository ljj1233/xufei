"""适应节点模块

实现面试智能体的适应性调整节点，集成到LangGraph工作流中。
使用基于规则的决策树方法而非训练模型，通过JSON存储适应历史和参数。
"""

from typing import Dict, Any, Optional, Tuple, List, Callable
import logging

from ..state import GraphState, Task, AnalysisResult
from ..learning.adaptation_manager_refactored import AdaptationManager


class AdaptationNode:
    """适应节点
    
    负责在工作流中执行适应性调整，优化模型参数和阈值。
    使用基于规则的决策树方法而非训练模型进行适应。
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化适应节点
        
        Args:
            config: 配置参数
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # 初始化适应管理器
        self.adaptation_manager = AdaptationManager(config)
        
        # 适应触发条件
        self.adaptation_triggers = {
            'performance_decline': self._check_performance_decline,
            'feedback_negative': self._check_negative_feedback,
            'confidence_low': self._check_low_confidence,
            'periodic': self._check_periodic_adaptation
        }
        
        # 上次适应时间
        self.last_adaptation_time = None
    
    def __call__(self, state: GraphState) -> GraphState:
        """执行适应节点
        
        Args:
            state: 图状态
            
        Returns:
            GraphState: 更新后的图状态
        """
        try:
            # 检查是否需要适应
            if self._should_adapt(state):
                # 执行适应
                adaptation_result = self.adaptation_manager.adapt(state)
                
                # 更新状态
                if adaptation_result.get('adapted', False):
                    state = self._update_state_after_adaptation(state, adaptation_result)
                    self.logger.info(f"执行适应性调整: {adaptation_result.get('adaptation_type')}")
                else:
                    self.logger.info(f"跳过适应性调整: {adaptation_result.get('reason')}")
            else:
                self.logger.debug("不需要适应性调整")
            
            return state
            
        except Exception as e:
            self.logger.error(f"适应节点执行失败: {e}")
            return state
    
    def _should_adapt(self, state: GraphState) -> bool:
        """检查是否应该执行适应
        
        Args:
            state: 图状态
            
        Returns:
            bool: 是否应该适应
        """
        # 检查各触发条件
        for trigger_name, trigger_func in self.adaptation_triggers.items():
            if trigger_func(state):
                self.logger.info(f"适应触发条件满足: {trigger_name}")
                return True
        
        return False
    
    def _check_performance_decline(self, state: GraphState) -> bool:
        """检查性能是否下降
        
        Args:
            state: 图状态
            
        Returns:
            bool: 性能是否下降
        """
        # 使用适应管理器的性能监控器检查
        return self.adaptation_manager.performance_monitor.is_performance_declining()
    
    def _check_negative_feedback(self, state: GraphState) -> bool:
        """检查是否有负面反馈
        
        Args:
            state: 图状态
            
        Returns:
            bool: 是否有负面反馈
        """
        if not state.feedback_state or not hasattr(state.feedback_state, 'feedback_score'):
            return False
        
        # 检查反馈分数是否低于阈值
        threshold = self.config.get('negative_feedback_threshold', 0.4)
        return state.feedback_state.feedback_score < threshold
    
    def _check_low_confidence(self, state: GraphState) -> bool:
        """检查置信度是否过低
        
        Args:
            state: 图状态
            
        Returns:
            bool: 置信度是否过低
        """
        if not state.analysis_state or not state.analysis_state.result:
            return False
        
        # 检查分析结果的置信度是否低于阈值
        threshold = self.config.get('low_confidence_threshold', 0.6)
        return state.analysis_state.result.confidence < threshold
    
    def _check_periodic_adaptation(self, state: GraphState) -> bool:
        """检查是否应该定期适应
        
        Args:
            state: 图状态
            
        Returns:
            bool: 是否应该定期适应
        """
        # 检查是否已经处理了足够多的任务
        if not hasattr(state, 'task_count') or state.task_count < 10:
            return False
        
        # 检查是否是第N个任务（每N个任务适应一次）
        adaptation_interval = self.config.get('adaptation_interval', 10)
        return state.task_count % adaptation_interval == 0
    
    def _update_state_after_adaptation(self, state: GraphState, adaptation_result: Dict[str, Any]) -> GraphState:
        """适应后更新状态
        
        Args:
            state: 图状态
            adaptation_result: 适应结果
            
        Returns:
            GraphState: 更新后的图状态
        """
        # 更新分析阈值
        if state.analysis_state and hasattr(state.analysis_state, 'thresholds'):
            parameters_after = adaptation_result.get('parameters_after', {})
            
            # 更新阈值
            if 'speech_threshold' in parameters_after:
                state.analysis_state.thresholds['speech'] = parameters_after['speech_threshold']
            
            if 'visual_threshold' in parameters_after:
                state.analysis_state.thresholds['visual'] = parameters_after['visual_threshold']
            
            if 'content_threshold' in parameters_after:
                state.analysis_state.thresholds['content'] = parameters_after['content_threshold']
            
            if 'confidence_threshold' in parameters_after:
                state.analysis_state.thresholds['confidence'] = parameters_after['confidence_threshold']
        
        # 记录适应事件
        if not hasattr(state, 'adaptation_events'):
            state.adaptation_events = []
        
        state.adaptation_events.append({
            'timestamp': adaptation_result.get('timestamp', None),
            'adaptation_type': str(adaptation_result.get('adaptation_type', 'unknown')),
            'success': adaptation_result.get('adapted', False)
        })
        
        return state