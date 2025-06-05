"""
健康检查API端点
"""
from fastapi import APIRouter
import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("")
async def health_check():
    """健康检查端点
    
    返回应用状态信息
    
    Returns:
        dict: 应用状态信息
    """
    logger.info("访问健康检查端点")
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "service": "interview-analysis-api"
    } 