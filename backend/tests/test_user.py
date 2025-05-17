import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.database import Base, get_db
from app.main import app as original_app
from app.core.config import settings
from app.api.api_v1.api import api_router
from pydantic import BaseModel, ConfigDict

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