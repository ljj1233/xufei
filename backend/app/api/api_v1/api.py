from fastapi import APIRouter

from app.api.api_v1.endpoints import interviews, users, analysis, job_positions, interview_session, health

api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(interview_session.router, prefix="/interview-sessions", tags=["interview-sessions"])
api_router.include_router(job_positions.router, prefix="/job-positions", tags=["job_positions"])
api_router.include_router(health.router, prefix="/health", tags=["health"])

