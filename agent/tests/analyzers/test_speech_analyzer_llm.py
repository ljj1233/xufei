import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

from agent.src.analyzers.speech.speech_analyzer import SpeechAnalyzer
from agent.src.core.system.config import AgentConfig
from agent.src.services.xunfei_service import XunFeiService
from agent.src.services.async_xunfei_service import AsyncXunFeiService
from agent.src.analyzers.speech.audio_feature_extractor import AudioFeatureExtractor

# 测试数据
MOCK_AUDIO_PATH = "test_audio.wav"
MOCK_AUDIO_BYTES = b"mock_audio_data"
MOCK_TRANSCRIPT = "这是一段测试用的语音转写文本，用于评估语音质量"
MOCK_FEATURES = {
    "speech_rate": 5.5,  # 语速（字/秒）
    "pitch_mean": 220.5,  # 平均音高
    "energy_mean": 75.3,  # 平均音量
    "xunfei_assessment": {
        "clarity": 85,  # 清晰度评分
        "fluency": 80,  # 流畅度评分
        "integrity": 90,  # 完整度评分
        "speed": 70,  # 语速评分
    },
    "xunfei_emotion": {
        "emotion": "平静",  # 情感类型
        "confidence": 0.8,  # 置信度
    }
}

MOCK_LLM_RESPONSE = {
    "status": "success",
    "content": """
    {
        "scores": {
            "clarity": 85,
            "fluency": 80,
            "rhythm": 75,
            "expressiveness": 70,
            "voice_quality": 85,
            "overall_score": 78
        },
        "analysis": {
            "strengths": [
                "语音清晰度高，发音准确",
                "语速适中，表达流畅"
            ],
            "suggestions": [
                "可以增加语音表现力",
                "适当增加语调变化"
            ]
        },
        "summary": "整体语音表现良好，清晰度高，语速适中，但需要增加表现力和语调变化"
    }
    """
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
    config.set_config("use_xunfei_llm", True)
    return config


@pytest.fixture
def speech_analyzer_with_llm(mock_config):
    """创建带有LLM功能的语音分析器实例"""
    with patch("agent.src.analyzers.speech.speech_analyzer.XunFeiService") as mock_xunfei_service_cls, \
         patch("agent.src.analyzers.speech.speech_analyzer.AsyncXunFeiService") as mock_async_xunfei_service_cls:
        # 配置模拟的讯飞服务
        mock_xunfei_service = MagicMock()
        mock_xunfei_service_cls.return_value = mock_xunfei_service
        
        # 配置模拟的讯飞异步服务
        mock_async_xunfei_service = MagicMock()
        mock_async_xunfei_service_cls.return_value = mock_async_xunfei_service
        
        # 创建分析器实例
        analyzer = SpeechAnalyzer(config=mock_config)
        
        # 确保讯飞服务和讯飞LLM服务被正确初始化
        assert analyzer.xunfei_service is not None
        assert analyzer.async_xunfei_service is not None
        assert analyzer.use_xunfei is True
        assert analyzer.use_xunfei_llm is True
        
        yield analyzer


@pytest.fixture
def speech_analyzer_no_llm(mock_config):
    """创建不使用讯飞LLM服务的语音分析器实例"""
    # 修改配置，禁用讯飞LLM服务
    mock_config.set("speech", "use_xunfei_llm", False)
    
    with patch("agent.src.analyzers.speech.speech_analyzer.XunFeiService") as mock_xunfei_service_cls:
        # 配置模拟的讯飞服务
        mock_xunfei_service = MagicMock()
        mock_xunfei_service_cls.return_value = mock_xunfei_service
        
        # 创建分析器实例
        analyzer = SpeechAnalyzer(config=mock_config)
        
        # 确保讯飞服务被正确初始化，但LLM服务被禁用
        assert analyzer.xunfei_service is not None
        assert analyzer.async_xunfei_service is None
        assert analyzer.use_xunfei is True
        assert analyzer.use_xunfei_llm is False
        
        yield analyzer


def test_init_with_llm(mock_config):
    """测试带有LLM功能的初始化"""
    # 测试正常初始化
    with patch("agent.src.analyzers.speech.speech_analyzer.XunFeiService") as mock_xunfei_service_cls, \
         patch("agent.src.analyzers.speech.speech_analyzer.AsyncXunFeiService") as mock_async_xunfei_service_cls:
        analyzer = SpeechAnalyzer(config=mock_config)
        assert analyzer.use_xunfei is True
        assert analyzer.use_xunfei_llm is True
        assert analyzer.xunfei_service is not None
        assert analyzer.async_xunfei_service is not None
    
    # 测试LLM服务初始化失败的情况
    with patch("agent.src.analyzers.speech.speech_analyzer.XunFeiService") as mock_xunfei_service_cls, \
         patch("agent.src.analyzers.speech.speech_analyzer.AsyncXunFeiService", side_effect=Exception("初始化失败")):  
        analyzer = SpeechAnalyzer(config=mock_config)
        # 根据SpeechAnalyzer.__init__中的异常处理，初始化失败时use_xunfei会被设置为False
        assert analyzer.use_xunfei is False
        assert analyzer.use_xunfei_llm is False
        assert analyzer.xunfei_service is None
        assert analyzer.async_xunfei_service is None


@pytest.mark.asyncio
async def test_analyze_with_llm_success(speech_analyzer_with_llm):
    """测试使用LLM分析成功的情况"""
    # 配置模拟的特征提取
    speech_analyzer_with_llm.extract_features = MagicMock(return_value=MOCK_FEATURES)
    
    # 配置模拟的讯飞异步服务响应
    speech_analyzer_with_llm.async_xunfei_service.chat_spark = AsyncMock(return_value=MOCK_LLM_RESPONSE)
    
    # 调用方法
    result = await speech_analyzer_with_llm.analyze_with_llm(MOCK_AUDIO_PATH, MOCK_TRANSCRIPT)
    
    # 验证结果
    assert "scores" in result
    assert "analysis" in result
    assert "summary" in result
    assert result["scores"]["clarity"] == 85
    assert result["scores"]["fluency"] == 80
    assert result["scores"]["rhythm"] == 75
    assert result["scores"]["expressiveness"] == 70
    assert result["scores"]["voice_quality"] == 85
    assert result["scores"]["overall_score"] == 78
    assert len(result["analysis"]["strengths"]) == 2
    assert len(result["analysis"]["suggestions"]) == 2
    
    # 验证讯飞星火大模型服务被正确调用
    speech_analyzer_with_llm.async_xunfei_service.chat_spark.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_with_llm_no_transcript(speech_analyzer_with_llm):
    """测试无文本时使用语音识别"""
    # 配置模拟的特征提取
    speech_analyzer_with_llm.extract_features = MagicMock(return_value=MOCK_FEATURES)
    
    # 配置模拟的音频读取 - 移到调用前，确保mock生效
    with patch.object(AudioFeatureExtractor, 'read_audio_bytes', return_value=MOCK_AUDIO_BYTES) as mock_read:
        # 配置模拟的讯飞服务进行语音识别
        speech_analyzer_with_llm.xunfei_service.speech_recognition = MagicMock(return_value=MOCK_TRANSCRIPT)
        
        # 配置模拟的讯飞异步服务响应
        speech_analyzer_with_llm.async_xunfei_service.chat_spark = AsyncMock(return_value=MOCK_LLM_RESPONSE)
        
        # 调用方法，不提供文本
        result = await speech_analyzer_with_llm.analyze_with_llm(MOCK_AUDIO_PATH)
        
        # 验证音频读取被调用
        mock_read.assert_called_once_with(MOCK_AUDIO_PATH)
        
        # 验证语音识别被调用
        speech_analyzer_with_llm.xunfei_service.speech_recognition.assert_called_once_with(MOCK_AUDIO_BYTES)
        
        # 验证结果
        assert "scores" in result
        assert "analysis" in result
        assert "summary" in result


@pytest.mark.asyncio
async def test_analyze_with_llm_response_error(speech_analyzer_with_llm):
    """测试LLM响应错误的情况"""
    # 配置模拟的特征提取
    speech_analyzer_with_llm.extract_features = MagicMock(return_value=MOCK_FEATURES)
    
    # 配置模拟的讯飞异步服务响应失败
    mock_error_response = {
        "status": "error",
        "error": "API请求失败",
        "content": None
    }
    speech_analyzer_with_llm.async_xunfei_service.chat_spark = AsyncMock(return_value=mock_error_response)
    
    # 模拟回退分析方法
    speech_analyzer_with_llm._fallback_analysis = MagicMock(return_value={"scores": {"overall_score": 75}})
    
    # 调用方法
    result = await speech_analyzer_with_llm.analyze_with_llm(MOCK_AUDIO_PATH, MOCK_TRANSCRIPT)
    
    # 验证回退方法被调用
    speech_analyzer_with_llm._fallback_analysis.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_with_llm_exception(speech_analyzer_with_llm):
    """测试LLM调用异常的情况"""
    # 配置模拟的特征提取
    speech_analyzer_with_llm.extract_features = MagicMock(return_value=MOCK_FEATURES)
    
    # 配置模拟的讯飞异步服务抛出异常
    speech_analyzer_with_llm.async_xunfei_service.chat_spark = AsyncMock(side_effect=Exception("API调用失败"))
    
    # 模拟回退分析方法
    speech_analyzer_with_llm._fallback_analysis = MagicMock(return_value={"scores": {"overall_score": 75}})
    
    # 调用方法
    result = await speech_analyzer_with_llm.analyze_with_llm(MOCK_AUDIO_PATH, MOCK_TRANSCRIPT)
    
    # 验证回退方法被调用
    speech_analyzer_with_llm._fallback_analysis.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_async_with_llm(speech_analyzer_with_llm):
    """测试异步分析接口使用LLM"""
    # 配置模拟的analyze_with_llm结果
    mock_llm_result = {
        "scores": {
            "clarity": 85,
            "fluency": 80,
            "rhythm": 75,
            "expressiveness": 70,
            "voice_quality": 85,
            "overall_score": 78
        },
        "analysis": {
            "strengths": ["优势1", "优势2"],
            "suggestions": ["建议1", "建议2"]
        },
        "summary": "总结评价"
    }
    
    speech_analyzer_with_llm.analyze_with_llm = AsyncMock(return_value=mock_llm_result)
    
    # 调用异步分析方法
    result = await speech_analyzer_with_llm.analyze_async(MOCK_AUDIO_PATH)
    
    # 验证结果
    assert "speech_rate" in result
    assert "fluency" in result
    assert "emotion" in result
    assert "overall_score" in result
    assert "detailed_scores" in result
    assert "analysis" in result
    assert result["overall_score"] == 78


@pytest.mark.asyncio
async def test_analyze_async_no_llm(speech_analyzer_no_llm):
    """测试异步分析接口不使用LLM"""
    # 确保async_xunfei_service为None
    assert speech_analyzer_no_llm.async_xunfei_service is None
    
    # 配置模拟的特征提取
    speech_analyzer_no_llm.extract_features_async = AsyncMock(return_value=MOCK_FEATURES)
    
    # 配置模拟的分析方法
    speech_analyzer_no_llm.analyze_pace_async = AsyncMock(return_value={"score": 80, "feedback": "语速适中"})
    speech_analyzer_no_llm.analyze_clarity_async = AsyncMock(return_value={"score": 85, "feedback": "清晰度高"})
    speech_analyzer_no_llm.analyze_emotion_async = AsyncMock(return_value={"score": 75, "feedback": "情感表达适度"})
    
    # 调用异步分析方法
    result = await speech_analyzer_no_llm.analyze_async(MOCK_AUDIO_PATH)
    
    # 验证结果
    assert "speech_rate" in result
    assert "fluency" in result
    assert "emotion" in result
    assert "overall_score" in result
    assert result["speech_rate"]["score"] == 80
    assert result["fluency"]["score"] == 85
    assert result["emotion"]["score"] == 75


def test_parse_llm_response_valid(speech_analyzer_with_llm):
    """测试解析有效的LLM响应"""
    # 准备测试数据
    mock_response = MOCK_LLM_RESPONSE["content"]
    
    # 调用方法
    result = speech_analyzer_with_llm._parse_llm_response(mock_response)
    
    # 验证结果
    assert "scores" in result
    assert "analysis" in result
    assert "summary" in result
    assert result["scores"]["clarity"] == 85
    assert result["scores"]["fluency"] == 80
    assert result["scores"]["overall_score"] == 78
    assert len(result["analysis"]["strengths"]) == 2
    assert len(result["analysis"]["suggestions"]) == 2


def test_parse_llm_response_missing_overall_score(speech_analyzer_with_llm):
    """测试解析缺少overall_score的LLM响应"""
    # 准备测试数据 - 缺少overall_score
    mock_response = """
    {
        "scores": {
            "clarity": 85,
            "fluency": 80,
            "rhythm": 75,
            "expressiveness": 70,
            "voice_quality": 85
        },
        "analysis": {
            "strengths": ["优势1", "优势2"],
            "suggestions": ["建议1", "建议2"]
        },
        "summary": "总结评价"
    }
    """
    
    # 调用方法
    result = speech_analyzer_with_llm._parse_llm_response(mock_response)
    
    # 验证结果 - 应该自动计算overall_score
    assert "scores" in result
    assert "overall_score" in result["scores"]
    assert result["scores"]["overall_score"] == 79  # (85+80+75+70+85)/5


def test_parse_llm_response_invalid_json(speech_analyzer_with_llm):
    """测试解析无效JSON的LLM响应"""
    # 准备测试数据 - 无效JSON
    mock_response = "这不是有效的JSON格式"
    
    # 调用方法
    result = speech_analyzer_with_llm._parse_llm_response(mock_response)
    
    # 验证结果 - 应该返回默认值
    assert "scores" in result
    assert "analysis" in result
    assert "error" in result
    assert result["scores"]["overall_score"] == 0
    assert "解析失败" in result["analysis"]["strengths"][0]


def test_build_speech_analysis_prompt(speech_analyzer_with_llm):
    """测试构建语音分析提示词"""
    # 调用方法
    prompt = speech_analyzer_with_llm._build_speech_analysis_prompt(MOCK_TRANSCRIPT, MOCK_FEATURES)
    
    # 验证结果
    assert "语音转写文本" in prompt
    assert MOCK_TRANSCRIPT in prompt
    assert "语速: 5.5" in prompt
    assert "清晰度: 85" in prompt
    assert "流畅度: 80" in prompt
    assert "情感类型: 平静" in prompt
    assert "JSON格式" in prompt 