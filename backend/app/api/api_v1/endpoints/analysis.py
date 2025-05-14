from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
from typing import Dict, Any

from app.db.database import get_db
from app.db.models import Interview as DBInterview, InterviewAnalysis as DBAnalysis, User as DBUser
from app.models import schemas
from app.utils.auth import get_current_active_user
from app.services.analysis import analyze_interview

router = APIRouter()


@router.post("/{interview_id}", response_model=schemas.Analysis)
def create_interview_analysis(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    """创建面试分析
    
    对指定面试进行多模态分析
    
    Args:
        interview_id: 面试ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        Analysis: 分析结果
    """
    # 检查面试是否存在
    interview = db.query(DBInterview).filter(DBInterview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试记录不存在")
    
    # 检查权限
    if interview.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有权限分析此面试")
    
    # 检查是否已有分析结果
    existing_analysis = db.query(DBAnalysis).filter(DBAnalysis.interview_id == interview_id).first()
    if existing_analysis:
        return existing_analysis
    
    # 执行面试分析
    try:
        analysis_result = analyze_interview(interview.file_path, interview.file_type)
        
        # 创建分析记录
        db_analysis = InterviewAnalysis(
            interview_id=interview_id,
            speech_clarity=analysis_result.get("speech", {}).get("clarity"),
            speech_pace=analysis_result.get("speech", {}).get("pace"),
            speech_emotion=analysis_result.get("speech", {}).get("emotion"),
            facial_expressions=json.dumps(analysis_result.get("visual", {}).get("facial_expressions", {})),
            eye_contact=analysis_result.get("visual", {}).get("eye_contact"),
            body_language=json.dumps(analysis_result.get("visual", {}).get("body_language", {})),
            content_relevance=analysis_result.get("content", {}).get("relevance"),
            content_structure=analysis_result.get("content", {}).get("structure"),
            key_points=json.dumps(analysis_result.get("content", {}).get("key_points", [])),
            overall_score=analysis_result.get("overall", {}).get("score"),
            strengths=json.dumps(analysis_result.get("overall", {}).get("strengths", [])),
            weaknesses=json.dumps(analysis_result.get("overall", {}).get("weaknesses", [])),
            suggestions=json.dumps(analysis_result.get("overall", {}).get("suggestions", []))
        )
        
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)
        
        return db_analysis
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析过程中出错: {str(e)}"
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
    # 检查面试是否存在
    interview = db.query(DBInterview).filter(DBInterview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试记录不存在")
    
    # 检查权限
    if interview.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="没有权限查看此分析结果")
    
    # 获取分析结果
    analysis = db.query(InterviewAnalysis).filter(InterviewAnalysis.interview_id == interview_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="分析结果不存在，请先创建分析")
    
    return analysis