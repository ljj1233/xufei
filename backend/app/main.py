from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from app.db.database import engine, Base
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.security import get_password_hash

sys.path.append(str(Path(__file__).parent.resolve()))

from app.core.config import settings
from app.api.api_v1.api import api_router

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建上传目录
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

# 初始化默认管理员账号
def init_default_admin():
    """初始化默认管理员账号
    
    检查数据库中是否已有管理员账号，如果没有则创建一个默认管理员账号
    """
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        
        admin = session.query(User).filter(User.is_admin == True).first()
        if not admin:
            # 创建管理员账号
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_admin=True
            )
            session.add(admin_user)
            session.commit()
            logger.info("已创建默认管理员账号: admin@example.com / admin123")
        else:
            logger.info(f"已存在管理员账号: {admin.email}")
        
        session.close()
    except Exception as e:
        logger.error(f"初始化管理员账号失败: {str(e)}")

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
    
    # 初始化默认管理员账号
    init_default_admin()
    
    yield
    
    # 应用关闭时的清理操作
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


@app.get("/api/v1/admin/db-status")
async def check_db_pool_status():
    """检查数据库连接池状态
    
    Returns:
        dict: 连接池统计信息
    """
    try:
        stats = {
            "pool_size": engine.pool.size(),
            "checkedin": engine.pool.checkedin(),
            "overflow": engine.pool.overflow(),
            "checkedout": engine.pool.checkedout(),
            "status": "healthy"
        }
        return stats
    except Exception as e:
        logger.error(f"获取连接池状态失败: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app="main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )

