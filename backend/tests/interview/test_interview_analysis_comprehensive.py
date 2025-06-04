import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import io
from unittest.mock import patch, MagicMock, mock_open
import cv2

from app.db.database import Base, get_db
from app.main import app
from app.core.config import settings
from app.models.user import User
from app.models.job_position import JobPosition, TechField, PositionType
from app.models.interview import Interview, FileType
from app.models.analysis import Analysis
from app.core.security import get_password_hash

# 使用conftest_admin.py中的测试夹具
from ..conftest_admin import admin_test_db, admin_client, admin_token

# 创建测试用户和token
@pytest.fixture(scope="function")
def test_user(admin_test_db):
    # 创建普通测试用户
    test_user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_admin=False
    )
    admin_test_db.add(test_user)
    admin_test_db.commit()
    admin_test_db.refresh(test_user)
    return test_user

@pytest.fixture(scope="function")
def user_token(admin_client, test_user):
    response = admin_client.post(
        "/api/v1/users/login",
        data={"username": "testuser", "password": "password123"}
    )
    return response.json()["access_token"]

# 创建测试职位
@pytest.fixture(scope="function")
def test_job_position(admin_test_db):
    # 创建测试职位
    test_position = JobPosition(
        title="测试工程师",
        tech_field=TechField.AI,
        position_type=PositionType.TECHNICAL,
        required_skills="Python, 测试自动化",
        job_description="负责系统测试和自动化测试脚本开发",
        evaluation_criteria="测试经验, 编程能力, 沟通能力"
    )
    admin_test_db.add(test_position)
    admin_test_db.commit()
    admin_test_db.refresh(test_position)
    return test_position

# 创建测试面试记录
@pytest.fixture(scope="function")
def test_interview(admin_test_db, test_user, test_job_position):
    # 创建测试面试记录
    test_interview = Interview(
        user_id=test_user.id,
        job_position_id=test_job_position.id,
        title="测试面试记录",
        description="这是一个测试面试记录",
        file_path="/fake/path/test.mp4",
        file_type=FileType.VIDEO,
        duration=60.0
    )
    admin_test_db.add(test_interview)
    admin_test_db.commit()
    admin_test_db.refresh(test_interview)
    return test_interview

# 测试上传面试视频
@patch("app.api.api_v1.endpoints.interviews.shutil.copyfileobj")
@patch("app.api.api_v1.endpoints.interviews.os.makedirs")
@patch("app.api.api_v1.endpoints.interviews.cv2.VideoCapture")
@patch("builtins.open", new_callable=mock_open)
@patch("app.api.api_v1.endpoints.interviews.os.path.exists", return_value=True)
def test_upload_interview_video(mock_path_exists, mock_open_file, mock_video_capture, mock_makedirs, mock_copyfileobj, 
                               admin_client, user_token, test_job_position):
    # 模拟视频文件
    mock_video = MagicMock()
    mock_video.isOpened.return_value = True
    mock_video.get.side_effect = lambda x: 30.0 if x == cv2.CAP_PROP_FPS else 900 if x == cv2.CAP_PROP_FRAME_COUNT else 0
    mock_video_capture.return_value = mock_video
    
    # 创建测试文件
    test_file = io.BytesIO(b"test video content")
    test_file.name = "test_video.mp4"
    
    response = admin_client.post(
        "/api/v1/interviews/upload/",
        files={"file": ("test_video.mp4", test_file, "video/mp4")},
        data={
            "title": "视频面试测试",
            "description": "这是一个视频面试测试",
            "job_position_id": str(test_job_position.id)
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "视频面试测试"
    assert data["description"] == "这是一个视频面试测试"
    assert data["job_position_id"] == test_job_position.id
    assert data["file_type"] == "video"
    assert "id" in data

# 测试上传面试音频
@patch("app.api.api_v1.endpoints.interviews.shutil.copyfileobj")
@patch("app.api.api_v1.endpoints.interviews.os.makedirs")
@patch("builtins.open", new_callable=mock_open)
@patch("app.api.api_v1.endpoints.interviews.os.path.exists", return_value=True)
def test_upload_interview_audio(mock_path_exists, mock_open_file, mock_makedirs, mock_copyfileobj, 
                               admin_client, user_token, test_job_position):
    # 创建测试文件
    test_file = io.BytesIO(b"test audio content")
    test_file.name = "test_audio.mp3"
    
    response = admin_client.post(
        "/api/v1/interviews/upload/",
        files={"file": ("test_audio.mp3", test_file, "audio/mp3")},
        data={
            "title": "音频面试测试",
            "description": "这是一个音频面试测试",
            "job_position_id": str(test_job_position.id)
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "音频面试测试"
    assert data["description"] == "这是一个音频面试测试"
    assert data["job_position_id"] == test_job_position.id
    assert data["file_type"] == "audio"
    assert "id" in data

# 测试获取用户面试列表
def test_get_user_interviews(admin_client, user_token, test_user, test_interview):
    response = admin_client.get(
        "/api/v1/interviews/user",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(interview["title"] == "测试面试记录" for interview in data)

# 测试获取面试详情
def test_get_interview_detail(admin_client, user_token, test_interview):
    response = admin_client.get(
        f"/api/v1/interviews/{test_interview.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_interview.id
    assert data["title"] == test_interview.title
    assert data["description"] == test_interview.description

# 测试创建面试分析
@patch("app.services.analysis_service.AnalysisService.analyze_interview")
def test_create_interview_analysis(mock_analyze, admin_client, user_token, test_interview):
    # 模拟分析结果
    mock_analyze.return_value = {
        "overall_score": 85.5,
        "strengths": ["沟通能力强", "专业知识扎实"],
        "weaknesses": ["语速偏快", "眼神接触不足"],
        "suggestions": ["放慢语速", "增加眼神接触"],
        "speech_clarity": 90.0,
        "speech_pace": 70.0,
        "speech_emotion": "积极",
        "speech_logic": 85.0,
        "facial_expressions": {"happy": 0.7, "neutral": 0.3},
        "eye_contact": 75.0,
        "body_language": {"confidence": 80.0, "nervousness": 20.0},
        "content_relevance": 90.0,
        "content_structure": 85.0,
        "key_points": ["项目经验", "技术能力", "团队协作"],
        "professional_knowledge": 88.0,
        "skill_matching": 85.0,
        "logical_thinking": 87.0,
        "innovation_ability": 80.0,
        "stress_handling": 82.0,
        "situation_score": 85.0,
        "task_score": 87.0,
        "action_score": 86.0,
        "result_score": 88.0
    }
    
    response = admin_client.post(
        f"/api/v1/interviews/{test_interview.id}/analyze",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["interview_id"] == test_interview.id
    assert "overall_score" in data
    assert "details" in data
    assert "strengths" in data["details"]
    assert "weaknesses" in data["details"]
    assert "suggestions" in data["details"]

# 测试获取分析结果
def test_get_analysis_result(admin_client, user_token, test_interview, admin_test_db):
    # 创建分析结果
    from app.models.analysis import InterviewAnalysis
    analysis = InterviewAnalysis(
        interview_id=test_interview.id,
        summary="面试分析结果",
        score=85.5,
        details={
            "strengths": ["沟通能力强", "专业知识扎实"],
            "weaknesses": ["语速偏快", "眼神接触不足"],
            "suggestions": ["放慢语速", "增加眼神接触"]
        },
        speech_clarity=90.0,
        overall_score=85.5
    )
    admin_test_db.add(analysis)
    admin_test_db.commit()
    
    response = admin_client.get(
        f"/api/v1/interviews/{test_interview.id}/analysis",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["interview_id"] == test_interview.id
    assert "details" in data
    assert "strengths" in data["details"]
    assert "weaknesses" in data["details"]
    assert "suggestions" in data["details"]

# 测试分析结果比较
def test_compare_analysis_results(admin_client, user_token, test_user, test_job_position, admin_test_db):
    # 创建两个面试记录
    from app.models.interview import Interview, FileType
    from app.models.analysis import InterviewAnalysis
    
    interview1 = Interview(
        user_id=test_user.id,
        job_position_id=test_job_position.id,
        title="面试记录1",
        description="这是第一个面试记录",
        file_path="/fake/path/test1.mp4",
        file_type=FileType.VIDEO,
        duration=60.0
    )
    interview2 = Interview(
        user_id=test_user.id,
        job_position_id=test_job_position.id,
        title="面试记录2",
        description="这是第二个面试记录",
        file_path="/fake/path/test2.mp4",
        file_type=FileType.VIDEO,
        duration=70.0
    )
    admin_test_db.add(interview1)
    admin_test_db.add(interview2)
    admin_test_db.commit()
    admin_test_db.refresh(interview1)
    admin_test_db.refresh(interview2)
    
    # 创建分析结果
    analysis1 = InterviewAnalysis(
        interview_id=interview1.id,
        summary="面试1分析结果",
        score=80.0,
        details={
            "strengths": ["沟通能力强"],
            "weaknesses": ["技术细节不足"],
            "suggestions": ["加强技术学习"]
        },
        speech_clarity=85.0,
        overall_score=80.0
    )
    analysis2 = InterviewAnalysis(
        interview_id=interview2.id,
        summary="面试2分析结果",
        score=90.0,
        details={
            "strengths": ["技术能力强", "沟通清晰"],
            "weaknesses": ["紧张"],
            "suggestions": ["增加面试经验"]
        },
        speech_clarity=95.0,
        overall_score=90.0
    )
    admin_test_db.add(analysis1)
    admin_test_db.add(analysis2)
    admin_test_db.commit()
    
    # 获取第一个分析结果
    response1 = admin_client.get(
        f"/api/v1/interviews/{interview1.id}/analysis",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response1.status_code == 200
    data1 = response1.json()
    
    # 获取第二个分析结果
    response2 = admin_client.get(
        f"/api/v1/interviews/{interview2.id}/analysis",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    
    # 验证两个分析结果的差异
    assert data1["score"] < data2["score"]
    assert len(data1["details"]["strengths"]) < len(data2["details"]["strengths"])