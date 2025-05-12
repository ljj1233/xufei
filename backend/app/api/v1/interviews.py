from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Any, Optional
from app.core.auth import get_current_user
from app.db.base import get_db
from app.models.user import User
from app.models.interview import Interview, FileType
from app.models.analysis import Analysis
from pydantic import BaseModel
import os
import json
from datetime import datetime

router = APIRouter()

# 请求模型
class InterviewCreate(BaseModel):
    title: str
    description: Optional[str] = None

class InterviewResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    file_type: str
    duration: Optional[float]
    created_at: datetime

# 上传面试文件
@router.post("/upload", response_model=InterviewResponse)
async def upload_interview(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    # 检查文件类型
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext in [".mp4", ".avi", ".mov"]:
        file_type = FileType.VIDEO
    elif file_ext in [".mp3", ".wav"]:
        file_type = FileType.AUDIO
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件格式"
        )
    
    # 保存文件
    file_path = f"uploads/{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
    os.makedirs("uploads", exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # 创建面试记录
    interview = Interview(
        user_id=current_user.id,
        title=title,
        description=description,
        file_path=file_path,
        file_type=file_type
    )
    
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
    return interview

# 获取用户的所有面试记录
@router.get("", response_model=list[InterviewResponse])
async def get_interviews(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Any:
    interviews = db.query(Interview).filter(Interview.user_id == current_user.id).all()
    return interviews

# 获取单个面试记录详情
@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="面试记录不存在"
        )
    
    return interview

# 删除面试记录
@router.delete("/{interview_id}")
async def delete_interview(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="面试记录不存在"
        )
    
    # 删除关联的分析结果
    if interview.analysis:
        db.delete(interview.analysis)
    
    # 删除文件
    if os.path.exists(interview.file_path):
        os.remove(interview.file_path)
    
    # 删除记录
    db.delete(interview)
    db.commit()
    
    return {"message": "面试记录已删除"}