# -*- coding: utf-8 -*-
"""
分析器适配器测试

测试分析器适配器的功能和集成效果
"""

import unittest
import os
import tempfile
from unittest.mock import Mock, patch

from agent.src.core.analyzer_adapter import (
    AnalyzerFactory,
    SpeechAnalyzerAdapter,
    VisualAnalyzerAdapter,
    ContentAnalyzerAdapter,
    create_adapter
)
from agent.src.core.workflow.state import GraphState, TaskType


class TestAnalyzerFactory(unittest.TestCase):
    """测试分析器工厂类"""
    
    def test_create_speech_adapter(self):
        """测试创建语音分析器适配器"""
        adapter = AnalyzerFactory.create("speech")
        self.assertIsInstance(adapter, SpeechAnalyzerAdapter)
    
    def test_create_visual_adapter(self):
        """测试创建视觉分析器适配器"""
        adapter = AnalyzerFactory.create("visual")
        self.assertIsInstance(adapter, VisualAnalyzerAdapter)
    
    def test_create_content_adapter(self):
        """测试创建内容分析器适配器"""
        adapter = AnalyzerFactory.create("content")
        self.assertIsInstance(adapter, ContentAnalyzerAdapter)
    
    def test_create_unsupported_adapter(self):
        """测试创建不支持的分析器适配器"""
        with self.assertRaises(ValueError):
            AnalyzerFactory.create("unsupported")


class TestSpeechAnalyzerAdapter(unittest.TestCase):
    """测试语音分析器适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.adapter = SpeechAnalyzerAdapter()
        
    def test_extract_features(self):
        """测试特征提取"""
        data = {"audio_file": "test_audio.wav"}
        features = self.adapter.extract_features(data)
        
        self.assertEqual(features["audio_file"], "test_audio.wav")
    
    def test_analyze(self):
        """测试分析"""
        features = {"audio_file": "test_audio.wav"}
        result = self.adapter.analyze(features)
        
        self.assertIn("speech_rate", result)
        self.assertIn("fluency", result)
        
    def test_run(self):
        """测试运行"""
        data = {"audio_file": "test_audio.wav"}
        result = self.adapter.run(data)
        
        self.assertIn("speech_rate", result)
        self.assertIn("fluency", result)
    
    def test_missing_audio_file(self):
        """测试缺少音频文件"""
        data = {"other_data": "test"}
        
        with self.assertRaises(ValueError):
            self.adapter.extract_features(data)


class TestVisualAnalyzerAdapter(unittest.TestCase):
    """测试视觉分析器适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.adapter = VisualAnalyzerAdapter()
        
    def test_extract_features(self):
        """测试特征提取"""
        data = {"video_file": "test_video.mp4"}
        features = self.adapter.extract_features(data)
        
        self.assertEqual(features["video_file"], "test_video.mp4")
    
    def test_analyze(self):
        """测试分析"""
        features = {"video_file": "test_video.mp4"}
        result = self.adapter.analyze(features)
        
        self.assertIn("facial_expression", result)
        self.assertIn("eye_contact", result)
        
    def test_run(self):
        """测试运行"""
        data = {"video_file": "test_video.mp4"}
        result = self.adapter.run(data)
        
        self.assertIn("facial_expression", result)
        self.assertIn("eye_contact", result)
    
    def test_missing_video_file(self):
        """测试缺少视频文件"""
        data = {"other_data": "test"}
        
        with self.assertRaises(ValueError):
            self.adapter.extract_features(data)


class TestContentAnalyzerAdapter(unittest.TestCase):
    """测试内容分析器适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.adapter = ContentAnalyzerAdapter()
        
    def test_extract_features(self):
        """测试特征提取"""
        data = {"transcript": "测试文本内容"}
        features = self.adapter.extract_features(data)
        
        self.assertEqual(features["text"], "测试文本内容")
    
    def test_extract_features_with_job_position(self):
        """测试带职位信息的特征提取"""
        data = {
            "transcript": "测试文本内容",
            "job_position": {"title": "软件工程师"}
        }
        features = self.adapter.extract_features(data)
        
        self.assertEqual(features["text"], "测试文本内容")
        self.assertEqual(features["job_position"]["title"], "软件工程师")
    
    def test_analyze(self):
        """测试分析"""
        features = {"text": "测试文本内容"}
        result = self.adapter.analyze(features)
        
        self.assertIn("relevance", result)
        self.assertIn("completeness", result)
        
    def test_run(self):
        """测试运行"""
        data = {"transcript": "测试文本内容"}
        result = self.adapter.run(data)
        
        self.assertIn("relevance", result)
        self.assertIn("completeness", result)
    
    def test_missing_transcript(self):
        """测试缺少文本内容"""
        data = {"other_data": "test"}
        
        with self.assertRaises(ValueError):
            self.adapter.extract_features(data)


class TestCreateAdapter(unittest.TestCase):
    """测试create_adapter函数"""
    
    def test_create_speech_adapter(self):
        """测试创建语音分析器适配器"""
        adapter = create_adapter("speech")
        self.assertIsInstance(adapter, SpeechAnalyzerAdapter)
    
    def test_create_visual_adapter(self):
        """测试创建视觉分析器适配器"""
        adapter = create_adapter("visual")
        self.assertIsInstance(adapter, VisualAnalyzerAdapter)
    
    def test_create_content_adapter(self):
        """测试创建内容分析器适配器"""
        adapter = create_adapter("content")
        self.assertIsInstance(adapter, ContentAnalyzerAdapter)
    
    def test_create_unsupported_adapter(self):
        """测试创建不支持的分析器适配器"""
        with self.assertRaises(ValueError):
            create_adapter("unsupported")


if __name__ == '__main__':
    unittest.main()