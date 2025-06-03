import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.database import Base, get_db
from app.main import app
from app.models.user import User
from app.core.security import get_password_hash

# 创建测试数据库
@pytest.fixture(scope="function")
def admin_test_db():
    # 使用内存数据库进行测试
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # 创建测试会话
    db = TestingSessionLocal()
    
    # 创建管理员用户
    admin_user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_admin=True
    )
    db.add(admin_user)
    db.commit()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# 创建测试客户端
@pytest.fixture(scope="function")
def admin_client(admin_test_db):
    def override_get_db():
        try:
            yield admin_test_db
        finally:
            admin_test_db.rollback()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides = {}

# 创建管理员令牌
@pytest.fixture(scope="function")
def admin_token(admin_client):
    response = admin_client.post(
        "/api/v1/users/login",
        data={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"] 