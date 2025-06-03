# -*- coding: utf-8 -*-
"""
分析器适配器测试

测试分析器适配器的功能和集成效果
"""

import unittest
import os
import tempfile
import numpy as np
from unittest.mock import Mock, patch

from agent.core.analyzer_adapter import (
    AnalyzerFactory,
    SpeechAnalyzerAdapter,
    VisualAnalyzerAdapter,
    ContentAnalyzerAdapter
)
from agent.core.state import GraphState, TaskType, AnalysisResult


class TestAnalyzerFactory(unittest.TestCase):
    """测试分析器工厂类"""
    
    def test_get_supported_types(self):
        """测试获取支持的分析器类型"""
        supported_types = AnalyzerFactory.get_supported_types()
        expected_types = ["speech", "visual", "content"]
        
        self.assertEqual(set(supported_types), set(expected_types))
    
    def test_create_speech_adapter(self):
        """测试创建语音分析器适配器"""
        adapter = AnalyzerFactory.create_adapter("speech")
        self.assertIsInstance(adapter, SpeechAnalyzerAdapter)
    
    def test_create_visual_adapter(self):
        """测试创建视觉分析器适配器"""
        adapter = AnalyzerFactory.create_adapter("visual")
        self.assertIsInstance(adapter, VisualAnalyzerAdapter)
    
    def test_create_content_adapter(self):
        """测试创建内容分析器适配器"""
        adapter = AnalyzerFactory.create_adapter("content")
        self.assertIsInstance(adapter, ContentAnalyzerAdapter)
    
    def test_create_unsupported_adapter(self):
        """测试创建不支持的分析器适配器"""
        with self.assertRaises(ValueError):
            AnalyzerFactory.create_adapter("unsupported")


class TestSpeechAnalyzerAdapter(unittest.TestCase):
    """测试语音分析器适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.adapter = SpeechAnalyzerAdapter()
        self.state = GraphState()
    
    def test_process_with_audio_path(self):
        """测试使用音频文件路径进行处理"""
        # 创建临时音频文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            task_data = {
                "audio_path": temp_path,
                "params": {"clarity_weight": 0.4}
            }
            
            # 模拟分析器方法
            with patch.object(self.adapter, 'get_analyzer') as mock_analyzer:
                mock_analyzer_instance = Mock()
                mock_analyzer_instance.extract_features.return_value = {
                    "spectral_centroid": 1500,
                    "rms": 0.2
                }
                mock_analyzer_instance.analyze.return_value = {
                    "overall_score": 8.5,
                    "clarity": 8.0,
                    "pace": 9.0,
                    "emotion": "积极",
                    "emotion_score": 8.5
                }
                mock_analyzer.return_value = mock_analyzer_instance
                
                result = self.adapter.process(self.state, task_data)
                
                self.assertIsInstance(result, AnalysisResult)
                self.assertEqual(result.task_type, TaskType.SPEECH_ANALYSIS)
                self.assertEqual(result.score, 8.5)
                self.assertIn("clarity", result.details)
                self.assertIn("pace", result.details)
        
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_process_with_audio_data(self):
        """测试使用音频数据进行处理"""
        task_data = {
            "audio_data": b"fake_audio_data",
            "params": {}
        }
        
        with patch.object(self.adapter, 'get_analyzer') as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.extract_stream_features.return_value = {
                "rms": 0.15,
                "zero_crossing_rate": 0.1
            }
            mock_analyzer_instance.analyze.return_value = {
                "overall_score": 7.5,
                "clarity": 7.0,
                "pace": 8.0,
                "emotion": "中性",
                "emotion_score": 7.5
            }
            mock_analyzer.return_value = mock_analyzer_instance
            
            result = self.adapter.process(self.state, task_data)
            
            self.assertIsInstance(result, AnalysisResult)
            self.assertEqual(result.task_type, TaskType.SPEECH_ANALYSIS)
            self.assertEqual(result.score, 7.5)
    
    def test_process_stream(self):
        """测试流式处理"""
        audio_data = b"fake_stream_data"
        
        with patch.object(self.adapter, 'get_analyzer') as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.extract_stream_features.return_value = {
                "timestamp": 1234567890
            }
            mock_analyzer_instance.analyze_stream.return_value = {
                "clarity": 8.0,
                "pace": 7.5,
                "volume": 8.5,
                "confidence": 8.0,
                "timestamp": 1234567890
            }
            mock_analyzer.return_value = mock_analyzer_instance
            
            result = self.adapter.process_stream(self.state, audio_data)
            
            self.assertIsInstance(result, AnalysisResult)
            self.assertEqual(result.task_type, TaskType.SPEECH_ANALYSIS)
            self.assertAlmostEqual(result.score, 8.0, places=1)
    
    def test_process_error_handling(self):
        """测试错误处理"""
        task_data = {"audio_path": "/nonexistent/path.wav"}
        
        result = self.adapter.process(self.state, task_data)
        
        self.assertIsInstance(result, AnalysisResult)
        self.assertEqual(result.task_type, TaskType.SPEECH_ANALYSIS)
        self.assertEqual(result.confidence, 0.1)  # 低置信度表示错误
        self.assertIn("error", result.details)


class TestVisualAnalyzerAdapter(unittest.TestCase):
    """测试视觉分析器适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.adapter = VisualAnalyzerAdapter()
        self.state = GraphState()
    
    def test_process_with_video_path(self):
        """测试使用视频文件路径进行处理"""
        task_data = {
            "video_path": "/path/to/video.mp4",
            "params": {"frame_rate": 5}
        }
        
        with patch.object(self.adapter, 'get_analyzer') as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.extract_features.return_value = {
                "face_detections": [{"time": 1.0, "bbox": [100, 100, 200, 200]}],
                "eye_contacts": [{"time": 1.0, "score": 0.8}]
            }
            mock_analyzer_instance.analyze.return_value = {
                "overall_score": 8.0,
                "eye_contact": 8.5,
                "expression": 7.5,
                "posture": 8.0,
                "engagement": 8.0
            }
            mock_analyzer.return_value = mock_analyzer_instance
            
            result = self.adapter.process(self.state, task_data)
            
            self.assertIsInstance(result, AnalysisResult)
            self.assertEqual(result.task_type, TaskType.VISUAL_ANALYSIS)
            self.assertEqual(result.score, 8.0)
            self.assertIn("eye_contact", result.details)
            self.assertIn("expression", result.details)
    
    def test_process_with_frame_data(self):
        """测试使用帧数据进行处理"""
        # 创建模拟帧数据
        frame_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        task_data = {
            "frame_data": frame_data,
            "params": {}
        }
        
        with patch.object(self.adapter, 'get_analyzer') as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.extract_frame_features.return_value = {
                "face_detected": True,
                "expression": "neutral"
            }
            mock_analyzer_instance.analyze.return_value = {
                "overall_score": 7.5,
                "eye_contact": 7.0,
                "expression": 8.0,
                "posture": 7.5,
                "engagement": 7.5
            }
            mock_analyzer.return_value = mock_analyzer_instance
            
            result = self.adapter.process(self.state, task_data)
            
            self.assertIsInstance(result, AnalysisResult)
            self.assertEqual(result.task_type, TaskType.VISUAL_ANALYSIS)
            self.assertEqual(result.score, 7.5)


class TestContentAnalyzerAdapter(unittest.TestCase):
    """测试内容分析器适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.adapter = ContentAnalyzerAdapter()
        self.state = GraphState()
    
    def test_process_with_text(self):
        """测试文本内容处理"""
        task_data = {
            "text": "我在之前的项目中负责开发了一个机器学习模型，通过数据分析和算法优化，最终提升了系统性能。",
            "params": {"relevance_weight": 0.5}
        }
        
        with patch.object(self.adapter, 'get_analyzer') as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.extract_features.return_value = {
                "length": 50,
                "word_count": 25,
                "keywords": ["机器学习", "数据分析", "算法", "优化"]
            }
            mock_analyzer_instance.analyze.return_value = {
                "overall_score": 8.5,
                "relevance": 9.0,
                "structure": 8.0,
                "key_points": ["技术能力", "项目经验", "问题解决"]
            }
            mock_analyzer.return_value = mock_analyzer_instance
            
            result = self.adapter.process(self.state, task_data)
            
            self.assertIsInstance(result, AnalysisResult)
            self.assertEqual(result.task_type, TaskType.CONTENT_ANALYSIS)
            self.assertEqual(result.score, 8.5)
            self.assertIn("relevance", result.details)
            self.assertIn("structure", result.details)
            self.assertIn("key_points", result.details)
    
    def test_process_empty_text(self):
        """测试空文本处理"""
        task_data = {"text": "", "params": {}}
        
        result = self.adapter.process(self.state, task_data)
        
        self.assertIsInstance(result, AnalysisResult)
        self.assertEqual(result.task_type, TaskType.CONTENT_ANALYSIS)
        self.assertEqual(result.confidence, 0.1)  # 低置信度表示错误
        self.assertIn("error", result.details)
    
    def test_process_no_text(self):
        """测试未提供文本的情况"""
        task_data = {"params": {}}
        
        result = self.adapter.process(self.state, task_data)
        
        self.assertIsInstance(result, AnalysisResult)
        self.assertEqual(result.task_type, TaskType.CONTENT_ANALYSIS)
        self.assertEqual(result.confidence, 0.1)
        self.assertIn("error", result.details)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_all_adapters_creation(self):
        """测试所有适配器的创建"""
        for analyzer_type in AnalyzerFactory.get_supported_types():
            adapter = AnalyzerFactory.create_adapter(analyzer_type)
            self.assertIsNotNone(adapter)
            self.assertEqual(adapter.analyzer_type, analyzer_type)
    
    def test_adapter_config_passing(self):
        """测试配置参数传递"""
        config = {"test_param": "test_value"}
        adapter = AnalyzerFactory.create_adapter("speech", config)
        self.assertEqual(adapter.config, config)


if __name__ == '__main__':
    unittest.main()