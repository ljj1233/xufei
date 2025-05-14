from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
import os
import shutil
from typing import List, Optional
import cv2

from app.db.database import get_db
from app.db.models import Interview as DBInterview, User
from app.models.user import User
from app.models import schemas
from app.core.config import settings
from app.utils.auth import get_current_active_user

router = APIRouter()


@router.post("/upload/", response_model=schemas.Interview)
async def upload_interview_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """上传面试视频或音频文件
    
    接收用户上传的面试文件，保存并创建面试记录
    
    Args:
        file: 上传的文件
        title: 面试标题
        description: 面试描述
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        Interview: 创建的面试记录
    """
    # 检查文件类型
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件类型不支持，支持的类型: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # 创建用户上传目录
    user_upload_dir = os.path.join(settings.UPLOAD_FOLDER, f"user_{current_user.id}")
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(user_upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 确定文件类型和时长
    file_type = "video" if file_ext in ["mp4", "avi", "mov"] else "audio"
    duration = None
    
    # 如果是视频，获取时长
    if file_type == "video":
        try:
            video = cv2.VideoCapture(file_path)
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else None
            video.release()
        except Exception as e:
            print(f"获取视频时长失败: {e}")
    
    # 创建面试记录
    db_interview = DBInterview(
        title=title,
        description=description,
        file_path=file_path,
        file_type=file_type,
        duration=duration,
        user_id=current_user.id
    )
    
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    
    return db_interview


@router.get("/", response_model=List[schemas.Interview])
def read_interviews(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户的面试列表
    
    返回当前用户的所有面试记录
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        List[Interview]: 面试记录列表
    """
    interviews = db.query(DBInterview).filter(DBInterview.user_id == current_user.id).offset(skip).limit(limit).all()
    return interviews


@router.get("/{interview_id}", response_model=schemas.Interview)
def read_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取单个面试记录
    
    根据ID获取面试记录详情
    
    Args:
        interview_id: 面试ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        Interview: 面试记录
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试记录不存在")
    if interview.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有权限访问此面试记录")
    return interview


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除面试记录
    
    根据ID删除面试记录及其文件
    
    Args:
        interview_id: 面试ID
        db: 数据库会话
        current_user: 当前用户
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试记录不存在")
    if interview.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有权限删除此面试记录")
    
    # 删除文件
    try:
        if os.path.exists(interview.file_path):
            os.remove(interview.file_path)
    except Exception as e:
        print(f"删除文件失败: {e}")
    
    # 删除记录
    db.delete(interview)
    db.commit()
    
    return None