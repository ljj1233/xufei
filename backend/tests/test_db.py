import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db.models import User, Interview, AnalysisResult
from app.core.config import settings
import os
import datetime

# 使用测试数据库
TEST_DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/test_interview_db"

# 创建测试引擎和会话
@pytest.fixture(scope="module")
def test_db():
    """创建测试数据库会话"""
    engine = create_engine(TEST_DATABASE_URL)
    # 创建表
    Base.metadata.create_all(engine)
    # 创建会话
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # 清理表
        Base.metadata.drop_all(engine)


# 测试用户模型
def test_user_model(test_db):
    """测试用户模型的创建和查询"""
    # 创建测试用户
    test_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    
    # 添加到数据库
    test_db.add(test_user)
    test_db.commit()
    test_db.refresh(test_user)
    
    # 查询用户
    user = test_db.query(User).filter(User.username == "testuser").first()
    
    # 验证用户数据
    assert user is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.hashed_password == "hashed_password"
    assert user.created_at is not None


# 测试面试模型
def test_interview_model(test_db):
    """测试面试模型的创建和查询"""
    # 先创建用户
    user = test_db.query(User).filter(User.username == "testuser").first()
    if not user:
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
    
    # 创建测试面试
    test_interview = Interview(
        title="测试面试",
        description="这是一个测试面试",
        file_path="/path/to/test/file.mp3",
        file_type="audio",
        tech_field="人工智能",
        position_type="技术岗",
        status="pending",
        user_id=user.id
    )
    
    # 添加到数据库
    test_db.add(test_interview)
    test_db.commit()
    test_db.refresh(test_interview)
    
    # 查询面试
    interview = test_db.query(Interview).filter(Interview.title == "测试面试").first()
    
    # 验证面试数据
    assert interview is not None
    assert interview.title == "测试面试"
    assert interview.description == "这是一个测试面试"
    assert interview.file_path == "/path/to/test/file.mp3"
    assert interview.file_type == "audio"
    assert interview.tech_field == "人工智能"
    assert interview.position_type == "技术岗"
    assert interview.status == "pending"
    assert interview.user_id == user.id
    assert interview.created_at is not None


# 测试分析结果模型
def test_analysis_result_model(test_db):
    """测试分析结果模型的创建和查询"""
    # 获取面试
    interview = test_db.query(Interview).filter(Interview.title == "测试面试").first()
    if not interview:
        # 如果面试不存在，先创建用户和面试
        user = test_db.query(User).filter(User.username == "testuser").first()
        if not user:
            user = User(
                username="testuser",
                email="test@example.com",
                hashed_password="hashed_password"
            )
            test_db.add(user)
            test_db.commit()
            test_db.refresh(user)
        
        interview = Interview(
            title="测试面试",
            description="这是一个测试面试",
            file_path="/path/to/test/file.mp3",
            file_type="audio",
            tech_field="人工智能",
            position_type="技术岗",
            status="pending",
            user_id=user.id
        )
        test_db.add(interview)
        test_db.commit()
        test_db.refresh(interview)
    
    # 创建测试分析结果
    test_result = AnalysisResult(
        interview_id=interview.id,
        speech_text="这是一段测试面试的回答。",
        speech_assessment={
            "fluency": 85.5,
            "integrity": 90.2,
            "pronunciation": 88.7,
            "speed": 4.5
        },
        emotion_analysis={
            "positive": 0.75,
            "neutral": 0.20,
            "negative": 0.05
        },
        professional_score=85,
        skill_match_score=80,
        expression_score=90,
        logical_score=85,
        innovation_score=75,
        pressure_score=85,
        overall_score=83,
        improvement_suggestions=["建议1", "建议2", "建议3"]
    )
    
    # 添加到数据库
    test_db.add(test_result)
    test_db.commit()
    test_db.refresh(test_result)
    
    # 查询分析结果
    result = test_db.query(AnalysisResult).filter(AnalysisResult.interview_id == interview.id).first()
    
    # 验证分析结果数据
    assert result is not None
    assert result.interview_id == interview.id
    assert result.speech_text == "这是一段测试面试的回答。"
    assert result.speech_assessment["fluency"] == 85.5
    assert result.emotion_analysis["positive"] == 0.75
    assert result.professional_score == 85
    assert result.skill_match_score == 80
    assert result.expression_score == 90
    assert result.logical_score == 85
    assert result.innovation_score == 75
    assert result.pressure_score == 85
    assert result.overall_score == 83
    assert len(result.improvement_suggestions) == 3
    assert result.created_at is not None