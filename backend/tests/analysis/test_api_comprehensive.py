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
import logging
import io

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 使用MySQL数据库进行测试
@pytest.fixture(scope="function")
def test_db():
    # 使用MySQL数据库进行测试
    engine = create_engine(
        settings.DATABASE_URI,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=3600,
        pool_pre_ping=True
    )
    # 先强制清空所有表和依赖，避免外键约束导致 drop 失败
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"TRUNCATE TABLE {table.name};"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        conn.commit()
    
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    # 预先创建管理员账号
    admin_user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_admin=True
    )
    db.add(admin_user)
    
    # 预先创建普通测试用户
    test_user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_admin=False
    )
    db.add(test_user)
    
    # 预先创建测试职位
    test_position = JobPosition(
        title="测试工程师",
        tech_field=TechField.AI,
        position_type=PositionType.TECHNICAL,
        required_skills="Python, 测试自动化",
        job_description="负责系统测试和自动化测试脚本开发",
        evaluation_criteria="测试经验, 编程能力, 沟通能力"
    )
    db.add(test_position)
    
    # 预先创建AI开发职位
    ai_position = JobPosition(
        title="AI开发工程师",
        tech_field=TechField.AI,
        position_type=PositionType.TECHNICAL,
        required_skills="Python, TensorFlow, PyTorch",
        job_description="负责AI模型开发和优化",
        evaluation_criteria="机器学习经验, 编程能力, 算法设计能力"
    )
    db.add(ai_position)
    
    db.commit()
    
    yield db
    db.close()

@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.rollback()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# 获取测试用户的token
@pytest.fixture(scope="function")
def user_token(client):
    response = client.post(
        "/api/v1/users/login",
        data={"username": "testuser@example.com", "password": "password123"}
    )
    return response.json()["access_token"]

# 获取管理员用户的token
@pytest.fixture(scope="function")
def admin_token(client):
    response = client.post(
        "/api/v1/users/login",
        data={"username": "admin@example.com", "password": "admin123"}
    )
    return response.json()["access_token"]

# 测试用户注册接口
def test_register_user(client, test_db):
    # 测试正常注册
    response = client.post(
        "/api/v1/users/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    
    # 测试重复邮箱注册
    response = client.post(
        "/api/v1/users/register",
        json={
            "username": "anotheruser",
            "email": "newuser@example.com",
            "password": "anotherpassword123"
        }
    )
    assert response.status_code == 400
    assert "邮箱已被注册" in response.json()["detail"]
    
    # 测试重复用户名注册
    response = client.post(
        "/api/v1/users/register",
        json={
            "username": "newuser",
            "email": "different@example.com",
            "password": "newpassword123"
        }
    )
    assert response.status_code == 400
    assert "用户名已被使用" in response.json()["detail"]

# 测试用户登录接口
def test_login_user(client, test_db):
    # 测试正确登录
    response = client.post(
        "/api/v1/users/login",
        data={"username": "testuser@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # 测试错误密码
    response = client.post(
        "/api/v1/users/login",
        data={"username": "testuser@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "认证失败" in response.json()["detail"]
    
    # 测试不存在的用户
    response = client.post(
        "/api/v1/users/login",
        data={"username": "nonexistent@example.com", "password": "password123"}
    )
    assert response.status_code == 401
    assert "认证失败" in response.json()["detail"]

# 测试获取当前用户信息
def test_get_current_user(client, user_token):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert not data["is_admin"]

# 测试职位创建接口
def test_create_job_position(client, admin_token, user_token):
    # 测试管理员创建职位
    job_data = {
        "title": "前端开发工程师",
        "tech_field": "artificial_intelligence",
        "position_type": "technical",
        "required_skills": "JavaScript, Vue, React",
        "job_description": "负责前端界面开发和用户体验优化",
        "evaluation_criteria": "前端框架经验, UI设计能力, 代码质量"
    }
    response = client.post(
        "/api/v1/job-positions",
        json=job_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "前端开发工程师"
    assert "id" in data
    
    # 测试普通用户创建职位（应该失败）
    response = client.post(
        "/api/v1/job-positions",
        json=job_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403

# 测试获取职位列表
def test_get_job_positions(client):
    response = client.get("/api/v1/job-positions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # 至少有我们预先创建的两个职位
    assert any(job["title"] == "测试工程师" for job in data)
    assert any(job["title"] == "AI开发工程师" for job in data)

# 测试获取单个职位
def test_get_job_position(client, test_db):
    # 获取第一个职位的ID
    job = test_db.query(JobPosition).first()
    job_id = job.id
    
    response = client.get(f"/api/v1/job-positions/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["title"] == job.title

# 测试更新职位
def test_update_job_position(client, admin_token, test_db):
    # 获取第一个职位的ID
    job = test_db.query(JobPosition).first()
    job_id = job.id
    
    update_data = {
        "title": "高级测试工程师",
        "tech_field": job.tech_field.value,
        "position_type": job.position_type.value,
        "required_skills": "Python, 测试自动化, CI/CD",
        "job_description": job.job_description,
        "evaluation_criteria": job.evaluation_criteria
    }
    
    response = client.put(
        f"/api/v1/job-positions/{job_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "高级测试工程师"
    assert data["required_skills"] == "Python, 测试自动化, CI/CD"

# 测试删除职位
def test_delete_job_position(client, admin_token, test_db):
    # 创建一个新职位用于删除测试
    new_job = JobPosition(
        title="临时职位",
        tech_field=TechField.SYSTEM,
        position_type=PositionType.PRODUCT,
        required_skills="临时技能",
        job_description="临时描述",
        evaluation_criteria="临时标准"
    )
    test_db.add(new_job)
    test_db.commit()
    test_db.refresh(new_job)
    job_id = new_job.id
    
    response = client.delete(
        f"/api/v1/job-positions/{job_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # 验证职位已被删除
    job = test_db.query(JobPosition).filter(JobPosition.id == job_id).first()
    assert job is None

# 测试上传面试文件
@patch("app.api.api_v1.endpoints.interviews.shutil.copyfileobj")
@patch("app.api.api_v1.endpoints.interviews.os.makedirs")
@patch("app.api.api_v1.endpoints.interviews.cv2.VideoCapture")
def test_upload_interview(mock_video_capture, mock_makedirs, mock_copyfileobj, client, user_token, test_db):
    # 模拟视频文件
    mock_video = MagicMock()
    mock_video.get.return_value = 30.0  # 模拟30秒的视频
    mock_video_capture.return_value = mock_video
    
    # 获取职位ID
    job = test_db.query(JobPosition).first()
    job_id = job.id
    
    # 创建测试文件
    test_file = io.BytesIO(b"test video content")
    test_file.name = "test_video.mp4"
    
    response = client.post(
        "/api/v1/interviews/upload/",
        files={"file": ("test_video.mp4", test_file, "video/mp4")},
        data={
            "title": "测试面试",
            "description": "这是一个测试面试",
            "job_position_id": str(job_id)
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "测试面试"
    assert data["description"] == "这是一个测试面试"
    assert data["job_position_id"] == job_id
    assert "id" in data

# 测试获取用户面试列表
def test_get_user_interviews(client, user_token, test_db):
    # 获取用户ID
    user = test_db.query(User).filter(User.username == "testuser").first()
    user_id = user.id
    
    # 获取职位ID
    job = test_db.query(JobPosition).first()
    job_id = job.id
    
    # 创建测试面试记录
    test_interview = Interview(
        user_id=user_id,
        job_position_id=job_id,
        title="测试面试记录",
        description="这是一个测试面试记录",
        file_path="/fake/path/test.mp4",
        file_type=FileType.VIDEO,
        duration=60.0
    )
    test_db.add(test_interview)
    test_db.commit()
    
    response = client.get(
        "/api/v1/interviews/user",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(interview["title"] == "测试面试记录" for interview in data)

# 测试获取单个面试详情
def test_get_interview(client, user_token, test_db):
    # 获取用户的面试记录
    user = test_db.query(User).filter(User.username == "testuser").first()
    interview = test_db.query(Interview).filter(Interview.user_id == user.id).first()
    
    if not interview:
        # 如果没有面试记录，创建一个
        job = test_db.query(JobPosition).first()
        interview = Interview(
            user_id=user.id,
            job_position_id=job.id,
            title="测试面试记录",
            description="这是一个测试面试记录",
            file_path="/fake/path/test.mp4",
            file_type=FileType.VIDEO,
            duration=60.0
        )
        test_db.add(interview)
        test_db.commit()
        test_db.refresh(interview)
    
    interview_id = interview.id
    
    response = client.get(
        f"/api/v1/interviews/{interview_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == interview_id
    assert data["title"] == interview.title

# 测试创建面试分析
@patch("app.api.api_v1.endpoints.analysis.analyze_interview")
def test_create_analysis(mock_analyze, client, user_token, test_db):
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
    
    # 获取用户的面试记录
    user = test_db.query(User).filter(User.username == "testuser").first()
    interview = test_db.query(Interview).filter(Interview.user_id == user.id).first()
    
    if not interview:
        # 如果没有面试记录，创建一个
        job = test_db.query(JobPosition).first()
        interview = Interview(
            user_id=user.id,
            job_position_id=job.id,
            title="测试面试记录",
            description="这是一个测试面试记录",
            file_path="/fake/path/test.mp4",
            file_type=FileType.VIDEO,
            duration=60.0
        )
        test_db.add(interview)
        test_db.commit()
        test_db.refresh(interview)
    
    interview_id = interview.id
    
    response = client.post(
        f"/api/v1/analysis/{interview_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["interview_id"] == interview_id
    assert data["overall_score"] == 85.5
    assert "strengths" in data
    assert "weaknesses" in data
    assert "suggestions" in data

# 测试获取分析结果
def test_get_analysis(client, user_token, test_db):
    # 获取用户的面试记录
    user = test_db.query(User).filter(User.username == "testuser").first()
    interview = test_db.query(Interview).filter(Interview.user_id == user.id).first()
    
    if not interview:
        # 如果没有面试记录，创建一个
        job = test_db.query(JobPosition).first()
        interview = Interview(
            user_id=user.id,
            job_position_id=job.id,
            title="测试面试记录",
            description="这是一个测试面试记录",
            file_path="/fake/path/test.mp4",
            file_type=FileType.VIDEO,
            duration=60.0
        )
        test_db.add(interview)
        test_db.commit()
        test_db.refresh(interview)
    
    interview_id = interview.id
    
    # 创建分析结果
    analysis = Analysis(
        interview_id=interview_id,
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
    test_db.add(analysis)
    test_db.commit()
    
    response = client.get(
        f"/api/v1/analysis/{interview_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["interview_id"] == interview_id
    assert data["overall_score"] == 85.5
    assert "strengths" in data
    assert "weaknesses" in data
    assert "suggestions" in data