#!/usr/bin/env python3
"""
用户注册测试脚本
"""

import requests
import time
import json

API_BASE = "http://localhost:8000"

def test_register():
    """测试用户注册功能"""
    # 生成唯一用户名和邮箱
    timestamp = int(time.time())
    username = f"testuser{timestamp}"
    email = f"test{timestamp}@example.com"
    
    data = {
        "username": username,
        "email": email,
        "password": "password123"
    }
    
    print(f"尝试注册新用户: {username}, {email}")
    
    try:
        # 发送注册请求
        response = requests.post(f"{API_BASE}/api/v1/users/register", json=data)
        print(f"注册响应: 状态码 {response.status_code}")
        print(f"响应内容: {response.text}")
        
        # 测试重复注册
        print("\n测试重复注册同一用户:")
        response = requests.post(f"{API_BASE}/api/v1/users/register", json=data)
        print(f"重复注册响应: 状态码 {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    test_register() 