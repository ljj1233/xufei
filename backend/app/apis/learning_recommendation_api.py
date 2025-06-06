"""
学习推荐API

提供学习路径生成和资源推荐的API接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, List, Any, Optional
import os

from app.services.learning_recommendation.recommendation import RecommendationService
from app.services.learning_recommendation.job_skill_mapping import JobSkillMappingService
from app.services.learning_recommendation.models import LearningPath

# 创建路由
router = APIRouter(prefix="/api/learning-recommendation", tags=["learning_recommendation"])

# 获取OpenAI API密钥
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 初始化服务
job_skill_service = JobSkillMappingService()
recommendation_service = RecommendationService(
    job_skill_service=job_skill_service,
    api_key=OPENAI_API_KEY
)

@router.post("/learning-path", response_model=Dict[str, Any])
async def generate_learning_path(
    user_id: str = Query(..., description="用户ID"),
    job_position_id: str = Query(..., description="职位ID"),
    assessment_results: Dict[str, Any] = Body(..., description="面试评测结果"),
    user_preferences: Optional[Dict[str, Any]] = Body(None, description="用户偏好")
):
    """
    生成个性化学习路径
    
    基于面试评测结果和职位要求，为用户生成个性化学习路径
    """
    try:
        learning_path = recommendation_service.generate_learning_path(
            user_id=user_id,
            job_position_id=job_position_id,
            assessment_results=assessment_results,
            user_preferences=user_preferences
        )
        
        return learning_path.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成学习路径失败: {str(e)}")

@router.get("/resource-recommendations", response_model=List[Dict[str, Any]])
async def get_resource_recommendations(
    user_id: str = Query(..., description="用户ID"),
    query: str = Query(..., description="搜索查询"),
    job_position_id: str = Query(..., description="职位ID"),
    resource_types: Optional[List[str]] = Query(None, description="资源类型过滤"),
    difficulty: Optional[str] = Query(None, description="难度级别过滤"),
    term_type: Optional[str] = Query(None, description="学习期限"),
    limit: int = Query(10, description="返回结果数量限制")
):
    """
    获取学习资源推荐
    
    基于搜索查询和职位，返回推荐的学习资源
    """
    try:
        # 构建过滤条件
        filters = {}
        if resource_types:
            filters["resource_types"] = resource_types
        if difficulty:
            filters["difficulty"] = difficulty
        if term_type:
            filters["term_type"] = term_type
            
        results = recommendation_service.get_resource_recommendations(
            user_id=user_id,
            query=query,
            job_position_id=job_position_id,
            filters=filters,
            limit=limit
        )
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资源推荐失败: {str(e)}")

@router.get("/job-positions", response_model=List[Dict[str, str]])
async def get_job_positions():
    """
    获取支持的职位列表
    """
    try:
        positions = job_skill_service.get_all_job_titles()
        return positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取职位列表失败: {str(e)}")

@router.get("/job-skills/{job_id}", response_model=Dict[str, Any])
async def get_job_skills(job_id: str):
    """
    获取指定职位所需的技能
    """
    try:
        skills = job_skill_service.get_skills_for_job(job_id)
        return skills
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取职位技能失败: {str(e)}")

@router.post("/job-skill-mapping", response_model=Dict[str, Any])
async def update_job_skill_mapping(
    job_id: str = Query(..., description="职位ID"),
    job_info: Dict[str, Any] = Body(..., description="职位信息")
):
    """
    更新职位的技能映射
    """
    try:
        success = job_skill_service.update_job_skill_mapping(job_id, job_info)
        if success:
            return {"status": "success", "message": f"职位 {job_id} 的技能映射已更新"}
        else:
            raise HTTPException(status_code=500, detail=f"更新职位 {job_id} 的技能映射失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新职位技能映射失败: {str(e)}")

@router.delete("/job-position/{job_id}", response_model=Dict[str, Any])
async def delete_job_position(job_id: str):
    """
    删除职位及其技能映射
    """
    try:
        success = job_skill_service.delete_job(job_id)
        if success:
            return {"status": "success", "message": f"职位 {job_id} 已删除"}
        else:
            raise HTTPException(status_code=404, detail=f"职位 {job_id} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除职位失败: {str(e)}") 