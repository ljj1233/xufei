import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.main import app as original_app
from app.core.config import settings
from app.api.api_v1.api import api_router
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, text, Column, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, declared_attr
from app.core.config import settings
import logging


# PostgreSQL 测试数据库连接字符串
TEST_DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/interview_analysis_test"
)

@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"options": "-c timezone=Asia/Shanghai"}
    )
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
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


def test_register_and_login(client):
    user = {"username": "user1", "email": "user1@example.com", "password": "12345678Aa!"}
    r = client.post(f"{settings.API_V1_STR}/users/register", json=user)
    assert r.status_code in (200, 201)
    login_data = {"username": "user1", "password": "12345678Aa!"}
    r2 = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
    assert r2.status_code == 200
    assert "access_token" in r2.json()