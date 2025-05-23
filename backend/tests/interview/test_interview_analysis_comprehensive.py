import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.main import app
from app.core.config import settings
import os
import json
from unittest.mock import patch, MagicMock
from app.models.user import User
from app.models.job_position import JobPosition, TechField, PositionType
from app.models.interview import Interview, FileType
from app.models.analysis import Analysis
from app.core.security import get_password_hash
import io

# 使用conftest_admin.py中的测试夹具
from conftest_admin import admin_test_db, admin_client, admin_token

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
        data={"username": "testuser@example.com", "password": "password123"}
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
def test_upload_interview_video(mock_video_capture, mock_makedirs, mock_copyfileobj, 
                               admin_client, user_token, test_job_position):
    # 模拟视频文件
    mock_video = MagicMock()
    mock_video.get.return_value = 30.0  # 模拟30秒的视频
    mock_video.isOpened.return_value = True
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
def test_upload_interview_audio(mock_makedirs, mock_copyfileobj, 
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
@patch("app.api.api_v1.endpoints.analysis.analyze_interview")
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
        f"/api/v1/analysis/{test_interview.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["interview_id"] == test_interview.id
    assert data["overall_score"] == 85.5
    assert "strengths" in data
    assert "weaknesses" in data
    assert "suggestions" in data

# 测试获取分析结果
def test_get_analysis_result(admin_client, user_token, test_interview, admin_test_db):
    # 创建分析结果
    analysis = Analysis(
        interview_id=test_interview.id,
        overall_score=85.5,
        strengths=["沟通能力强", "专业知识扎实"],
        weaknesses=["语速偏快", "眼神接触不足"],
        suggestions=["放慢语速", "增加眼神接触"],
        speech_clarity=90.0,
        speech_pace=70.0,
        speech_emotion="积极",
        speech_logic=85.0,
        facial_expressions={"happy": 0.7, "neutral": 0.3},
        eye_contact=75.0,
        body_language={"confidence": 80.0, "nervousness": 20.0},
        content_relevance=90.0,
        content_structure=85.0,
        key_points=["项目经验", "技术能力", "团队协作"],
        professional_knowledge=88.0,
        skill_matching=85.0,
        logical_thinking=87.0,
        innovation_ability=80.0,
        stress_handling=82.0,
        situation_score=85.0,
        task_score=87.0,
        action_score=86.0,
        result_score=88.0
    )
    admin_test_db.add(analysis)
    admin_test_db.commit()
    
    response = admin_client.get(
        f"/api/v1/analysis/{test_interview.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["interview_id"] == test_interview.id
    assert data["overall_score"] == 85.5
    assert len(data["strengths"]) == 2
    assert len(data["weaknesses"]) == 2
    assert len(data["suggestions"]) == 2

# 测试分析结果比较
def test_compare_analysis_results(admin_client, user_token, test_user, test_job_position, admin_test_db):
    # 创建两个面试记录
    interview1 = Interview(
        user_id=test_user.id,
        job_position_id=test_job_position.id,
        title="面试记录1",
        description="第一次面试",
        file_path="/fake/path/test1.mp4",
        file_type=FileType.VIDEO,
        duration=60.0
    )
    interview2 = Interview(
        user_id=test_user.id,
        job_position_id=test_job_position.id,
        title="面试记录2",
        description="第二次面试",
        file_path="/fake/path/test2.mp4",
        file_type=FileType.VIDEO,
        duration=60.0
    )
    admin_test_db.add(interview1)
    admin_test_db.add(interview2)
    admin_test_db.commit()
    admin_test_db.refresh(interview1)
    admin_test_db.refresh(interview2)
    
    # 创建两个分析结果
    analysis1 = Analysis(
        interview_id=interview1.id,
        overall_score=75.0,
        strengths=["沟通能力强"],
        weaknesses=["专业知识不足", "语速偏快"],
        suggestions=["加强专业学习", "放慢语速"],
        speech_clarity=80.0,
        speech_pace=60.0,
        speech_emotion="紧张",
        speech_logic=75.0,
        facial_expressions={"nervous": 0.6, "neutral": 0.4},
        eye_contact=65.0,
        body_language={"confidence": 60.0, "nervousness": 40.0},
        content_relevance=70.0,
        content_structure=75.0,
        key_points=["基础知识", "项目经验"],
        professional_knowledge=70.0,
        skill_matching=75.0,
        logical_thinking=77.0,
        innovation_ability=70.0,
        stress_handling=72.0,
        situation_score=75.0,
        task_score=77.0,
        action_score=76.0,
        result_score=78.0
    )
    
    analysis2 = Analysis(
        interview_id=interview2.id,
        overall_score=85.0,
        strengths=["沟通能力强", "专业知识扎实"],
        weaknesses=["眼神接触不足"],
        suggestions=["增加眼神接触"],
        speech_clarity=90.0,
        speech_pace=80.0,
        speech_emotion="自信",
        speech_logic=85.0,
        facial_expressions={"confident": 0.7, "neutral": 0.3},
        eye_contact=75.0,
        body_language={"confidence": 80.0, "nervousness": 20.0},
        content_relevance=90.0,
        content_structure=85.0,
        key_points=["项目经验", "技术能力", "团队协作"],
        professional_knowledge=88.0,
        skill_matching=85.0,
        logical_thinking=87.0,
        innovation_ability=80.0,
        stress_handling=82.0,
        situation_score=85.0,
        task_score=87.0,
        action_score=86.0,
        result_score=88.0
    )
    
    admin_test_db.add(analysis1)
    admin_test_db.add(analysis2)
    admin_test_db.commit()
    
    # 测试比较两个分析结果
    response = admin_client.post(
        "/api/v1/analysis/compare",
        json={"interview_ids": [interview1.id, interview2.id]},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["interview_id"] == interview1.id
    assert data[1]["interview_id"] == interview2.id
    assert data[0]["overall_score"] < data[1]["overall_score"]