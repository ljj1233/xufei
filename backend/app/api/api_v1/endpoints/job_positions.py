from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import Any, List, Optional, Dict
from app.core.auth import get_current_user
from app.db.database import get_db
from app.models.job_position import JobPosition
from app.models.schemas import JobPosition as JobPositionSchema, JobPositionCreate
import json
from app.models.user import User as DBUser
from sqlalchemy import or_

router = APIRouter()

# 搜索职位 - 必须放在具有路径参数的路由之前
@router.get("/find", response_model=List[JobPositionSchema])
async def search_job_positions(
    keyword: str = "",
    db: Session = Depends(get_db)
) -> Any:
    """按关键词搜索职位"""
    if not keyword:
        return db.query(JobPosition).all()
        
    search = f"%{keyword}%"
    job_positions = db.query(JobPosition).filter(
        or_(
            JobPosition.title.ilike(search),
            JobPosition.job_description.ilike(search),
            JobPosition.required_skills.ilike(search)
        )
    ).all()
    
    return job_positions

# 创建职位
@router.post("", response_model=JobPositionSchema)
async def create_job_position(
    job_position: JobPositionCreate,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    # 检查用户权限（可选，如果只允许管理员创建职位）
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    # 创建职位记录
    db_job_position = JobPosition(
        title=job_position.title,
        tech_field=job_position.tech_field,
        position_type=job_position.position_type,
        required_skills=job_position.required_skills,
        job_description=job_position.job_description,
        evaluation_criteria=job_position.evaluation_criteria
    )
    
    db.add(db_job_position)
    db.commit()
    db.refresh(db_job_position)
    
    return db_job_position

# 获取所有职位
@router.get("", response_model=List[JobPositionSchema])
async def get_job_positions(
    db: Session = Depends(get_db),
    tech_field: Optional[str] = None,
    position_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> Any:
    query = db.query(JobPosition)
    
    if tech_field:
        query = query.filter(JobPosition.tech_field == tech_field)
    
    if position_type:
        query = query.filter(JobPosition.position_type == position_type)
    
    job_positions = query.offset(skip).limit(limit).all()
    return job_positions

# 获取单个职位详情
@router.get("/{job_position_id}", response_model=JobPositionSchema)
async def get_job_position(
    job_position_id: int,
    db: Session = Depends(get_db)
) -> Any:
    job_position = db.query(JobPosition).filter(JobPosition.id == job_position_id).first()
    
    if not job_position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="职位不存在"
        )
    
    return job_position

# 更新职位信息
@router.put("/{job_position_id}", response_model=JobPositionSchema)
async def update_job_position(
    job_position_id: int,
    job_position_update: JobPositionCreate,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    # 检查用户权限
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    # 获取职位记录
    db_job_position = db.query(JobPosition).filter(JobPosition.id == job_position_id).first()
    
    if not db_job_position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="职位不存在"
        )
    
    # 更新职位信息
    db_job_position.title = job_position_update.title
    db_job_position.tech_field = job_position_update.tech_field
    db_job_position.position_type = job_position_update.position_type
    db_job_position.required_skills = job_position_update.required_skills
    db_job_position.job_description = job_position_update.job_description
    db_job_position.evaluation_criteria = job_position_update.evaluation_criteria
    
    db.commit()
    db.refresh(db_job_position)
    
    return db_job_position

# 删除职位
@router.delete("/{job_position_id}")
async def delete_job_position(
    job_position_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    # 检查用户权限
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    # 获取职位记录
    db_job_position = db.query(JobPosition).filter(JobPosition.id == job_position_id).first()
    
    if not db_job_position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="职位不存在"
        )
    
    # 删除职位记录
    db.delete(db_job_position)
    db.commit()
    
    return {"message": "职位已成功删除"}

# 部分更新职位信息
@router.patch("/{job_position_id}", response_model=JobPositionSchema)
async def patch_job_position(
    job_position_id: int,
    job_position_update: Dict[str, Any] = Body(...),
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    # 检查用户权限
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    # 获取职位记录
    db_job_position = db.query(JobPosition).filter(JobPosition.id == job_position_id).first()
    
    if not db_job_position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="职位不存在"
        )
    
    # 更新职位信息
    for field, value in job_position_update.items():
        if hasattr(db_job_position, field):
            setattr(db_job_position, field, value)
    
    db.commit()
    db.refresh(db_job_position)
    
    return db_job_position

# 批量创建职位
@router.post("/batch", response_model=List[JobPositionSchema])
async def batch_create_job_positions(
    positions: Dict[str, List[Dict[str, Any]]] = Body(...),
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """批量创建职位"""
    # 检查用户权限
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    created_positions = []
    
    for position_data in positions.get("positions", []):
        # 创建职位记录
        db_job_position = JobPosition(
            title=position_data.get("title"),
            tech_field=position_data.get("tech_field"),
            position_type=position_data.get("position_type"),
            required_skills=position_data.get("required_skills"),
            job_description=position_data.get("job_description"),
            evaluation_criteria=position_data.get("evaluation_criteria")
        )
        
        db.add(db_job_position)
        db.commit()
        db.refresh(db_job_position)
        created_positions.append(db_job_position)
    
    return created_positions

# 批量获取职位
@router.post("/batch-get", response_model=List[JobPositionSchema])
async def batch_get_job_positions(
    ids: Dict[str, List[int]] = Body(...),
    db: Session = Depends(get_db)
) -> Any:
    """批量获取职位"""
    job_positions = db.query(JobPosition).filter(JobPosition.id.in_(ids.get("ids", []))).all()
    return job_positions

# 批量删除职位
@router.post("/batch-delete", response_model=Dict[str, Any])
async def batch_delete_job_positions(
    ids: Dict[str, List[int]] = Body(...),
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """批量删除职位"""
    # 检查用户权限
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作"
        )
    
    job_positions = db.query(JobPosition).filter(JobPosition.id.in_(ids.get("ids", []))).all()
    deleted_count = len(job_positions)
    
    for job_position in job_positions:
        db.delete(job_position)
    
    db.commit()
    
    return {"message": f"成功删除 {deleted_count} 个职位"}