"""
FastAPI主应用

集成所有API路由和服务
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 配置基本日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log")
    ]
)

logger = logging.getLogger("app")

# 导入API路由
from app.apis.learning_recommendation_api import router as learning_recommendation_router

# 创建应用
app = FastAPI(
    title="多模态面试智能体API",
    description="提供面试评测和个性化学习推荐服务",
    version="1.0.0",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(learning_recommendation_router)

@app.get("/")
async def root():
    """API根路由，返回欢迎信息"""
    logger.info("访问根路由")
    return {"message": "欢迎使用多模态面试智能体API"}

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的操作"""
    # 确保数据目录存在
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    logger.info("应用已启动")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行的操作"""
    logger.info("应用已关闭")

# 如果直接运行此文件
if __name__ == "__main__":
    import uvicorn
    
    # 启动服务器
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

