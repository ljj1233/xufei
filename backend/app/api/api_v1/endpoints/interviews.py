from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
import os
import shutil
from typing import List, Optional
import cv2
import logging
import traceback
from datetime import datetime

from app.db.database import get_db
from app.models.interview import Interview as DBInterview
from app.models.analysis import InterviewAnalysis as DBAnalysis
from app.models.user import User as DBUser
from app.models import schemas
from app.core.config import settings
from app.utils.auth import get_current_active_user

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload/", response_model=schemas.Interview)
async def upload_interview_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
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
    logger.info(f"用户 {current_user.id}({current_user.username}) 开始上传文件: {file.filename}")
    
    try:
        # 检查文件类型
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            logger.warning(f"用户 {current_user.id} 尝试上传不支持的文件类型: {file_ext}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件类型不支持，支持的类型: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # 检查文件大小
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()  # 获取文件大小
        file.file.seek(0)  # 重置文件指针
        
        if file_size > settings.MAX_CONTENT_LENGTH:
            logger.warning(f"用户 {current_user.id} 尝试上传超大文件: {file_size} 字节")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制，最大允许 {settings.MAX_CONTENT_LENGTH / (1024 * 1024)} MB"
            )
        
        # 创建用户上传目录
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user_upload_dir = os.path.join(settings.UPLOAD_FOLDER, f"user_{current_user.id}")
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # 生成唯一文件名，避免覆盖
        base_filename = os.path.splitext(file.filename)[0]
        safe_filename = f"{base_filename}_{timestamp}.{file_ext}"
        file_path = os.path.join(user_upload_dir, safe_filename)
        
        logger.info(f"保存文件到: {file_path}")
        
        # 保存文件
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"保存文件失败: {str(e)}"
            )
        
        # 确定文件类型和时长
        file_type = "video" if file_ext in ["mp4", "avi", "mov"] else "audio"
        duration = None
        
        # 如果是视频，获取时长
        if file_type == "video":
            try:
                video = cv2.VideoCapture(file_path)
                if not video.isOpened():
                    logger.warning(f"无法打开视频文件: {file_path}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="无法打开视频文件，文件可能已损坏"
                    )
                    
                fps = video.get(cv2.CAP_PROP_FPS)
                frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else None
                video.release()
                
                logger.info(f"视频信息: 帧率={fps}, 总帧数={frame_count}, 时长={duration}秒")
            except Exception as e:
                logger.error(f"获取视频时长失败: {str(e)}")
                # 不阻止创建记录，但记录错误
        
        # 创建面试记录
        try:
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
            
            logger.info(f"成功创建面试记录: ID={db_interview.id}")
            return db_interview
            
        except Exception as e:
            logger.error(f"创建面试记录失败: {str(e)}")
            # 如果数据库操作失败，删除已上传的文件
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"已删除文件: {file_path}")
                except:
                    logger.warning(f"删除文件失败: {file_path}")
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建面试记录失败: {str(e)}"
            )
    
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    
    except Exception as e:
        # 捕获所有其他异常
        error_detail = f"上传处理过程中发生错误: {str(e)}"
        logger.error(f"{error_detail}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.get("/", response_model=List[schemas.Interview])
def read_interviews(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
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
    logger.info(f"用户 {current_user.id}({current_user.username}) 请求面试列表")
    try:
        interviews = db.query(DBInterview).filter(DBInterview.user_id == current_user.id).offset(skip).limit(limit).all()
        logger.info(f"返回 {len(interviews)} 条面试记录")
        return interviews
    except Exception as e:
        error_msg = f"获取面试列表失败: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.get("/{interview_id}", response_model=schemas.Interview)
def read_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
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
    logger.info(f"用户 {current_user.id}({current_user.username}) 请求面试记录 ID={interview_id}")
    
    try:
        interview = db.query(DBInterview).filter(DBInterview.id == interview_id).first()
        if not interview:
            logger.warning(f"面试记录不存在: ID={interview_id}")
            raise HTTPException(status_code=404, detail="面试记录不存在")
        
        if interview.user_id != current_user.id and not current_user.is_admin:
            logger.warning(f"用户 {current_user.id} 尝试访问其他用户的面试记录: ID={interview_id}")
            raise HTTPException(status_code=403, detail="没有权限访问此面试记录")
        
        # 检查文件是否仍然存在
        if not os.path.exists(interview.file_path):
            logger.warning(f"面试记录 ID={interview_id} 的文件不存在: {interview.file_path}")
            # 不阻止返回记录，但记录警告
        
        return interview
        
    except HTTPException:
        raise
        
    except Exception as e:
        error_msg = f"获取面试记录失败: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    """删除面试记录
    
    根据ID删除面试记录及其文件
    
    Args:
        interview_id: 面试ID
        db: 数据库会话
        current_user: 当前用户
    """
    logger.info(f"用户 {current_user.id}({current_user.username}) 请求删除面试记录 ID={interview_id}")
    
    try:
        interview = db.query(DBInterview).filter(DBInterview.id == interview_id).first()
        if not interview:
            logger.warning(f"要删除的面试记录不存在: ID={interview_id}")
            raise HTTPException(status_code=404, detail="面试记录不存在")
        
        if interview.user_id != current_user.id and not current_user.is_admin:
            logger.warning(f"用户 {current_user.id} 尝试删除其他用户的面试记录: ID={interview_id}")
            raise HTTPException(status_code=403, detail="没有权限删除此面试记录")
        
        # 删除相关的分析结果
        analysis = db.query(DBAnalysis).filter(DBAnalysis.interview_id == interview_id).first()
        if analysis:
            logger.info(f"删除面试记录 ID={interview_id} 的分析结果")
            db.delete(analysis)
        
        # 删除文件
        file_path = interview.file_path
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"已删除文件: {file_path}")
            except Exception as e:
                logger.error(f"删除文件失败: {file_path}, 错误: {str(e)}")
                # 继续删除记录，但记录错误
        else:
            logger.warning(f"面试记录 ID={interview_id} 的文件不存在: {file_path}")
        
        # 删除记录
        db.delete(interview)
        db.commit()
        logger.info(f"成功删除面试记录: ID={interview_id}")
        
        return None
        
    except HTTPException:
        raise
        
    except Exception as e:
        error_msg = f"删除面试记录失败: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )