import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.database import Base
from app.db.models import User, Interview, InterviewAnalysis

@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    engine.dispose()

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
    interview = Interview(title="面试1", description="desc", file_path="/tmp/a.mp3", file_type="audio", user_id=user.id)
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
    interview = Interview(title="面试1", description="desc", file_path="/tmp/a.mp3", file_type="audio", user_id=user.id)
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