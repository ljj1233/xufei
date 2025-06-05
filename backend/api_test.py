#!/usr/bin/env python3
"""
API测试工具

用于测试API路由是否正常工作
"""

import requests
import json
import sys
import os
import time

API_BASE = "http://localhost:8000"

def test_api_version():
    """测试API版本信息"""
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"API根路由访问: 状态码 {response.status_code}")
        print(f"响应内容: {response.json()}")
    except Exception as e:
        print(f"访问API根路由失败: {str(e)}")
    
    print("\n" + "-" * 50 + "\n")

def test_register_route():
    """测试注册用户路由"""
    # 测试不带API版本前缀
    try:
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
        response = requests.post(f"{API_BASE}/users/register", json=data)
        print(f"普通注册路由访问: 状态码 {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"访问普通注册路由失败: {str(e)}")
    
    print("\n" + "-" * 50 + "\n")
    
    # 测试带API版本前缀 - 使用唯一用户名和邮箱
    try:
        # 生成唯一用户名和邮箱，避免重复注册错误
        timestamp = int(time.time())
        data = {
            "username": f"testuser{timestamp}",
            "email": f"test{timestamp}@example.com",
            "password": "password123"
        }
        print(f"尝试注册新用户: {data['username']}, {data['email']}")
        
        response = requests.post(f"{API_BASE}/api/v1/users/register", json=data)
        print(f"带API前缀注册路由访问: 状态码 {response.status_code}")
        print(f"响应内容: {response.text}")
        
        # 测试重复注册同一用户
        if response.status_code == 201:
            print("\n测试重复注册同一用户:")
            response = requests.post(f"{API_BASE}/api/v1/users/register", json=data)
            print(f"重复注册: 状态码 {response.status_code}")
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"访问带API前缀注册路由失败: {str(e)}")

def test_health_check():
    """测试健康检查路由"""
    try:
        response = requests.get(f"{API_BASE}/api/v1/health")
        print(f"健康检查路由访问: 状态码 {response.status_code}")
        if response.status_code == 200:
            try:
                print(f"响应内容: {response.json()}")
            except Exception as e:
                print(f"解析响应JSON失败: {str(e)}")
                print(f"原始响应内容: {response.text}")
        else:
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"访问健康检查路由失败: {str(e)}")

def test_login_route():
    """测试登录路由"""
    try:
        # OAuth2密码流要求使用表单数据格式
        data = {
            "username": "admin",  # 使用默认管理员账号
            "password": "admin"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(
            f"{API_BASE}/api/v1/users/login", 
            data=data,
            headers=headers
        )
        print(f"登录路由访问: 状态码 {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"获取到的令牌: {token_data.get('access_token')[:20]}...")
            
            # 测试使用令牌获取用户信息
            if 'access_token' in token_data:
                auth_headers = {
                    "Authorization": f"Bearer {token_data['access_token']}"
                }
                me_response = requests.get(f"{API_BASE}/api/v1/users/me", headers=auth_headers)
                print(f"\n获取用户信息: 状态码 {me_response.status_code}")
                print(f"响应内容: {me_response.text}")
    except Exception as e:
        print(f"访问登录路由失败: {str(e)}")

if __name__ == "__main__":
    print("开始API路由测试...\n")
    test_api_version()
    test_register_route()
    test_health_check()
    test_login_route()
    print("\n测试完成。") 