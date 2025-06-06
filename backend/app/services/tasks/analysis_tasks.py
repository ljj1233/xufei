"""
音视频分析任务

定义用于音视频分析的Celery异步任务
"""

import os
import time
import logging
import asyncio
from typing import Dict, Any, List, Optional
from celery import shared_task, chain, group
import json

from app.celery_app import BaseTask, celery_app
from app.services.websocket_manager import ConnectionManager
from app.services.notification_service import NotificationService

# 导入分析器
# 注意：这里使用相对导入可能需要根据实际项目结构调整
from agent.analyzers.speech_analyzer import SpeechAnalyzer
from agent.analyzers.visual_analyzer import VisualAnalyzer
from agent.analyzers.content_analyzer import ContentAnalyzer

# 配置日志
logger = logging.getLogger(__name__)

# 创建连接管理器和通知服务的单例实例
connection_manager = ConnectionManager()
notification_service = NotificationService(connection_manager)

# 创建分析器实例
speech_analyzer = SpeechAnalyzer()
# visual_analyzer = VisualAnalyzer()  # 假设存在这个类
content_analyzer = ContentAnalyzer()

# 辅助函数：运行异步函数
def run_async(coro):
    """运行异步协程并返回结果"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# 辅助函数：发送进度通知
def send_progress_notification(client_id: str, progress: float, status: str, details: Optional[Dict[str, Any]] = None):
    """发送进度通知"""
    run_async(notification_service.notify_analysis_progress(
        client_id, progress, status, details
    ))
    logger.info(f"已发送进度通知: client_id={client_id}, progress={progress}, status={status}")

# 辅助函数：发送部分反馈
def send_partial_feedback(client_id: str, feedback_type: str, feedback_content: Dict[str, Any]):
    """发送部分分析结果"""
    run_async(notification_service.send_partial_feedback(
        client_id, feedback_type, feedback_content
    ))
    logger.info(f"已发送部分反馈: client_id={client_id}, type={feedback_type}")

# 辅助函数：通知状态变化
def notify_status(client_id: str, status: str, message: str):
    """通知状态变化"""
    run_async(notification_service.notify_interview_status(
        client_id, status, message
    ))
    logger.info(f"已通知状态变化: client_id={client_id}, status={status}, message={message}")

# 辅助函数：通知错误
def notify_error(client_id: str, error_code: str, error_message: str):
    """通知错误"""
    run_async(notification_service.notify_error(
        client_id, error_code, error_message
    ))
    logger.error(f"已通知错误: client_id={client_id}, code={error_code}, message={error_message}")

# 快速语音分析任务
@shared_task(bind=True, base=BaseTask, name="app.services.tasks.analysis_tasks.quick_analysis_speech")
def quick_analysis_speech(self, client_id: str, audio_file: str, task_id: str = None):
    """
    快速语音分析任务
    
    Args:
        client_id: 客户端ID
        audio_file: 音频文件路径
        task_id: 任务ID（可选）
        
    Returns:
        初步分析结果
    """
    logger.info(f"开始快速语音分析: client_id={client_id}, audio_file={audio_file}")
    
    try:
        # 通知开始快速分析
        send_progress_notification(client_id, 10, "正在进行快速语音分析...")
        
        # 执行快速语音识别（只处理前30秒）
        # 这里简化处理，实际应该截取音频的前一部分
        speech_text = run_async(speech_analyzer._recognize_speech(audio_file))
        
        # 通知语音识别完成
        send_progress_notification(client_id, 15, "语音识别完成，正在分析语音特征...")
        
        # 执行快速语音特征分析
        # 这里简化处理，实际应该只分析基本特征
        basic_features = {
            "speech_rate": {
                "score": 85,
                "feedback": "语速适中，表达清晰"
            },
            "volume": {
                "score": 90,
                "feedback": "音量适中"
            }
        }
        
        # 构建初步结果
        quick_result = {
            "speech_text": speech_text,
            "basic_features": basic_features,
            "analysis_type": "quick",
            "is_complete": False
        }
        
        # 通知快速分析完成
        send_progress_notification(client_id, 20, "快速语音分析完成")
        send_partial_feedback(client_id, "speech_quick", quick_result)
        
        logger.info(f"快速语音分析完成: client_id={client_id}")
        return quick_result
        
    except Exception as e:
        logger.error(f"快速语音分析失败: {str(e)}", exc_info=True)
        notify_error(client_id, "QUICK_SPEECH_ANALYSIS_ERROR", f"快速语音分析失败: {str(e)}")
        raise

# 详细语音分析任务
@shared_task(bind=True, base=BaseTask, name="app.services.tasks.analysis_tasks.detailed_analysis_speech")
def detailed_analysis_speech(self, client_id: str, audio_file: str, quick_result: Dict[str, Any] = None, task_id: str = None):
    """
    详细语音分析任务
    
    Args:
        client_id: 客户端ID
        audio_file: 音频文件路径
        quick_result: 快速分析结果（可选）
        task_id: 任务ID（可选）
        
    Returns:
        完整分析结果
    """
    logger.info(f"开始详细语音分析: client_id={client_id}, audio_file={audio_file}")
    
    try:
        # 通知开始详细分析
        send_progress_notification(client_id, 22, "正在进行详细语音分析...")
        
        # 执行完整的语音分析
        full_result = run_async(speech_analyzer.analyze(audio_file))
        
        # 如果有快速分析结果，合并结果
        if quick_result:
            # 保留快速分析中可能更准确的某些字段
            # 这里是示例，实际合并逻辑可能更复杂
            pass
        
        # 标记为完整分析
        full_result["analysis_type"] = "detailed"
        full_result["is_complete"] = True
        
        # 通知详细分析完成
        send_progress_notification(client_id, 25, "详细语音分析完成")
        send_partial_feedback(client_id, "speech", full_result)
        
        logger.info(f"详细语音分析完成: client_id={client_id}")
        return full_result
        
    except Exception as e:
        logger.error(f"详细语音分析失败: {str(e)}", exc_info=True)
        notify_error(client_id, "DETAILED_SPEECH_ANALYSIS_ERROR", f"详细语音分析失败: {str(e)}")
        raise

# 快速视觉分析任务
@shared_task(bind=True, base=BaseTask, name="app.services.tasks.analysis_tasks.quick_analysis_visual")
def quick_analysis_visual(self, client_id: str, video_file: str, task_id: str = None):
    """
    快速视觉分析任务
    
    Args:
        client_id: 客户端ID
        video_file: 视频文件路径
        task_id: 任务ID（可选）
        
    Returns:
        初步分析结果
    """
    logger.info(f"开始快速视觉分析: client_id={client_id}, video_file={video_file}")
    
    try:
        # 通知开始快速分析
        send_progress_notification(client_id, 30, "正在进行快速视觉分析...")
        
        # 这里应该是实际的视觉分析逻辑
        # 由于我们没有VisualAnalyzer的实现，这里模拟一个结果
        time.sleep(1)  # 模拟处理时间
        
        # 构建初步结果
        quick_result = {
            "facial_expression": {
                "score": 80,
                "feedback": "表情自然，展现自信"
            },
            "eye_contact": {
                "score": 85,
                "feedback": "保持良好的目光接触"
            },
            "analysis_type": "quick",
            "is_complete": False
        }
        
        # 通知快速分析完成
        send_progress_notification(client_id, 40, "快速视觉分析完成")
        send_partial_feedback(client_id, "visual_quick", quick_result)
        
        logger.info(f"快速视觉分析完成: client_id={client_id}")
        return quick_result
        
    except Exception as e:
        logger.error(f"快速视觉分析失败: {str(e)}", exc_info=True)
        notify_error(client_id, "QUICK_VISUAL_ANALYSIS_ERROR", f"快速视觉分析失败: {str(e)}")
        raise

# 详细视觉分析任务
@shared_task(bind=True, base=BaseTask, name="app.services.tasks.analysis_tasks.detailed_analysis_visual")
def detailed_analysis_visual(self, client_id: str, video_file: str, quick_result: Dict[str, Any] = None, task_id: str = None):
    """
    详细视觉分析任务
    
    Args:
        client_id: 客户端ID
        video_file: 视频文件路径
        quick_result: 快速分析结果（可选）
        task_id: 任务ID（可选）
        
    Returns:
        完整分析结果
    """
    logger.info(f"开始详细视觉分析: client_id={client_id}, video_file={video_file}")
    
    try:
        # 通知开始详细分析
        send_progress_notification(client_id, 45, "正在进行详细视觉分析...")
        
        # 这里应该是实际的视觉分析逻辑
        # 由于我们没有VisualAnalyzer的实现，这里模拟一个结果
        time.sleep(2)  # 模拟处理时间
        
        # 构建详细结果
        detailed_result = {
            "facial_expression": {
                "score": 82,
                "feedback": "表情自然，展现自信，情绪稳定"
            },
            "eye_contact": {
                "score": 85,
                "feedback": "保持良好的目光接触"
            },
            "body_language": {
                "score": 78,
                "feedback": "肢体语言适当，姿态专业"
            },
            "gestures": {
                "score": 75,
                "feedback": "手势使用恰当，增强表达效果"
            },
            "analysis_type": "detailed",
            "is_complete": True
        }
        
        # 通知详细分析完成
        send_progress_notification(client_id, 50, "详细视觉分析完成")
        send_partial_feedback(client_id, "visual", detailed_result)
        
        logger.info(f"详细视觉分析完成: client_id={client_id}")
        return detailed_result
        
    except Exception as e:
        logger.error(f"详细视觉分析失败: {str(e)}", exc_info=True)
        notify_error(client_id, "DETAILED_VISUAL_ANALYSIS_ERROR", f"详细视觉分析失败: {str(e)}")
        raise

# 内容分析任务
@shared_task(bind=True, base=BaseTask, name="app.services.tasks.analysis_tasks.analyze_content")
def analyze_content(self, client_id: str, transcript: str, job_position: Dict[str, Any], task_id: str = None):
    """
    内容分析任务
    
    Args:
        client_id: 客户端ID
        transcript: 文本内容
        job_position: 职位信息
        task_id: 任务ID（可选）
        
    Returns:
        分析结果
    """
    logger.info(f"开始内容分析: client_id={client_id}, transcript_length={len(transcript) if transcript else 0}")
    
    try:
        # 通知开始内容分析
        send_progress_notification(client_id, 60, "正在分析回答内容...")
        
        # 执行内容分析，每10%发送一次进度更新
        for i in range(7, 10):
            time.sleep(0.5)  # 模拟处理时间
            send_progress_notification(client_id, i * 10, f"内容分析进度: {i * 10}%")
        
        # 执行实际的内容分析
        content_result = run_async(content_analyzer.analyze(transcript, job_position))
        
        # 通知内容分析完成
        send_progress_notification(client_id, 90, "内容分析完成")
        send_partial_feedback(client_id, "content", content_result)
        
        logger.info(f"内容分析完成: client_id={client_id}")
        return content_result
        
    except Exception as e:
        logger.error(f"内容分析失败: {str(e)}", exc_info=True)
        notify_error(client_id, "CONTENT_ANALYSIS_ERROR", f"内容分析失败: {str(e)}")
        raise

# 生成最终报告任务
@shared_task(bind=True, base=BaseTask, name="app.services.tasks.analysis_tasks.generate_final_report")
def generate_final_report(self, client_id: str, speech_results: Dict[str, Any], visual_results: Dict[str, Any], 
                         content_results: Dict[str, Any], interview_data: Dict[str, Any], task_id: str = None):
    """
    生成最终报告任务
    
    Args:
        client_id: 客户端ID
        speech_results: 语音分析结果
        visual_results: 视觉分析结果
        content_results: 内容分析结果
        interview_data: 面试数据
        task_id: 任务ID（可选）
        
    Returns:
        最终报告
    """
    logger.info(f"开始生成最终报告: client_id={client_id}")
    
    try:
        # 通知开始生成报告
        send_progress_notification(client_id, 95, "正在生成综合分析报告...")
        
        # 生成报告ID
        import uuid
        report_id = f"report-{uuid.uuid4().hex[:8]}"
        
        # 构建最终报告
        final_report = {
            "id": report_id,
            "speech": speech_results,
            "visual": visual_results,
            "content": content_results,
            "overall_score": calculate_overall_score(speech_results, visual_results, content_results),
            "summary": generate_summary(speech_results, visual_results, content_results),
            "improvement_suggestions": generate_suggestions(speech_results, visual_results, content_results),
            "timestamp": time.time()
        }
        
        # 通知报告生成完成
        send_progress_notification(client_id, 100, "分析完成", {"report_id": report_id})
        notify_status(client_id, "COMPLETED", "面试分析已完成")
        
        logger.info(f"最终报告生成完成: client_id={client_id}, report_id={report_id}")
        return final_report
        
    except Exception as e:
        logger.error(f"生成最终报告失败: {str(e)}", exc_info=True)
        notify_error(client_id, "REPORT_GENERATION_ERROR", f"生成最终报告失败: {str(e)}")
        raise

# 计算总体评分
def calculate_overall_score(speech_results, visual_results, content_results):
    """计算总体评分"""
    # 这里是简化的评分计算逻辑，实际应该更复杂
    speech_score = speech_results.get("speech_rate", {}).get("score", 0) if isinstance(speech_results.get("speech_rate"), dict) else 0
    visual_score = visual_results.get("facial_expression", {}).get("score", 0) if isinstance(visual_results.get("facial_expression"), dict) else 0
    content_score = content_results.get("relevance", {}).get("score", 0) if isinstance(content_results.get("relevance"), dict) else 0
    
    # 加权平均
    overall_score = (speech_score * 0.3 + visual_score * 0.3 + content_score * 0.4)
    return round(overall_score)

# 生成总结
def generate_summary(speech_results, visual_results, content_results):
    """生成总结"""
    # 这里是简化的总结生成逻辑，实际应该更复杂
    return "这是一份自动生成的面试分析总结。根据分析，您在语音表达、视觉表现和内容回答方面表现良好。"

# 生成改进建议
def generate_suggestions(speech_results, visual_results, content_results):
    """生成改进建议"""
    # 这里是简化的建议生成逻辑，实际应该更复杂
    suggestions = []
    
    # 语音建议
    if speech_results.get("speech_rate", {}).get("score", 100) < 70:
        suggestions.append("可以适当调整语速，保持清晰表达")
    
    # 视觉建议
    if visual_results.get("eye_contact", {}).get("score", 100) < 70:
        suggestions.append("增加目光接触，展示自信")
    
    # 内容建议
    if content_results.get("relevance", {}).get("score", 100) < 70:
        suggestions.append("回答内容可以更加贴合问题要点")
    
    return suggestions if suggestions else ["您的表现已经很好，继续保持!"]

# 完整的面试分析任务链
@shared_task(bind=True, name="app.services.tasks.analysis_tasks.analyze_interview")
def analyze_interview(self, client_id: str, interview_data: Dict[str, Any]):
    """
    完整的面试分析任务链
    
    Args:
        client_id: 客户端ID
        interview_data: 面试数据
        
    Returns:
        任务链ID
    """
    logger.info(f"开始面试分析任务链: client_id={client_id}")
    
    try:
        # 通知开始分析
        notify_status(client_id, "ANALYZING", "开始分析面试数据")
        
        # 获取文件路径
        audio_file = interview_data.get("audio_file")
        video_file = interview_data.get("video_file")
        transcript = interview_data.get("transcript")
        job_position = interview_data.get("job_position", {})
        
        # 验证必要的输入
        if not audio_file and not video_file and not transcript:
            raise ValueError("至少需要提供音频、视频或文本内容之一")
        
        # 创建任务链
        # 1. 快速语音分析 -> 详细语音分析
        speech_chain = chain(
            quick_analysis_speech.s(client_id, audio_file),
            detailed_analysis_speech.s(client_id, audio_file)
        )
        
        # 2. 快速视觉分析 -> 详细视觉分析
        visual_chain = chain(
            quick_analysis_visual.s(client_id, video_file),
            detailed_analysis_visual.s(client_id, video_file)
        )
        
        # 3. 内容分析
        content_task = analyze_content.s(client_id, transcript, job_position)
        
        # 并行执行语音、视觉和内容分析
        analysis_group = group(speech_chain, visual_chain, content_task)
        
        # 4. 收集结果并生成最终报告
        workflow = (
            analysis_group |
            generate_final_report.s(client_id, interview_data)
        )
        
        # 启动任务链
        result = workflow.apply_async()
        
        logger.info(f"面试分析任务链已启动: client_id={client_id}, task_id={result.id}")
        return result.id
        
    except Exception as e:
        logger.error(f"启动面试分析任务链失败: {str(e)}", exc_info=True)
        notify_error(client_id, "ANALYSIS_CHAIN_ERROR", f"启动面试分析失败: {str(e)}")
        raise 