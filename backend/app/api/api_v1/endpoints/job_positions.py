from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from app.core.auth import get_current_user
from app.db.base import get_db
from app.db.models import User as DBUser
from app.db.job_position import JobPosition as JobPositionSchema
from app.models import schemas, TechField, PositionType
import json

router = APIRouter()

# 创建职位
@router.post("", response_model=schemas.JobPosition)
async def create_job_position(
    job_position: schemas.JobPositionCreate,
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
    db_job_position = JobPositionSchema(
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
@router.get("", response_model=List[schemas.JobPosition])
async def get_job_positions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    job_positions = db.query(JobPositionSchema).offset(skip).limit(limit).all()
    return job_positions

# 获取单个职位详情
@router.get("/{job_position_id}", response_model=schemas.JobPosition)
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
@router.put("/{job_position_id}", response_model=schemas.JobPosition)
async def update_job_position(
    job_position_id: int,
    job_position_update: schemas.JobPositionCreate,
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