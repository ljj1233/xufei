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
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建SQLAlchemy引擎，添加连接池配置和重试机制
try:
    engine = create_engine(
        settings.DATABASE_URI,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=3600,  # 连接回收时间
        pool_pre_ping=True  # 连接前ping测试
    )
    logger.info(f"数据库连接成功: {settings.MYSQL_SERVER}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}")
except Exception as e:
    logger.error(f"数据库连接失败: {str(e)}")
    raise

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


def test_register_user_success(client):
    test_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test@password123"
    }
    response = client.post(f"{settings.API_V1_STR}/users/register", json=test_user)
    assert response.status_code == 200 or response.status_code == 201
    data = response.json()
    assert data["username"] == test_user["username"]
    assert "id" in data

def test_register_duplicate_username(client):
    test_user = {
        "username": "testuser",
        "email": "test1@example.com",
        "password": "Test@password123"
    }
    client.post(f"{settings.API_V1_STR}/users/register", json=test_user)
    duplicate_user = test_user.copy()
    duplicate_user["email"] = "test2@example.com"
    response = client.post(f"{settings.API_V1_STR}/users/register", json=duplicate_user)
    assert response.status_code == 400
    assert "用户名已被使用" in response.json()["detail"] or "username" in response.json()["detail"].lower()

def test_register_duplicate_email(client):
    test_user = {
        "username": "testuser1",
        "email": "test@example.com",
        "password": "Test@password123"
    }
    client.post(f"{settings.API_V1_STR}/users/register", json=test_user)
    duplicate_user = test_user.copy()
    duplicate_user["username"] = "testuser2"
    response = client.post(f"{settings.API_V1_STR}/users/register", json=duplicate_user)
    assert response.status_code == 400
    assert "邮箱已被注册" in response.json()["detail"] or "email" in response.json()["detail"].lower()

def test_login_user_success(client):
    test_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test@password123"
    }
    client.post(f"{settings.API_V1_STR}/users/register", json=test_user)
    login_data = {
        "username": "testuser",
        "password": "Test@password123"
    }
    response = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_user_wrong_password(client):
    test_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test@password123"
    }
    client.post(f"{settings.API_V1_STR}/users/register", json=test_user)
    login_data = {
        "username": "testuser",
        "password": "wrongpassword"
    }
    response = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
    assert response.status_code == 401
    assert "用户名或密码" in response.json()["detail"] or "错误" in response.json()["detail"]