import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.main import app as original_app
from app.core.config import settings
from app.models.interview import Interview 
from app.models.analysis import InterviewAnalysis 
from app.models.user import User 


@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        settings.DATABASE_URI,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=3600,
        pool_pre_ping=True
    )
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"TRUNCATE TABLE {table.name};"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        conn.commit()
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    engine.dispose()

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

def test_user_model(test_db):
    user = User(username="testuser", email="test@example.com", hashed_password="hashed")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    u = test_db.query(User).filter_by(username="testuser").first()
    assert u is not None
    assert u.email == "test@example.com"

def test_interview_model(test_db):
    user = User(username="testuser", email="test@example.com", hashed_password="hashed")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    from app.models.job_position import JobPosition, PositionType
    job_position = JobPosition(title="开发工程师", tech_field="AI", position_type=PositionType.TECHNICAL, required_skills="Python", job_description="开发AI相关项目", evaluation_criteria="具备AI开发能力")
    test_db.add(job_position)
    test_db.commit()
    test_db.refresh(job_position)
    interview = Interview(title="面试1", description="desc", file_path="/tmp/a.mp3", file_type="audio", user_id=user.id, job_position_id=job_position.id)
    test_db.add(interview)
    test_db.commit()
    test_db.refresh(interview)
    i = test_db.query(Interview).filter_by(title="面试1").first()
    assert i is not None
    assert i.user_id == user.id

def test_analysis_model(test_db):
    user = User(username="testuser", email="test@example.com", hashed_password="hashed")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    from app.models.job_position import JobPosition, PositionType
    job_position = JobPosition(title="开发工程师", tech_field="AI", position_type=PositionType.TECHNICAL, required_skills="Python", job_description="开发AI相关项目", evaluation_criteria="具备AI开发能力")
    test_db.add(job_position)
    test_db.commit()
    test_db.refresh(job_position)
    interview = Interview(title="面试1", description="desc", file_path="/tmp/a.mp3", file_type="audio", user_id=user.id, job_position_id=job_position.id)
    test_db.add(interview)
    test_db.commit()
    test_db.refresh(interview)
    analysis = InterviewAnalysis(interview_id=interview.id, speech_clarity=8.0, overall_score=7.5)
    test_db.add(analysis)
    test_db.commit()
    test_db.refresh(analysis)
    a = test_db.query(InterviewAnalysis).filter_by(interview_id=interview.id).first()
    assert a is not None
    assert a.speech_clarity == 8.0