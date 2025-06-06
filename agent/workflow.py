import asyncio
import logging
from typing import Dict, Any, List
from langchain.agents import AgentExecutor
from langchain_core.messages import HumanMessage
from langchain_experimental.utilities import PythonREPL
import langgraph
from .analyzers.speech_analyzer import SpeechAnalyzer
from .analyzers.visual_analyzer import VisualAnalyzer
from .analyzers.content_analyzer import ContentAnalyzer
from backend.app.services.notification_service import NotificationService
from backend.app.services.tasks.analysis_tasks import analyze_interview

# 配置日志
logger = logging.getLogger(__name__)

class InterviewAnalysisWorkflow:
    def __init__(self, 
                 notification_service: NotificationService,
                 speech_analyzer: SpeechAnalyzer = None,
                 visual_analyzer: VisualAnalyzer = None,
                 content_analyzer: ContentAnalyzer = None):
        """
        初始化面试分析工作流
        
        Args:
            notification_service: 通知服务
            speech_analyzer: 语音分析器（可选，用于直接分析）
            visual_analyzer: 视觉分析器（可选，用于直接分析）
            content_analyzer: 内容分析器（可选，用于直接分析）
        """
        self.notification_service = notification_service
        self.speech_analyzer = speech_analyzer
        self.visual_analyzer = visual_analyzer
        self.content_analyzer = content_analyzer
        logger.info("面试分析工作流初始化完成")
        
    async def analyze_interview(self, client_id: str, interview_data: Dict[str, Any]):
        """
        执行面试分析工作流，并发送实时进度反馈
        
        Args:
            client_id: 客户端ID
            interview_data: 面试数据
            
        Returns:
            任务ID
        """
        try:
            logger.info(f"开始面试分析工作流: client_id={client_id}")
            
            # 通知开始分析
            await self.notification_service.notify_interview_status(
                client_id, 
                "ANALYZING", 
                "开始分析面试数据"
            )
            
            # 检查是否使用异步任务处理
            use_async_tasks = True  # 可以通过配置控制
            
            if use_async_tasks:
                # 使用Celery任务链进行异步处理
                from backend.app.services.tasks.analysis_tasks import analyze_interview
                
                # 启动异步任务链
                task_id = analyze_interview.delay(client_id, interview_data)
                
                logger.info(f"已启动异步分析任务: client_id={client_id}, task_id={task_id}")
                
                # 通知任务已开始
                await self.notification_service.notify_task_status(
                    client_id,
                    str(task_id),
                    "STARTED",
                    {"message": "面试分析任务已启动"}
                )
                
                return {"task_id": str(task_id)}
                
            else:
                # 使用同步处理（旧方法，保留作为备份）
                return await self._analyze_interview_sync(client_id, interview_data)
            
        except Exception as e:
            # 通知错误
            logger.error(f"面试分析失败: {str(e)}", exc_info=True)
            await self.notification_service.notify_error(
                client_id,
                "ANALYSIS_ERROR",
                f"分析过程中出错: {str(e)}"
            )
            raise
    
    async def _analyze_interview_sync(self, client_id: str, interview_data: Dict[str, Any]):
        """
        同步执行面试分析工作流（旧方法，保留作为备份）
        
        Args:
            client_id: 客户端ID
            interview_data: 面试数据
            
        Returns:
            分析报告
        """
        logger.info(f"使用同步方式分析面试: client_id={client_id}")
        
        # 1. 语音分析 (25%)
        await self.notification_service.notify_analysis_progress(
            client_id, 25, "正在分析语音数据..."
        )
        speech_results = await self._analyze_speech(interview_data.get("audio_file"))
        
        # 发送部分反馈结果
        await self.notification_service.send_partial_feedback(
            client_id, 
            "speech", 
            speech_results
        )
        
        # 2. 视觉分析 (50%)
        await self.notification_service.notify_analysis_progress(
            client_id, 50, "正在分析视频数据..."
        )
        visual_results = await self._analyze_visual(interview_data.get("video_file"))
        
        # 发送部分反馈结果
        await self.notification_service.send_partial_feedback(
            client_id, 
            "visual", 
            visual_results
        )
        
        # 3. 内容分析 (75%)
        await self.notification_service.notify_analysis_progress(
            client_id, 75, "正在分析回答内容..."
        )
        content_results = await self._analyze_content(
            interview_data.get("transcript"),
            interview_data.get("job_position")
        )
        
        # 发送部分反馈结果
        await self.notification_service.send_partial_feedback(
            client_id, 
            "content", 
            content_results
        )
        
        # 4. 综合分析 (90%)
        await self.notification_service.notify_analysis_progress(
            client_id, 90, "正在生成综合分析报告..."
        )
        
        # 生成综合报告
        final_report = await self._generate_final_report(
            speech_results,
            visual_results,
            content_results,
            interview_data
        )
        
        # 完成分析 (100%)
        await self.notification_service.notify_analysis_progress(
            client_id, 100, "分析完成", 
            {"report_id": final_report["id"]}
        )
        
        # 通知面试分析完成
        await self.notification_service.notify_interview_status(
            client_id, 
            "COMPLETED", 
            "面试分析已完成"
        )
        
        logger.info(f"同步面试分析完成: client_id={client_id}, report_id={final_report['id']}")
        return final_report
    
    # 以下是实际的分析方法
    async def _analyze_speech(self, audio_file):
        """
        分析语音
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            语音分析结果
        """
        if not self.speech_analyzer:
            logger.warning("语音分析器未初始化，返回模拟结果")
            # 返回模拟结果
            return {
                "speech_rate": {"score": 80, "feedback": "语速适中"},
                "fluency": {"score": 85, "feedback": "表达流畅"}
            }
            
        # 实际的语音分析逻辑
        logger.info(f"开始分析语音: audio_file={audio_file}")
        return await self.speech_analyzer.analyze(audio_file)
    
    async def _analyze_visual(self, video_file):
        """
        分析视频
        
        Args:
            video_file: 视频文件路径
            
        Returns:
            视觉分析结果
        """
        if not self.visual_analyzer:
            logger.warning("视觉分析器未初始化，返回模拟结果")
            # 返回模拟结果
            return {
                "facial_expression": {"score": 80, "feedback": "表情自然"},
                "eye_contact": {"score": 85, "feedback": "目光接触良好"}
            }
            
        # 实际的视觉分析逻辑
        logger.info(f"开始分析视频: video_file={video_file}")
        return await self.visual_analyzer.analyze(video_file)
    
    async def _analyze_content(self, transcript, job_position):
        """
        分析内容
        
        Args:
            transcript: 文本内容
            job_position: 职位信息
            
        Returns:
            内容分析结果
        """
        if not self.content_analyzer:
            logger.warning("内容分析器未初始化，返回模拟结果")
            # 返回模拟结果
            return {
                "relevance": {"score": 80, "feedback": "回答与问题相关"},
                "completeness": {"score": 85, "feedback": "回答全面"}
            }
            
        # 实际的内容分析逻辑
        logger.info(f"开始分析内容: transcript_length={len(transcript) if transcript else 0}")
        return await self.content_analyzer.analyze(transcript, job_position)
    
    async def _generate_final_report(self, speech_results, visual_results, content_results, interview_data):
        """
        生成最终报告
        
        Args:
            speech_results: 语音分析结果
            visual_results: 视觉分析结果
            content_results: 内容分析结果
            interview_data: 面试数据
            
        Returns:
            最终报告
        """
        # 生成最终综合报告的逻辑
        import uuid
        report_id = f"report-{uuid.uuid4().hex[:8]}"
        
        logger.info(f"生成最终报告: report_id={report_id}")
        
        return {
            "id": report_id,
            "speech": speech_results,
            "visual": visual_results,
            "content": content_results,
            "overall_score": 85,
            # 其他综合评价...
        }