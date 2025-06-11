import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

from agent.src.analyzers.content.content_analyzer import ContentAnalyzer
from agent.src.core.system.config import AgentConfig
from agent.src.services.content_filter_service import ContentFilterService
from agent.src.services.openai_service import OpenAIService


@pytest.fixture
def content_analyzer():
    """创建内容分析器实例"""
    # 创建分析器实例
    analyzer = ContentAnalyzer()
    
    # 创建并设置模拟的OpenAI服务
    mock_openai_service = AsyncMock()
    analyzer.openai_service = mock_openai_service
    
    return analyzer


@pytest.fixture
def mock_content_filter():
    """创建模拟的内容过滤器"""
    mock_filter = MagicMock()
    mock_filter_result = MagicMock()
    mock_filter_result.filtered_text = "这是过滤后的文本，包含Python和团队协作"
    mock_filter_result.has_sensitive_content = False
    mock_filter.filter_text = MagicMock(return_value=mock_filter_result)
    
    # 设置静态方法返回模拟过滤器
    with patch('agent.src.services.content_filter_service.ContentFilterService.get_instance', return_value=mock_filter):
        yield mock_filter


@pytest.mark.asyncio
async def test_analyze_with_llm_success(content_analyzer, mock_content_filter):
    """测试LLM分析成功的情况"""
    # 准备测试数据
    mock_llm_response = {
        "status": "success",
        "content": """
        {
            "scores": {
                "professional_relevance": 85,
                "question_understanding": 90,
                "completeness": 75,
                "structure_logic": 80,
                "fluency": 85,
                "depth_detail": 70,
                "practical_experience": 75,
                "innovative_thinking": 65,
                "cultural_fit": 80,
                "overall_score": 78
            },
            "analysis": {
                "strengths": [
                    "展示了深厚的技术知识",
                    "结构清晰，逻辑严密",
                    "有具体的工作案例"
                ],
                "suggestions": [
                    "可以更加突出创新思维",
                    "增加更多专业术语",
                    "进一步展示团队协作能力"
                ]
            },
            "summary": "整体表现良好，专业能力突出，逻辑清晰"
        }
        """
    }
    
    # 配置模拟的OpenAI服务响应
    content_analyzer.openai_service.chat_completion = AsyncMock(return_value=mock_llm_response)
    
    # 调用方法
    result = await content_analyzer.analyze_async(
        "这是一段面试回答，展示了Python编程能力和团队协作经验", 
        params={"job_position": {"title": "软件工程师"}}
    )
    
    # 验证结果
    assert "relevance" in result
    assert "completeness" in result
    assert "structure" in result
    assert "overall_score" in result
    assert "detailed_scores" in result
    assert "analysis" in result
    
    # 验证多维度评分
    assert "professional_relevance" in result["detailed_scores"]
    assert "question_understanding" in result["detailed_scores"]
    assert "completeness" in result["detailed_scores"]
    assert "structure_logic" in result["detailed_scores"]
    
    # 验证分数准确传递
    assert result["detailed_scores"]["professional_relevance"] == 85
    assert result["overall_score"] == 78
    assert len(result["analysis"]["strengths"]) == 3
    assert len(result["analysis"]["suggestions"]) == 3


@pytest.mark.asyncio
async def test_analyze_with_llm_response_error(content_analyzer, mock_content_filter):
    """测试LLM响应错误的情况"""
    # 准备测试数据 - 响应状态错误
    mock_llm_response = {
        "status": "error",
        "error": "API请求失败",
        "content": None
    }
    
    # 配置模拟的OpenAI服务响应
    content_analyzer.openai_service.chat_completion = AsyncMock(return_value=mock_llm_response)
    
    # 调用方法
    result = await content_analyzer.analyze_async(
        "这是一段面试回答", 
        params={"job_position": {"title": "软件工程师"}}
    )
    
    # 验证结果 - 应该使用回退方法
    assert "relevance" in result
    assert "completeness" in result
    assert "structure" in result
    assert "overall_score" in result


@pytest.mark.asyncio
async def test_analyze_with_llm_json_parse_error(content_analyzer, mock_content_filter):
    """测试LLM返回结果JSON解析错误的情况"""
    # 准备测试数据 - 无效的JSON格式
    mock_llm_response = {
        "status": "success",
        "content": "这不是有效的JSON格式"
    }
    
    # 配置模拟的OpenAI服务响应
    content_analyzer.openai_service.chat_completion = AsyncMock(return_value=mock_llm_response)
    
    # 调用方法
    result = await content_analyzer.analyze_async(
        "这是一段面试回答", 
        params={"job_position": {"title": "软件工程师"}}
    )
    
    # 验证结果 - 应该使用回退方法
    assert "relevance" in result
    assert "completeness" in result
    assert "structure" in result
    assert "overall_score" in result


@pytest.mark.asyncio
async def test_analyze_with_llm_exception(content_analyzer, mock_content_filter):
    """测试LLM调用异常的情况"""
    # 配置模拟的OpenAI服务抛出异常
    content_analyzer.openai_service.chat_completion = AsyncMock(side_effect=Exception("API调用失败"))
    
    # 调用方法
    result = await content_analyzer.analyze_async(
        "这是一段面试回答", 
        params={"job_position": {"title": "软件工程师"}}
    )
    
    # 验证结果 - 应该使用回退方法
    assert "relevance" in result
    assert "completeness" in result
    assert "structure" in result
    assert "overall_score" in result


@pytest.mark.asyncio
async def test_analyze_with_llm_disabled(content_analyzer, mock_content_filter):
    """测试禁用LLM的情况"""
    # 禁用LLM
    content_analyzer.use_llm = False
    
    # 调用方法
    result = await content_analyzer.analyze_async(
        "这是一段面试回答", 
        params={"job_position": {"title": "软件工程师"}}
    )
    
    # 验证结果 - 应该使用规则评分
    assert "relevance" in result
    assert "completeness" in result
    assert "structure" in result
    assert "overall_score" in result
    assert "detailed_scores" in result
    assert content_analyzer.openai_service.chat_completion.call_count == 0


@pytest.mark.asyncio
async def test_parse_llm_response_valid(content_analyzer):
    """测试解析有效的LLM响应"""
    # 准备测试数据
    mock_response = """
    {
        "scores": {
            "professional_relevance": 85,
            "question_understanding": 90,
            "completeness": 75,
            "structure_logic": 80,
            "fluency": 85,
            "depth_detail": 70,
            "practical_experience": 75,
            "innovative_thinking": 65,
            "cultural_fit": 80,
            "overall_score": 78
        },
        "analysis": {
            "strengths": [
                "展示了深厚的技术知识",
                "结构清晰，逻辑严密",
                "有具体的工作案例"
            ],
            "suggestions": [
                "可以更加突出创新思维",
                "增加更多专业术语",
                "进一步展示团队协作能力"
            ]
        },
        "summary": "整体表现良好，专业能力突出，逻辑清晰"
    }
    """
    
    # 调用方法
    result = content_analyzer._parse_llm_response(mock_response)
    
    # 验证结果
    assert "scores" in result
    assert "analysis" in result
    assert "summary" in result
    assert result["scores"]["professional_relevance"] == 85
    assert result["scores"]["overall_score"] == 78
    assert len(result["analysis"]["strengths"]) == 3
    assert len(result["analysis"]["suggestions"]) == 3


@pytest.mark.asyncio
async def test_parse_llm_response_missing_overall_score(content_analyzer):
    """测试解析缺少overall_score的LLM响应"""
    # 准备测试数据 - 缺少overall_score
    mock_response = """
    {
        "scores": {
            "professional_relevance": 85,
            "question_understanding": 90,
            "completeness": 75,
            "structure_logic": 80,
            "fluency": 85
        },
        "analysis": {
            "strengths": ["优势1"],
            "suggestions": ["建议1"]
        }
    }
    """
    
    # 调用方法
    result = content_analyzer._parse_llm_response(mock_response)
    
    # 验证结果 - 应该自动计算overall_score
    assert "scores" in result
    assert "overall_score" in result["scores"]
    assert result["scores"]["overall_score"] > 0


@pytest.mark.asyncio
async def test_parse_llm_response_invalid_json(content_analyzer):
    """测试解析无效JSON的LLM响应"""
    # 准备测试数据 - 无效JSON
    mock_response = "这不是有效的JSON格式"
    
    # 调用方法
    result = content_analyzer._parse_llm_response(mock_response)
    
    # 验证结果 - 应该返回默认值
    assert "scores" in result
    assert "analysis" in result
    assert "error" in result
    assert result["scores"]["overall_score"] == 0
    assert "解析失败" in result["analysis"]["strengths"][0] 