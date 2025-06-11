# 导入所需的库
import pytest  # 用于编写测试用例的框架
import json  # Python 内置的 JSON 库，此处代码并未使用，可能是预留功能
from unittest.mock import patch, MagicMock  # 用于模拟（mock）对象和函数，方便进行单元测试

# 从 agent.src.services.content_filter_service 模块导入内容过滤服务类和结果类
from agent.src.services.content_filter_service import ContentFilterService, FilterResult


# --- 测试文本样例 ---
# 定义一些用于测试的文本字符串

# 正常的、不包含敏感内容的文本
CLEAN_TEXT = "这是一段正常的面试回答，描述了我的技术经验和团队协作能力。"

# 包含政治敏感词的文本
POLITICAL_TEXT = "我认为政治立场和政治事件不应该在面试中讨论，这可能会引起争议。"

# 包含不当言论（如脏话）的文本
INAPPROPRIATE_TEXT = "我上一家公司的同事经常说脏话1和脏话2，工作环境很不好。"

# 包含歧视性言论的文本
DISCRIMINATION_TEXT = "有些人会用种族歧视词汇和性别歧视词汇，这是不对的。"

# 包含多种类型敏感词的混合文本
MIXED_SENSITIVE_TEXT = """
我在上一家公司遇到了一些问题。老板经常表达政治立场，有些同事会说脏话1和侮辱性词汇。
我觉得这种环境对工作效率有影响，特别是当有人使用种族歧视词汇的时候。
我希望新公司不会有这样的问题，我不喜欢听到不文明用语和误导性表述。
"""

# --- 测试装置 (Test Fixture) ---

@pytest.fixture
def content_filter_service():
    """
    这是一个 pytest 的 fixture（测试装置）。
    它会在每个使用它的测试函数运行前被调用，创建一个新的 ContentFilterService 实例。
    这样做可以确保每个测试用例都在一个干净、独立的环境中运行，避免测试间的相互干扰。
    """
    return ContentFilterService()


# --- 测试用例 ---

def test_filter_clean_text(content_filter_service):
    """
    测试用例：测试过滤无敏感内容的文本。
    目的：验证服务能够正确处理正常的、干净的文本。
    """
    # 步骤1: 执行过滤操作
    result = content_filter_service.filter_text(CLEAN_TEXT)
    
    # 步骤2: 验证过滤结果
    assert result.has_sensitive_content is False  # 断言：不应检测到敏感内容
    assert result.sensitive_word_count == 0  # 断言：敏感词数量应为 0
    assert len(result.sensitive_categories) == 0  # 断言：敏感类别列表应为空
    assert result.filtered_text == CLEAN_TEXT  # 断言：过滤后的文本应与原文保持一致
    assert result.highest_severity == "low"  # 断言：最高敏感级别应为 "low"
    assert len(result.detected_words) == 0  # 断言：检测到的敏感词字典应为空


def test_filter_political_text(content_filter_service):
    """
    测试用例：测试过滤包含政治敏感内容的文本。
    目的：验证服务能正确识别政治类敏感词并进行处理。
    """
    # 步骤1: 执行过滤操作
    result = content_filter_service.filter_text(POLITICAL_TEXT)
    
    # 步骤2: 验证过滤结果
    assert result.has_sensitive_content is True  # 断言：应检测到敏感内容
    assert result.sensitive_word_count >= 2  # 断言：至少应检测到 "政治立场" 和 "政治事件" 两个敏感词
    assert ContentFilterService.CATEGORY_POLITICAL in result.sensitive_categories  # 断言：敏感类别中应包含 "political"
    
    # 验证敏感词是否已被替换（通常替换为 '*'）
    assert "政治立场" not in result.filtered_text
    assert "政治事件" not in result.filtered_text
    
    # 验证检测到的敏感词详情
    assert ContentFilterService.CATEGORY_POLITICAL in result.detected_words  # 断言：检测到的词字典中应有 "political" 这个键
    assert len(result.detected_words[ContentFilterService.CATEGORY_POLITICAL]) >= 2 # 断言：在 "political" 类别下至少检测到两个词


def test_filter_inappropriate_text(content_filter_service):
    """
    测试用例：测试过滤包含不当言论的文本。
    目的：验证服务能正确识别不当言论并进行处理。
    """
    # 步骤1: 执行过滤操作
    result = content_filter_service.filter_text(INAPPROPRIATE_TEXT)
    
    # 步骤2: 验证过滤结果
    assert result.has_sensitive_content is True  # 断言：应检测到敏感内容
    assert result.sensitive_word_count >= 2  # 断言：至少应检测到 "脏话1" 和 "脏话2"
    assert ContentFilterService.CATEGORY_INAPPROPRIATE in result.sensitive_categories # 断言：敏感类别中应包含 "inappropriate"
    
    # 验证敏感词是否已被替换
    assert "脏话1" not in result.filtered_text
    assert "脏话2" not in result.filtered_text
    
    # 验证检测到的敏感词详情
    assert ContentFilterService.CATEGORY_INAPPROPRIATE in result.detected_words # 断言：检测到的词字典中应有 "inappropriate" 这个键
    assert len(result.detected_words[ContentFilterService.CATEGORY_INAPPROPRIATE]) >= 2 # 断言：在该类别下至少检测到两个词


def test_filter_discrimination_text(content_filter_service):
    """
    测试用例：测试过滤包含歧视性语言的文本。
    目的：验证服务能正确识别歧视性言论并进行处理。
    """
    # 步骤1: 执行过滤操作
    result = content_filter_service.filter_text(DISCRIMINATION_TEXT)
    
    # 步骤2: 验证过滤结果
    assert result.has_sensitive_content is True  # 断言：应检测到敏感内容
    assert result.sensitive_word_count >= 2  # 断言：至少应检测到 "种族歧视词汇" 和 "性别歧视词汇"
    assert ContentFilterService.CATEGORY_DISCRIMINATION in result.sensitive_categories # 断言：敏感类别中应包含 "discrimination"
    
    # 验证敏感词是否已被替换
    assert "种族歧视词汇" not in result.filtered_text
    assert "性别歧视词汇" not in result.filtered_text
    
    # 验证检测到的敏感词详情
    assert ContentFilterService.CATEGORY_DISCRIMINATION in result.detected_words # 断言：检测到的词字典中应有 "discrimination" 这个键
    assert len(result.detected_words[ContentFilterService.CATEGORY_DISCRIMINATION]) >= 2 # 断言：在该类别下至少检测到两个词


def test_filter_mixed_sensitive_text(content_filter_service):
    """
    测试用例：测试过滤包含多种类型敏感内容的混合文本。
    目的：验证服务能同时处理来自不同类别的多个敏感词。
    """
    # 步骤1: 执行过滤操作
    result = content_filter_service.filter_text(MIXED_SENSITIVE_TEXT)
    
    # 步骤2: 验证过滤结果
    assert result.has_sensitive_content is True  # 断言：应检测到敏感内容
    assert result.sensitive_word_count >= 5  # 断言：应检测到多个敏感词
    assert len(result.sensitive_categories) >= 3  # 断言：应检测到至少3个不同的敏感类别
    
    # 验证多个敏感词都已被替换
    assert "政治立场" not in result.filtered_text
    assert "脏话1" not in result.filtered_text
    assert "侮辱性词汇" not in result.filtered_text
    assert "种族歧视词汇" not in result.filtered_text
    assert "不文明用语" not in result.filtered_text
    
    # 验证检测到的敏感词类别是否符合预期
    expected_categories = {
        ContentFilterService.CATEGORY_POLITICAL,
        ContentFilterService.CATEGORY_INAPPROPRIATE,
        ContentFilterService.CATEGORY_DISCRIMINATION,
        ContentFilterService.CATEGORY_FRAUD
    }
    detected_categories = set(result.sensitive_categories)
    # 计算检测到的类别与预期类别的交集，判断是否检测出了大部分预期的类别
    assert len(detected_categories.intersection(expected_categories)) >= 3


def test_filter_empty_text(content_filter_service):
    """
    测试用例：测试过滤空字符串。
    目的：验证服务在处理边缘情况（空输入）时不会出错。
    """
    # 步骤1: 执行过滤操作
    result = content_filter_service.filter_text("")
    
    # 步骤2: 验证过滤结果，应与处理干净文本的结果类似
    assert result.has_sensitive_content is False
    assert result.sensitive_word_count == 0
    assert len(result.sensitive_categories) == 0
    assert result.filtered_text == ""
    assert result.highest_severity == "low"


def test_filter_none_text(content_filter_service):
    """
    测试用例：测试过滤 None 输入。
    目的：验证服务在处理边缘情况（None 输入）时能优雅地处理，而不是抛出异常。
    """
    # 步骤1: 执行过滤操作
    result = content_filter_service.filter_text(None)
    
    # 步骤2: 验证过滤结果，应返回一个表示无内容的默认结果
    assert result.has_sensitive_content is False
    assert result.sensitive_word_count == 0
    assert len(result.sensitive_categories) == 0
    assert result.filtered_text == ""
    assert result.highest_severity == "low"


def test_severity_level(content_filter_service):
    """
    测试用例：测试敏感级别判断逻辑。
    目的：验证服务能根据不同敏感词的预设级别，正确判断出文本的最高敏感级别。
    """
    # 准备不同敏感级别的测试数据
    text_with_high_severity = "这段文本包含侮辱性词汇和种族歧视词汇" # 假设这两个词是 high 级别
    text_with_medium_severity = "这段文本包含脏话1和政治倾向" # 假设这两个词是 medium 级别
    text_with_low_severity = "这段文本包含不文明用语和误导性表述" # 假设这两个词是 low 级别
    
    # 执行过滤
    high_result = content_filter_service.filter_text(text_with_high_severity)
    medium_result = content_filter_service.filter_text(text_with_medium_severity)
    low_result = content_filter_service.filter_text(text_with_low_severity)
    
    # 验证结果
    assert high_result.highest_severity == "high"
    assert medium_result.highest_severity == "medium"
    assert low_result.highest_severity == "low"


def test_add_custom_sensitive_words(content_filter_service):
    """
    测试用例：测试添加自定义敏感词的功能。
    目的：验证服务可以动态扩展其敏感词库。
    """
    # 准备测试数据
    custom_category = "测试类别"
    custom_words = {
        "自定义敏感词1": "high",  # 自定义一个 high 级别的词
        "自定义敏感词2": "medium" # 自定义一个 medium 级别的词
    }
    test_text = "这段文本包含自定义敏感词1和自定义敏感词2"
    
    # 在添加自定义敏感词之前，文本应被认为是干净的
    before_result = content_filter_service.filter_text(test_text)
    assert before_result.has_sensitive_content is False
    
    # 添加自定义敏感词
    content_filter_service.add_custom_sensitive_words(custom_category, custom_words)
    
    # 添加之后，再次过滤，此时应能检测到敏感内容
    after_result = content_filter_service.filter_text(test_text)
    assert after_result.has_sensitive_content is True
    assert custom_category in after_result.sensitive_categories # 断言：检测到的类别应包含我们自定义的类别
    assert after_result.sensitive_word_count >= 2
    assert after_result.highest_severity == "high" # 因为包含 "自定义敏感词1" (high)
    assert "自定义敏感词1" not in after_result.filtered_text # 断言：自定义的词应被替换
    assert "自定义敏感词2" not in after_result.filtered_text


def test_filter_audio(content_filter_service):
    """
    测试用例：测试音频过滤功能（模拟场景）。
    目的：验证 filter_audio 方法能够正确调用底层的文本过滤逻辑。
    注意：这里并没有真的进行音频转文本，而是通过模拟（mock）来测试流程。
    """
    # 准备假的音频数据
    mock_audio_data = b"mock_audio_data"
    
    # 使用 unittest.mock.patch 来模拟 filter_text 方法
    # 我们不关心音频转文本的具体实现，只关心 filter_audio 是否调用了 filter_text
    with patch.object(content_filter_service, 'filter_text') as mock_filter_text:
        # 设置模拟对象的返回值，假装 filter_text 已经处理完毕并返回了一个结果
        mock_filter_text.return_value = FilterResult(
            filtered_text="这是从音频转写的文本",
            has_sensitive_content=False,
            sensitive_word_count=0,
            sensitive_categories=[],
            highest_severity="low",
            detected_words={}
        )
        
        # 执行音频过滤
        result = content_filter_service.filter_audio(mock_audio_data)
        
        # 验证结果是否与我们模拟的返回值一致
        assert result.filtered_text == "这是从音频转写的文本"
        assert result.has_sensitive_content is False
        
        # 验证 filter_text 方法是否被正确调用了一次
        mock_filter_text.assert_called_once()


def test_filter_audio_exception_handling(content_filter_service):
    """
    测试用例：测试音频过滤过程中的异常处理。
    目的：验证当底层依赖（如音频转文本或文本过滤）抛出异常时，filter_audio 方法能捕获异常并返回一个安全的默认值。
    """
    # 准备假的音频数据
    mock_audio_data = b"mock_audio_data"
    
    # 模拟 filter_text 方法在被调用时抛出一个异常
    with patch.object(content_filter_service, 'filter_text', side_effect=Exception("模拟异常")):
        # 执行过滤
        result = content_filter_service.filter_audio(mock_audio_data)
        
        # 验证结果 - 即使发生异常，也应该返回一个默认的、无害的结果，而不是让程序崩溃
        assert result.filtered_text == ""
        assert result.has_sensitive_content is False
        assert result.sensitive_word_count == 0


def test_singleton_pattern():
    """
    测试用例：测试内容过滤服务的单例模式。
    目的：验证通过 ContentFilterService.get_instance() 获取的始终是同一个对象实例。
    """
    # 步骤1: 获取两个实例
    instance1 = ContentFilterService.get_instance()
    instance2 = ContentFilterService.get_instance()
    
    # 步骤2: 验证这两个变量是否指向内存中的同一个对象
    assert instance1 is instance2
    
    # 步骤3: 通过一个实例修改服务内部状态
    custom_category = "测试单例"
    custom_words = {"单例测试词": "medium"}
    instance1.add_custom_sensitive_words(custom_category, custom_words)
    
    # 步骤4: 验证通过另一个实例访问时，状态也被改变了
    # 这证明了它们确实是同一个对象
    assert custom_category in instance2.sensitive_words_dict
    assert "单例测试词" in instance2.sensitive_words_dict[custom_category]

