"""
问题生成器测试

本文件包含针对 QuestionGenerator 类的单元测试，
主要测试其在不同模式、不同岗位、不同输入下生成面试问题的行为。
"""

# 导入所需库
import pytest
import asyncio
import os
from typing import Dict, Any, List

# 导入被测试类和相关依赖
from agent.src.core.system.config import AgentConfig
from agent.src.services.openai_service import OpenAIService
from agent.src.services.question_generator import QuestionGenerator, QuestionGeneratorConfig

# --- 测试职位数据 ---
# 定义一系列不同岗位的字典，用于模拟真实的职位信息输入

AI_POSITION = {
    "id": 1,
    "title": "AI工程师",
    "description": "负责开发人工智能模型和算法",
    "tech_field": "ai",
    "position_type": "TECHNICAL",
    "required_skills": ["机器学习", "Python", "深度学习"]
}

BIGDATA_POSITION = {
    "id": 2,
    "title": "大数据工程师",
    "description": "负责大规模数据处理和分析系统的开发",
    "tech_field": "bigdata",
    "position_type": "TECHNICAL",
    "required_skills": ["Hadoop", "Spark", "Hive", "SQL"]
}

BACKEND_POSITION = {
    "id": 3,
    "title": "后端开发工程师",
    "description": "负责服务端系统设计和API开发",
    "tech_field": "backend",
    "position_type": "TECHNICAL",
    "required_skills": ["Java", "Spring Boot", "MySQL", "Redis"]
}

FRONTEND_POSITION = {
    "id": 4,
    "title": "前端开发工程师",
    "description": "负责Web前端界面设计和开发",
    "tech_field": "frontend",
    "position_type": "TECHNICAL",
    "required_skills": ["JavaScript", "React", "Vue", "CSS"]
}

IOT_POSITION = {
    "id": 5,
    "title": "物联网架构师",
    "description": "负责物联网系统架构设计和实现",
    "tech_field": "iot",
    "position_type": "TECHNICAL",
    "required_skills": ["嵌入式系统", "MQTT", "边缘计算", "传感器技术"]
}

PRODUCT_POSITION = {
    "id": 6,
    "title": "产品经理",
    "description": "负责产品规划和需求管理",
    "tech_field": "product",
    "position_type": "PRODUCT",
    "required_skills": ["产品规划", "需求分析", "用户研究", "项目管理"]
}

# --- 测试装置 (Test Fixtures) ---

@pytest.fixture
def openai_service():
    """创建OpenAI服务实例"""
    agent_config = AgentConfig()
    # 如果需要从环境变量读取API密钥
    if "OPENAI_API_KEY" not in os.environ:
        # 提供一个默认API密钥用于测试，实际应用中应使用环境变量
        os.environ["OPENAI_API_KEY"] = "your-api-key-here" 
    
    return OpenAIService(agent_config)

@pytest.fixture
def question_generator_config():
    """创建测试用的问题生成器配置"""
    return QuestionGeneratorConfig(
        api_model="gpt-3.5-turbo",  # 使用更便宜的模型用于测试
        temperature=0.5,
        max_tokens=1000,
        use_cache=True  # 启用缓存以加速测试
    )

@pytest.fixture
def question_generator(openai_service, question_generator_config):
    """创建问题生成器实例"""
    return QuestionGenerator(openai_service, question_generator_config)


# --- 测试用例 ---

@pytest.mark.asyncio
async def test_fallback_questions():
    """
    测试用例：测试备用（fallback）问题生成逻辑。
    目的：验证系统可以生成一套预设的、合理的面试问题。
    这个测试不依赖外部API调用。
    """
    generator = QuestionGenerator()
    
    # 测试快速模式的备用问题
    quick_fallback = generator._get_fallback_quick_questions(AI_POSITION, 3, "medium")
    assert len(quick_fallback) == 3
    assert quick_fallback[0]["type"] == "SELF_INTRO"
    
    # 测试完整模式的备用问题
    full_fallback = generator._get_fallback_full_questions(AI_POSITION, 5, "medium")
    assert len(full_fallback) == 5
    assert any(q["type"] == "SYSTEM_DESIGN" for q in full_fallback)
    
    # 验证备用问题能根据不同技术领域生成不同内容
    bigdata_position = {**AI_POSITION, "tech_field": "bigdata"}
    bigdata_questions = generator._get_fallback_full_questions(bigdata_position, 5, "medium")
    assert any("Hadoop" in q["text"] for q in bigdata_questions)

@pytest.mark.asyncio
async def test_quick_mode_questions(question_generator):
    """
    测试用例：测试在"快速模式"下生成问题。
    目的：验证快速模式生成的问题数量正确，且问题类型和时长符合预期。
    """
    # 调用问题生成方法
    questions = await question_generator.generate_questions(
        job_position=AI_POSITION,
        question_count=3,
        difficulty_level="medium",
        mode="quick"
    )
    
    # 验证结果
    assert len(questions) == 3  # 验证问题数量
    assert isinstance(questions, list)  # 验证返回类型为列表
    assert all(isinstance(q, dict) for q in questions)  # 验证每个问题都是字典
    assert all("text" in q for q in questions)  # 验证每个问题都有text字段

@pytest.mark.asyncio
#@pytest.mark.skipif(not os.environ.get("RUN_API_TESTS"), reason="跳过API测试，设置环境变量RUN_API_TESTS=1以启用")
async def test_full_mode_questions(question_generator):
    """
    测试用例：测试在"完整模式"下生成问题。
    目的：验证完整模式能生成更多样化、更深入的问题。
    """
    # 调用问题生成方法
    questions = await question_generator.generate_questions(
        job_position=AI_POSITION,
        question_count=5,
        difficulty_level="medium",
        mode="full"
    )
    
    # 验证结果
    assert len(questions) == 5  # 验证问题数量
    assert isinstance(questions, list)  # 验证返回类型为列表
    assert all(isinstance(q, dict) for q in questions)  # 验证每个问题都是字典
    assert all("text" in q for q in questions)  # 验证每个问题都有text字段

@pytest.mark.asyncio
#@pytest.mark.skipif(not os.environ.get("RUN_API_TESTS"), reason="跳过API测试，设置环境变量RUN_API_TESTS=1以启用")
async def test_multiple_tech_fields(question_generator):
    """
    测试用例：测试对不同技术领域的岗位生成问题。
    目的：验证系统能根据岗位的 tech_field 调整生成的问题内容。
    """
    # 后端岗位
    backend_questions = await question_generator.generate_questions(
        job_position=BACKEND_POSITION,
        question_count=3,
        difficulty_level="medium",
        mode="quick"
    )
    assert len(backend_questions) == 3
    
    # 前端岗位
    frontend_questions = await question_generator.generate_questions(
        job_position=FRONTEND_POSITION,
        question_count=3,
        difficulty_level="medium",
        mode="quick"
    )
    assert len(frontend_questions) == 3
    
    # 验证两个岗位的问题内容不完全相同
    backend_texts = [q["text"] for q in backend_questions]
    frontend_texts = [q["text"] for q in frontend_questions]
    assert not all(bt == ft for bt, ft in zip(backend_texts, frontend_texts))

@pytest.mark.asyncio
#@pytest.mark.skipif(not os.environ.get("RUN_API_TESTS"), reason="跳过API测试，设置环境变量RUN_API_TESTS=1以启用")
async def test_cache_mechanism(question_generator):
    """
    测试用例：测试缓存机制。
    目的：验证对于完全相同的请求参数，第二次调用会直接使用缓存而不是再次调用 API。
    """
    # 第一次调用，此时会调用 API 并缓存结果
    questions1 = await question_generator.generate_questions(
        job_position=AI_POSITION,
        question_count=3,
        difficulty_level="medium",
        mode="quick"
    )
    
    # 关闭API服务，如果缓存失效则会抛出异常
    question_generator.openai_service = None
    
    # 第二次使用完全相同的参数调用
    questions2 = await question_generator.generate_questions(
        job_position=AI_POSITION,
        question_count=3,
        difficulty_level="medium",
        mode="quick"
    )
    
    # 验证两次获取的问题列表是相同的
    assert questions1 == questions2

@pytest.mark.asyncio
async def test_validate_params():
    """
    测试用例：测试参数验证逻辑。
    目的：确保提供无效参数时会引发适当的异常。
    这个测试不依赖外部API调用。
    """
    generator = QuestionGenerator()
    
    # 测试无效的职位信息
    with pytest.raises(ValueError):
        generator._validate_params(None, 3, "medium", "quick")
    
    # 测试无效的问题数量
    with pytest.raises(ValueError):
        generator._validate_params(AI_POSITION, 0, "medium", "quick")
    
    # 测试无效的难度级别
    with pytest.raises(ValueError):
        generator._validate_params(AI_POSITION, 3, "invalid", "quick")
    
    # 测试无效的面试模式
    with pytest.raises(ValueError):
        generator._validate_params(AI_POSITION, 3, "medium", "invalid")

# 当该脚本作为主程序运行时，执行 pytest
if __name__ == "__main__":
    # 使用 asyncio.run 来执行异步的 pytest.main
    asyncio.run(pytest.main(["-xvs", __file__]))
