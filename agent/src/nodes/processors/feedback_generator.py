# agent/core/nodes/feedback_generator.py

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
        
        # 获取内容和语音分析结果
        content_analysis = output.get("content_analysis", {})
        speech_analysis = output.get("speech_analysis", {})
        
        # 生成摘要
        summary = []
        
        # 添加标题
        summary.append("# 面试表现综合诊断报告")
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
            summary.append(f"**面试总分：{score_percent}/100**")
            summary.append("")
        
        # 添加模块评分
        # 内容质量模块
        content_quality_score = content_analysis.get("content_quality_score", 0) * 100
        summary.append(f"- **内容质量模块：{int(content_quality_score)}/100**")
        
        # 思维能力模块
        cognitive_skills_score = content_analysis.get("cognitive_skills_score", 0) * 100
        summary.append(f"- **思维能力模块：{int(cognitive_skills_score)}/100**")
        
        # 沟通技巧模块
        if speech_analysis:
            speech_score = speech_analysis.get("overall_score", 0) * 100
            summary.append(f"- **沟通技巧模块：{int(speech_score)}/100**")
        
        summary.append("")
        summary.append("---")
        
        # 添加亮点
        summary.append("#### **亮点时刻 (Strengths)**")
        summary.append("")
        
        # 从内容分析中提取亮点
        if content_analysis:
            # 相关性亮点
            relevance = content_analysis.get("relevance", 0)
            if relevance > 7.5:
                summary.append(f"* **亮点1**: 回答的相关性极高，你的回答紧扣问题核心，展现了良好的理解能力。")
            
            # 逻辑结构亮点
            logical_structure = content_analysis.get("logical_structure", 0)
            if logical_structure > 7.5:
                summary.append(f"* **亮点2**: 你的回答结构清晰，逻辑性强，让面试官能够轻松跟随你的思路。")
        
        # 从语音分析中提取亮点
        if speech_analysis:
            # 声音能量亮点
            vocal_energy = speech_analysis.get("vocal_energy", 0)
            if vocal_energy > 7.5:
                summary.append(f"* **亮点3**: 你的声音能量很足，音调富有变化，听起来充满自信和热情，给面试官留下了非常好的第一印象。")
        
        summary.append("")
        summary.append("---")
        
        # 添加改进建议
        summary.append("#### **优先成长区 (Areas for Growth)**")
        summary.append("")
        
        # 从内容分析中提取建议
        if content_analysis:
            # 细节与深度建议
            depth_and_detail = content_analysis.get("depth_and_detail", 0)
            if depth_and_detail < 7.0:
                summary.append(f"* **建议1 (最重要)**: **提升回答的细节与深度。**")
                summary.append(f"    * **现状诊断**: 我注意到你的回答虽然逻辑清晰，但在描述项目时缺少具体的数据和成果来支撑。")
                summary.append(f"    * **行动建议**: 尝试使用STAR法则来重构你的回答。在描述\"Action\"后，一定要用具体的数字来量化你的\"Result\"，例如\"我将处理时间从2小时缩短到了15分钟，效率提升了8倍\"。")
                summary.append("")
        
        # 从语音分析中提取建议
        if speech_analysis:
            # 流畅度建议
            fluency = speech_analysis.get("fluency", 0)
            fluency_details = speech_analysis.get("fluency_details", {})
            filler_words_count = fluency_details.get("filler_words_count", 0)
            
            if fluency < 7.0:
                summary.append(f"* **建议2**: **优化语言的流畅度。**")
                summary.append(f"    * **现状诊断**: 本次回答中，我们监测到{filler_words_count}次\"嗯...\"这样的填充词，这可能会削弱你表达的专业性。")
                summary.append(f"    * **行动建议**: 这是非常正常的现象！下次练习时，当你感觉要卡顿时，试着用一个短暂的、有意的停顿来代替填充词。这会让你听起来更从容、更有掌控力。")
                summary.append("")
            
            # 语速建议
            pace = speech_analysis.get("pace", 0)
            pace_details = speech_analysis.get("pace_details", {})
            pace_category = pace_details.get("pace_category", "")
            
            if pace < 7.0 and pace_category:
                summary.append(f"* **建议3**: **调整语速。**")
                summary.append(f"    * **现状诊断**: 你的语速偏{pace_category}，可能会影响信息的有效传递。")
                if pace_category == "过快":
                    summary.append(f"    * **行动建议**: 尝试在关键点前后有意识地放慢语速，给听者留出思考的空间。练习时可以在重要内容前暂停一下，然后再继续。")
                else:
                    summary.append(f"    * **行动建议**: 适当提高语速可以让你的表达更加有力。练习时可以尝试朗读文章，逐渐提高速度但保持清晰度。")
        
        # 添加结束语
        summary.append("---")
        summary.append("")
        if comprehensive_score is not None:
            if comprehensive_score >= 0.9:
                summary.append("你的面试表现非常出色！继续保持这种水平，相信你会在求职过程中取得优异的成绩。")
            elif comprehensive_score >= 0.8:
                summary.append("你的面试表现良好，在大多数方面都展现出了不错的能力。针对需要改进的地方进行有针对性的练习，你的表现会更加出色。")
            elif comprehensive_score >= 0.7:
                summary.append("你的面试表现中等，有一些亮点，但也有明显需要改进的地方。建议你重点关注改进建议，进行有针对性的练习。")
            elif comprehensive_score >= 0.6:
                summary.append("你的面试表现及格，但距离理想状态还有一定差距。建议你认真阅读改进建议，并进行系统性的面试训练。")
            else:
                summary.append("你的面试表现需要显著改进。建议你系统学习面试技巧，并进行大量的模拟面试练习，逐步提升各方面的表现。")
        else:
            summary.append("感谢你使用我们的面试评估系统。希望我们的反馈对你有所帮助，祝你在未来的面试中取得好成绩！")
        
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