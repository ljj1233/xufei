from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, Optional
from app.core.auth import get_current_user
from app.db.base import get_db
from app.models.user import User
from app.models.interview import Interview
from app.models.analysis import Analysis
from pydantic import BaseModel
import json

router = APIRouter()

# 响应模型
class AnalysisResponse(BaseModel):
    id: int
    interview_id: int
    overall_score: Optional[float]
    strengths: Optional[list[str]]
    weaknesses: Optional[list[str]]
    suggestions: Optional[list[str]]
    speech_clarity: Optional[float]
    speech_pace: Optional[float]
    speech_emotion: Optional[str]
    facial_expressions: Optional[dict]
    eye_contact: Optional[float]
    body_language: Optional[dict]
    content_relevance: Optional[float]
    content_structure: Optional[float]
    key_points: Optional[list[str]]

# 开始分析
@router.post("/{interview_id}", response_model=AnalysisResponse)
async def start_analysis(
    interview_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    # 获取面试记录
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="面试记录不存在"
        )
    
    # 检查是否已有分析结果
    existing_analysis = db.query(Analysis).filter(Analysis.interview_id == interview_id).first()
    if existing_analysis:
        return existing_analysis
    
    # TODO: 调用实际的分析服务
    # 这里暂时使用模拟数据
    analysis = Analysis(
        interview_id=interview_id,
        overall_score=7.5,
        strengths=json.dumps(["表达清晰", "回答有条理", "态度积极"]),
        weaknesses=json.dumps(["语速偏快", "眼神接触不足"]),
        suggestions=json.dumps(["适当放慢语速", "增加与面试官的眼神交流", "进一步丰富专业知识"]),
        speech_clarity=8.0,
        speech_pace=6.5,
        speech_emotion="自信",
        facial_expressions=json.dumps({"微笑": 0.6, "严肃": 0.3, "思考": 0.1}),
        eye_contact=6.0,
        body_language=json.dumps({"confidence": 7.5, "openness": 8.0}),
        content_relevance=8.0,
        content_structure=7.5,
        key_points=json.dumps(["项目经验丰富", "团队协作能力强", "解决问题思路清晰"])
    )
    
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    return analysis

# 获取分析结果
@router.get("/{interview_id}", response_model=AnalysisResponse)
async def get_analysis(
    interview_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    # 检查面试记录是否属于当前用户
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="面试记录不存在"
        )
    
    # 获取分析结果
    analysis = db.query(Analysis).filter(Analysis.interview_id == interview_id).first()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析结果不存在"
        )
    
    return analysis

# 删除分析结果
@router.delete("/{interview_id}")
async def delete_analysis(
    interview_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    # 检查面试记录是否属于当前用户
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="面试记录不存在"
        )
    
    # 删除分析结果
    analysis = db.query(Analysis).filter(Analysis.interview_id == interview_id).first()
    if analysis:
        db.delete(analysis)
        db.commit()
    
    return {"message": "分析结果已删除"}