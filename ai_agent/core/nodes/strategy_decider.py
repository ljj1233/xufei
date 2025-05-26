# ai_agent/core/nodes/strategy_decider.py

"""
策略决策节点

该节点负责根据任务类型和上下文决定分析策略，包括：
- 确定需要使用的分析器
- 设置分析参数
- 决定是否需要并行处理
"""

from typing import Dict, Any, List, Set
from datetime import datetime

from ai_agent.core.state import GraphState, TaskType


class StrategyDecider:
    """策略决策器节点"""
    
    def __init__(self):
        """初始化策略决策器"""
        # 定义任务类型到分析器的映射
        self.task_analyzer_map = {
            TaskType.SPEECH_ANALYSIS: {"speech_analyzer"},
            TaskType.VISION_ANALYSIS: {"vision_analyzer"},
            TaskType.CONTENT_ANALYSIS: {"content_analyzer"},
            TaskType.COMPREHENSIVE_ANALYSIS: {"speech_analyzer", "vision_analyzer", "content_analyzer"},
            TaskType.CUSTOM: set(),  # 自定义任务需要单独处理
        }
        
        # 定义分析器的默认参数
        self.default_analyzer_params = {
            "speech_analyzer": {
                "sample_rate": 16000,
                "feature_extraction": "mfcc",
                "model": "default",
            },
            "vision_analyzer": {
                "frame_rate": 5,  # 每秒分析的帧数
                "resolution": "medium",  # 分析分辨率
                "features": ["facial_expression", "posture", "eye_contact"],
                "model": "default",
            },
            "content_analyzer": {
                "language": "zh",  # 默认语言
                "analysis_depth": "standard",  # 分析深度
                "features": ["relevance", "structure", "clarity"],
                "model": "default",
            },
        }
    
    def _determine_analyzers(self, task_type: TaskType) -> Set[str]:
        """根据任务类型确定需要使用的分析器
        
        Args:
            task_type: 任务类型
            
        Returns:
            需要使用的分析器集合
        """
        return self.task_analyzer_map.get(task_type, set())
    
    def _customize_analyzer_params(self, analyzers: Set[str], task_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """根据任务数据自定义分析器参数
        
        Args:
            analyzers: 分析器集合
            task_data: 任务数据
            
        Returns:
            自定义的分析器参数
        """
        # 复制默认参数
        params = {}
        for analyzer in analyzers:
            params[analyzer] = self.default_analyzer_params.get(analyzer, {}).copy()
        
        # 根据任务数据自定义参数
        # 这里是一个简化的示例，实际实现可能更复杂
        
        # 语音分析器参数自定义
        if "speech_analyzer" in analyzers:
            # 如果任务数据中指定了采样率，则使用指定的采样率
            if "sample_rate" in task_data:
                params["speech_analyzer"]["sample_rate"] = task_data["sample_rate"]
            
            # 如果任务数据中指定了特征提取方法，则使用指定的方法
            if "feature_extraction" in task_data:
                params["speech_analyzer"]["feature_extraction"] = task_data["feature_extraction"]
        
        # 视觉分析器参数自定义
        if "vision_analyzer" in analyzers:
            # 如果任务数据中指定了帧率，则使用指定的帧率
            if "frame_rate" in task_data:
                params["vision_analyzer"]["frame_rate"] = task_data["frame_rate"]
            
            # 如果任务数据中指定了分辨率，则使用指定的分辨率
            if "resolution" in task_data:
                params["vision_analyzer"]["resolution"] = task_data["resolution"]
        
        # 内容分析器参数自定义
        if "content_analyzer" in analyzers:
            # 如果任务数据中指定了语言，则使用指定的语言
            if "language" in task_data:
                params["content_analyzer"]["language"] = task_data["language"]
            
            # 如果任务数据中指定了分析深度，则使用指定的深度
            if "analysis_depth" in task_data:
                params["content_analyzer"]["analysis_depth"] = task_data["analysis_depth"]
        
        return params
    
    def _decide_parallel_processing(self, analyzers: Set[str], task_data: Dict[str, Any]) -> bool:
        """决定是否需要并行处理
        
        Args:
            analyzers: 分析器集合
            task_data: 任务数据
            
        Returns:
            是否需要并行处理
        """
        # 如果分析器数量大于1，且没有明确指定不并行，则使用并行处理
        if len(analyzers) > 1 and task_data.get("parallel", True):
            return True
        
        # 如果任务数据中明确指定了并行处理，则使用并行处理
        if task_data.get("parallel", False):
            return True
        
        return False
    
    def __call__(self, state: GraphState) -> GraphState:
        """执行策略决策
        
        Args:
            state: 当前图状态
            
        Returns:
            更新后的图状态
        """
        # 确保有当前任务
        if not state.task_state.current_task:
            state.error = "No current task"
            return state
        
        try:
            # 获取当前任务
            current_task = state.task_state.current_task
            
            # 确定需要使用的分析器
            analyzers = self._determine_analyzers(current_task.type)
            
            # 自定义分析器参数
            analyzer_params = self._customize_analyzer_params(analyzers, current_task.data)
            
            # 决定是否需要并行处理
            parallel = self._decide_parallel_processing(analyzers, current_task.data)
            
            # 更新任务数据
            current_task.data["analyzers"] = list(analyzers)
            current_task.data["analyzer_params"] = analyzer_params
            current_task.data["parallel"] = parallel
            
            # 更新状态
            state.task_state.current_task = current_task
            state.next_node = "task_planner"  # 设置下一个节点
            
        except Exception as e:
            state.error = f"Error deciding strategy: {str(e)}"
        
        # 更新时间戳
        state.update_timestamp()
        
        return state