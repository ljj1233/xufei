import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.database import Base, get_db
from app.main import app
from app.core.config import settings
import os
import json
from app.models.user import User
from app.core.security import get_password_hash

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
    
    # 预先创建一个测试用户
    test_user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_admin=False
    )
    db.add(test_user)
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

# 用户API测试
class TestUserAPI:
    
    def test_register_user(self, client):
        """测试用户注册功能"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "Password123!"
        }
        
        response = client.post(f"{settings.API_V1_STR}/users/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data
    
    def test_register_existing_user(self, client):
        """测试注册已存在的用户名"""
        user_data = {
            "username": "testuser",  # 已存在的用户名
            "email": "another@example.com",
            "password": "Password123!"
        }
        
        response = client.post(f"{settings.API_V1_STR}/users/register", json=user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_login_user(self, client):
        """测试用户登录功能"""
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        
        response = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client):
        """测试错误密码登录"""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_get_current_user(self, client):
        """测试获取当前用户信息"""
        # 先登录获取token
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        login_response = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # 使用token获取用户信息
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "testuser@example.com"
    
    def test_get_user_unauthorized(self, client):
        """测试未授权获取用户信息"""
        response = client.get(f"{settings.API_V1_STR}/users/me")
        assert response.status_code == 401
        
    def test_update_user(self, client):
        """测试更新用户信息"""
        # 先登录获取token
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        login_response = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # 更新用户信息
        update_data = {
            "email": "updated@example.com"
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put(f"{settings.API_V1_STR}/users/me", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == update_data["email"]
        
    def test_delete_user(self, client):
        """测试删除用户"""
        # 先创建一个新用户
        user_data = {
            "username": "usertoremove",
            "email": "remove@example.com",
            "password": "Password123!"
        }
        client.post(f"{settings.API_V1_STR}/users/register", json=user_data)
        
        # 登录新用户
        login_data = {
            "username": "usertoremove",
            "password": "Password123!"
        }
        login_response = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # 删除用户
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete(f"{settings.API_V1_STR}/users/me", headers=headers)
        
        assert response.status_code == 200
        
        # 尝试再次登录已删除的用户
        login_response = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
        assert login_response.status_code == 401