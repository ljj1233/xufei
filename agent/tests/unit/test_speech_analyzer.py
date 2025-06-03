# agent/tests/test_speech_analyzer.py

import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
from typing import Dict, Any

from agent.analyzers.speech_analyzer import SpeechAnalyzer
from agent.core.config import AgentConfig
from agent.services.xunfei_service import XunFeiService
from agent.analyzers.audio_feature_extractor import AudioFeatureExtractor


# 测试数据
MOCK_AUDIO_PATH = "test_audio.wav"
MOCK_AUDIO_BYTES = b"mock_audio_data"
MOCK_XUNFEI_ASSESSMENT = {
    "clarity": 85,  # 清晰度评分（百分制）
    "speed": 60,   # 语速评分（百分制，50为标准语速）
}
MOCK_XUNFEI_EMOTION = {
    "emotion": "平静",
    "confidence": 0.8,
}
MOCK_BASIC_FEATURES = {
    "spectral_centroid": 1500,
    "rms": 0.15,
    "tempo": 120,
    "zero_crossing_rate": 0.12,
    "mfcc": [1.0, 2.0, 3.0, 4.0, 5.0],
}


@pytest.fixture
def mock_config():
    """创建模拟配置对象"""
    config = AgentConfig()
    # 设置测试配置
    config.set_config("clarity_weight", 0.3)
    config.set_config("pace_weight", 0.3)
    config.set_config("emotion_weight", 0.4)
    config.set_config("use_xunfei", True)
    return config


@pytest.fixture
def speech_analyzer(mock_config):
    """创建语音分析器实例"""
    with patch("agent.analyzers.speech_analyzer.XunFeiService") as mock_xunfei_service_cls:
        # 配置模拟的讯飞服务
        mock_xunfei_service = MagicMock()
        mock_xunfei_service_cls.return_value = mock_xunfei_service
        
        # 创建分析器实例
        analyzer = SpeechAnalyzer(config=mock_config)
        
        # 确保讯飞服务被正确初始化
        assert analyzer.xunfei_service is not None
        
        yield analyzer


@pytest.fixture
def speech_analyzer_no_xunfei(mock_config):
    """创建不使用讯飞服务的语音分析器实例"""
    # 修改配置，禁用讯飞服务
    mock_config.set_config("use_xunfei", False)
    
    # 创建分析器实例
    analyzer = SpeechAnalyzer(config=mock_config)
    
    # 确保讯飞服务被禁用
    assert analyzer.use_xunfei is False
    assert analyzer.xunfei_service is None
    
    yield analyzer


def test_init(mock_config):
    """测试初始化"""
    # 测试正常初始化
    with patch("agent.analyzers.speech_analyzer.XunFeiService") as mock_xunfei_service_cls:
        analyzer = SpeechAnalyzer(config=mock_config)
        assert analyzer.name == "speech_analyzer"
        assert analyzer.analyzer_type == "speech"
        assert analyzer.use_xunfei is True
        assert analyzer.xunfei_service is not None
    
    # 测试讯飞服务初始化失败的情况
    with patch("agent.analyzers.speech_analyzer.XunFeiService", side_effect=Exception("初始化失败")):  
        analyzer = SpeechAnalyzer(config=mock_config)
        assert analyzer.use_xunfei is False
        assert analyzer.xunfei_service is None


def test_extract_xunfei_features(speech_analyzer):
    """测试提取讯飞API特征"""
    # 配置模拟的讯飞服务响应
    speech_analyzer.xunfei_service.speech_assessment.return_value = MOCK_XUNFEI_ASSESSMENT
    speech_analyzer.xunfei_service.emotion_analysis.return_value = MOCK_XUNFEI_EMOTION
    
    # 调用方法
    features = speech_analyzer._extract_xunfei_features(MOCK_AUDIO_BYTES)
    
    # 验证结果
    assert "xunfei_assessment" in features
    assert features["xunfei_assessment"] == MOCK_XUNFEI_ASSESSMENT
    assert "xunfei_emotion" in features
    assert features["xunfei_emotion"] == MOCK_XUNFEI_EMOTION
    
    # 验证讯飞服务方法被正确调用
    speech_analyzer.xunfei_service.speech_assessment.assert_called_once_with(MOCK_AUDIO_BYTES)
    speech_analyzer.xunfei_service.emotion_analysis.assert_called_once_with(MOCK_AUDIO_BYTES)


def test_extract_xunfei_features_no_xunfei(speech_analyzer_no_xunfei):
    """测试在讯飞服务不可用时提取讯飞API特征"""
    # 调用方法
    features = speech_analyzer_no_xunfei._extract_xunfei_features(MOCK_AUDIO_BYTES)
    
    # 验证结果为空
    assert features == {}


def test_extract_xunfei_features_exception(speech_analyzer):
    """测试提取讯飞API特征时发生异常"""
    # 配置模拟的讯飞服务抛出异常
    speech_analyzer.xunfei_service.speech_assessment.side_effect = Exception("API调用失败")
    
    # 调用方法
    features = speech_analyzer._extract_xunfei_features(MOCK_AUDIO_BYTES)
    
    # 验证结果为空
    assert features == {}


def test_extract_features(speech_analyzer):
    """测试提取语音特征"""
    # 模拟AudioFeatureExtractor的方法
    with patch("agent.analyzers.speech_analyzer.AudioFeatureExtractor") as mock_extractor_cls:
        # 配置模拟的音频特征提取器
        mock_extractor_cls.read_audio_bytes.return_value = MOCK_AUDIO_BYTES
        mock_extractor_cls.extract_from_file.return_value = MOCK_BASIC_FEATURES
        
        # 配置模拟的讯飞服务响应
        speech_analyzer.xunfei_service.speech_assessment.return_value = MOCK_XUNFEI_ASSESSMENT
        speech_analyzer.xunfei_service.emotion_analysis.return_value = MOCK_XUNFEI_EMOTION
        
        # 调用方法
        features = speech_analyzer.extract_features(MOCK_AUDIO_PATH)
        
        # 验证结果
        assert "xunfei_assessment" in features
        assert features["xunfei_assessment"] == MOCK_XUNFEI_ASSESSMENT
        assert "xunfei_emotion" in features
        assert features["xunfei_emotion"] == MOCK_XUNFEI_EMOTION
        assert "spectral_centroid" in features
        assert features["spectral_centroid"] == MOCK_BASIC_FEATURES["spectral_centroid"]
        
        # 验证方法被正确调用
        mock_extractor_cls.read_audio_bytes.assert_called_once_with(MOCK_AUDIO_PATH)
        mock_extractor_cls.extract_from_file.assert_called_once_with(MOCK_AUDIO_PATH)


def test_extract_features_exception(speech_analyzer):
    """测试提取语音特征时发生异常"""
    # 模拟AudioFeatureExtractor的方法抛出异常
    with patch("agent.analyzers.speech_analyzer.AudioFeatureExtractor") as mock_extractor_cls:
        mock_extractor_cls.read_audio_bytes.side_effect = Exception("读取音频失败")
        
        # 调用方法
        features = speech_analyzer.extract_features(MOCK_AUDIO_PATH)
        
        # 验证结果为空
        assert features == {}


def test_get_analysis_weights(speech_analyzer):
    """测试获取分析权重"""
    # 使用默认参数
    weights = speech_analyzer._get_analysis_weights()
    assert weights["clarity"] == 0.3
    assert weights["pace"] == 0.3
    assert weights["emotion"] == 0.4
    
    # 使用自定义参数
    custom_params = {
        "clarity_weight": 0.5,
        "pace_weight": 0.2,
        "emotion_weight": 0.3
    }
    weights = speech_analyzer._get_analysis_weights(custom_params)
    assert weights["clarity"] == 0.5
    assert weights["pace"] == 0.2
    assert weights["emotion"] == 0.3


def test_analyze_empty_features(speech_analyzer):
    """测试分析空特征"""
    # 调用方法
    result = speech_analyzer.analyze({})
    
    # 验证结果
    assert result["clarity"] == 5.0
    assert result["pace"] == 5.0
    assert result["emotion"] == "中性"
    assert result["emotion_score"] == 5.0
    assert result["overall_score"] == 5.0


def test_analyze_with_xunfei_features(speech_analyzer):
    """测试使用讯飞特征进行分析"""
    # 准备测试数据
    features = {
        "xunfei_assessment": MOCK_XUNFEI_ASSESSMENT,
        "xunfei_emotion": MOCK_XUNFEI_EMOTION,
    }
    
    # 调用方法
    result = speech_analyzer.analyze(features)
    
    # 验证结果
    assert 0 <= result["clarity"] <= 10
    assert 0 <= result["pace"] <= 10
    assert result["emotion"] == "平静"
    assert 0 <= result["emotion_score"] <= 10
    assert 0 <= result["overall_score"] <= 10


def test_analyze_with_basic_features(speech_analyzer):
    """测试使用基本特征进行分析"""
    # 准备测试数据
    features = MOCK_BASIC_FEATURES.copy()
    
    # 调用方法
    result = speech_analyzer.analyze(features)
    
    # 验证结果
    assert 0 <= result["clarity"] <= 10
    assert 0 <= result["pace"] <= 10
    assert result["emotion"] in ["积极", "消极", "中性"]
    assert 0 <= result["emotion_score"] <= 10
    assert 0 <= result["overall_score"] <= 10


def test_analyze_clarity_with_xunfei(speech_analyzer):
    """测试使用讯飞评测结果分析清晰度"""
    # 调用方法
    clarity = speech_analyzer._analyze_clarity_with_xunfei(MOCK_XUNFEI_ASSESSMENT)
    
    # 验证结果
    assert 0 <= clarity <= 10
    assert clarity == 8.5  # 85 / 10


def test_analyze_clarity_with_basic_features(speech_analyzer):
    """测试使用基本音频特征分析清晰度"""
    # 调用方法
    clarity = speech_analyzer._analyze_clarity_with_basic_features(MOCK_BASIC_FEATURES)
    
    # 验证结果
    assert 0 <= clarity <= 10


def test_analyze_clarity(speech_analyzer):
    """测试分析清晰度"""
    # 使用讯飞评测结果
    features_with_xunfei = {
        "xunfei_assessment": MOCK_XUNFEI_ASSESSMENT,
    }
    clarity_with_xunfei = speech_analyzer._analyze_clarity(features_with_xunfei)
    assert 0 <= clarity_with_xunfei <= 10
    
    # 使用基本特征
    features_basic = MOCK_BASIC_FEATURES.copy()
    clarity_basic = speech_analyzer._analyze_clarity(features_basic)
    assert 0 <= clarity_basic <= 10


def test_analyze_pace_with_xunfei(speech_analyzer):
    """测试使用讯飞评测结果分析语速"""
    # 标准语速
    assessment_standard = {"speed": 50}
    pace_standard = speech_analyzer._analyze_pace_with_xunfei(assessment_standard)
    assert pace_standard == 5.0
    
    # 快语速
    assessment_fast = {"speed": 70}
    pace_fast = speech_analyzer._analyze_pace_with_xunfei(assessment_fast)
    assert 0 <= pace_fast < 5.0
    
    # 慢语速
    assessment_slow = {"speed": 30}
    pace_slow = speech_analyzer._analyze_pace_with_xunfei(assessment_slow)
    assert 0 <= pace_slow < 5.0


def test_analyze_pace_with_basic_features(speech_analyzer):
    """测试使用基本音频特征分析语速"""
    # 标准语速
    features_standard = {"tempo": 120, "zero_crossing_rate": 0.1}
    pace_standard = speech_analyzer._analyze_pace_with_basic_features(features_standard)
    assert pace_standard > 7.0
    
    # 快语速
    features_fast = {"tempo": 160, "zero_crossing_rate": 0.2}
    pace_fast = speech_analyzer._analyze_pace_with_basic_features(features_fast)
    assert 0 <= pace_fast <= 10
    
    # 慢语速
    features_slow = {"tempo": 80, "zero_crossing_rate": 0.05}
    pace_slow = speech_analyzer._analyze_pace_with_basic_features(features_slow)
    assert 0 <= pace_slow <= 10


def test_analyze_pace(speech_analyzer):
    """测试分析语速"""
    # 使用讯飞评测结果
    features_with_xunfei = {
        "xunfei_assessment": MOCK_XUNFEI_ASSESSMENT,
    }
    pace_with_xunfei = speech_analyzer._analyze_pace(features_with_xunfei)
    assert 0 <= pace_with_xunfei <= 10
    
    # 使用基本特征
    features_basic = MOCK_BASIC_FEATURES.copy()
    pace_basic = speech_analyzer._analyze_pace(features_basic)
    assert 0 <= pace_basic <= 10


def test_analyze_emotion_with_xunfei(speech_analyzer):
    """测试使用讯飞情感分析结果分析情感"""
    # 平静情感
    emotion_calm = {"emotion": "平静", "confidence": 0.8}
    result_calm = speech_analyzer._analyze_emotion_with_xunfei(emotion_calm)
    assert result_calm[0] == "平静"
    assert 7.0 <= result_calm[1] <= 10.0
    
    # 积极情感
    emotion_positive = {"emotion": "高兴", "confidence": 0.7}
    result_positive = speech_analyzer._analyze_emotion_with_xunfei(emotion_positive)
    assert result_positive[0] == "高兴"
    assert 6.0 <= result_positive[1] <= 10.0
    
    # 紧张情感
    emotion_nervous = {"emotion": "紧张", "confidence": 0.6}
    result_nervous = speech_analyzer._analyze_emotion_with_xunfei(emotion_nervous)
    assert result_nervous[0] == "紧张"
    assert 5.0 <= result_nervous[1] <= 7.0
    
    # 其他情感
    emotion_other = {"emotion": "愤怒", "confidence": 0.5}
    result_other = speech_analyzer._analyze_emotion_with_xunfei(emotion_other)
    assert result_other[0] == "愤怒"
    assert 3.0 <= result_other[1] <= 5.0


def test_analyze_emotion_with_basic_features(speech_analyzer):
    """测试使用基本音频特征分析情感"""
    # 积极情感
    features_positive = {"rms": 0.25, "zero_crossing_rate": 0.2}
    result_positive = speech_analyzer._analyze_emotion_with_basic_features(features_positive)
    assert result_positive[0] == "积极"
    assert result_positive[1] == 8.0
    
    # 消极情感
    features_negative = {"rms": 0.04, "zero_crossing_rate": 0.04}
    result_negative = speech_analyzer._analyze_emotion_with_basic_features(features_negative)
    assert result_negative[0] == "消极"
    assert result_negative[1] == 4.0
    
    # 中性情感
    features_neutral = {"rms": 0.1, "zero_crossing_rate": 0.1}
    result_neutral = speech_analyzer._analyze_emotion_with_basic_features(features_neutral)
    assert result_neutral[0] == "中性"
    assert result_neutral[1] == 6.0


def test_analyze_emotion(speech_analyzer):
    """测试分析情感"""
    # 使用讯飞情感分析结果
    features_with_xunfei = {
        "xunfei_emotion": MOCK_XUNFEI_EMOTION,
    }
    emotion, score = speech_analyzer._analyze_emotion(features_with_xunfei)
    assert emotion == "平静"
    assert 0 <= score <= 10
    
    # 使用基本特征
    features_basic = MOCK_BASIC_FEATURES.copy()
    emotion, score = speech_analyzer._analyze_emotion(features_basic)
    assert emotion in ["积极", "消极", "中性"]
    assert 0 <= score <= 10


def test_speech_to_text(speech_analyzer):
    """测试语音转文本"""
    # 模拟AudioFeatureExtractor的方法
    with patch("agent.analyzers.speech_analyzer.AudioFeatureExtractor") as mock_extractor_cls:
        # 配置模拟的音频特征提取器
        mock_extractor_cls.read_audio_bytes.return_value = MOCK_AUDIO_BYTES
        
        # 配置模拟的讯飞服务响应
        speech_analyzer.xunfei_service.speech_recognition.return_value = "这是一段测试语音"
        
        # 调用方法
        text = speech_analyzer.speech_to_text(MOCK_AUDIO_PATH)
        
        # 验证结果
        assert text == "这是一段测试语音"
        
        # 验证方法被正确调用
        mock_extractor_cls.read_audio_bytes.assert_called_once_with(MOCK_AUDIO_PATH)
        speech_analyzer.xunfei_service.speech_recognition.assert_called_once_with(MOCK_AUDIO_BYTES)


def test_speech_to_text_no_xunfei(speech_analyzer_no_xunfei):
    """测试在讯飞服务不可用时语音转文本"""
    # 模拟AudioFeatureExtractor的方法
    with patch("agent.analyzers.speech_analyzer.AudioFeatureExtractor") as mock_extractor_cls:
        # 配置模拟的音频特征提取器
        mock_extractor_cls.read_audio_bytes.return_value = MOCK_AUDIO_BYTES
        
        # 调用方法
        text = speech_analyzer_no_xunfei.speech_to_text(MOCK_AUDIO_PATH)
        
        # 验证结果为空
        assert text == ""


def test_speech_to_text_exception(speech_analyzer):
    """测试语音转文本时发生异常"""
    # 模拟AudioFeatureExtractor的方法抛出异常
    with patch("agent.analyzers.speech_analyzer.AudioFeatureExtractor") as mock_extractor_cls:
        mock_extractor_cls.read_audio_bytes.side_effect = Exception("读取音频失败")
        
        # 调用方法
        text = speech_analyzer.speech_to_text(MOCK_AUDIO_PATH)
        
        # 验证结果为空
        assert text == ""