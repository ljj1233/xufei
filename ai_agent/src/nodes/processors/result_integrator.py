# ai_agent/core/nodes/result_integrator.py

"""
结果整合节点

该节点负责整合各个分析器的结果，生成综合评估，包括：
- 收集所有分析结果
- 权重分配和综合评分
- 生成综合评估报告
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ...core.workflow.state import GraphState, TaskType, AnalysisResult

# 配置日志
logger = logging.getLogger(__name__)


class ResultIntegrator:
    """结果整合器节点"""
    
    def __init__(self):
        """初始化结果整合器"""
        # 定义各类分析的默认权重
        self.default_weights = {
            TaskType.SPEECH_ANALYSIS: 0.3,
            TaskType.VISION_ANALYSIS: 0.3,
            TaskType.CONTENT_ANALYSIS: 0.4,
        }
    
    def _collect_results(self, state: GraphState) -> Dict[TaskType, List[AnalysisResult]]:
        """收集所有分析结果
        
        Args:
            state: 当前图状态
            
        Returns:
            按任务类型分组的分析结果
        """
        # 按任务类型分组结果
        grouped_results = {task_type: [] for task_type in TaskType}
        
        # 收集所有结果
        for result in state.analysis_state.results.values():
            grouped_results[result.type].append(result)
        
        return grouped_results
    
    def _calculate_type_score(self, results: List[AnalysisResult]) -> Optional[float]:
        """计算某一类型分析的综合得分
        
        Args:
            results: 同一类型的分析结果列表
            
        Returns:
            综合得分，如果没有有效结果则返回None
        """
        if not results:
            return None
        
        # 过滤掉没有得分的结果
        valid_results = [result for result in results if result.score is not None]
        if not valid_results:
            return None
        
        # 计算平均得分
        total_score = sum(result.score for result in valid_results)
        return total_score / len(valid_results)
    
    def _calculate_comprehensive_score(self, type_scores: Dict[TaskType, Optional[float]]) -> Optional[float]:
        """计算综合得分
        
        Args:
            type_scores: 各类型分析的得分
            
        Returns:
            综合得分，如果没有有效得分则返回None
        """
        # 过滤掉没有得分的类型
        valid_scores = {task_type: score for task_type, score in type_scores.items() if score is not None}
        if not valid_scores:
            return None
        
        # 计算总权重
        total_weight = sum(self.default_weights.get(task_type, 0) for task_type in valid_scores.keys())
        if total_weight == 0:
            # 如果总权重为0，则使用简单平均
            return sum(valid_scores.values()) / len(valid_scores)
        
        # 计算加权平均得分
        weighted_score = sum(score * self.default_weights.get(task_type, 0) / total_weight 
                            for task_type, score in valid_scores.items())
        return weighted_score
    
    def _generate_comprehensive_report(self, grouped_results: Dict[TaskType, List[AnalysisResult]], 
                                      type_scores: Dict[TaskType, Optional[float]], 
                                      comprehensive_score: Optional[float]) -> Dict[str, Any]:
        """生成综合评估报告
        
        Args:
            grouped_results: 按任务类型分组的分析结果
            type_scores: 各类型分析的得分
            comprehensive_score: 综合得分
            
        Returns:
            综合评估报告
        """
        # 创建报告基本结构
        report = {
            "timestamp": datetime.now().isoformat(),
            "comprehensive_score": comprehensive_score,
            "type_scores": {},
            "details": {},
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],
        }
        
        # 添加各类型得分
        for task_type, score in type_scores.items():
            if score is not None:
                report["type_scores"][task_type.name] = score
        
        # 添加详细信息
        for task_type, results in grouped_results.items():
            if results:
                # 合并同一类型的详细信息
                type_details = {}
                for result in results:
                    for key, value in result.details.items():
                        if key not in type_details:
                            type_details[key] = []
                        type_details[key].append(value)
                
                # 计算平均值
                for key, values in type_details.items():
                    if all(isinstance(v, (int, float)) for v in values):
                        type_details[key] = sum(values) / len(values)
                
                report["details"][task_type.name] = type_details
        
        # 生成优势、劣势和建议
        # 这里是一个简化的示例，实际实现可能更复杂，可能会使用LLM生成
        
        # 优势：得分高于0.8的项目
        for task_type_name, details in report["details"].items():
            for key, value in details.items():
                if isinstance(value, (int, float)) and value >= 0.8:
                    report["strengths"].append(f"{task_type_name} - {key}: {value:.2f}")
        
        # 劣势：得分低于0.7的项目
        for task_type_name, details in report["details"].items():
            for key, value in details.items():
                if isinstance(value, (int, float)) and value < 0.7:
                    report["weaknesses"].append(f"{task_type_name} - {key}: {value:.2f}")
        
        # 建议：基于劣势生成建议
        for weakness in report["weaknesses"]:
            # 从劣势中提取类型和项目
            parts = weakness.split(' - ')
            if len(parts) >= 2:
                task_type_name = parts[0]
                item_parts = parts[1].split(':')
                if len(item_parts) >= 1:
                    item = item_parts[0]
                    
                    # 根据类型和项目生成建议
                    if task_type_name == "SPEECH_ANALYSIS":
                        if item == "clarity":
                            report["suggestions"].append("提高语音清晰度，注意发音和语速")
                        elif item == "pace":
                            report["suggestions"].append("调整语速，避免说话过快或过慢")
                        elif item == "tone":
                            report["suggestions"].append("注意语调变化，避免单调")
                        elif item == "volume":
                            report["suggestions"].append("调整音量，确保听众能清晰听到")
                        elif item == "pronunciation":
                            report["suggestions"].append("改进发音，注意重点词的发音")
                    
                    elif task_type_name == "VISION_ANALYSIS":
                        if item == "facial_expression":
                            report["suggestions"].append("增加面部表情的丰富度，展示自信和热情")
                        elif item == "posture":
                            report["suggestions"].append("改善姿势，保持挺拔但放松的状态")
                        elif item == "eye_contact":
                            report["suggestions"].append("增加眼神交流，展示专注和自信")
                        elif item == "gestures":
                            report["suggestions"].append("适当使用手势，增强表达效果")
                        elif item == "appearance":
                            report["suggestions"].append("注意着装和整体形象，展示专业性")
                    
                    elif task_type_name == "CONTENT_ANALYSIS":
                        if item == "relevance":
                            report["suggestions"].append("提高内容相关性，确保回答紧扣问题")
                        elif item == "structure":
                            report["suggestions"].append("改善内容结构，使表达更有条理")
                        elif item == "clarity":
                            report["suggestions"].append("提高表达清晰度，避免模糊或歧义")
                        elif item == "depth":
                            report["suggestions"].append("增加内容深度，提供更详细的分析和例子")
                        elif item == "originality":
                            report["suggestions"].append("增加内容原创性，展示个人见解")
        
        return report
    
    def __call__(self, state: GraphState) -> GraphState:
        """执行结果整合
        
        Args:
            state: 当前图状态
            
        Returns:
            更新后的图状态
        """
        logger.info(f"开始整合分析结果，输入状态: {state}")
        try:
            # 收集所有分析结果
            grouped_results = self._collect_results(state)
            logger.debug(f"分组分析结果: {grouped_results}")
            
            # 计算各类型得分
            type_scores = {task_type: self._calculate_type_score(results) 
                          for task_type, results in grouped_results.items()}
            
            # 计算综合得分
            comprehensive_score = self._calculate_comprehensive_score(type_scores)
            
            # 生成综合评估报告
            report = self._generate_comprehensive_report(grouped_results, type_scores, comprehensive_score)
            logger.info(f"综合评估报告生成完成: {report}")
            
            # 更新状态
            state.output = {
                "comprehensive_score": comprehensive_score,
                "type_scores": {task_type.name: score for task_type, score in type_scores.items() if score is not None},
                "report": report,
            }
            
            # 设置下一个节点
            state.next_node = "feedback_generator"
            
        except Exception as e:
            logger.error(f"结果整合异常: {e}")
            state.error = f"Error integrating results: {str(e)}"
            # 出错时也转到反馈生成节点
            state.next_node = "feedback_generator"
        
        # 更新时间戳
        state.update_timestamp()
        
        return state