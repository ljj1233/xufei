from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.db.database import engine, Base

# 创建上传目录
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def read_root():
    """根路由
    
    返回应用基本信息
    
    Returns:
        dict: 应用信息
    """
    return {"message": "欢迎使用多模态面试评测智能体API"}


# 在应用启动时创建数据库表
@app.on_event("startup")
async def startup_event():
    """应用启动事件
    
    在应用启动时执行的操作，如创建数据库表
    """
    # 创建数据库表
    # 注意：在生产环境中应该使用Alembic进行数据库迁移
    Base.metadata.create_all(bind=engine)