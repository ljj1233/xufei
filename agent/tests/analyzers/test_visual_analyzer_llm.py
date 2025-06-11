import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
import os
import numpy as np
import cv2

from agent.src.analyzers.visual.visual_analyzer import VisualAnalyzer
from agent.src.core.system.config import AgentConfig
from agent.src.services.async_xunfei_service import AsyncXunFeiService

# 测试数据
MOCK_VIDEO_PATH = "test_video.mp4"
MOCK_VIDEO_FEATURES = {
    "duration": 120.0,  # 120秒
    "frame_count": 3600,  # 30fps x 120秒
    "face_detected_ratio": 0.95,  # 95%的帧检测到人脸
    "smile_ratio": 0.6,  # 60%的时间在微笑
    "eye_contact_ratio": 0.8,  # 80%的时间有眼神接触
    "posture_changes": 5,  # 5次姿势变化
    "hand_gestures": 12  # 12次手势
}

MOCK_LLM_RESPONSE = {
    "status": "success",
    "content": """
    {
        "scores": {
            "facial_expression": 85,
            "eye_contact": 80,
            "body_language": 75,
            "overall_score": 80
        },
        "analysis": {
            "strengths": [
                "面部表情自然，微笑适度",
                "与摄像头保持良好的眼神交流"
            ],
            "suggestions": [
                "可以增加一些肢体动作辅助表达",
                "注意减少不必要的姿势调整"
            ]
        },
        "summary": "整体视觉表现良好，表情自然，眼神交流充分，可适当增加手势辅助表达"
    }
    """
}


@pytest.fixture
def mock_config():
    """创建模拟配置对象"""
    config = AgentConfig()
    # 设置测试配置 - 修改为使用正确的set方法
    config.set("visual", "face_detection_model", "haarcascade")
    config.set("visual", "frame_sample_rate", 5)
    config.set("visual", "use_xunfei_llm", True)
    return config


@pytest.fixture
def visual_analyzer_with_llm(mock_config):
    """创建带有LLM功能的视觉分析器实例"""
    with patch("agent.src.analyzers.visual.visual_analyzer.AsyncXunFeiService") as mock_async_xunfei_service_cls:
        # 配置模拟的讯飞异步服务
        mock_async_xunfei_service = MagicMock()
        mock_async_xunfei_service_cls.return_value = mock_async_xunfei_service
        
        # 创建分析器实例
        analyzer = VisualAnalyzer(config=mock_config)
        
        # 确保讯飞LLM服务被正确初始化
        assert analyzer.use_xunfei_llm is True
        assert analyzer.async_xunfei_service is not None
        
        yield analyzer


@pytest.fixture
def visual_analyzer_no_llm(mock_config):
    """创建不使用讯飞LLM服务的视觉分析器实例"""
    # 修改配置，禁用讯飞LLM服务 - 修改为使用正确的set方法
    mock_config.set("visual", "use_xunfei_llm", False)
    
    # 创建分析器实例
    analyzer = VisualAnalyzer(config=mock_config)
    
    # 确保LLM服务被禁用
    assert analyzer.use_xunfei_llm is False
    assert analyzer.async_xunfei_service is None
    
    yield analyzer


def test_init_with_llm(mock_config):
    """测试带有LLM功能的初始化"""
    # 测试正常初始化
    with patch("agent.src.analyzers.visual.visual_analyzer.AsyncXunFeiService") as mock_async_xunfei_service_cls:
        analyzer = VisualAnalyzer(config=mock_config)
        assert analyzer.use_xunfei_llm is True
        assert analyzer.async_xunfei_service is not None
    
    # 测试LLM服务初始化失败的情况
    with patch("agent.src.analyzers.visual.visual_analyzer.AsyncXunFeiService", side_effect=Exception("初始化失败")):  
        analyzer = VisualAnalyzer(config=mock_config)
        assert analyzer.use_xunfei_llm is False
        assert analyzer.async_xunfei_service is None


@pytest.mark.asyncio
async def test_analyze_with_llm_success(visual_analyzer_with_llm):
    """测试使用LLM分析成功的情况"""
    # 配置模拟的讯飞异步服务响应
    visual_analyzer_with_llm.async_xunfei_service.chat_spark = AsyncMock(return_value=MOCK_LLM_RESPONSE)
    
    # 调用方法
    result = await visual_analyzer_with_llm.analyze_with_llm(MOCK_VIDEO_FEATURES)
    
    # 验证结果
    assert "scores" in result
    assert "analysis" in result
    assert "summary" in result
    assert result["scores"]["facial_expression"] == 85
    assert result["scores"]["eye_contact"] == 80
    assert result["scores"]["body_language"] == 75
    assert result["scores"]["overall_score"] == 80
    assert len(result["analysis"]["strengths"]) == 2
    assert len(result["analysis"]["suggestions"]) == 2
    
    # 验证讯飞星火大模型服务被正确调用
    visual_analyzer_with_llm.async_xunfei_service.chat_spark.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_with_llm_response_error(visual_analyzer_with_llm):
    """测试LLM响应错误的情况"""
    # 配置模拟的讯飞异步服务响应失败
    mock_error_response = {
        "status": "error",
        "error": "API请求失败",
        "content": None
    }
    visual_analyzer_with_llm.async_xunfei_service.chat_spark = AsyncMock(return_value=mock_error_response)
    
    # 调用方法并验证异常
    with pytest.raises(ValueError):
        await visual_analyzer_with_llm.analyze_with_llm(MOCK_VIDEO_FEATURES)


@pytest.mark.asyncio
async def test_analyze_with_llm_exception(visual_analyzer_with_llm):
    """测试LLM调用异常的情况"""
    # 配置模拟的讯飞异步服务抛出异常
    visual_analyzer_with_llm.async_xunfei_service.chat_spark = AsyncMock(side_effect=Exception("API调用失败"))
    
    # 调用方法并验证异常传播
    with pytest.raises(Exception):
        await visual_analyzer_with_llm.analyze_with_llm(MOCK_VIDEO_FEATURES)


@pytest.mark.asyncio
async def test_analyze_with_llm_integration(visual_analyzer_with_llm):
    """测试analyze方法中的LLM集成"""
    # 模拟extract_features方法
    visual_analyzer_with_llm.extract_features = AsyncMock(return_value=MOCK_VIDEO_FEATURES)
    
    # 模拟analyze_with_llm方法
    mock_llm_result = {
        "scores": {
            "facial_expression": 85,
            "eye_contact": 80,
            "body_language": 75,
            "overall_score": 80
        },
        "analysis": {
            "strengths": ["优势1", "优势2"],
            "suggestions": ["建议1", "建议2"]
        },
        "summary": "总结评价"
    }
    visual_analyzer_with_llm.analyze_with_llm = AsyncMock(return_value=mock_llm_result)
    
    # 调用analyze方法
    result = await visual_analyzer_with_llm.analyze(MOCK_VIDEO_PATH)
    
    # 验证结果
    assert "facial_expression" in result
    assert "eye_contact" in result
    assert "body_language" in result
    assert "overall_score" in result
    assert "detailed_scores" in result
    assert "analysis" in result
    assert result["facial_expression"]["score"] == 85
    assert result["eye_contact"]["score"] == 80
    assert result["body_language"]["score"] == 75
    assert result["overall_score"] == 80


@pytest.mark.asyncio
async def test_analyze_without_llm(visual_analyzer_no_llm):
    """测试不使用LLM的分析方法"""
    # 模拟特征提取
    visual_analyzer_no_llm.extract_features = AsyncMock(return_value=MOCK_VIDEO_FEATURES)
    
    # 模拟传统分析方法
    visual_analyzer_no_llm.analyze_facial_expression = AsyncMock(return_value={"score": 85, "feedback": "表情自然"})
    visual_analyzer_no_llm.analyze_eye_contact = AsyncMock(return_value={"score": 80, "feedback": "眼神接触良好"})
    visual_analyzer_no_llm.analyze_body_language = AsyncMock(return_value={"score": 75, "feedback": "肢体语言适度"})
    
    # 调用analyze方法
    result = await visual_analyzer_no_llm.analyze(MOCK_VIDEO_PATH)
    
    # 验证结果
    assert "facial_expression" in result
    assert "eye_contact" in result
    assert "body_language" in result
    assert "overall_score" in result
    assert result["facial_expression"]["score"] == 85
    assert result["eye_contact"]["score"] == 80
    assert result["body_language"]["score"] == 75
    assert result["overall_score"] == 80


def test_parse_llm_response_valid(visual_analyzer_with_llm):
    """测试解析有效的LLM响应"""
    # 准备测试数据
    mock_response = MOCK_LLM_RESPONSE["content"]
    
    # 调用方法
    result = visual_analyzer_with_llm._parse_llm_response(mock_response)
    
    # 验证结果
    assert "scores" in result
    assert "analysis" in result
    assert "summary" in result
    assert result["scores"]["facial_expression"] == 85
    assert result["scores"]["eye_contact"] == 80
    assert result["scores"]["body_language"] == 75
    assert result["scores"]["overall_score"] == 80
    assert len(result["analysis"]["strengths"]) == 2
    assert len(result["analysis"]["suggestions"]) == 2


def test_parse_llm_response_missing_overall_score(visual_analyzer_with_llm):
    """测试解析缺少overall_score的LLM响应"""
    # 准备测试数据 - 缺少overall_score
    mock_response = """
    {
        "scores": {
            "facial_expression": 85,
            "eye_contact": 80,
            "body_language": 75
        },
        "analysis": {
            "strengths": ["优势1", "优势2"],
            "suggestions": ["建议1", "建议2"]
        },
        "summary": "总结评价"
    }
    """
    
    # 调用方法
    result = visual_analyzer_with_llm._parse_llm_response(mock_response)
    
    # 验证结果 - 应该自动计算overall_score
    assert "scores" in result
    assert "overall_score" in result["scores"]
    assert result["scores"]["overall_score"] == 80  # (85+80+75)/3


def test_parse_llm_response_invalid_json(visual_analyzer_with_llm):
    """测试解析无效JSON的LLM响应"""
    # 准备测试数据 - 无效JSON
    mock_response = "这不是有效的JSON格式"
    
    # 调用方法
    result = visual_analyzer_with_llm._parse_llm_response(mock_response)
    
    # 验证结果 - 应该返回默认值
    assert "scores" in result
    assert "analysis" in result
    assert "error" in result
    assert result["scores"]["overall_score"] == 0
    assert "解析失败" in result["analysis"]["strengths"][0]


def test_build_visual_analysis_prompt(visual_analyzer_with_llm):
    """测试构建视觉分析提示词"""
    # 调用方法
    prompt = visual_analyzer_with_llm._build_visual_analysis_prompt(MOCK_VIDEO_FEATURES)
    
    # 验证结果
    assert "视频特征数据" in prompt
    assert "视频时长: 120.0 秒" in prompt
    assert "人脸检测率: 0.95" in prompt
    assert "微笑比例: 0.60" in prompt
    assert "眼神接触比例: 0.80" in prompt
    assert "姿势变化次数: 5 次" in prompt
    assert "手势使用次数: 12 次" in prompt
    assert "面部表情" in prompt
    assert "眼神接触" in prompt
    assert "肢体语言" in prompt
    assert "JSON格式" in prompt 