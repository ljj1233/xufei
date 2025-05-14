import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
import os

# 创建测试客户端
client = TestClient(app)

# 测试用户相关API
def test_register_user():
    """测试用户注册API"""
    # 创建测试用户数据
    test_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    # 发送注册请求
    response = client.post(f"{settings.API_V1_STR}/users/register", json=test_user)
    
    # 验证响应
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert "password" not in data  # 确保密码不在响应中


def test_login_user():
    """测试用户登录API"""
    # 创建登录数据
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    # 发送登录请求
    response = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# 测试面试相关API
def test_upload_interview():
    """测试面试上传API"""
    # 模拟登录获取token
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    login_response = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # 准备测试文件和数据
    test_file_path = os.path.join(os.path.dirname(__file__), "test_data", "test_audio.mp3")
    
    # 确保测试目录存在
    os.makedirs(os.path.join(os.path.dirname(__file__), "test_data"), exist_ok=True)
    
    # 如果测试文件不存在，创建一个空文件用于测试
    if not os.path.exists(test_file_path):
        with open(test_file_path, "wb") as f:
            f.write(b"test audio content")
    
    # 准备表单数据
    form_data = {
        "title": "测试面试",
        "description": "这是一个测试面试",
        "tech_field": "人工智能",
        "position_type": "技术岗"
    }
    
    # 发送上传请求
    with open(test_file_path, "rb") as f:
        files = {"file": ("test_audio.mp3", f, "audio/mpeg")}
        response = client.post(
            f"{settings.API_V1_STR}/interviews/upload",
            data=form_data,
            files=files,
            headers={"Authorization": f"Bearer {token}"}
        )
    
    # 验证响应
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == form_data["title"]
    assert data["status"] == "pending"  # 初始状态应为pending


def test_get_interviews():
    """测试获取面试列表API"""
    # 模拟登录获取token
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    login_response = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # 发送获取面试列表请求
    response = client.get(
        f"{settings.API_V1_STR}/interviews/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # 应该至少有一个面试记录（之前测试上传的）
    assert len(data) >= 1


def test_get_interview_detail():
    """测试获取面试详情API"""
    # 模拟登录获取token
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    login_response = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # 先获取面试列表
    list_response = client.get(
        f"{settings.API_V1_STR}/interviews/",
        headers={"Authorization": f"Bearer {token}"}
    )
    interviews = list_response.json()
    
    # 确保有面试记录
    if len(interviews) > 0:
        interview_id = interviews[0]["id"]
        
        # 发送获取面试详情请求
        response = client.get(
            f"{settings.API_V1_STR}/interviews/{interview_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == interview_id
        assert "title" in data
        assert "analysis_results" in data