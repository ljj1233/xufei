import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import json
import os

from agent.workflow import InterviewAnalysisWorkflow
from agent.analyzers.speech_analyzer import SpeechAnalyzer
from agent.analyzers.visual_analyzer import VisualAnalyzer
from agent.analyzers.content_analyzer import ContentAnalyzer
from backend.app.services.notification_service import NotificationService


class TestIntegrationWorkflow:
    """工作流与分析器集成测试"""
    
    @pytest.fixture
    def setup_test_data(self, tmp_path):
        """设置测试数据"""
        # 创建测试数据目录
        test_data_dir = tmp_path / "test_data"
        test_data_dir.mkdir()
        
        # 创建测试音频文件
        audio_file = test_data_dir / "test_audio.wav"
        audio_file.write_bytes(b"mock audio data")
        
        # 创建测试视频文件
        video_file = test_data_dir / "test_video.mp4"
        video_file.write_bytes(b"mock video data")
        
        # 创建测试文本文件
        transcript_file = test_data_dir / "test_transcript.txt"
        transcript_file.write_text("这是一段面试回答的文本内容，用于测试内容分析器。")
        
        # 返回测试数据
        return {
            "audio_file": str(audio_file),
            "video_file": str(video_file),
            "transcript_file": str(transcript_file),
            "transcript": transcript_file.read_text(),
            "job_position": {"title": "软件工程师", "requirements": ["编程能力", "沟通能力"]}
        }
    
    @pytest.fixture
    def mock_notification_service(self):
        """创建模拟的通知服务"""
        notification_service = MagicMock(spec=NotificationService)
        notification_service.notify_interview_status = AsyncMock()
        notification_service.notify_analysis_progress = AsyncMock()
        notification_service.send_partial_feedback = AsyncMock()
        notification_service.notify_task_status = AsyncMock()
        notification_service.notify_error = AsyncMock()
        return notification_service
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self, setup_test_data, mock_notification_service):
        """测试完整工作流集成"""
        # 准备测试数据
        test_data = setup_test_data
        client_id = "test_client_123"
        
        # 创建真实的分析器实例
        with patch("agent.analyzers.speech_analyzer.ContentFilterService") as mock_speech_filter, \
             patch("agent.analyzers.content_analyzer.ContentFilterService") as mock_content_filter:
            
            # 配置模拟的内容过滤服务
            mock_filter = MagicMock()
            mock_filter.filter_text.return_value = MagicMock(
                filtered_text="这是过滤后的文本",
                has_sensitive_content=False,
                sensitive_word_count=0,
                sensitive_categories=[],
                highest_severity="low"
            )
            mock_speech_filter.get_instance.return_value = mock_filter
            mock_content_filter.get_instance.return_value = mock_filter
            
            # 创建真实的分析器
            speech_analyzer = SpeechAnalyzer()
            content_analyzer = ContentAnalyzer()
            
            # 创建模拟的视觉分析器
            visual_analyzer = MagicMock(spec=VisualAnalyzer)
            visual_analyzer.analyze = AsyncMock(return_value={
                "facial_expression": {"score": 80, "feedback": "表情自然"},
                "eye_contact": {"score": 85, "feedback": "目光接触良好"}
            })
            
            # 创建工作流实例
            workflow = InterviewAnalysisWorkflow(
                notification_service=mock_notification_service,
                speech_analyzer=speech_analyzer,
                visual_analyzer=visual_analyzer,
                content_analyzer=content_analyzer
            )
            
            # 准备面试数据
            interview_data = {
                "audio_file": test_data["audio_file"],
                "video_file": test_data["video_file"],
                "transcript": test_data["transcript"],
                "job_position": test_data["job_position"]
            }
            
            # 执行同步分析
            result = await workflow._analyze_interview_sync(client_id, interview_data)
            
            # 验证结果结构
            assert "id" in result
            assert "speech_analysis" in result
            assert "visual_analysis" in result
            assert "content_analysis" in result
            
            # 验证通知服务调用
            assert mock_notification_service.notify_interview_status.call_count >= 1
            assert mock_notification_service.notify_analysis_progress.call_count >= 3
            assert mock_notification_service.send_partial_feedback.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_workflow_with_missing_files(self, setup_test_data, mock_notification_service):
        """测试缺少文件时的工作流"""
        # 准备测试数据
        test_data = setup_test_data
        client_id = "test_client_123"
        
        # 删除音频文件
        os.remove(test_data["audio_file"])
        
        # 创建模拟的分析器
        speech_analyzer = MagicMock(spec=SpeechAnalyzer)
        speech_analyzer.analyze = AsyncMock(return_value={
            "speech_rate": {"score": 80, "feedback": "语速适中"},
            "fluency": {"score": 85, "feedback": "表达流畅"}
        })
        
        visual_analyzer = MagicMock(spec=VisualAnalyzer)
        visual_analyzer.analyze = AsyncMock(return_value={
            "facial_expression": {"score": 80, "feedback": "表情自然"},
            "eye_contact": {"score": 85, "feedback": "目光接触良好"}
        })
        
        content_analyzer = MagicMock(spec=ContentAnalyzer)
        content_analyzer.analyze = AsyncMock(return_value={
            "relevance": {"score": 80, "feedback": "回答与问题相关"},
            "completeness": {"score": 85, "feedback": "回答全面"}
        })
        
        # 创建工作流实例
        workflow = InterviewAnalysisWorkflow(
            notification_service=mock_notification_service,
            speech_analyzer=speech_analyzer,
            visual_analyzer=visual_analyzer,
            content_analyzer=content_analyzer
        )
        
        # 准备面试数据
        interview_data = {
            "audio_file": test_data["audio_file"],  # 不存在的文件
            "video_file": test_data["video_file"],
            "transcript": test_data["transcript"],
            "job_position": test_data["job_position"]
        }
        
        # 执行同步分析
        result = await workflow._analyze_interview_sync(client_id, interview_data)
        
        # 验证结果结构
        assert "id" in result
        assert "speech_analysis" in result
        assert "visual_analysis" in result
        assert "content_analysis" in result
        
        # 验证语音分析器调用
        speech_analyzer.analyze.assert_called_once_with(test_data["audio_file"])
    
    @pytest.mark.asyncio
    async def test_workflow_with_analyzer_exception(self, setup_test_data, mock_notification_service):
        """测试分析器异常时的工作流"""
        # 准备测试数据
        test_data = setup_test_data
        client_id = "test_client_123"
        
        # 创建模拟的分析器
        speech_analyzer = MagicMock(spec=SpeechAnalyzer)
        speech_analyzer.analyze = AsyncMock(side_effect=Exception("语音分析器异常"))
        
        visual_analyzer = MagicMock(spec=VisualAnalyzer)
        visual_analyzer.analyze = AsyncMock(return_value={
            "facial_expression": {"score": 80, "feedback": "表情自然"},
            "eye_contact": {"score": 85, "feedback": "目光接触良好"}
        })
        
        content_analyzer = MagicMock(spec=ContentAnalyzer)
        content_analyzer.analyze = AsyncMock(return_value={
            "relevance": {"score": 80, "feedback": "回答与问题相关"},
            "completeness": {"score": 85, "feedback": "回答全面"}
        })
        
        # 创建工作流实例
        workflow = InterviewAnalysisWorkflow(
            notification_service=mock_notification_service,
            speech_analyzer=speech_analyzer,
            visual_analyzer=visual_analyzer,
            content_analyzer=content_analyzer
        )
        
        # 准备面试数据
        interview_data = {
            "audio_file": test_data["audio_file"],
            "video_file": test_data["video_file"],
            "transcript": test_data["transcript"],
            "job_position": test_data["job_position"]
        }
        
        # 执行同步分析
        result = await workflow._analyze_interview_sync(client_id, interview_data)
        
        # 验证结果结构
        assert "id" in result
        assert "speech_analysis" in result  # 即使分析器异常，也应该有默认结果
        assert "visual_analysis" in result
        assert "content_analysis" in result
        
        # 验证语音分析器调用
        speech_analyzer.analyze.assert_called_once_with(test_data["audio_file"])
        
        # 验证通知服务调用（应该有错误通知）
        # 注意：这里不会调用notify_error，因为异常被工作流内部处理了
        assert mock_notification_service.notify_analysis_progress.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, setup_test_data, mock_notification_service):
        """测试端到端工作流"""
        # 准备测试数据
        test_data = setup_test_data
        client_id = "test_client_123"
        
        # 创建模拟的分析器
        speech_analyzer = MagicMock(spec=SpeechAnalyzer)
        speech_analyzer.analyze = AsyncMock(return_value={
            "speech_rate": {"score": 80, "feedback": "语速适中"},
            "fluency": {"score": 85, "feedback": "表达流畅"}
        })
        
        visual_analyzer = MagicMock(spec=VisualAnalyzer)
        visual_analyzer.analyze = AsyncMock(return_value={
            "facial_expression": {"score": 80, "feedback": "表情自然"},
            "eye_contact": {"score": 85, "feedback": "目光接触良好"}
        })
        
        content_analyzer = MagicMock(spec=ContentAnalyzer)
        content_analyzer.analyze = AsyncMock(return_value={
            "relevance": {"score": 80, "feedback": "回答与问题相关"},
            "completeness": {"score": 85, "feedback": "回答全面"}
        })
        
        # 模拟Celery任务
        with patch("agent.workflow.analyze_interview") as mock_analyze_task:
            mock_task = MagicMock()
            mock_task.id = "task_123"
            mock_analyze_task.delay.return_value = mock_task
            
            # 创建工作流实例
            workflow = InterviewAnalysisWorkflow(
                notification_service=mock_notification_service,
                speech_analyzer=speech_analyzer,
                visual_analyzer=visual_analyzer,
                content_analyzer=content_analyzer
            )
            
            # 准备面试数据
            interview_data = {
                "audio_file": test_data["audio_file"],
                "video_file": test_data["video_file"],
                "transcript": test_data["transcript"],
                "job_position": test_data["job_position"]
            }
            
            # 执行异步分析
            result = await workflow.analyze_interview(client_id, interview_data)
            
            # 验证结果
            assert "task_id" in result
            assert result["task_id"] == "task_123"
            
            # 验证Celery任务是否被调用
            mock_analyze_task.delay.assert_called_once_with(client_id, interview_data)
            
            # 验证通知服务是否被正确调用
            mock_notification_service.notify_interview_status.assert_called_once_with(
                client_id, "ANALYZING", "开始分析面试数据"
            )
            mock_notification_service.notify_task_status.assert_called_once_with(
                client_id, "task_123", "STARTED", {"message": "面试分析任务已启动"}
            ) 