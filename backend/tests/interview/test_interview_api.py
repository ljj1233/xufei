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
    
    # 预先创建测试用户
    test_user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_admin=False
    )
    db.add(test_user)
    db.commit()
    
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
    db.commit()
    
    yield db
    db.close()
    engine.dispose()

@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.rollback()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides = {}

@pytest.fixture(scope="function")
def auth_headers(client):
    # 登录获取token
    login_data = {
        "username": "testuser",
        "password": "password123"
    }
    login_response = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
    token = login_response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

# 面试API测试
class TestInterviewAPI:
    
    def test_create_interview(self, client, test_db, auth_headers, tmp_path):
        """测试创建面试记录"""
        # 获取测试用户和职位ID
        user = test_db.query(User).filter(User.username == "testuser").first()
        job_position = test_db.query(JobPosition).first()
        
        # 创建测试音频文件
        test_audio = tmp_path / "test_audio.mp3"
        test_audio.write_bytes(b"test audio content")
        
        # 创建面试记录
        with open(test_audio, "rb") as f:
            files = {"file": ("test_audio.mp3", f, "audio/mpeg")}
            form_data = {
                "title": "测试面试",
                "description": "这是一个测试面试",
                "job_position_id": str(job_position.id),
                "file_type": "audio"
            }
            response = client.post(
                f"{settings.API_V1_STR}/interviews/",
                files=files,
                data=form_data,
                headers=auth_headers
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "测试面试"
        assert data["description"] == "这是一个测试面试"
        assert data["job_position_id"] == job_position.id
        assert data["user_id"] == user.id
        assert data["file_type"] == "audio"
        assert "id" in data
    
    def test_get_interviews(self, client, test_db, auth_headers):
        """测试获取面试列表"""
        # 获取测试用户和职位
        user = test_db.query(User).filter(User.username == "testuser").first()
        job_position = test_db.query(JobPosition).first()
        
        # 创建测试面试记录
        test_interview = Interview(
            user_id=user.id,
            job_position_id=job_position.id,
            title="测试面试2",
            description="这是第二个测试面试",
            file_path="/fake/path/test.mp3",
            file_type=FileType.AUDIO,
            duration=120.5
        )
        test_db.add(test_interview)
        test_db.commit()
        
        # 获取面试列表
        response = client.get(f"{settings.API_V1_STR}/interviews/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(interview["title"] == "测试面试2" for interview in data)
    
    def test_get_interview_by_id(self, client, test_db, auth_headers):
        """测试通过ID获取面试详情"""
        # 获取测试面试
        interview = test_db.query(Interview).first()
        
        # 获取面试详情
        response = client.get(f"{settings.API_V1_STR}/interviews/{interview.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == interview.id
        assert data["title"] == interview.title
        assert data["description"] == interview.description
    
    def test_update_interview(self, client, test_db, auth_headers):
        """测试更新面试信息"""
        # 获取测试面试
        interview = test_db.query(Interview).first()
        
        # 更新面试信息
        update_data = {
            "title": "更新后的面试标题",
            "description": "更新后的面试描述"
        }
        response = client.put(
            f"{settings.API_V1_STR}/interviews/{interview.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
    
    def test_delete_interview(self, client, test_db, auth_headers):
        """测试删除面试"""
        # 获取测试用户和职位
        user = test_db.query(User).filter(User.username == "testuser").first()
        job_position = test_db.query(JobPosition).first()
        
        # 创建要删除的测试面试
        test_interview = Interview(
            user_id=user.id,
            job_position_id=job_position.id,
            title="要删除的面试",
            description="这个面试将被删除",
            file_path="/fake/path/delete.mp3",
            file_type=FileType.AUDIO,
            duration=60.0
        )
        test_db.add(test_interview)
        test_db.commit()
        test_db.refresh(test_interview)
        
        # 删除面试
        response = client.delete(f"{settings.API_V1_STR}/interviews/{test_interview.id}", headers=auth_headers)
        
        assert response.status_code == 200
        
        # 确认面试已被删除
        check_response = client.get(f"{settings.API_V1_STR}/interviews/{test_interview.id}", headers=auth_headers)
        assert check_response.status_code == 404

# 面试分析API测试
class TestInterviewAnalysisAPI:
    
    @patch("app.services.analysis_service.AnalysisService.analyze_interview")
    def test_analyze_interview(self, mock_analyze, client, test_db, auth_headers):
        """测试面试分析功能"""
        # 获取测试面试
        interview = test_db.query(Interview).first()
        
        # 模拟分析服务返回结果
        mock_analysis_result = {
            "overall_score": 85.5,
            "strengths": ["沟通能力强", "专业知识扎实"],
            "weaknesses": ["回答有些冗长"],
            "suggestions": ["可以更加简洁地表达核心观点"],
            "speech_clarity": 90.0,
            "speech_pace": 75.0,
            "speech_emotion": "积极",
            "speech_logic": 85.0,
            "facial_expressions": {"微笑": 60, "严肃": 30, "思考": 10},
            "eye_contact": 80.0,
            "body_language": {"自信": 85, "紧张": 15},
            "content_relevance": 90.0,
            "content_structure": 85.0,
            "key_points": ["项目经验", "技术能力", "团队协作"],
            "professional_knowledge": 88.0,
            "skill_matching": 85.0,
            "logical_thinking": 87.0,
            "innovation_ability": 80.0,
            "stress_handling": 82.0,
            "situation_score": 85.0,
            "task_score": 88.0,
            "action_score": 90.0,
            "result_score": 85.0
        }
        mock_analyze.return_value = mock_analysis_result
        
        # 请求分析面试
        response = client.post(f"{settings.API_V1_STR}/interviews/{interview.id}/analyze", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["interview_id"] == interview.id
        assert data["overall_score"] == mock_analysis_result["overall_score"]
        assert data["strengths"] == mock_analysis_result["strengths"]
        
        # 验证数据库中是否创建了分析记录
        analysis = test_db.query(Analysis).filter(Analysis.interview_id == interview.id).first()
        assert analysis is not None
        assert analysis.overall_score == mock_analysis_result["overall_score"]
    
    def test_get_interview_analysis(self, client, test_db, auth_headers):
        """测试获取面试分析结果"""
        # 获取测试面试
        interview = test_db.query(Interview).first()
        
        # 创建测试分析结果
        test_analysis = Analysis(
            interview_id=interview.id,
            overall_score=88.5,
            strengths=["表达清晰", "逻辑性强"],
            weaknesses=["技术细节不够深入"],
            suggestions=["可以准备更多技术案例"],
            speech_clarity=92.0,
            speech_pace=78.0,
            speech_emotion="自信",
            speech_logic=90.0,
            facial_expressions={"微笑": 70, "专注": 30},
            eye_contact=85.0,
            body_language={"放松": 80, "自信": 20},
            content_relevance=88.0,
            content_structure=86.0,
            key_points=["技术背景", "项目经验", "解决问题能力"],
            professional_knowledge=90.0,
            skill_matching=87.0,
            logical_thinking=92.0,
            innovation_ability=85.0,
            stress_handling=88.0,
            situation_score=90.0,
            task_score=92.0,
            action_score=94.0,
            result_score=90.0
        )
        test_db.add(test_analysis)
        test_db.commit()
        
        # 获取分析结果
        response = client.get(f"{settings.API_V1_STR}/interviews/{interview.id}/analysis", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["interview_id"] == interview.id
        assert data["overall_score"] == test_analysis.overall_score
        assert data["strengths"] == test_analysis.strengths
        assert data["weaknesses"] == test_analysis.weaknesses
        assert data["speech_clarity"] == test_analysis.speech_clarity
        assert data["professional_knowledge"] == test_analysis.professional_knowledge