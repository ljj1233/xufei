import pytest
import asyncio
import json
import io
from unittest.mock import patch, MagicMock, AsyncMock
import os

from app.services.ai_agent_service import AIAgentService, ai_agent_service
from app.services.content_analyzer import ContentAnalyzer
from app.services.speech_analyzer import SpeechAnalyzer
from app.services.audio_feature_extractor import AudioFeatureExtractor
from app.services.feedback_generator import FeedbackGenerator
from app.schemas.analysis import QuickPracticeAnalysis

# 创建测试用的音频数据
def create_test_audio():
    # 这里使用简单的二进制数据模拟音频文件
    return b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xAC\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'

# 测试数据
TEST_ANSWER = "这是一个测试回答，包含一些专业术语如算法、数据结构和系统设计。"
TEST_QUESTION = "请介绍你的项目经验。"
TEST_JOB_DESCRIPTION = "软件工程师职位，需要良好的算法和数据结构知识。"

# 模拟分析结果
MOCK_CONTENT_ANALYSIS = {
    "relevance": 7.5,
    "relevance_review": "回答高度相关，直接针对问题进行了回应",
    "depth_and_detail": 6.0,
    "depth_review": "回答包含了一些具体例子，但缺少具体数据支撑",
    "professionalism": 8.0,
    "matched_keywords": ["算法", "数据结构", "系统设计"],
    "professional_style_review": "使用了专业术语，表达专业"
}

MOCK_COGNITIVE_ANALYSIS = {
    "logical_structure": 7.0,
    "structure_review": "总分总结构，逻辑较为清晰",
    "clarity_of_thought": 7.5,
    "clarity_review": "思路清晰，没有明显矛盾"
}

MOCK_SPEECH_ANALYSIS = {
    "fluency": 7.0,
    "fluency_details": {
        "filler_words_count": 3,
        "unnatural_pauses_count": 1
    },
    "speech_rate": 7.5,
    "speech_rate_details": {
        "words_per_minute": 160,
        "pace_category": "适中"
    },
    "vocal_energy": 6.5,
    "vocal_energy_details": {
        "pitch_std_dev": 15.0,
        "pitch_category": "平稳有变化"
    },
    "conciseness": 6.5,
    "conciseness_review": "表达较为简洁，但有少量冗余"
}

MOCK_FEEDBACK = {
    "strengths": [
        {
            "category": "content_quality",
            "item": "relevance",
            "description": "回答的相关性极高，你的回答紧扣问题核心，展现了良好的理解能力。"
        }
    ],
    "growth_areas": [
        {
            "category": "content_quality",
            "item": "depth_and_detail",
            "description": "回答缺乏具体的数据和例子支撑",
            "action_suggestion": "使用STAR法则，特别是在描述结果时加入具体数据"
        }
    ],
    "content_quality_score": 72.5,
    "cognitive_skills_score": 72.5,
    "communication_skills_score": 69.0,
    "overall_score": 71.5
}

@pytest.fixture
def test_audio():
    return create_test_audio()

@pytest.mark.asyncio
@patch('app.services.ai_agent_service.InterviewAgent.analyze_quick_practice')
async def test_analyze_quick_practice_service(mock_analyze_quick_practice):
    """测试AIAgentService的analyze_quick_practice方法"""
    # 设置模拟返回值
    mock_analyze_quick_practice.return_value = {
        "content_quality": MOCK_CONTENT_ANALYSIS,
        "cognitive_skills": MOCK_COGNITIVE_ANALYSIS,
        "communication_skills": MOCK_SPEECH_ANALYSIS,
        "feedback": MOCK_FEEDBACK
    }
    
    # 调用分析方法
    result = await ai_agent_service.analyze_quick_practice(
        session_id=1,
        question_id=1,
        answer_text=TEST_ANSWER,
        audio_data=create_test_audio(),
        job_description=TEST_JOB_DESCRIPTION,
        question=TEST_QUESTION
    )
    
    # 验证结果
    assert result is not None
    assert "content_quality" in result
    assert "cognitive_skills" in result
    assert "communication_skills" in result
    assert "feedback" in result
    assert result["feedback"]["overall_score"] == MOCK_FEEDBACK["overall_score"]
    
    # 验证模拟函数调用
    mock_analyze_quick_practice.assert_called_once()

@pytest.mark.asyncio
@patch('app.services.ai_agent_service.InterviewAgent.analyze_quick_practice')
async def test_analyze_quick_practice_no_audio(mock_analyze_quick_practice):
    """测试没有音频数据时的分析服务"""
    # 设置模拟返回值（不包含语音分析）
    mock_analyze_quick_practice.return_value = {
        "content_quality": MOCK_CONTENT_ANALYSIS,
        "cognitive_skills": MOCK_COGNITIVE_ANALYSIS,
        "feedback": {
            **MOCK_FEEDBACK,
            "communication_skills_score": 0
        }
    }
    
    # 调用分析方法（不提供音频数据）
    result = await ai_agent_service.analyze_quick_practice(
        session_id=1,
        question_id=1,
        answer_text=TEST_ANSWER,
        audio_data=None,
        job_description=TEST_JOB_DESCRIPTION,
        question=TEST_QUESTION
    )
    
    # 验证结果
    assert result is not None
    assert "content_quality" in result
    assert "cognitive_skills" in result
    assert "communication_skills" not in result  # 没有音频时不应有语音分析
    
    # 验证模拟函数调用
    mock_analyze_quick_practice.assert_called_once()

@pytest.mark.asyncio
@patch('app.api.api_v1.endpoints.analysis.ai_agent_service.analyze_quick_practice')
def test_quick_practice_api_endpoint(mock_analyze_quick_practice, test_client, test_db):
    """测试快速练习API接口"""
    # 设置模拟返回值
    mock_analyze_quick_practice.return_value = {
        "content_quality": MOCK_CONTENT_ANALYSIS,
        "cognitive_skills": MOCK_COGNITIVE_ANALYSIS,
        "communication_skills": MOCK_SPEECH_ANALYSIS,
        "feedback": MOCK_FEEDBACK
    }
    
    # 准备测试数据
    test_data = {
        "interview_id": 1,
        "question_id": 1,
        "answer_text": TEST_ANSWER,
        "job_description": TEST_JOB_DESCRIPTION,
        "question": TEST_QUESTION
    }
    
    # 创建测试文件
    test_audio_path = "test_audio.wav"
    with open(test_audio_path, "wb") as f:
        f.write(create_test_audio())
    
    # 发送API请求
    with open(test_audio_path, "rb") as f:
        files = {"audio_file": ("test_audio.wav", f, "audio/wav")}
        response = test_client.post(
            "/api/v1/analyses/quick-practice",
            data=test_data,
            files=files
        )
    
    # 删除测试文件
    if os.path.exists(test_audio_path):
        os.remove(test_audio_path)
    
    # 验证响应
    assert response.status_code == 200
    assert response.json()["analysis_type"] == "quick_practice"
    assert "quick_practice" in response.json()
    
    # 验证模拟函数调用
    mock_analyze_quick_practice.assert_called_once()

@pytest.mark.asyncio
def test_api_error_handling(test_client):
    """测试API错误处理"""
    # 准备不完整的测试数据
    incomplete_data = {
        # 缺少必要的interview_id字段
        "question_id": 1,
        "answer_text": TEST_ANSWER
    }
    
    # 发送API请求
    response = test_client.post(
        "/api/v1/analyses/quick-practice",
        data=incomplete_data
    )
    
    # 验证响应
    assert response.status_code == 422  # Unprocessable Entity

def test_quick_practice_schema():
    """测试QuickPracticeAnalysis模式验证"""
    # 创建有效的数据
    valid_data = {
        "content_quality": MOCK_CONTENT_ANALYSIS,
        "cognitive_skills": MOCK_COGNITIVE_ANALYSIS,
        "communication_skills": MOCK_SPEECH_ANALYSIS,
        "feedback": MOCK_FEEDBACK
    }
    
    # 验证Schema能正确解析数据
    analysis = QuickPracticeAnalysis(**valid_data)
    
    # 验证字段值
    assert analysis.content_quality.relevance == 7.5
    assert analysis.cognitive_skills.logical_structure == 7.0
    assert analysis.communication_skills.fluency == 7.0
    assert analysis.feedback.overall_score == 71.5
    
    # 测试缺少必要字段时的行为
    import pytest
    from pydantic import ValidationError
    
    invalid_data = {
        "content_quality": MOCK_CONTENT_ANALYSIS,
        # 缺少cognitive_skills和feedback
    }
    
    # 应该抛出验证错误
    with pytest.raises(ValidationError):
        QuickPracticeAnalysis(**invalid_data)
