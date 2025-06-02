# ai_agent/core/nodes/feedback_generator.py

"""
反馈生成节点

该节点负责根据整合的结果生成用户反馈，包括：
- 生成结构化反馈
- 格式化反馈内容
- 添加个性化建议
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ...core.workflow.state import GraphState

# 配置日志
logger = logging.getLogger(__name__)


class FeedbackGenerator:
    """反馈生成器节点"""
    
    def __init__(self):
        """初始化反馈生成器"""
        pass
    
    def _generate_feedback_summary(self, output: Dict[str, Any]) -> str:
        """生成反馈摘要
        
        Args:
            output: 输出数据
            
        Returns:
            反馈摘要
        """
        # 获取综合得分和报告
        comprehensive_score = output.get("comprehensive_score")
        report = output.get("report", {})
        
        # 生成摘要
        summary = []
        
        # 添加标题
        summary.append("# 面试评估报告")
        summary.append("")
        
        # 添加时间
        timestamp = report.get("timestamp")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                summary.append(f"**评估时间**: {formatted_time}")
                summary.append("")
            except:
                pass
        
        # 添加综合得分
        if comprehensive_score is not None:
            # 将分数转换为百分比
            score_percent = int(comprehensive_score * 100)
            summary.append(f"**综合评分**: {score_percent}/100")
            summary.append("")
            
            # 添加评分等级
            if score_percent >= 90:
                summary.append("**评级**: 优秀 (A+)")
            elif score_percent >= 80:
                summary.append("**评级**: 良好 (A)")
            elif score_percent >= 70:
                summary.append("**评级**: 中等 (B)")
            elif score_percent >= 60:
                summary.append("**评级**: 及格 (C)")
            else:
                summary.append("**评级**: 需要改进 (D)")
            summary.append("")
        
        # 添加分项评分
        type_scores = output.get("type_scores", {})
        if type_scores:
            summary.append("## 分项评分")
            summary.append("")
            
            for task_type, score in type_scores.items():
                # 将分数转换为百分比
                score_percent = int(score * 100)
                
                # 格式化任务类型名称
                if task_type == "SPEECH_ANALYSIS":
                    type_name = "语音表现"
                elif task_type == "VISION_ANALYSIS":
                    type_name = "视觉表现"
                elif task_type == "CONTENT_ANALYSIS":
                    type_name = "内容表现"
                elif task_type == "COMPREHENSIVE_ANALYSIS":
                    type_name = "综合表现"
                else:
                    type_name = task_type
                
                summary.append(f"**{type_name}**: {score_percent}/100")
            
            summary.append("")
        
        # 添加优势
        strengths = report.get("strengths", [])
        if strengths:
            summary.append("## 优势")
            summary.append("")
            
            for strength in strengths:
                # 格式化优势描述
                parts = strength.split(' - ')
                if len(parts) >= 2:
                    task_type = parts[0]
                    item_parts = parts[1].split(':')
                    if len(item_parts) >= 1:
                        item = item_parts[0]
                        
                        # 翻译任务类型和项目
                        if task_type == "SPEECH_ANALYSIS":
                            task_type = "语音表现"
                            if item == "clarity":
                                item = "清晰度"
                            elif item == "pace":
                                item = "语速"
                            elif item == "tone":
                                item = "语调"
                            elif item == "volume":
                                item = "音量"
                            elif item == "pronunciation":
                                item = "发音"
                        
                        elif task_type == "VISION_ANALYSIS":
                            task_type = "视觉表现"
                            if item == "facial_expression":
                                item = "面部表情"
                            elif item == "posture":
                                item = "姿势"
                            elif item == "eye_contact":
                                item = "眼神交流"
                            elif item == "gestures":
                                item = "手势"
                            elif item == "appearance":
                                item = "外表"
                        
                        elif task_type == "CONTENT_ANALYSIS":
                            task_type = "内容表现"
                            if item == "relevance":
                                item = "相关性"
                            elif item == "structure":
                                item = "结构"
                            elif item == "clarity":
                                item = "清晰度"
                            elif item == "depth":
                                item = "深度"
                            elif item == "originality":
                                item = "原创性"
                        
                        summary.append(f"- **{task_type} - {item}**: 表现优秀")
                else:
                    summary.append(f"- {strength}")
            
            summary.append("")
        
        # 添加劣势
        weaknesses = report.get("weaknesses", [])
        if weaknesses:
            summary.append("## 需要改进的地方")
            summary.append("")
            
            for weakness in weaknesses:
                # 格式化劣势描述
                parts = weakness.split(' - ')
                if len(parts) >= 2:
                    task_type = parts[0]
                    item_parts = parts[1].split(':')
                    if len(item_parts) >= 1:
                        item = item_parts[0]
                        
                        # 翻译任务类型和项目
                        if task_type == "SPEECH_ANALYSIS":
                            task_type = "语音表现"
                            if item == "clarity":
                                item = "清晰度"
                            elif item == "pace":
                                item = "语速"
                            elif item == "tone":
                                item = "语调"
                            elif item == "volume":
                                item = "音量"
                            elif item == "pronunciation":
                                item = "发音"
                        
                        elif task_type == "VISION_ANALYSIS":
                            task_type = "视觉表现"
                            if item == "facial_expression":
                                item = "面部表情"
                            elif item == "posture":
                                item = "姿势"
                            elif item == "eye_contact":
                                item = "眼神交流"
                            elif item == "gestures":
                                item = "手势"
                            elif item == "appearance":
                                item = "外表"
                        
                        elif task_type == "CONTENT_ANALYSIS":
                            task_type = "内容表现"
                            if item == "relevance":
                                item = "相关性"
                            elif item == "structure":
                                item = "结构"
                            elif item == "clarity":
                                item = "清晰度"
                            elif item == "depth":
                                item = "深度"
                            elif item == "originality":
                                item = "原创性"
                        
                        summary.append(f"- **{task_type} - {item}**: 需要改进")
                else:
                    summary.append(f"- {weakness}")
            
            summary.append("")
        
        # 添加建议
        suggestions = report.get("suggestions", [])
        if suggestions:
            summary.append("## 改进建议")
            summary.append("")
            
            for suggestion in suggestions:
                summary.append(f"- {suggestion}")
            
            summary.append("")
        
        # 添加结束语
        summary.append("## 总结")
        summary.append("")
        if comprehensive_score is not None:
            if comprehensive_score >= 0.9:
                summary.append("您的面试表现非常出色！继续保持这种水平，相信您会在求职过程中取得优异的成绩。")
            elif comprehensive_score >= 0.8:
                summary.append("您的面试表现良好，在大多数方面都展现出了不错的能力。针对需要改进的地方进行有针对性的练习，您的表现会更加出色。")
            elif comprehensive_score >= 0.7:
                summary.append("您的面试表现中等，有一些亮点，但也有明显需要改进的地方。建议您重点关注改进建议，进行有针对性的练习。")
            elif comprehensive_score >= 0.6:
                summary.append("您的面试表现及格，但距离理想状态还有一定差距。建议您认真阅读改进建议，并进行系统性的面试训练。")
            else:
                summary.append("您的面试表现需要显著改进。建议您系统学习面试技巧，并进行大量的模拟面试练习，逐步提升各方面的表现。")
        else:
            summary.append("感谢您使用我们的面试评估系统。希望我们的反馈对您有所帮助，祝您在未来的面试中取得好成绩！")
        
        # 合并所有内容
        return "\n".join(summary)
    
    def generate(self, state: GraphState) -> GraphState:
        logger.info(f"反馈生成节点开始，输入状态: {state}")
        try:
            # 确保有输出
            if not state.output:
                state.output = {"error": "No analysis results available"}
            
            # 生成反馈摘要
            feedback_summary = self._generate_feedback_summary(state.output)
            
            # 更新输出
            state.output["feedback_summary"] = feedback_summary
            
            # 添加到待发送反馈
            feedback_item = {
                "timestamp": datetime.now().isoformat(),
                "summary": feedback_summary,
                "details": state.output,
            }
            state.feedback_state.pending_feedback.append(feedback_item)
            
            # 设置下一个节点为None，表示工作流结束
            state.next_node = None
            
            logger.info(f"反馈生成完成，结果: {feedback_summary}")
            return state
        except Exception as e:
            logger.error(f"反馈生成异常: {e}")
            state.error = str(e)
            # 工作流结束
            state.next_node = None
        
        # 更新时间戳
        state.update_timestamp()
        
        return state