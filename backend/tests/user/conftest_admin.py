import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.main import app
from app.core.config import settings
from fastapi.testclient import TestClient
from app.models.user import User
from app.models.job_position import JobPosition, TechField, PositionType
from app.core.security import get_password_hash

# 使用MySQL数据库进行测试，并确保有管理员账号
@pytest.fixture(scope="function")
def admin_test_db():
    # 使用MySQL数据库进行测试
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
    
    # 预先创建管理员账号
    admin_user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_admin=True
    )
    db.add(admin_user)
    db.commit()
    
    yield db
    db.close()

@pytest.fixture(scope="function")
def admin_client(admin_test_db):
    def override_get_db():
        try:
            yield admin_test_db
        finally:
            admin_test_db.rollback()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# 获取管理员用户的token
@pytest.fixture(scope="function")
def admin_token(admin_client):
    response = admin_client.post(
        "/api/v1/users/login",
        data={"username": "admin@example.com", "password": "admin123"}
    )
    return response.json()["access_token"]