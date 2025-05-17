from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from app.db.database import engine, Base

sys.path.append(str(Path(__file__).parent.resolve()))

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.db.database import engine, Base

# 创建上传目录
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)


# 应用生命周期管理
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理
    
    在应用启动时执行的操作，如创建数据库表
    """
    # 创建数据库表
    # 注意：在生产环境中应该使用Alembic进行数据库迁移
    Base.metadata.create_all(bind=engine, checkfirst=True)
    
    # 初始化数据库连接池
    from sqlalchemy.pool import QueuePool
    engine.pool = QueuePool(
        creator=engine.connect,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        timeout=settings.DB_POOL_TIMEOUT
    )
    
    yield
    
    # 应用关闭时的清理操作
    engine.pool.dispose()
    # 关闭所有数据库连接
    engine.dispose()

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app="main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.LOG_LEVEL
    )

