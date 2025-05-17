import pytest
from sqlalchemy import text
from app.db.database import engine, Base
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="function")
def test_db():
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.rollback()