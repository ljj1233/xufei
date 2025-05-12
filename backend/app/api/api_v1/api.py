from fastapi import APIRouter

from app.api.api_v1.endpoints import interviews, users, analysis

api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])