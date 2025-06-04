import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.main import app
from app.core.config import settings
import json
from app.models.user import User
from app.models.job_position import JobPosition, TechField, PositionType
from app.core.security import get_password_hash

# 使用conftest_admin.py中的测试夹具
from ..conftest_admin import admin_test_db, admin_client, admin_token

# 测试职位创建接口的全面功能
def test_create_job_position_comprehensive(admin_client, admin_token, admin_test_db):
    # 测试创建不同类型的职位
    positions_data = [
        {
            "title": "前端开发工程师",
            "tech_field": "artificial_intelligence",
            "position_type": "technical",
            "required_skills": "JavaScript, Vue, React",
            "job_description": "负责前端界面开发和用户体验优化",
            "evaluation_criteria": "前端框架经验, UI设计能力, 代码质量"
        },
        {
            "title": "后端开发工程师",
            "tech_field": "big_data",
            "position_type": "technical",
            "required_skills": "Python, Django, FastAPI",
            "job_description": "负责后端API开发和数据处理",
            "evaluation_criteria": "后端框架经验, 数据库设计能力, 代码质量"
        },
        {
            "title": "产品经理",
            "tech_field": "internet_of_things",
            "position_type": "product",
            "required_skills": "产品设计, 用户研究, 需求分析",
            "job_description": "负责产品规划和需求管理",
            "evaluation_criteria": "产品思维, 沟通能力, 项目管理能力"
        },
        {
            "title": "测试工程师",
            "tech_field": "intelligent_system",
            "position_type": "operation",
            "required_skills": "自动化测试, 性能测试, 安全测试",
            "job_description": "负责系统测试和质量保证",
            "evaluation_criteria": "测试经验, 问题分析能力, 自动化脚本开发能力"
        }
    ]
    
    created_ids = []
    
    for position_data in positions_data:
        response = admin_client.post(
            "/api/v1/job-positions",
            json=position_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == position_data["title"]
        assert data["tech_field"] == position_data["tech_field"]
        assert data["position_type"] == position_data["position_type"]
        assert "id" in data
        created_ids.append(data["id"])
    
    # 测试获取所有职位
    response = admin_client.get("/api/v1/job-positions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= len(positions_data)
    
    # 测试按技术领域筛选职位
    response = admin_client.get("/api/v1/job-positions?tech_field=big_data")
    assert response.status_code == 200
    data = response.json()
    assert all(job["tech_field"] == "big_data" for job in data)
    
    # 测试按职位类型筛选职位
    response = admin_client.get("/api/v1/job-positions?position_type=product")
    assert response.status_code == 200
    data = response.json()
    assert all(job["position_type"] == "product" for job in data)
    
    # 测试职位详情获取
    for job_id in created_ids:
        response = admin_client.get(f"/api/v1/job-positions/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
    
    # 测试更新职位
    update_data = {
        "title": "高级前端开发工程师",
        "tech_field": "artificial_intelligence",
        "position_type": "technical",
        "required_skills": "JavaScript, Vue, React, TypeScript",
        "job_description": "负责前端架构设计和团队管理",
        "evaluation_criteria": "前端框架经验, 架构设计能力, 团队管理能力"
    }
    
    response = admin_client.put(
        f"/api/v1/job-positions/{created_ids[0]}",
        json=update_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "高级前端开发工程师"
    assert "TypeScript" in data["required_skills"]
    
    # 测试部分更新职位
    patch_data = {
        "title": "资深后端开发工程师",
        "required_skills": "Python, Django, FastAPI, SQLAlchemy"
    }
    
    response = admin_client.patch(
        f"/api/v1/job-positions/{created_ids[1]}",
        json=patch_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "资深后端开发工程师"
    assert "SQLAlchemy" in data["required_skills"]
    
    # 测试删除职位
    response = admin_client.delete(
        f"/api/v1/job-positions/{created_ids[-1]}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # 验证职位已被删除
    response = admin_client.get(f"/api/v1/job-positions/{created_ids[-1]}")
    assert response.status_code == 404

# 测试职位搜索功能
def test_search_job_positions(admin_client, admin_token, admin_test_db):
    # 创建测试职位
    positions_data = [
        {
            "title": "人工智能研究员",
            "tech_field": "artificial_intelligence",
            "position_type": "technical",
            "required_skills": "机器学习, 深度学习, Python",
            "job_description": "负责AI算法研究和模型开发",
            "evaluation_criteria": "研究能力, 算法设计能力, 论文发表情况"
        },
        {
            "title": "大数据工程师",
            "tech_field": "big_data",
            "position_type": "technical",
            "required_skills": "Hadoop, Spark, Hive",
            "job_description": "负责大数据平台开发和数据处理",
            "evaluation_criteria": "大数据技术经验, 分布式系统设计能力"
        }
    ]
    
    for position_data in positions_data:
        admin_client.post(
            "/api/v1/job-positions",
            json=position_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    # 测试按关键词搜索
    response = admin_client.get("/api/v1/job-positions/find?keyword=人工智能")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any("人工智能" in job["title"] for job in data)
    
    # 测试按技能搜索
    response = admin_client.get("/api/v1/job-positions/find?keyword=Hadoop")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any("Hadoop" in job["required_skills"] for job in data)
    
    # 测试按描述搜索
    response = admin_client.get("/api/v1/job-positions/find?keyword=算法")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any("算法" in job["job_description"] for job in data)

# 测试职位批量操作
def test_batch_job_positions(admin_client, admin_token, admin_test_db):
    # 批量创建职位
    batch_positions = [
        {
            "title": "数据分析师",
            "tech_field": "big_data",
            "position_type": "technical",
            "required_skills": "SQL, Python, 数据可视化",
            "job_description": "负责数据分析和报表生成",
            "evaluation_criteria": "数据分析能力, 统计学知识, 可视化技能"
        },
        {
            "title": "机器学习工程师",
            "tech_field": "artificial_intelligence",
            "position_type": "technical",
            "required_skills": "TensorFlow, PyTorch, 机器学习算法",
            "job_description": "负责机器学习模型开发和优化",
            "evaluation_criteria": "算法实现能力, 模型调优经验, 编程能力"
        },
        {
            "title": "DevOps工程师",
            "tech_field": "intelligent_system",
            "position_type": "operation",
            "required_skills": "Docker, Kubernetes, CI/CD",
            "job_description": "负责自动化部署和运维",
            "evaluation_criteria": "自动化工具使用经验, 系统架构设计能力"
        }
    ]
    
    response = admin_client.post(
        "/api/v1/job-positions/batch",
        json={"positions": batch_positions},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(batch_positions)
    created_ids = [job["id"] for job in data]
    
    # 批量获取职位
    response = admin_client.post(
        "/api/v1/job-positions/batch-get",
        json={"ids": created_ids},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(created_ids)
    
    # 批量删除职位
    response = admin_client.post(
        "/api/v1/job-positions/batch-delete",
        json={"ids": created_ids},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # 验证职位已被删除
    for job_id in created_ids:
        response = admin_client.get(f"/api/v1/job-positions/{job_id}")
        assert response.status_code == 404