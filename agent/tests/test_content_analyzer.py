import pytest
import asyncio
from unittest.mock import patch, MagicMock

from agent.analyzers.content_analyzer import ContentAnalyzer
from agent.tests.conftest import MockContentFilterService


@pytest.fixture
def content_analyzer():
    """创建内容分析器实例"""
    with patch("agent.analyzers.content_analyzer.ContentFilterService", MockContentFilterService):
        analyzer = ContentAnalyzer()
        
        # 确保过滤服务被正确初始化
        assert analyzer.content_filter is not None
        
        yield analyzer


@pytest.mark.asyncio
async def test_analyze_with_valid_input(content_analyzer):
    """测试有效输入的内容分析"""
    # 准备测试数据
    transcript = "这是一段面试回答的文本，包含了对问题的详细解答。"
    job_position = {"title": "软件工程师", "requirements": ["编程能力", "沟通能力"]}
    
    # 执行分析
    result = await content_analyzer.analyze(transcript, job_position)
    
    # 验证结果
    assert "relevance" in result
    assert "logic" in result
    assert "professionalism" in result
    assert "content_quality" in result
    assert "sensitive_content" in result
    
    # 验证敏感内容过滤服务是否被调用
    content_analyzer.content_filter.filter_text.assert_called_once_with(transcript)


@pytest.mark.asyncio
async def test_analyze_with_sensitive_content(content_analyzer):
    """测试包含敏感内容的分析"""
    # 准备测试数据
    transcript = "这是包含敏感内容的文本"
    job_position = {"title": "软件工程师"}
    
    # 配置过滤方法返回敏感内容
    content_analyzer.content_filter.filter_text.return_value = MagicMock(
        filtered_text="这是过滤后的文本",
        has_sensitive_content=True,
        sensitive_word_count=2,
        sensitive_categories=["政治", "不当言论"],
        highest_severity="high"
    )
    
    # 执行分析
    result = await content_analyzer.analyze(transcript, job_position)
    
    # 验证敏感内容标记
    assert result["sensitive_content"]["has_sensitive_content"] is True
    assert result["sensitive_content"]["sensitive_word_count"] == 2
    assert "政治" in result["sensitive_content"]["sensitive_categories"]
    assert result["sensitive_content"]["highest_severity"] == "high"


@pytest.mark.asyncio
async def test_analyze_with_empty_transcript(content_analyzer):
    """测试空文本的分析"""
    # 准备测试数据
    transcript = ""
    job_position = {"title": "软件工程师"}
    
    # 执行分析
    result = await content_analyzer.analyze(transcript, job_position)
    
    # 验证结果仍然包含所有必要字段
    assert "relevance" in result
    assert "logic" in result
    assert "professionalism" in result
    assert "content_quality" in result
    assert "sensitive_content" in result
    
    # 验证敏感内容过滤服务是否被调用（即使是空文本）
    content_analyzer.content_filter.filter_text.assert_called_once_with(transcript)


@pytest.mark.asyncio
async def test_analyze_with_none_transcript(content_analyzer):
    """测试None文本的分析"""
    # 准备测试数据
    transcript = None
    job_position = {"title": "软件工程师"}
    
    # 执行分析
    result = await content_analyzer.analyze(transcript, job_position)
    
    # 验证结果仍然包含所有必要字段
    assert "relevance" in result
    assert "logic" in result
    assert "professionalism" in result
    assert "content_quality" in result
    assert "sensitive_content" in result
    
    # 验证敏感内容过滤服务没有被调用（因为文本是None）
    content_analyzer.content_filter.filter_text.assert_not_called()


@pytest.mark.asyncio
async def test_analyze_with_different_job_positions(content_analyzer):
    """测试不同职位的内容分析"""
    # 准备测试数据
    transcript = "这是一段关于编程和技术的回答"
    
    # 测试不同职位
    job_positions = [
        {"title": "软件工程师", "requirements": ["编程能力", "算法能力"]},
        {"title": "产品经理", "requirements": ["沟通能力", "产品思维"]},
        {"title": "UI设计师", "requirements": ["设计能力", "审美能力"]},
        None  # 测试None职位
    ]
    
    for job_position in job_positions:
        # 执行分析
        result = await content_analyzer.analyze(transcript, job_position)
        
        # 验证结果
        assert "relevance" in result
        assert "logic" in result
        assert "professionalism" in result
        assert "content_quality" in result
        
        # 重置mock
        content_analyzer.content_filter.filter_text.reset_mock()


@pytest.mark.asyncio
async def test_analyze_with_filter_exception(content_analyzer):
    """测试过滤服务异常情况"""
    # 准备测试数据
    transcript = "这是一段面试回答的文本"
    job_position = {"title": "软件工程师"}
    
    # 配置过滤方法抛出异常
    content_analyzer.content_filter.filter_text.side_effect = Exception("过滤服务异常")
    
    # 执行分析
    result = await content_analyzer.analyze(transcript, job_position)
    
    # 验证结果仍然包含所有必要字段
    assert "relevance" in result
    assert "logic" in result
    assert "professionalism" in result
    assert "content_quality" in result
    assert "sensitive_content" in result
    
    # 验证敏感内容标记为无敏感内容（因为过滤失败）
    assert result["sensitive_content"]["has_sensitive_content"] is False 