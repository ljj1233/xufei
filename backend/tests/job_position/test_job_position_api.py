import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.database import Base, get_db
from app.main import app
from app.core.config import settings
import os
import json
from app.models.user import User
from app.models.job_position import JobPosition, TechField, PositionType
from app.core.security import get_password_hash

# 使用MySQL数据库进行测试
@pytest.fixture(scope="function")
def test_db():
    # 使用MySQL数据库进行测试
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
    
    # 预先创建测试用户（管理员权限）
    admin_user = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass"),
        is_active=True,
        is_admin=True
    )
    db.add(admin_user)
    
    # 预先创建普通用户
    normal_user = User(
        username="normaluser",
        email="normal@example.com",
        hashed_password=get_password_hash("normalpass"),
        is_active=True,
        is_admin=False
    )
    db.add(normal_user)
    
    # 预先创建测试职位
    test_position = JobPosition(
        title="软件工程师",
        tech_field=TechField.AI,
        position_type=PositionType.TECHNICAL,
        required_skills="Python, FastAPI, SQLAlchemy",
        job_description="负责后端API开发和数据库设计",
        evaluation_criteria="编程能力, 系统设计能力, 沟通能力"
    )
    db.add(test_position)
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

@pytest.fixture(scope="function")
def admin_headers(client):
    # 管理员登录获取token
    login_data = {
        "username": "adminuser",
        "password": "adminpass"
    }
    login_response = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
    token = login_response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def normal_headers(client):
    # 普通用户登录获取token
    login_data = {
        "username": "normaluser",
        "password": "normalpass"
    }
    login_response = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
    token = login_response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

# 职位API测试
class TestJobPositionAPI:
    
    def test_create_job_position(self, client, admin_headers):
        """测试创建职位（管理员权限）"""
        position_data = {
            "title": "数据科学家",
            "tech_field": "artificial_intelligence",
            "position_type": "technical",
            "required_skills": "Python, 机器学习, 数据分析",
            "job_description": "负责数据分析和机器学习模型开发",
            "evaluation_criteria": "算法能力, 数据处理能力, 研究能力"
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/job-positions/",
            json=position_data,
            headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == position_data["title"]
        assert data["tech_field"] == position_data["tech_field"]
        assert data["position_type"] == position_data["position_type"]
        assert data["required_skills"] == position_data["required_skills"]
        assert "id" in data
    
    def test_create_job_position_unauthorized(self, client, normal_headers):
        """测试非管理员创建职位（应当失败）"""
        position_data = {
            "title": "产品经理",
            "tech_field": "artificial_intelligence",
            "position_type": "product",
            "required_skills": "产品设计, 用户研究, 需求分析",
            "job_description": "负责产品规划和需求管理",
            "evaluation_criteria": "产品思维, 沟通能力, 项目管理能力"
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/job-positions/",
            json=position_data,
            headers=normal_headers
        )
        
        # 应当返回403禁止访问
        assert response.status_code == 403
    
    def test_get_job_positions(self, client):
        """测试获取职位列表（无需登录）"""
        response = client.get(f"{settings.API_V1_STR}/job-positions/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(position["title"] == "软件工程师" for position in data)
    
    def test_get_job_position_by_id(self, client, test_db):
        """测试通过ID获取职位详情"""
        # 获取测试职位
        position = test_db.query(JobPosition).filter(JobPosition.title == "软件工程师").first()
        
        response = client.get(f"{settings.API_V1_STR}/job-positions/{position.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == position.id
        assert data["title"] == position.title
        assert data["tech_field"] == position.tech_field.value
        assert data["position_type"] == position.position_type.value
    
    def test_update_job_position(self, client, test_db, admin_headers):
        """测试更新职位信息（管理员权限）"""
        # 获取测试职位
        position = test_db.query(JobPosition).filter(JobPosition.title == "软件工程师").first()
        
        update_data = {
            "title": "高级软件工程师",
            "required_skills": "Python, FastAPI, SQLAlchemy, 系统设计",
            "job_description": "负责后端架构设计和API开发"
        }
        
        response = client.patch(
            f"{settings.API_V1_STR}/job-positions/{position.id}",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["required_skills"] == update_data["required_skills"]
        assert data["job_description"] == update_data["job_description"]
    
    def test_update_job_position_unauthorized(self, client, test_db, normal_headers):
        """测试非管理员更新职位（应当失败）"""
        # 获取测试职位
        position = test_db.query(JobPosition).filter(JobPosition.title == "软件工程师").first()
        
        update_data = {
            "title": "初级软件工程师"
        }
        
        response = client.patch(
            f"{settings.API_V1_STR}/job-positions/{position.id}",
            json=update_data,
            headers=normal_headers
        )
        
        # 应当返回403禁止访问
        assert response.status_code == 403
    
    def test_delete_job_position(self, client, test_db, admin_headers):
        """测试删除职位（管理员权限）"""
        # 创建要删除的测试职位
        test_position = JobPosition(
            title="要删除的职位",
            tech_field=TechField.SYSTEM,
            position_type=PositionType.OPERATION,
            required_skills="测试技能",
            job_description="测试描述",
            evaluation_criteria="测试标准"
        )
        test_db.add(test_position)
        test_db.commit()
        test_db.refresh(test_position)
        
        response = client.delete(
            f"{settings.API_V1_STR}/job-positions/{test_position.id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        
        # 确认职位已被删除
        check_response = client.get(f"{settings.API_V1_STR}/job-positions/{test_position.id}")
        assert check_response.status_code == 404
    
    def test_delete_job_position_unauthorized(self, client, test_db, normal_headers):
        """测试非管理员删除职位（应当失败）"""
        # 获取测试职位
        position = test_db.query(JobPosition).filter(JobPosition.title == "软件工程师").first()
        
        response = client.delete(
            f"{settings.API_V1_STR}/job-positions/{position.id}",
            headers=normal_headers
        )
        
        # 应当返回403禁止访问
        assert response.status_code == 403
        
        # 确认职位未被删除
        check_response = client.get(f"{settings.API_V1_STR}/job-positions/{position.id}")
        assert check_response.status_code == 200
    
    def test_filter_job_positions(self, client, test_db):
        """测试按条件筛选职位"""
        # 创建额外的测试职位用于筛选测试
        positions = [
            JobPosition(
                title="AI研究员",
                tech_field=TechField.AI,
                position_type=PositionType.TECHNICAL,
                required_skills="深度学习, 计算机视觉",
                job_description="负责AI算法研究",
                evaluation_criteria="研究能力, 创新能力"
            ),
            JobPosition(
                title="运维工程师",
                tech_field=TechField.SYSTEM,
                position_type=PositionType.OPERATION,
                required_skills="Linux, Docker, Kubernetes",
                job_description="负责系统运维和部署",
                evaluation_criteria="运维经验, 问题排查能力"
            )
        ]
        for position in positions:
            test_db.add(position)
        test_db.commit()
        
        # 按技术领域筛选
        response = client.get(f"{settings.API_V1_STR}/job-positions/?tech_field=artificial_intelligence")
        assert response.status_code == 200
        data = response.json()
        assert all(position["tech_field"] == "artificial_intelligence" for position in data)
        
        # 按岗位类型筛选
        response = client.get(f"{settings.API_V1_STR}/job-positions/?position_type=operation")
        assert response.status_code == 200
        data = response.json()
        assert all(position["position_type"] == "operation" for position in data)
        assert any(position["title"] == "运维工程师" for position in data)