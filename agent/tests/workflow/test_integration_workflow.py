import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import json
import os
import uuid

from agent.workflow import InterviewAnalysisWorkflow
from agent.src.analyzers.speech.speech_analyzer import SpeechAnalyzer
from agent.src.analyzers.visual.visual_analyzer import VisualAnalyzer
from agent.src.analyzers.content.content_analyzer import ContentAnalyzer
from agent.src.services.content_filter_service import ContentFilterService
from agent.src.core.workflow import analyze_interview
from agent.tests.conftest import MockNotificationService


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
        audio_file.write_text("Mock audio data")
        
        # 创建测试视频文件
        video_file = test_data_dir / "test_video.mp4"
        video_file.write_text("Mock video data")
        
        # 创建测试文本文件
        text_file = test_data_dir / "test_transcript.txt"
        text_file.write_text("测试面试文本内容")
        
        return {
            "audio_file": str(audio_file),
            "video_file": str(video_file),
            "text_file": str(text_file),
            "text_content": "测试面试文本内容"
        }
    
    @patch.object(InterviewAnalysisWorkflow, "_analyze_speech")
    @patch.object(InterviewAnalysisWorkflow, "_analyze_visual")
    @patch.object(InterviewAnalysisWorkflow, "_analyze_content")
    def test_workflow_execution(self, mock_content_analyze, mock_visual_analyze, mock_speech_analyze, setup_test_data):
        """测试工作流执行"""
        # 配置模拟返回值
        mock_speech_analyze.return_value = {
            "speech_rate": {"score": 85, "feedback": "语速适中"},
            "fluency": {"score": 90, "feedback": "表达流畅"}
        }
        
        mock_visual_analyze.return_value = {
            "facial_expression": {"score": 80, "feedback": "表情自然"},
            "eye_contact": {"score": 75, "feedback": "目光接触良好"}
        }
        
        mock_content_analyze.return_value = {
            "relevance": {"score": 95, "feedback": "回答与问题高度相关"},
            "completeness": {"score": 85, "feedback": "回答比较全面"}
        }
        
        # 创建工作流
        workflow = InterviewAnalysisWorkflow(
            notification_service=MockNotificationService()
        )
        
        # 准备输入数据
        client_id = "test_user"
        interview_data = {
            "audio_file": setup_test_data["audio_file"],
            "video_file": setup_test_data["video_file"],
            "transcript": setup_test_data["text_content"],
            "job_position": {"title": "软件工程师"}
        }
        
        # 执行工作流（使用同步分析方法）
        result = asyncio.run(workflow._analyze_interview_sync(client_id, interview_data))
        
        # 验证结果
        assert result is not None
        assert "id" in result
        assert "speech_analysis" in result
        assert "visual_analysis" in result
        assert "content_analysis" in result
        
        # 验证分析器调用
        mock_speech_analyze.assert_called_once_with(interview_data["audio_file"])
        mock_visual_analyze.assert_called_once_with(interview_data["video_file"])
        mock_content_analyze.assert_called_once_with(
            interview_data["transcript"], 
            interview_data["job_position"]
        )
    
    @patch.object(InterviewAnalysisWorkflow, "_analyze_content")
    def test_text_only_workflow(self, mock_content_analyze, setup_test_data):
        """测试仅文本工作流"""
        # 配置模拟返回值
        mock_content_analyze.return_value = {
            "relevance": {"score": 90, "feedback": "回答与问题高度相关"},
            "completeness": {"score": 80, "feedback": "回答比较全面"}
        }
        
        # 创建工作流
        workflow = InterviewAnalysisWorkflow(
            notification_service=MockNotificationService()
        )
        
        # 准备输入数据（仅文本）
        client_id = "test_user"
        interview_data = {
            "audio_file": None,
            "video_file": None,
            "transcript": setup_test_data["text_content"],
            "job_position": {"title": "软件工程师"}
        }
        
        # 执行工作流（使用同步分析方法）
        result = asyncio.run(workflow._analyze_interview_sync(client_id, interview_data))
        
        # 验证结果
        assert result is not None
        assert "id" in result
        assert "content_analysis" in result
        
        # 验证仅调用了内容分析器
        mock_content_analyze.assert_called_once_with(
            interview_data["transcript"], 
            interview_data["job_position"]
        )
    
    def test_empty_input_handling(self):
        """测试空输入处理"""
        # 创建工作流
        workflow = InterviewAnalysisWorkflow(
            notification_service=MockNotificationService()
        )
        
        # 准备空输入数据
        input_data = {
            "interview_data": {
                "audio": None,
                "video": None,
                "text": ""
            },
            "user_id": "test_user",
            "session_id": "test_session"
        }
        
        # 执行工作流，期望出现错误信息
        result = workflow.execute(input_data)
        
        # 验证错误处理
        assert result is not None
        assert "error" in result

    @pytest.fixture
    def mock_notification_service(self):
        """创建模拟的通知服务"""
        notification_service = MagicMock(spec=MockNotificationService)
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
        with patch.object(ContentFilterService, "get_instance") as mock_filter_instance:
            
            # 配置模拟的内容过滤服务
            mock_filter = MagicMock()
            mock_filter.filter_text.return_value = MagicMock(
                filtered_text="这是过滤后的文本",
                has_sensitive_content=False,
                sensitive_word_count=0,
                sensitive_categories=[],
                highest_severity="low"
            )
            mock_filter_instance.return_value = mock_filter
            
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
                "transcript": test_data["text_content"],
                "job_position": {"title": "软件工程师", "requirements": ["编程能力", "沟通能力"]}
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
        # 分别模拟extract_features和analyze方法
        content_analyzer.extract_features = MagicMock(return_value={"text": test_data["text_content"]})
        content_analyzer.analyze = MagicMock(return_value={
            "relevance": {"score": 80, "feedback": "回答与问题相关"},
            "completeness": {"score": 85, "feedback": "回答全面"},
            "structure": {"score": 75, "feedback": "结构清晰"}
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
            "transcript": test_data["text_content"],
            "job_position": {"title": "软件工程师", "requirements": ["编程能力", "沟通能力"]}
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
        # 分别模拟extract_features和analyze方法
        content_analyzer.extract_features = MagicMock(return_value={"text": test_data["text_content"]})
        content_analyzer.analyze = MagicMock(return_value={
            "relevance": {"score": 80, "feedback": "回答与问题相关"},
            "completeness": {"score": 85, "feedback": "回答全面"},
            "structure": {"score": 75, "feedback": "结构清晰"}
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
            "transcript": test_data["text_content"],
            "job_position": {"title": "软件工程师", "requirements": ["编程能力", "沟通能力"]}
        }
        
        # 执行同步分析
        result = await workflow._analyze_interview_sync(client_id, interview_data)
        
        # 验证结果结构
        assert "id" in result  # 即使分析器异常，也应该有默认结果
        assert "speech_analysis" in result
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
        # 分别模拟extract_features和analyze方法
        content_analyzer.extract_features = MagicMock(return_value={"text": test_data["text_content"]})
        content_analyzer.analyze = MagicMock(return_value={
            "relevance": {"score": 80, "feedback": "回答与问题相关"},
            "completeness": {"score": 85, "feedback": "回答全面"},
            "structure": {"score": 75, "feedback": "结构清晰"}
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
            "transcript": test_data["text_content"],
            "job_position": {"title": "软件工程师", "requirements": ["编程能力", "沟通能力"]}
        }
        
        # 模拟UUID和analyze_interview
        with patch("uuid.uuid4", return_value="task_123"), \
             patch.object(workflow, "_analyze_interview_sync", AsyncMock(return_value={"id": "result_123"})):
            
            # 执行异步分析
            result = await workflow.analyze_interview(client_id, interview_data)
            
            # 验证结果
            assert "task_id" in result
            assert result["task_id"] == "task_123"
            
            # 验证通知服务是否被正确调用
            mock_notification_service.notify_interview_status.assert_called_once_with(
                client_id, "ANALYZING", "开始分析面试数据"
            )
            mock_notification_service.notify_task_status.assert_called_once_with(
                client_id, "task_123", "STARTED", {"message": "面试分析任务已启动"}
            ) 