import pytest
from unittest.mock import patch, MagicMock

from agent.src.analyzers.content.content_analyzer import ContentAnalyzer
from agent.tests.conftest import MockContentFilterService


@pytest.fixture
def content_analyzer():
    """创建内容分析器实例"""
    # 创建分析器实例
    analyzer = ContentAnalyzer()
    
    # 创建并设置模拟的内容过滤器
    mock_filter = MagicMock()
    mock_filter.filter_text = MagicMock(return_value=MagicMock(
        filtered_text="这是过滤后的文本",
        has_sensitive_content=False,
        sensitive_word_count=0,
        sensitive_categories=[],
        highest_severity="low"
    ))
    
    # 直接设置content_filter属性
    analyzer.content_filter = mock_filter
    
    return analyzer


def test_analyze_with_valid_input(content_analyzer):
    """测试有效输入的内容分析"""
    # 准备测试数据
    transcript = "这是一段面试回答的文本，包含了对问题的详细解答。"
    job_position = {"title": "软件工程师", "requirements": ["编程能力", "沟通能力"]}
    
    # 执行分析
    features = content_analyzer.extract_features(transcript)
    result = content_analyzer.analyze(features, params={"job_position": job_position})
    
    # 验证结果
    assert "relevance" in result
    assert "structure" in result or "depth_and_detail" in result
    assert "overall_score" in result


def test_analyze_with_sensitive_content(content_analyzer):
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
    features = content_analyzer.extract_features(transcript)
    result = content_analyzer.analyze(features, params={"job_position": job_position})
    
    # 验证结果
    assert "relevance" in result
    assert "overall_score" in result


def test_analyze_with_empty_transcript(content_analyzer):
    """测试空文本的分析"""
    # 准备测试数据
    transcript = ""
    job_position = {"title": "软件工程师"}
    
    # 执行分析
    features = content_analyzer.extract_features(transcript)
    result = content_analyzer.analyze(features, params={"job_position": job_position})
    
    # 验证结果仍然包含所有必要字段
    assert "relevance" in result
    assert "overall_score" in result


def test_analyze_with_none_transcript(content_analyzer):
    """测试None文本的分析"""
    # 准备测试数据
    transcript = None
    job_position = {"title": "软件工程师"}
    
    # 执行分析
    features = content_analyzer.extract_features(transcript) if transcript is not None else {}
    result = content_analyzer.analyze(features, params={"job_position": job_position})
    
    # 验证结果仍然包含所有必要字段
    assert "relevance" in result
    assert "overall_score" in result
    
    # 验证敏感内容过滤服务没有被调用（因为文本是None）
    content_analyzer.content_filter.filter_text.assert_not_called()


def test_analyze_with_different_job_positions(content_analyzer):
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
    
    features = content_analyzer.extract_features(transcript)
    
    for job_position in job_positions:
        # 执行分析
        result = content_analyzer.analyze(features, params={"job_position": job_position})
        
        # 验证结果
        assert "relevance" in result
        assert "overall_score" in result
        
        # 重置mock
        content_analyzer.content_filter.filter_text.reset_mock()


def test_analyze_with_filter_exception(content_analyzer):
    """测试过滤服务异常情况"""
    # 准备测试数据
    transcript = "这是一段面试回答的文本"
    job_position = {"title": "软件工程师"}
    
    # 配置过滤方法抛出异常
    content_analyzer.content_filter.filter_text.side_effect = Exception("过滤服务异常")
    
    # 执行分析
    features = content_analyzer.extract_features(transcript)
    result = content_analyzer.analyze(features, params={"job_position": job_position})
    
    # 验证结果仍然包含所有必要字段
    assert "relevance" in result
    assert "overall_score" in result 