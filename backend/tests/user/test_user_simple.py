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


@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        settings.DATABASE_URI,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=3600,  # 连接回收时间
        pool_pre_ping=True  # 连接前ping测试
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