from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import json
from typing import Dict, Any
import logging
import traceback
import os

from app.db.database import get_db
from app.models.interview import Interview as DBInterview
from app.models.analysis import InterviewAnalysis as DBAnalysis
from app.models.user import User as DBUser
from app.models import schemas
from app.utils.auth import get_current_active_user
from app.services.analysis import analyze_interview

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{interview_id}", response_model=schemas.Analysis)
def create_interview_analysis(
    interview_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    """创建面试分析
    
    对指定面试进行多模态分析
    
    Args:
        interview_id: 面试ID
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        Analysis: 分析结果
    """
    logger.info(f"用户 {current_user.id}({current_user.username}) 请求分析面试 ID={interview_id}")
    
    try:
        # 检查面试是否存在
        interview = db.query(DBInterview).filter(DBInterview.id == interview_id).first()
        if not interview:
            logger.warning(f"面试记录不存在: ID={interview_id}")
            raise HTTPException(status_code=404, detail="面试记录不存在")
        
        # 检查权限
        if interview.user_id != current_user.id and not current_user.is_admin:
            logger.warning(f"用户 {current_user.id} 尝试分析其他用户的面试: ID={interview_id}")
            raise HTTPException(status_code=403, detail="没有权限分析此面试")
        
        # 检查面试文件是否存在
        if not os.path.exists(interview.file_path):
            logger.error(f"面试文件不存在: {interview.file_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="面试文件不存在，无法进行分析"
            )
        
        # 检查是否已有分析结果
        existing_analysis = db.query(DBAnalysis).filter(DBAnalysis.interview_id == interview_id).first()
        if existing_analysis:
            logger.info(f"面试 ID={interview_id} 已有分析结果，直接返回")
            return existing_analysis
        
        # 创建初始分析记录，状态为"处理中"
        initial_analysis = DBAnalysis(
            interview_id=interview_id,
            status="processing",
            overall_score=0
        )
        db.add(initial_analysis)
        db.commit()
        db.refresh(initial_analysis)
        
        logger.info(f"开始分析面试 ID={interview_id}, 文件类型: {interview.file_type}")
        
        # 执行面试分析（可选：作为后台任务）
        def perform_analysis(db_id: int, file_path: str, file_type: str):
            """执行分析并更新数据库"""
            logger.info(f"开始后台分析面试 ID={interview_id}")
            
            try:
                # 创建新的数据库会话
                from app.db.database import SessionLocal
                analysis_db = SessionLocal()
                
                # 获取分析结果
                analysis_result = analyze_interview(file_path, file_type)
                
                # 获取分析记录
                db_analysis = analysis_db.query(DBAnalysis).filter(DBAnalysis.interview_id == db_id).first()
                if not db_analysis:
                    logger.error(f"分析记录不存在: interview_id={db_id}")
                    return
                
                # 更新分析记录
                db_analysis.speech_clarity = analysis_result.get("speech", {}).get("clarity")
                db_analysis.speech_pace = analysis_result.get("speech", {}).get("pace")
                db_analysis.speech_emotion = analysis_result.get("speech", {}).get("emotion")
                db_analysis.facial_expressions = json.dumps(analysis_result.get("visual", {}).get("facial_expressions", {}))
                db_analysis.eye_contact = analysis_result.get("visual", {}).get("eye_contact")
                db_analysis.body_language = json.dumps(analysis_result.get("visual", {}).get("body_language", {}))
                db_analysis.content_relevance = analysis_result.get("content", {}).get("relevance")
                db_analysis.content_structure = analysis_result.get("content", {}).get("structure")
                db_analysis.key_points = json.dumps(analysis_result.get("content", {}).get("key_points", []))
                db_analysis.overall_score = analysis_result.get("overall", {}).get("score")
                db_analysis.strengths = json.dumps(analysis_result.get("overall", {}).get("strengths", []))
                db_analysis.weaknesses = json.dumps(analysis_result.get("overall", {}).get("weaknesses", []))
                db_analysis.suggestions = json.dumps(analysis_result.get("overall", {}).get("suggestions", []))
                db_analysis.status = "completed"
                
                analysis_db.commit()
                logger.info(f"面试 ID={db_id} 分析完成")
                
            except Exception as e:
                logger.error(f"分析面试 ID={db_id} 失败: {str(e)}\n{traceback.format_exc()}")
                try:
                    # 更新分析状态为失败
                    db_analysis = analysis_db.query(DBAnalysis).filter(DBAnalysis.interview_id == db_id).first()
                    if db_analysis:
                        db_analysis.status = "failed"
                        db_analysis.error_message = str(e)
                        analysis_db.commit()
                except:
                    pass
            finally:
                analysis_db.close()
        
        # 对于大文件，使用后台任务处理
        if interview.file_type == "video" or (interview.duration and interview.duration > 60):
            logger.info(f"面试 ID={interview_id} 将在后台处理")
            background_tasks.add_task(
                perform_analysis, 
                interview_id, 
                interview.file_path, 
                interview.file_type
            )
            return initial_analysis
        else:
            # 对于小文件，直接处理
            try:
                analysis_result = analyze_interview(interview.file_path, interview.file_type)
                
                # 更新分析记录
                initial_analysis.speech_clarity = analysis_result.get("speech", {}).get("clarity")
                initial_analysis.speech_pace = analysis_result.get("speech", {}).get("pace")
                initial_analysis.speech_emotion = analysis_result.get("speech", {}).get("emotion")
                initial_analysis.facial_expressions = json.dumps(analysis_result.get("visual", {}).get("facial_expressions", {}))
                initial_analysis.eye_contact = analysis_result.get("visual", {}).get("eye_contact")
                initial_analysis.body_language = json.dumps(analysis_result.get("visual", {}).get("body_language", {}))
                initial_analysis.content_relevance = analysis_result.get("content", {}).get("relevance")
                initial_analysis.content_structure = analysis_result.get("content", {}).get("structure")
                initial_analysis.key_points = json.dumps(analysis_result.get("content", {}).get("key_points", []))
                initial_analysis.overall_score = analysis_result.get("overall", {}).get("score")
                initial_analysis.strengths = json.dumps(analysis_result.get("overall", {}).get("strengths", []))
                initial_analysis.weaknesses = json.dumps(analysis_result.get("overall", {}).get("weaknesses", []))
                initial_analysis.suggestions = json.dumps(analysis_result.get("overall", {}).get("suggestions", []))
                initial_analysis.status = "completed"
                
                db.commit()
                db.refresh(initial_analysis)
                
                logger.info(f"面试 ID={interview_id} 分析完成")
                return initial_analysis
                
            except Exception as e:
                error_msg = f"分析面试失败: {str(e)}"
                logger.error(f"{error_msg}\n{traceback.format_exc()}")
                
                # 更新分析状态为失败
                initial_analysis.status = "failed"
                initial_analysis.error_message = str(e)
                db.commit()
                
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                )
    
    except HTTPException:
        raise
        
    except Exception as e:
        error_msg = f"创建面试分析过程中出错: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.get("/{interview_id}", response_model=schemas.Analysis)
def get_interview_analysis(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    """获取面试分析结果
    
    获取指定面试的分析结果
    
    Args:
        interview_id: 面试ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        Analysis: 分析结果
    """
    logger.info(f"用户 {current_user.id}({current_user.username}) 请求面试分析结果 ID={interview_id}")
    
    try:
        # 检查面试是否存在
        interview = db.query(DBInterview).filter(DBInterview.id == interview_id).first()
        if not interview:
            logger.warning(f"面试记录不存在: ID={interview_id}")
            raise HTTPException(status_code=404, detail="面试记录不存在")
        
        # 检查权限
        if interview.user_id != current_user.id and not current_user.is_admin:
            logger.warning(f"用户 {current_user.id} 尝试查看其他用户的分析结果: ID={interview_id}")
            raise HTTPException(status_code=403, detail="没有权限查看此分析结果")
        
        # 获取分析结果
        analysis = db.query(DBAnalysis).filter(DBAnalysis.interview_id == interview_id).first()
        if not analysis:
            logger.warning(f"面试 ID={interview_id} 的分析结果不存在")
            raise HTTPException(status_code=404, detail="分析结果不存在，请先创建分析")
        
        # 如果分析状态为失败，返回错误信息
        if analysis.status == "failed":
            error_message = analysis.error_message or "未知错误"
            logger.warning(f"面试 ID={interview_id} 的分析失败: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"分析失败: {error_message}"
            )
        
        # 如果分析状态为处理中，返回相应信息
        if analysis.status == "processing":
            logger.info(f"面试 ID={interview_id} 的分析正在处理中")
            return analysis
        
        return analysis
        
    except HTTPException:
        raise
        
    except Exception as e:
        error_msg = f"获取分析结果失败: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )