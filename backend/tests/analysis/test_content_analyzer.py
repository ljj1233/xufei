import pytest
import asyncio
from unittest.mock import patch, MagicMock

from app.services.content_analyzer import ContentAnalyzer

@pytest.fixture
def content_analyzer():
    return ContentAnalyzer()

@pytest.mark.asyncio
async def test_analyze_content_mock_llm(content_analyzer):
    """测试内容分析器的模拟LLM模式"""
    # 准备测试数据
    answer_text = "这是一个测试回答，包含一些专业术语如算法、数据结构和系统设计。"
    question = "请介绍你的项目经验。"
    
    # 分析内容
    result = await content_analyzer.analyze_content(
        answer_text=answer_text,
        question=question
    )
    
    # 验证结果包含所有必要字段
    assert "relevance" in result
    assert "relevance_review" in result
    assert "depth_and_detail" in result
    assert "depth_review" in result
    assert "professionalism" in result
    assert "matched_keywords" in result
    assert "professional_style_review" in result
    
    # 验证专业关键词匹配
    assert len([kw for kw in ["算法", "数据结构", "系统设计"] if kw in result["matched_keywords"]]) > 0

@pytest.mark.asyncio
@patch('app.services.content_analyzer.ContentAnalyzer.llm_client')
async def test_analyze_content_with_llm_client(mock_llm_client, content_analyzer):
    """测试内容分析器与LLM客户端的集成"""
    # 设置模拟LLM响应
    mock_llm_response = """
    ```json
    {
        "relevance": 8.0,
        "relevance_review": "回答非常相关，直接回应了问题",
        "depth_and_detail": 7.0,
        "depth_review": "回答提供了一定深度，但可以更详细",
        "professionalism": 8.5,
        "matched_keywords": ["算法", "数据结构", "优化"],
        "professional_style_review": "展现了扎实的专业知识"
    }
    ```
    """
    
    # 设置模拟LLM客户端
    content_analyzer.llm_client = MagicMock()
    content_analyzer.llm_client.generate = AsyncMock(return_value=mock_llm_response)
    
    # 分析内容
    result = await content_analyzer.analyze_content(
        answer_text="我在项目中应用了高效的算法和数据结构，优化了系统性能。",
        question="请描述你的技术优势。",
        job_description="软件工程师，负责系统优化"
    )
    
    # 验证LLM调用
    content_analyzer.llm_client.generate.assert_called_once()
    
    # 验证结果解析
    assert result["relevance"] == 8.0
    assert "回答非常相关" in result["relevance_review"]
    assert len(result["matched_keywords"]) == 3

@pytest.mark.parametrize("answer_length,expected_depth_range", [
    ("短回答", (1, 5)),  # 短回答应该得到较低的深度分数
    ("这是一个中等长度的回答，包含一些内容但不是很详细。", (4, 7)),  # 中等长度回答
    ("这是一个较长的回答，包含了很多细节和专业术语。我们使用了算法优化、数据结构设计和系统架构来解决问题。项目中我们实现了高效的数据处理流程，提高了系统性能30%。我们还应用了机器学习技术预测用户行为，进一步提升了用户体验。", (6, 10))  # 长回答应该得到较高的深度分数
])
@pytest.mark.asyncio
async def test_analyze_content_depth_scores(content_analyzer, answer_length, expected_depth_range):
    """测试内容分析器对不同长度回答的深度评分"""
    # 分析内容
    result = await content_analyzer.analyze_content(
        answer_text=answer_length,
        question="请描述你的项目经验。"
    )
    
    # 验证深度分数在预期范围内
    min_depth, max_depth = expected_depth_range
    assert min_depth <= result["depth_and_detail"] <= max_depth

@pytest.mark.asyncio
async def test_analyze_content_error_handling(content_analyzer):
    """测试内容分析器的错误处理"""
    # 故意传入空回答
    result = await content_analyzer.analyze_content("", "问题")
    
    # 验证即使输入无效也能得到有效的结果
    assert "relevance" in result
    assert "depth_and_detail" in result
    assert "professionalism" in result
