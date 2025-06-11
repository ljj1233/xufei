import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

from agent.src.analyzers.content.content_analyzer import ContentAnalyzer
from agent.src.services.content_filter_service import ContentFilterService, FilterResult


# LLM响应样例
SUCCESSFUL_LLM_RESPONSE = {
    "status": "success",
    "content": """
    {
        "scores": {
            "professional_relevance": 85,
            "question_understanding": 90,
            "completeness": 78,
            "structure_logic": 82,
            "fluency": 88,
            "depth_detail": 75,
            "practical_experience": 80,
            "innovative_thinking": 70,
            "cultural_fit": 85,
            "overall_score": 81
        },
        "analysis": {
            "strengths": [
                "丰富的技术经验，特别是在Python开发和数据处理方面",
                "良好的团队协作意识和工程实践",
                "持续学习的态度和对新技术的热情"
            ],
            "suggestions": [
                "可以更详细地描述解决具体技术挑战的经历",
                "增加对项目成果的量化描述",
                "可以更多地展示软技能和沟通能力"
            ]
        },
        "summary": "整体表现优秀，技术背景扎实，具有团队协作精神和学习能力，适合软件工程师职位"
    }
    """
}

MALFORMED_JSON_RESPONSE = {
    "status": "success",
    "content": """
    这不是一个有效的JSON格式，缺少大括号和引号
    scores: {
        professional_relevance: 85,
        question_understanding: 90,
        ...
    """
}

MISSING_FIELDS_RESPONSE = {
    "status": "success",
    "content": """
    {
        "scores": {
            "professional_relevance": 85,
            "question_understanding": 90
            // 缺少其他字段和overall_score
        },
        "analysis": {
            "strengths": [
                "优势1"
            ]
            // 缺少suggestions
        }
    }
    """
}

ERROR_RESPONSE = {
    "status": "error",
    "error": "模拟API调用失败",
    "content": None
}

# 面试回答样例
SOFTWARE_ENGINEER_ANSWER = """
我有5年的Python开发经验，主要负责后端API开发和数据处理系统。在上一家公司，我负责设计并实现了一个高并发的日志处理系统，该系统每天能处理超过1亿条日志记录，使用了Kafka进行消息队列，Elasticsearch进行存储和检索。

我熟悉常见的设计模式，如单例模式、工厂模式、观察者模式等，并在实际项目中应用它们来提高代码质量和可维护性。我还有丰富的数据库经验，包括MySQL、MongoDB和Redis，能够设计高效的数据模型和优化查询性能。

在团队协作方面，我习惯使用Git进行版本控制，遵循CI/CD流程，确保代码质量。我相信良好的代码应该是自文档化的，同时我也注重编写单元测试和集成测试，保证代码的健壮性。

我对新技术充满热情，最近在学习容器编排技术如Kubernetes，以及微服务架构设计。我认为持续学习是保持技术竞争力的关键。
"""


@pytest.fixture
def content_analyzer():
    """创建内容分析器实例"""
    analyzer = ContentAnalyzer()
    
    # 创建并设置模拟的内容过滤器
    mock_filter = MagicMock()
    mock_filter.filter_text = MagicMock(return_value=FilterResult(
        filtered_text="这是过滤后的文本",
        has_sensitive_content=False,
        sensitive_word_count=0,
        sensitive_categories=[],
        highest_severity="low",
        detected_words={}
    ))
    
    # 设置内容过滤器
    analyzer.content_filter = mock_filter
    
    # 启用LLM评分
    analyzer.use_llm = True
    
    return analyzer


@pytest.mark.asyncio
async def test_analyze_with_llm_success(content_analyzer):
    """测试LLM分析成功的情况"""
    # 模拟OpenAI服务
    mock_openai_service = MagicMock()
    mock_openai_service.chat_completion = AsyncMock(return_value=SUCCESSFUL_LLM_RESPONSE)
    content_analyzer.openai_service = mock_openai_service
    
    # 准备测试数据
    transcript = SOFTWARE_ENGINEER_ANSWER
    job_position = {"title": "高级软件工程师"}
    
    # 执行分析
    result = await content_analyzer.analyze_with_llm(transcript, job_position)
    
    # 验证OpenAI服务被调用
    mock_openai_service.chat_completion.assert_called_once()
    
    # 验证结果格式
    assert "scores" in result
    assert "analysis" in result
    assert "summary" in result
    
    # 验证评分
    assert result["scores"]["professional_relevance"] == 85
    assert result["scores"]["question_understanding"] == 90
    assert result["scores"]["completeness"] == 78
    assert result["scores"]["overall_score"] == 81
    
    # 验证分析
    assert len(result["analysis"]["strengths"]) == 3
    assert len(result["analysis"]["suggestions"]) == 3
    assert "丰富的技术经验" in result["analysis"]["strengths"][0]
    
    # 验证摘要
    assert "整体表现优秀" in result["summary"]


@pytest.mark.asyncio
async def test_analyze_with_llm_api_error(content_analyzer):
    """测试LLM API调用错误的情况"""
    # 模拟OpenAI服务返回错误
    mock_openai_service = MagicMock()
    mock_openai_service.chat_completion = AsyncMock(return_value=ERROR_RESPONSE)
    content_analyzer.openai_service = mock_openai_service
    
    # 准备测试数据
    transcript = SOFTWARE_ENGINEER_ANSWER
    job_position = {"title": "高级软件工程师"}
    
    # 模拟_fallback_analysis方法
    content_analyzer._fallback_analysis = MagicMock(return_value={"fallback": True})
    
    # 执行分析
    with pytest.raises(Exception):
        await content_analyzer.analyze_with_llm(transcript, job_position)
    
    # 验证OpenAI服务被调用
    mock_openai_service.chat_completion.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_with_llm_malformed_json(content_analyzer):
    """测试LLM返回格式错误JSON的情况"""
    # 模拟OpenAI服务返回格式错误的JSON
    mock_openai_service = MagicMock()
    mock_openai_service.chat_completion = AsyncMock(return_value=MALFORMED_JSON_RESPONSE)
    content_analyzer.openai_service = mock_openai_service
    
    # 准备测试数据
    transcript = SOFTWARE_ENGINEER_ANSWER
    job_position = {"title": "高级软件工程师"}
    
    # 执行分析
    with pytest.raises(Exception):
        await content_analyzer.analyze_with_llm(transcript, job_position)
    
    # 验证OpenAI服务被调用
    mock_openai_service.chat_completion.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_with_llm_missing_fields(content_analyzer):
    """测试LLM返回缺少字段的情况"""
    # 模拟OpenAI服务返回缺少字段的响应
    mock_openai_service = MagicMock()
    mock_openai_service.chat_completion = AsyncMock(return_value=MISSING_FIELDS_RESPONSE)
    content_analyzer.openai_service = mock_openai_service
    
    # 准备测试数据
    transcript = SOFTWARE_ENGINEER_ANSWER
    job_position = {"title": "高级软件工程师"}
    
    # 执行分析
    with pytest.raises(Exception):
        await content_analyzer.analyze_with_llm(transcript, job_position)
    
    # 验证OpenAI服务被调用
    mock_openai_service.chat_completion.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_async_integration(content_analyzer):
    """测试analyze_async方法的集成"""
    # 模拟OpenAI服务
    mock_openai_service = MagicMock()
    mock_openai_service.chat_completion = AsyncMock(return_value=SUCCESSFUL_LLM_RESPONSE)
    content_analyzer.openai_service = mock_openai_service
    
    # 准备测试数据
    transcript = SOFTWARE_ENGINEER_ANSWER
    job_position = {"title": "高级软件工程师"}
    
    # 执行异步分析
    result = await content_analyzer.analyze_async(transcript, params={"job_position": job_position})
    
    # 验证OpenAI服务被调用
    mock_openai_service.chat_completion.assert_called_once()
    
    # 验证结果格式
    assert "overall_score" in result
    assert "detailed_scores" in result
    assert "analysis" in result
    
    # 验证详细评分
    assert "professional_relevance" in result["detailed_scores"]
    assert "completeness" in result["detailed_scores"]
    assert "structure_logic" in result["detailed_scores"]
    assert "fluency" in result["detailed_scores"]
    
    # 验证总评分
    assert result["overall_score"] == 81
    
    # 验证分析内容
    assert "strengths" in result["analysis"]
    assert "suggestions" in result["analysis"]
    assert len(result["analysis"]["strengths"]) == 3
    assert len(result["analysis"]["suggestions"]) == 3


@pytest.mark.asyncio
async def test_analyze_async_with_llm_disabled(content_analyzer):
    """测试禁用LLM时的异步分析"""
    # 禁用LLM
    content_analyzer.use_llm = False
    
    # 模拟OpenAI服务（不应该被调用）
    mock_openai_service = MagicMock()
    mock_openai_service.chat_completion = AsyncMock(return_value=SUCCESSFUL_LLM_RESPONSE)
    content_analyzer.openai_service = mock_openai_service
    
    # 准备测试数据
    transcript = SOFTWARE_ENGINEER_ANSWER
    job_position = {"title": "高级软件工程师"}
    
    # 执行异步分析
    result = await content_analyzer.analyze_async(transcript, params={"job_position": job_position})
    
    # 验证OpenAI服务没有被调用
    mock_openai_service.chat_completion.assert_not_called()
    
    # 验证结果格式
    assert "overall_score" in result
    assert "detailed_scores" in result
    assert "analysis" in result


@pytest.mark.asyncio
async def test_analyze_async_with_llm_exception(content_analyzer):
    """测试LLM异常时的回退策略"""
    # 模拟OpenAI服务抛出异常
    mock_openai_service = MagicMock()
    mock_openai_service.chat_completion = AsyncMock(side_effect=Exception("模拟API调用异常"))
    content_analyzer.openai_service = mock_openai_service
    
    # 准备测试数据
    transcript = SOFTWARE_ENGINEER_ANSWER
    job_position = {"title": "高级软件工程师"}
    
    # 执行异步分析
    result = await content_analyzer.analyze_async(transcript, params={"job_position": job_position})
    
    # 验证OpenAI服务被调用
    mock_openai_service.chat_completion.assert_called_once()
    
    # 验证结果格式（应该是回退策略的结果）
    assert "overall_score" in result
    assert "detailed_scores" in result
    assert "analysis" in result


def test_build_analysis_prompt(content_analyzer):
    """测试构建分析提示词"""
    # 准备测试数据
    transcript = "这是一段面试回答"
    job_position = {
        "title": "软件工程师",
        "requirements": ["Python开发", "系统设计", "团队协作"]
    }
    
    # 执行方法
    prompt = content_analyzer._build_analysis_prompt(transcript, job_position)
    
    # 验证提示词包含必要信息
    assert "面试回答内容" in prompt
    assert transcript in prompt
    assert "职位要求" in prompt
    assert job_position["title"] in prompt
    assert "Python开发" in prompt
    assert "系统设计" in prompt
    assert "团队协作" in prompt
    assert "专业技能相关性" in prompt
    assert "回答完整度" in prompt
    assert "结构逻辑" in prompt
    assert "JSON格式" in prompt


def test_parse_llm_response_success(content_analyzer):
    """测试成功解析LLM响应"""
    # 准备测试数据
    response_text = SUCCESSFUL_LLM_RESPONSE["content"]
    
    # 执行解析
    result = content_analyzer._parse_llm_response(response_text)
    
    # 验证解析结果
    assert "scores" in result
    assert "analysis" in result
    assert "summary" in result
    
    # 验证评分
    assert result["scores"]["professional_relevance"] == 85
    assert result["scores"]["question_understanding"] == 90
    assert result["scores"]["overall_score"] == 81
    
    # 验证分析
    assert len(result["analysis"]["strengths"]) == 3
    assert len(result["analysis"]["suggestions"]) == 3


def test_parse_llm_response_malformed_json(content_analyzer):
    """测试解析格式错误的JSON"""
    # 准备测试数据
    response_text = "这不是有效的JSON格式"
    
    # 执行解析
    result = content_analyzer._parse_llm_response(response_text)
    
    # 验证返回默认结构
    assert "scores" in result
    assert "analysis" in result
    assert "error" in result
    
    # 验证默认评分
    assert result["scores"]["overall_score"] == 0
    
    # 验证默认分析
    assert len(result["analysis"]["strengths"]) == 1
    assert "解析失败" in result["analysis"]["strengths"][0]


def test_parse_llm_response_missing_overall_score(content_analyzer):
    """测试解析缺少overall_score的响应"""
    # 准备测试数据
    response_text = """
    {
        "scores": {
            "professional_relevance": 85,
            "question_understanding": 90,
            "completeness": 78,
            "structure_logic": 82,
            "fluency": 88
            // 缺少overall_score
        },
        "analysis": {
            "strengths": ["优势1", "优势2"],
            "suggestions": ["建议1", "建议2"]
        },
        "summary": "总结"
    }
    """
    
    # 执行解析
    result = content_analyzer._parse_llm_response(response_text)
    
    # 验证自动计算overall_score
    assert "overall_score" in result["scores"]
    assert result["scores"]["overall_score"] > 0  # 应该计算平均分


def test_fallback_analysis(content_analyzer):
    """测试回退分析方法"""
    # 准备测试数据
    transcript = SOFTWARE_ENGINEER_ANSWER
    job_position = {"title": "高级软件工程师"}
    
    # 执行回退分析
    result = content_analyzer._fallback_analysis(transcript, job_position)
    
    # 验证结果格式
    assert "relevance" in result
    assert "completeness" in result
    assert "structure" in result
    assert "overall_score" in result
    assert "detailed_scores" in result
    assert "analysis" in result
    
    # 验证详细评分
    assert "professional_relevance" in result["detailed_scores"]
    assert "completeness" in result["detailed_scores"]
    assert "structure_logic" in result["detailed_scores"]
    assert "fluency" in result["detailed_scores"]
    
    # 验证分析内容
    assert "strengths" in result["analysis"]
    assert "suggestions" in result["analysis"]
    assert len(result["analysis"]["strengths"]) > 0
    assert len(result["analysis"]["suggestions"]) > 0 