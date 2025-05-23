import pytest
import os
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.services.xunfei_service import XunfeiService
from app.services.analysis_service import AnalysisService
from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app as original_app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 测试讯飞服务
class TestXunfeiService:
    
    def setup_method(self):
        """测试前的准备工作"""
        self.xunfei_service = XunfeiService()
        # 创建测试音频文件路径
        self.test_audio_path = os.path.join(os.path.dirname(__file__), "test_data", "test_audio.mp3")
        # 确保测试目录存在
        os.makedirs(os.path.join(os.path.dirname(__file__), "test_data"), exist_ok=True)
        # 如果测试文件不存在，创建一个空文件用于测试
        if not os.path.exists(self.test_audio_path):
            with open(self.test_audio_path, "wb") as f:
                f.write(b"test audio content")
    
    @patch("app.services.xunfei_service.requests.post")
    def test_speech_recognition(self, mock_post):
        """测试语音识别功能"""
        # 模拟讯飞API的响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "0",
            "data": {
                "result": "这是一段测试语音识别的文本。"
            }
        }
        mock_post.return_value = mock_response
        
        # 调用语音识别服务
        with open(self.test_audio_path, "rb") as f:
            audio_data = f.read()
        result = self.xunfei_service.speech_recognition(audio_data)
        
        # 验证结果
        assert result == "这是一段测试语音识别的文本。"
        # 验证API调用
        mock_post.assert_called_once()
    
    @patch("app.services.xunfei_service.requests.post")
    def test_speech_assessment(self, mock_post):
        """测试语音评测功能"""
        # 模拟讯飞API的响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "0",
            "data": {
                "fluency": 85.5,
                "integrity": 90.2,
                "pronunciation": 88.7,
                "speed": 4.5
            }
        }
        mock_post.return_value = mock_response
        
        # 调用语音评测服务
        with open(self.test_audio_path, "rb") as f:
            audio_data = f.read()
        result = self.xunfei_service.speech_assessment(audio_data)
        
        # 验证结果
        assert "fluency" in result
        assert result["fluency"] == 85.5
        assert "integrity" in result
        assert "pronunciation" in result
        assert "speed" in result
        # 验证API调用
        mock_post.assert_called_once()
    
    @patch("app.services.xunfei_service.requests.post")
    def test_emotion_analysis(self, mock_post):
        """测试情感分析功能"""
        # 模拟讯飞API的响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "0",
            "data": {
                "emotion": {
                    "positive": 0.75,
                    "neutral": 0.20,
                    "negative": 0.05
                }
            }
        }
        mock_post.return_value = mock_response
        
        # 调用情感分析服务
        with open(self.test_audio_path, "rb") as f:
            audio_data = f.read()
        result = self.xunfei_service.emotion_analysis(audio_data)
        
        # 验证结果
        assert "positive" in result
        assert result["positive"] == 0.75
        assert "neutral" in result
        assert "negative" in result
        # 验证API调用
        mock_post.assert_called_once()


# 测试分析服务
class TestAnalysisService:
    
    def setup_method(self):
        """测试前的准备工作"""
        # 模拟讯飞服务
        self.mock_xunfei_service = MagicMock()
        self.analysis_service = AnalysisService(xunfei_service=self.mock_xunfei_service)
        # 创建测试音频文件路径
        self.test_audio_path = os.path.join(os.path.dirname(__file__), "test_data", "test_audio.mp3")
        # 确保测试目录存在
        os.makedirs(os.path.join(os.path.dirname(__file__), "test_data"), exist_ok=True)
        # 如果测试文件不存在，创建一个空文件用于测试
        if not os.path.exists(self.test_audio_path):
            with open(self.test_audio_path, "wb") as f:
                f.write(b"test audio content")
    
    def test_analyze_interview(self):
        """测试面试分析功能"""
        # 模拟讯飞服务的返回结果
        self.mock_xunfei_service.speech_recognition.return_value = "这是一段测试面试的回答。"
        self.mock_xunfei_service.speech_assessment.return_value = {
            "fluency": 85.5,
            "integrity": 90.2,
            "pronunciation": 88.7,
            "speed": 4.5
        }
        self.mock_xunfei_service.emotion_analysis.return_value = {
            "positive": 0.75,
            "neutral": 0.20,
            "negative": 0.05
        }
        
        # 调用面试分析服务
        interview_data = {
            "id": 1,
            "title": "测试面试",
            "file_path": self.test_audio_path,
            "tech_field": "人工智能",
            "position_type": "技术岗"
        }
        result = self.analysis_service.analyze_interview(interview_data)
        
        # 验证结果
        assert "speech_text" in result
        assert result["speech_text"] == "这是一段测试面试的回答。"
        assert "speech_assessment" in result
        assert "emotion_analysis" in result
        assert "professional_score" in result
        assert "skill_match_score" in result
        assert "expression_score" in result
        assert "logical_score" in result
        assert "innovation_score" in result
        assert "pressure_score" in result
        assert "overall_score" in result
        assert "improvement_suggestions" in result
        
        # 验证服务调用
        self.mock_xunfei_service.speech_recognition.assert_called_once_with(self.test_audio_path)
        self.mock_xunfei_service.speech_assessment.assert_called_once()
        self.mock_xunfei_service.emotion_analysis.assert_called_once()


@pytest.fixture(scope="function")
def test_db():
    from .conftest import test_db as _test_db
    yield from _test_db()


@pytest.fixture(scope="function")
def client(test_db):
    app = original_app
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.rollback()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_register_and_login(client):
    user = {"username": "serviceuser", "email": "serviceuser@example.com", "password": "Test@123456"}
    r = client.post(f"{settings.API_V1_STR}/users/register", json=user)
    assert r.status_code in (200, 201)
    login_data = {"username": "serviceuser", "password": "Test@123456"}
    r2 = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
    assert r2.status_code == 200
    assert "access_token" in r2.json()