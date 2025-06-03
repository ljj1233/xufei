import pytest
import json
from unittest.mock import patch, MagicMock
from app.services.analysis_service import AnalysisService
from app.models.interview import Interview, FileType
from app.models.analysis import Analysis
from app.models.user import User
from app.models.job_position import JobPosition, TechField, PositionType
from app.core.security import get_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.database import Base
import os

# 创建内存数据库用于测试
@pytest.fixture(scope="function")
def test_db():
    # 使用SQLite内存数据库进行测试
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
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
    
    # 预先创建测试面试
    test_interview = Interview(
        user_id=test_user.id,
        job_position_id=test_position.id,
        title="测试面试",
        description="这是一个测试面试",
        file_path="/fake/path/test.mp3",
        file_type=FileType.AUDIO,
        duration=120.5
    )
    db.add(test_interview)
    db.commit()
    
    yield db
    db.close()
    engine.dispose()

# 分析服务测试
class TestAnalysisService:
    
    @patch("app.services.analysis_service.XunfeiService")
    def test_analyze_interview(self, mock_xunfei, test_db):
        """测试面试分析功能"""
        # 获取测试面试
        interview = test_db.query(Interview).first()
        
        # 模拟讯飞服务返回结果
        mock_xunfei_instance = MagicMock()
        mock_xunfei_instance.speech_recognition.return_value = "这是一段测试的面试回答内容，我有丰富的项目经验和技术能力。"
        mock_xunfei_instance.speech_assessment.return_value = {
            "fluency": 85.5,
            "clarity": 90.2,
            "pronunciation": 88.7,
            "speed": 4.5
        }
        mock_xunfei_instance.emotion_analysis.return_value = {
            "emotion": "积极",
            "confidence": 0.85
        }
        mock_xunfei.return_value = mock_xunfei_instance
        
        # 创建分析服务实例
        analysis_service = AnalysisService(db=test_db, xunfei_service=mock_xunfei_instance)
        
        # 模拟视频/音频文件存在
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", MagicMock()):
                # 执行分析
                result = analysis_service.analyze_interview(interview.id)
        
        # 验证分析结果
        assert result is not None
        assert "overall_score" in result
        assert "strengths" in result
        assert "weaknesses" in result
        assert "suggestions" in result
        assert "speech_clarity" in result
        assert "facial_expressions" in result
        assert "content_relevance" in result
        assert "professional_knowledge" in result
        
        # 验证数据库中是否创建了分析记录
        analysis = test_db.query(Analysis).filter(Analysis.interview_id == interview.id).first()
        assert analysis is not None
        assert analysis.overall_score > 0
        assert len(analysis.strengths) > 0
        assert len(analysis.weaknesses) > 0
        assert len(analysis.suggestions) > 0
    
    def test_get_analysis(self, test_db):
        """测试获取分析结果"""
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
        
        # 创建分析服务实例
        analysis_service = AnalysisService(db=test_db)
        
        # 获取分析结果
        result = analysis_service.get_analysis(interview.id)
        
        # 验证结果
        assert result is not None
        assert result.interview_id == interview.id
        assert result.overall_score == test_analysis.overall_score
        assert result.strengths == test_analysis.strengths
        assert result.weaknesses == test_analysis.weaknesses
        assert result.speech_clarity == test_analysis.speech_clarity
        assert result.professional_knowledge == test_analysis.professional_knowledge
    
    def test_analyze_speech(self, test_db):
        """测试语音分析功能"""
        # 创建分析服务实例
        analysis_service = AnalysisService(test_db)
        
        # 模拟语音识别文本和情感分析结果
        transcript = "这是一段测试的面试回答内容，我有丰富的项目经验和技术能力。"
        emotion_result = {"emotion": "积极", "confidence": 0.85}
        
        # 执行语音分析
        with patch.object(analysis_service, "_calculate_speech_clarity", return_value=90.0):
            with patch.object(analysis_service, "_calculate_speech_pace", return_value=75.0):
                with patch.object(analysis_service, "_calculate_speech_logic", return_value=85.0):
                    result = analysis_service._analyze_speech(transcript, emotion_result)
        
        # 验证结果
        assert result is not None
        assert "speech_clarity" in result
        assert result["speech_clarity"] == 90.0
        assert "speech_pace" in result
        assert result["speech_pace"] == 75.0
        assert "speech_emotion" in result
        assert result["speech_emotion"] == "积极"
        assert "speech_logic" in result
        assert result["speech_logic"] == 85.0
    
    def test_analyze_content(self, test_db):
        """测试内容分析功能"""
        # 获取测试面试和职位
        interview = test_db.query(Interview).first()
        job_position = test_db.query(JobPosition).first()
        
        # 创建分析服务实例
        analysis_service = AnalysisService(test_db)
        
        # 模拟面试文本
        transcript = """我在过去的项目中担任测试工程师角色，负责自动化测试框架的搭建和维护。
        在一个关键项目中，我们面临的挑战是测试效率低下，测试周期长。
        我设计并实现了一套基于Python的自动化测试框架，集成了CI/CD流程。
        最终，测试效率提升了60%，测试覆盖率提高到90%以上，大大缩短了产品发布周期。
        我擅长Python编程和测试自动化工具的使用，有丰富的测试经验。"""
        
        # 执行内容分析
        with patch.object(analysis_service, "_calculate_content_relevance", return_value=90.0):
            with patch.object(analysis_service, "_calculate_content_structure", return_value=85.0):
                with patch.object(analysis_service, "_extract_key_points", return_value=["自动化测试", "Python", "效率提升"]):
                    with patch.object(analysis_service, "_evaluate_professional_skills", return_value={
                        "professional_knowledge": 88.0,
                        "skill_matching": 85.0,
                        "logical_thinking": 87.0,
                        "innovation_ability": 80.0,
                        "stress_handling": 82.0
                    }):
                        with patch.object(analysis_service, "_evaluate_star_structure", return_value={
                            "situation_score": 85.0,
                            "task_score": 88.0,
                            "action_score": 90.0,
                            "result_score": 85.0
                        }):
                            result = analysis_service._analyze_content(transcript, job_position)
        
        # 验证结果
        assert result is not None
        assert "content_relevance" in result
        assert result["content_relevance"] == 90.0
        assert "content_structure" in result
        assert result["content_structure"] == 85.0
        assert "key_points" in result
        assert len(result["key_points"]) == 3
        assert "professional_knowledge" in result
        assert result["professional_knowledge"] == 88.0
        assert "situation_score" in result
        assert result["situation_score"] == 85.0
    
    def test_generate_overall_analysis(self, test_db):
        """测试生成综合分析结果"""
        # 创建分析服务实例
        analysis_service = AnalysisService(test_db)
        
        # 模拟各部分分析结果
        speech_analysis = {
            "speech_clarity": 90.0,
            "speech_pace": 75.0,
            "speech_emotion": "积极",
            "speech_logic": 85.0
        }
        
        visual_analysis = {
            "facial_expressions": {"微笑": 60, "专注": 40},
            "eye_contact": 85.0,
            "body_language": {"自信": 80, "放松": 20}
        }
        
        content_analysis = {
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
        
        # 执行综合分析
        with patch.object(analysis_service, "_calculate_overall_score", return_value=86.5):
            with patch.object(analysis_service, "_identify_strengths", return_value=["表达清晰", "专业知识扎实", "逻辑思维能力强"]):
                with patch.object(analysis_service, "_identify_weaknesses", return_value=["眼神接触不足", "创新性表现一般"]):
                    with patch.object(analysis_service, "_generate_suggestions", return_value=["增加眼神接触", "准备更多创新性案例"]):
                        result = analysis_service._generate_overall_analysis(
                            speech_analysis, visual_analysis, content_analysis
                        )
        
        # 验证结果
        assert result is not None
        assert "overall_score" in result
        assert result["overall_score"] == 86.5
        assert "strengths" in result
        assert len(result["strengths"]) == 3
        assert "weaknesses" in result
        assert len(result["weaknesses"]) == 2
        assert "suggestions" in result
        assert len(result["suggestions"]) == 2