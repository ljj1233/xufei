import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.database import Base, get_db
from app.main import app as original_app
from app.core.config import settings
import os

@pytest.fixture(scope="function")
def test_db():
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

def test_register_login_upload_and_get_interview(client, tmp_path):
    # 注册
    user = {"username": "apiuser", "email": "apiuser@example.com", "password": "12345678Aa!"}
    r = client.post(f"{settings.API_V1_STR}/users/register", json=user)
    assert r.status_code in (200, 201)
    # 登录
    login_data = {"username": "apiuser", "password": "12345678Aa!"}
    r2 = client.post(f"{settings.API_V1_STR}/users/login", data=login_data)
    assert r2.status_code == 200
    token = r2.json()["access_token"]
    # 上传面试
    test_audio = tmp_path / "test_audio.mp3"
    test_audio.write_bytes(b"test audio content")
    form_data = {
        "title": "测试面试",
        "description": "desc",
        "tech_field": "AI",
        "position_type": "技术岗",
        "job_position_id": "1"  # 假设ID为1的职位已存在
    }
    with open(test_audio, "rb") as f:
        files = {"file": ("test_audio.mp3", f, "audio/mpeg")}
        resp = client.post(f"{settings.API_V1_STR}/interviews/upload/", data=form_data, files=files, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code in (200, 201)
    interview_id = resp.json()["id"]
    # 获取面试列表
    resp2 = client.get(f"{settings.API_V1_STR}/interviews/", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    assert any(i["id"] == interview_id for i in resp2.json())
    # 获取面试详情
    resp3 = client.get(f"{settings.API_V1_STR}/interviews/{interview_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 200
    assert resp3.json()["id"] == interview_id