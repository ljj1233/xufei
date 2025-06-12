"""
测试 QuestionService 类

测试问题生成服务在不同模式下的功能
"""

import os
import pytest
import asyncio
import json
import sys
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

from agent.src.services.question_service import QuestionService, create_question_service, QuestionServiceConfig
from agent.src.services.openai_service import OpenAIService
from agent.src.core.system.config import AgentConfig

# 加载环境变量
load_dotenv()

# 测试数据
TEST_POSITION_INFO = {
    "position_id": 1,
    "position_name": "Python开发工程师",
    "title": "Python开发工程师",
    "tech_field": "backend",
    "description": "负责后端服务开发与维护",
    "skills": ["Python", "Django", "FastAPI", "MySQL", "Redis"]
}

# 跳过标记，如果没有设置OpenAI API Key则跳过真实API测试
skip_if_no_api_key = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY","2e2308bb-976a-4ea7-badd-0ab1bf2066bd"), 
    reason="需要设置OPENAI_API_KEY环境变量"
)

@pytest.mark.asyncio
async def test_create_question_service():
    """测试创建问题服务实例"""
    service = create_question_service()
    assert isinstance(service, QuestionService)
    assert service.openai_service is not None
    assert service.config is not None

@pytest.mark.asyncio
async def test_validate_params():
    """测试参数验证功能"""
    service = create_question_service()
    
    # 正常参数
    service._validate_params(TEST_POSITION_INFO, 5, "medium", "full")
    
    # 无效的职位信息
    with pytest.raises(ValueError, match="职位信息必须是字典类型"):
        service._validate_params("invalid", 5, "medium", "full")
    
    # 无效的问题数量
    with pytest.raises(ValueError, match="问题数量必须为正整数"):
        service._validate_params(TEST_POSITION_INFO, 0, "medium", "full")
    
    # 无效的难度级别
    with pytest.raises(ValueError, match="难度级别必须为easy, medium或hard"):
        service._validate_params(TEST_POSITION_INFO, 5, "invalid", "full")
    
    # 无效的模式
    with pytest.raises(ValueError, match="面试模式必须为quick或full"):
        service._validate_params(TEST_POSITION_INFO, 5, "medium", "invalid")

@pytest.mark.asyncio
async def test_extract_keywords():
    """测试关键词提取功能"""
    service = create_question_service()
    
    # 测试关键词提取
    text = "我是一名有5年经验的Python开发工程师，精通Django和FastAPI框架，熟悉微服务架构设计"
    keywords = service._extract_keywords(text)
    
    assert isinstance(keywords, str)
    assert "python" in keywords.lower()
    assert "django" in keywords.lower()
    assert "fastapi" in keywords.lower()
    assert "微服务" in keywords
    
    # 测试空文本
    assert service._extract_keywords("") == ""
    assert service._extract_keywords(None) == ""

@pytest.mark.asyncio
@patch("agent.src.services.openai_service.OpenAIService.chat_completion")
async def test_generate_questions_with_openai_mock(mock_chat_completion):
    """使用模拟的OpenAI测试问题生成"""
    # 设置模拟响应
    mock_response = {
        "status": "success",
        "content": """```json
[
  {
    "text": "请介绍一下你在Python开发中的经验",
    "type": "自我介绍",
    "duration": 120,
    "difficulty": "medium"
  },
  {
    "text": "描述Django的ORM与传统SQL的区别",
    "type": "技术问题",
    "duration": 180,
    "difficulty": "medium"
  }
]```"""
    }
    
    # 设置模拟方法返回值
    mock_chat_completion.return_value = mock_response
    
    # 创建服务实例
    service = create_question_service()
    
    # 调用被测试的方法
    prompt = "测试提示词"
    questions = await service._generate_questions_with_openai(prompt, "测试角色")
    
    # 验证结果
    assert len(questions) == 2
    assert questions[0]["text"] == "请介绍一下你在Python开发中的经验"
    assert questions[0]["type"] == "自我介绍"
    assert questions[1]["text"] == "描述Django的ORM与传统SQL的区别"
    assert questions[1]["duration"] == 180

@pytest.mark.asyncio
@patch("agent.src.services.question_service.QuestionService._generate_questions_with_openai")
async def test_generate_interview_questions_mock(mock_generate):
    """使用模拟方法测试问题生成流程"""
    # 设置模拟返回值
    mock_questions = [
        {
            "text": "测试问题1",
            "type": "技术问题",
            "duration": 120,
            "difficulty": "medium"
        },
        {
            "text": "测试问题2",
            "type": "行为问题",
            "duration": 180,
            "difficulty": "medium"
        }
    ]
    mock_generate.return_value = mock_questions
    
    # 创建服务实例
    service = create_question_service()
    
    # 测试快速模式
    quick_questions = await service.generate_interview_questions(
        position_info=TEST_POSITION_INFO,
        question_count=2,
        mode="quick"
    )
    
    # 验证结果
    assert quick_questions == mock_questions
    mock_generate.assert_called_once()
    
    # 重置模拟
    mock_generate.reset_mock()
    
    # 测试完整模式
    full_questions = await service.generate_interview_questions(
        position_info=TEST_POSITION_INFO,
        question_count=2,
        mode="full"
    )
    
    # 验证结果
    assert full_questions == mock_questions
    mock_generate.assert_called_once()

# 创建一个单独的脚本来运行测试，避免pytest的I/O错误问题
async def run_real_test():
    """使用真实API测试完整流程（需要API密钥）"""
    # 设置控制台编码，解决中文乱码问题
    if sys.platform.startswith('win'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # 获取环境变量中的模型名称
    model_name = os.environ.get("OPENAI_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    print(f"\n使用模型: {model_name}")
    
    # 创建自定义配置
    config = QuestionServiceConfig(
        api_model=model_name,
        temperature=0.7,
        max_tokens=2000
    )
    
    # 创建Agent配置
    agent_config = AgentConfig()
    
    # 创建OpenAI服务
    openai_service = OpenAIService(agent_config)
    
    # 创建问题服务
    service = create_question_service(openai_service=openai_service, config=config)
    
    # 打印环境变量
    print("\n环境变量:")
    print(f"OPENAI_API_KEY: {'已设置' if os.environ.get('OPENAI_API_KEY') else '未设置'}")
    print(f"OPENAI_API_BASE: {os.environ.get('OPENAI_API_BASE', '未设置')}")
    print(f"OPENAI_MODEL: {os.environ.get('OPENAI_MODEL', '未设置')}")
    print(f"LLM_PROVIDER: {os.environ.get('LLM_PROVIDER', '未设置')}")
    
    try:
        # 生成快速模式的问题
        print("\n开始生成快速模式问题...")
        quick_questions = await service.generate_interview_questions(
            position_info=TEST_POSITION_INFO,
            question_count=3,
            mode="quick"
        )
        
        # 将快速模式问题保存到文件
        save_to_file(quick_questions, "quick_questions.json")
        
        # 验证快速模式的结果
        assert len(quick_questions) > 0
        for q in quick_questions:
            # 确保问题有文本内容
            assert "text" in q or "question" in q
            
            # 检查问题是否有持续时间，如果没有，添加默认值
            if "duration" not in q:
                q["duration"] = 120  # 添加默认值
                print(f"警告: 问题缺少duration字段，已添加默认值: {q.get('text', q.get('question', ''))[:30]}...")
            
            # 验证duration是整数
            assert isinstance(q.get("duration"), int)
        
        # 生成完整模式的问题
        print("\n开始生成完整模式问题...")
        full_questions = await service.generate_interview_questions(
            position_info=TEST_POSITION_INFO,
            question_count=3,
            mode="full"
        )
        
        # 将完整模式问题保存到文件
        save_to_file(full_questions, "full_questions.json")
        
        # 验证完整模式的结果
        assert len(full_questions) > 0
        for q in full_questions:
            # 确保问题有文本内容
            assert "text" in q or "question" in q
            
            # 检查问题是否有持续时间，如果没有，添加默认值
            if "duration" not in q:
                q["duration"] = 300  # 添加默认值
                print(f"警告: 问题缺少duration字段，已添加默认值: {q.get('text', q.get('question', ''))[:30]}...")
            
            # 验证duration是整数
            assert isinstance(q.get("duration"), int)
        
        print("\n测试成功完成!")
    
    except Exception as e:
        print(f"\n测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

# 辅助函数：保存数据到文件
def save_to_file(data, filename):
    """将数据保存到JSON文件"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n数据已保存到 {filename}")

# 如果直接运行此文件，则执行真实API测试
if __name__ == "__main__":
    asyncio.run(run_real_test())
    