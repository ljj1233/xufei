import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.main import app
from app.core.config import settings
import json
from app.models.user import User
from app.core.security import get_password_hash

# 使用conftest_admin.py中的测试夹具
from conftest_admin import admin_test_db, admin_client, admin_token

# 测试用户注册的全面功能
def test_register_user_comprehensive(admin_client):
    # 测试正常注册
    response = admin_client.post(
        "/api/v1/users/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    
    # 测试重复邮箱注册
    response = admin_client.post(
        "/api/v1/users/register",
        json={
            "username": "anotheruser",
            "email": "newuser@example.com",
            "password": "anotherpassword123"
        }
    )
    assert response.status_code == 400
    assert "邮箱已被注册" in response.json()["detail"]
    
    # 测试重复用户名注册
    response = admin_client.post(
        "/api/v1/users/register",
        json={
            "username": "newuser",
            "email": "different@example.com",
            "password": "newpassword123"
        }
    )
    assert response.status_code == 400
    assert "用户名已被使用" in response.json()["detail"]
    
    # 测试密码过短
    response = admin_client.post(
        "/api/v1/users/register",
        json={
            "username": "shortpwduser",
            "email": "shortpwd@example.com",
            "password": "short"
        }
    )
    assert response.status_code == 400
    assert "密码长度" in response.json()["detail"]
    
    # 测试无效邮箱格式
    response = admin_client.post(
        "/api/v1/users/register",
        json={
            "username": "invalidemail",
            "email": "notanemail",
            "password": "validpassword123"
        }
    )
    assert response.status_code == 400
    assert "邮箱格式" in response.json()["detail"]

# 测试用户登录的全面功能
def test_login_user_comprehensive(admin_client, admin_test_db):
    # 创建测试用户
    test_user = User(
        username="logintest",
        email="logintest@example.com",
        hashed_password=get_password_hash("loginpassword123"),
        is_active=True,
        is_admin=False
    )
    admin_test_db.add(test_user)
    admin_test_db.commit()
    
    # 测试使用邮箱登录
    response = admin_client.post(
        "/api/v1/users/login",
        data={"username": "logintest@example.com", "password": "loginpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # 测试使用用户名登录
    response = admin_client.post(
        "/api/v1/users/login",
        data={"username": "logintest", "password": "loginpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    
    # 测试错误密码
    response = admin_client.post(
        "/api/v1/users/login",
        data={"username": "logintest@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "认证失败" in response.json()["detail"]
    
    # 测试不存在的用户
    response = admin_client.post(
        "/api/v1/users/login",
        data={"username": "nonexistent@example.com", "password": "password123"}
    )
    assert response.status_code == 401
    assert "认证失败" in response.json()["detail"]
    
    # 测试非激活用户
    inactive_user = User(
        username="inactive",
        email="inactive@example.com",
        hashed_password=get_password_hash("inactivepassword123"),
        is_active=False,
        is_admin=False
    )
    admin_test_db.add(inactive_user)
    admin_test_db.commit()
    
    response = admin_client.post(
        "/api/v1/users/login",
        data={"username": "inactive@example.com", "password": "inactivepassword123"}
    )
    assert response.status_code == 401
    assert "用户未激活" in response.json()["detail"]

# 获取测试用户的token
@pytest.fixture(scope="function")
def test_user_token(admin_client, admin_test_db):
    # 创建测试用户
    test_user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_admin=False
    )
    admin_test_db.add(test_user)
    admin_test_db.commit()
    
    response = admin_client.post(
        "/api/v1/users/login",
        data={"username": "testuser@example.com", "password": "password123"}
    )
    return response.json()["access_token"]

# 测试获取当前用户信息
def test_get_current_user(admin_client, test_user_token):
    response = admin_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert not data["is_admin"]

# 测试更新用户信息
def test_update_user(admin_client, test_user_token, admin_test_db):
    # 获取用户ID
    user = admin_test_db.query(User).filter(User.username == "testuser").first()
    user_id = user.id
    
    # 更新用户信息
    update_data = {
        "username": "updateduser",
        "email": "updated@example.com"
    }
    
    response = admin_client.put(
        f"/api/v1/users/{user_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "updateduser"
    assert data["email"] == "updated@example.com"

# 测试更改密码
def test_change_password(admin_client, test_user_token):
    response = admin_client.post(
        "/api/v1/users/change-password",
        json={
            "current_password": "password123",
            "new_password": "newpassword456"
        },
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    
    # 测试使用新密码登录
    response = admin_client.post(
        "/api/v1/users/login",
        data={"username": "updateduser@example.com", "password": "newpassword456"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

# 测试管理员功能
def test_admin_functions(admin_client, admin_token, admin_test_db):
    # 创建普通用户
    regular_user = User(
        username="regularuser",
        email="regular@example.com",
        hashed_password=get_password_hash("regular123"),
        is_active=True,
        is_admin=False
    )
    admin_test_db.add(regular_user)
    admin_test_db.commit()
    admin_test_db.refresh(regular_user)
    
    # 获取所有用户（管理员权限）
    response = admin_client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # 至少有管理员和普通用户
    
    # 获取特定用户（管理员权限）
    response = admin_client.get(
        f"/api/v1/users/{regular_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "regularuser"
    
    # 更新用户状态（激活/停用）
    response = admin_client.patch(
        f"/api/v1/users/{regular_user.id}/status",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert not data["is_active"]
    
    # 授予管理员权限
    response = admin_client.patch(
        f"/api/v1/users/{regular_user.id}/admin",
        json={"is_admin": True},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_admin"]
    
    # 删除用户
    response = admin_client.delete(
        f"/api/v1/users/{regular_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # 验证用户已被删除
    user = admin_test_db.query(User).filter(User.id == regular_user.id).first()
    assert user is None

# 测试权限控制
def test_permission_control(admin_client, test_user_token, admin_token, admin_test_db):
    # 创建另一个普通用户
    another_user = User(
        username="anotheruser",
        email="another@example.com",
        hashed_password=get_password_hash("another123"),
        is_active=True,
        is_admin=False
    )
    admin_test_db.add(another_user)
    admin_test_db.commit()
    admin_test_db.refresh(another_user)
    
    # 普通用户尝试获取所有用户（应该失败）
    response = admin_client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 403
    
    # 普通用户尝试获取其他用户信息（应该失败）
    response = admin_client.get(
        f"/api/v1/users/{another_user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 403
    
    # 普通用户尝试更新其他用户信息（应该失败）
    response = admin_client.put(
        f"/api/v1/users/{another_user.id}",
        json={"username": "hacked"},
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 403
    
    # 普通用户尝试删除其他用户（应该失败）
    response = admin_client.delete(
        f"/api/v1/users/{another_user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 403
    
    # 验证用户未被删除
    user = admin_test_db.query(User).filter(User.id == another_user.id).first()
    assert user is not None