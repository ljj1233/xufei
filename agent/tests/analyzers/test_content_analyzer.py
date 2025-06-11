import pytest
import json
import os
from unittest.mock import patch, MagicMock, AsyncMock

from agent.src.analyzers.content.content_analyzer import ContentAnalyzer
from agent.src.services.content_filter_service import ContentFilterService, FilterResult


# 真实场景的面试回答样例
SOFTWARE_ENGINEER_ANSWER = """
我有5年的Python开发经验，主要负责后端API开发和数据处理系统。在上一家公司，我负责设计并实现了一个高并发的日志处理系统，该系统每天能处理超过1亿条日志记录，使用了Kafka进行消息队列，Elasticsearch进行存储和检索。

我熟悉常见的设计模式，如单例模式、工厂模式、观察者模式等，并在实际项目中应用它们来提高代码质量和可维护性。我还有丰富的数据库经验，包括MySQL、MongoDB和Redis，能够设计高效的数据模型和优化查询性能。

在团队协作方面，我习惯使用Git进行版本控制，遵循CI/CD流程，确保代码质量。我相信良好的代码应该是自文档化的，同时我也注重编写单元测试和集成测试，保证代码的健壮性。

我对新技术充满热情，最近在学习容器编排技术如Kubernetes，以及微服务架构设计。我认为持续学习是保持技术竞争力的关键。
"""

PRODUCT_MANAGER_ANSWER = """
作为一名产品经理，我主导过多个从0到1的产品开发过程。我的工作方法是首先深入了解用户需求，通过用户访谈、问卷调查和数据分析来识别痛点和机会。

在我上一个项目中，我负责开发一款针对中小企业的CRM系统。我首先组织了20场用户访谈，绘制了用户旅程图，识别出用户在客户管理过程中的主要痛点是缺乏自动化工具和数据整合能力。基于这些发现，我制定了产品路线图，并与设计团队合作创建了低保真和高保真原型。

我特别重视数据驱动的决策过程。在产品发布后，我建立了关键指标监控仪表板，包括用户活跃度、功能使用频率和转化率等。通过A/B测试，我们优化了注册流程，将转化率提高了25%。

我认为一个好的产品经理需要平衡用户需求、业务目标和技术可行性。我善于与跨职能团队合作，包括工程师、设计师和市场人员，确保产品按时交付并满足质量标准。
"""

SENSITIVE_ANSWER = """
我认为这个职位很适合我，因为我有丰富的经验。虽然我上一家公司的老板是个政治立场极端的人，经常说脏话1和侮辱性词汇，但我还是学到了很多。

我擅长处理复杂问题，不像那些种族歧视词汇的人那样思考问题。我相信我的能力远超其他应聘者，那些人可能都是不文明用语。

如果贵公司雇佣我，我保证不会像我前同事那样传播误导性表述或者虚假宣传词。我会用我的专业知识为公司创造价值。
"""

@pytest.fixture
def real_content_filter_service():
    """创建真实的内容过滤服务实例"""
    return ContentFilterService()

@pytest.fixture
def content_analyzer_with_real_filter(real_content_filter_service):
    """创建使用真实过滤器的内容分析器"""
    analyzer = ContentAnalyzer()
    
    # 使用真实的过滤服务
    with patch('agent.src.services.content_filter_service.ContentFilterService.get_instance', 
               return_value=real_content_filter_service):
        analyzer.content_filter = real_content_filter_service
        yield analyzer

@pytest.fixture
def content_analyzer_with_mock_filter():
    """创建使用模拟过滤器的内容分析器"""
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
    
    # 直接设置content_filter属性
    analyzer.content_filter = mock_filter
    
    return analyzer

@pytest.fixture
def mock_openai_service():
    """模拟OpenAI服务"""
    mock_service = MagicMock()
    mock_service.chat_completion = AsyncMock(return_value={
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
    })
    return mock_service


# 测试真实场景的内容分析
def test_analyze_software_engineer_answer(content_analyzer_with_real_filter):
    """测试软件工程师职位的面试回答分析"""
    # 准备测试数据
    transcript = SOFTWARE_ENGINEER_ANSWER
    job_position = {
        "title": "高级软件工程师", 
        "requirements": ["Python开发经验", "后端系统设计能力", "数据库优化", "团队协作"]
    }
    
    # 执行分析
    features = content_analyzer_with_real_filter.extract_features(transcript)
    result = content_analyzer_with_real_filter.analyze(features, params={"job_position": job_position})
    
    # 验证结果
    assert "relevance" in result
    assert "completeness" in result
    assert "structure" in result
    assert "overall_score" in result
    
    # 验证相关性评分较高（因为回答与职位要求高度相关）
    assert result["relevance"]["score"] >= 75
    
    # 验证完整性评分合理
    assert 60 <= result["completeness"]["score"] <= 100
    
    # 验证结构评分合理
    assert 60 <= result["structure"]["score"] <= 100
    
    # 验证总评分在合理范围内
    assert 60 <= result["overall_score"] <= 100


def test_analyze_product_manager_answer(content_analyzer_with_real_filter):
    """测试产品经理职位的面试回答分析"""
    # 准备测试数据
    transcript = PRODUCT_MANAGER_ANSWER
    job_position = {
        "title": "产品经理", 
        "requirements": ["产品规划能力", "用户研究经验", "数据分析能力", "跨团队协作"]
    }
    
    # 执行分析
    features = content_analyzer_with_real_filter.extract_features(transcript)
    result = content_analyzer_with_real_filter.analyze(features, params={"job_position": job_position})
    
    # 验证结果
    assert "relevance" in result
    assert "completeness" in result
    assert "structure" in result
    assert "overall_score" in result
    
    # 验证相关性评分较高（因为回答与职位要求高度相关）
    assert result["relevance"]["score"] >= 75
    
    # 验证完整性评分合理
    assert 60 <= result["completeness"]["score"] <= 100
    
    # 验证结构评分合理
    assert 60 <= result["structure"]["score"] <= 100
    
    # 验证总评分在合理范围内
    assert 60 <= result["overall_score"] <= 100


def test_analyze_with_sensitive_content(content_analyzer_with_real_filter):
    """测试包含敏感内容的面试回答分析"""
    # 准备测试数据
    transcript = SENSITIVE_ANSWER
    job_position = {"title": "软件工程师"}
    
    # 执行分析
    features = content_analyzer_with_real_filter.extract_features(transcript)
    result = content_analyzer_with_real_filter.analyze(features, params={"job_position": job_position})
    
    # 验证结果
    assert "relevance" in result
    assert "completeness" in result
    assert "structure" in result
    assert "overall_score" in result
    
    # 验证包含敏感内容提示
    assert "sensitive_content" in result
    assert result["sensitive_content"]["has_sensitive_content"] is True
    assert len(result["sensitive_content"]["categories"]) > 0
    
    # 验证总评分受到敏感内容的影响（应该有所降低）
    assert result["overall_score"] < 80


def test_content_filter_real_functionality(real_content_filter_service):
    """测试内容过滤服务的实际功能"""
    # 准备测试数据
    test_text = "这是一段包含政治立场、脏话1和种族歧视词汇的文本，还包含了一些误导性表述。"
    
    # 执行过滤
    result = real_content_filter_service.filter_text(test_text)
    
    # 验证结果
    assert result.has_sensitive_content is True
    assert result.sensitive_word_count >= 3  # 至少应该检测到3个敏感词
    assert len(result.sensitive_categories) >= 2  # 至少应该检测到2个敏感类别
    assert "***" in result.filtered_text  # 文本中的敏感词应该被替换为星号
    
    # 验证检测到的敏感词类别
    detected_categories = set(result.sensitive_categories)
    expected_categories = {
        ContentFilterService.CATEGORY_POLITICAL,
        ContentFilterService.CATEGORY_INAPPROPRIATE,
        ContentFilterService.CATEGORY_DISCRIMINATION,
        ContentFilterService.CATEGORY_FRAUD
    }
    assert len(detected_categories.intersection(expected_categories)) > 0


def test_content_filter_with_clean_text(real_content_filter_service):
    """测试内容过滤服务处理无敏感内容的文本"""
    # 准备测试数据
    clean_text = "这是一段正常的面试回答，描述了我的技术经验和团队协作能力。"
    
    # 执行过滤
    result = real_content_filter_service.filter_text(clean_text)
    
    # 验证结果
    assert result.has_sensitive_content is False
    assert result.sensitive_word_count == 0
    assert len(result.sensitive_categories) == 0
    assert result.filtered_text == clean_text  # 文本应该保持不变
    assert result.highest_severity == "low"


def test_extract_features_with_real_text(content_analyzer_with_real_filter):
    """测试特征提取功能"""
    # 准备测试数据
    transcript = SOFTWARE_ENGINEER_ANSWER
    
    # 执行特征提取
    features = content_analyzer_with_real_filter.extract_features(transcript)
    
    # 验证结果
    assert "text_length" in features
    assert features["text_length"] > 0
    
    assert "word_count" in features
    assert features["word_count"] > 0
    
    assert "sentence_count" in features
    assert features["sentence_count"] > 0
    
    assert "keywords" in features
    assert len(features["keywords"]) > 0
    
    # 验证关键词提取
    expected_keywords = ["Python", "开发", "数据", "系统", "设计"]
    found_keywords = [kw for kw in expected_keywords if any(kw in k for k in features["keywords"])]
    assert len(found_keywords) > 0


@pytest.mark.asyncio
async def test_analyze_async_with_real_llm(content_analyzer_with_real_filter, mock_openai_service):
    """测试使用LLM进行异步分析"""
    # 设置使用LLM
    content_analyzer_with_real_filter.use_llm = True
    content_analyzer_with_real_filter.openai_service = mock_openai_service
    
    # 准备测试数据
    transcript = SOFTWARE_ENGINEER_ANSWER
    job_position = {"title": "高级软件工程师"}
    
    # 执行异步分析
    result = await content_analyzer_with_real_filter.analyze_async(
        transcript, 
        params={"job_position": job_position}
    )
    
    # 验证LLM服务被调用
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
    
    # 验证分析内容
    assert "strengths" in result["analysis"]
    assert "suggestions" in result["analysis"]
    assert len(result["analysis"]["strengths"]) >= 3
    assert len(result["analysis"]["suggestions"]) >= 3


@pytest.mark.asyncio
async def test_analyze_async_with_llm_failure_fallback(content_analyzer_with_real_filter):
    """测试LLM失败时的回退策略"""
    # 设置使用LLM
    content_analyzer_with_real_filter.use_llm = True
    
    # 模拟LLM服务失败
    mock_failed_service = MagicMock()
    mock_failed_service.chat_completion = AsyncMock(side_effect=Exception("模拟LLM调用失败"))
    content_analyzer_with_real_filter.openai_service = mock_failed_service
    
    # 准备测试数据
    transcript = SOFTWARE_ENGINEER_ANSWER
    job_position = {"title": "高级软件工程师"}
    
    # 执行异步分析
    result = await content_analyzer_with_real_filter.analyze_async(
        transcript, 
        params={"job_position": job_position}
    )
    
    # 验证回退到基于规则的评分
    assert "overall_score" in result
    assert "detailed_scores" in result
    assert "analysis" in result
    
    # 验证详细评分
    assert "professional_relevance" in result["detailed_scores"]
    assert "completeness" in result["detailed_scores"]
    assert "structure_logic" in result["detailed_scores"]
    
    # 验证生成了优势和建议
    assert len(result["analysis"]["strengths"]) > 0
    assert len(result["analysis"]["suggestions"]) > 0


def test_analyze_with_different_job_positions(content_analyzer_with_real_filter):
    """测试不同职位的内容分析"""
    # 准备测试数据
    transcript = SOFTWARE_ENGINEER_ANSWER
    
    # 测试不同职位
    job_positions = [
        {"title": "软件工程师", "requirements": ["Python开发", "系统设计"]},
        {"title": "数据科学家", "requirements": ["数据分析", "机器学习"]},
        {"title": "前端开发", "requirements": ["JavaScript", "UI设计"]},
        None  # 测试None职位
    ]
    
    features = content_analyzer_with_real_filter.extract_features(transcript)
    
    for job_position in job_positions:
        # 执行分析
        result = content_analyzer_with_real_filter.analyze(features, params={"job_position": job_position})
        
        # 验证结果
        assert "relevance" in result
        assert "completeness" in result
        assert "structure" in result
        assert "overall_score" in result
        
        # 验证职位相关性评分
        if job_position and "软件工程师" in job_position["title"]:
            # 软件工程师职位应该有较高的相关性
            assert result["relevance"]["score"] >= 70
        elif job_position and "数据科学家" in job_position["title"]:
            # 数据科学家职位应该有中等相关性（因为回答中提到了数据处理）
            assert result["relevance"]["score"] >= 50
        elif job_position and "前端开发" in job_position["title"]:
            # 前端开发职位应该有较低的相关性
            assert result["relevance"]["score"] < 70


def test_analyze_with_empty_transcript(content_analyzer_with_real_filter):
    """测试空文本的分析"""
    # 准备测试数据
    transcript = ""
    job_position = {"title": "软件工程师"}
    
    # 执行分析
    features = content_analyzer_with_real_filter.extract_features(transcript)
    result = content_analyzer_with_real_filter.analyze(features, params={"job_position": job_position})
    
    # 验证结果仍然包含所有必要字段
    assert "relevance" in result
    assert "completeness" in result
    assert "structure" in result
    assert "overall_score" in result
    
    # 验证空文本的评分应该较低
    assert result["overall_score"] <= 50
    assert result["completeness"]["score"] <= 30  # 完整性应该很低


def test_analyze_with_very_short_answer(content_analyzer_with_real_filter):
    """测试非常简短回答的分析"""
    # 准备测试数据
    transcript = "我有五年Python经验。"
    job_position = {"title": "高级软件工程师", "requirements": ["Python开发经验", "系统设计能力"]}
    
    # 执行分析
    features = content_analyzer_with_real_filter.extract_features(transcript)
    result = content_analyzer_with_real_filter.analyze(features, params={"job_position": job_position})
    
    # 验证结果
    assert "relevance" in result
    assert "completeness" in result
    assert "structure" in result
    assert "overall_score" in result
    
    # 验证相关性可能较高（因为提到了Python）
    assert result["relevance"]["score"] >= 50
    
    # 但完整性和结构应该较低
    assert result["completeness"]["score"] <= 50
    assert result["structure"]["score"] <= 60
    
    # 总评分应该不高
    assert result["overall_score"] <= 60 