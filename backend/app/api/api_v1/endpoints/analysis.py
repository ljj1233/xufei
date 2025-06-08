from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import json

from app.api.deps import get_db
from app.models.analysis import Analysis as AnalysisModel
from app.schemas.analysis import Analysis as AnalysisSchema
from app.schemas.analysis import AnalysisCreate
from app.services.ai_agent_service import ai_agent_service

router = APIRouter()

@router.get("/", response_model=List[AnalysisSchema])
def read_analyses(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取分析结果列表"""
    analyses = db.query(AnalysisModel).offset(skip).limit(limit).all()
    return analyses

@router.get("/{analysis_id}", response_model=AnalysisSchema)
def read_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """获取特定分析结果"""
    analysis = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis

@router.get("/interview/{interview_id}", response_model=AnalysisSchema)
def read_analysis_by_interview(interview_id: int, db: Session = Depends(get_db)):
    """通过面试ID获取分析结果"""
    analysis = db.query(AnalysisModel).filter(AnalysisModel.interview_id == interview_id).first()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis

@router.post("/", response_model=AnalysisSchema)
def create_analysis(analysis: AnalysisCreate, db: Session = Depends(get_db)):
    """创建分析结果"""
    db_analysis = AnalysisModel(
        interview_id=analysis.interview_id,
        overall_score=analysis.overall.score if analysis.overall else None,
        strengths=analysis.overall.strengths if analysis.overall else None,
        weaknesses=analysis.overall.weaknesses if analysis.overall else None,
        suggestions=analysis.overall.suggestions if analysis.overall else None,
        speech_clarity=analysis.speech.clarity if analysis.speech else None,
        speech_pace=analysis.speech.pace if analysis.speech else None,
        speech_emotion=analysis.speech.emotion if analysis.speech else None,
        facial_expressions=analysis.visual.facial_expressions if analysis.visual else None,
        eye_contact=analysis.visual.eye_contact if analysis.visual else None,
        body_language=analysis.visual.body_language if analysis.visual else None,
        content_relevance=analysis.content.relevance if analysis.content else None,
        content_structure=analysis.content.structure if analysis.content else None,
        key_points=analysis.content.key_points if analysis.content else None
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis

@router.post("/quick-practice", response_model=AnalysisSchema)
async def analyze_quick_practice(
    interview_id: int = Form(...),
    question_id: int = Form(...),
    answer_text: str = Form(...),
    job_description: Optional[str] = Form(""),
    question: Optional[str] = Form(""),
    audio_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """分析快速练习回答并保存结果"""
    try:
        # 读取音频文件（如果有）
        audio_data = None
        if audio_file:
            audio_data = await audio_file.read()
        
        # 调用AI智能体服务进行快速练习分析
        analysis_result = await ai_agent_service.analyze_quick_practice(
            session_id=interview_id,
            question_id=question_id,
            answer_text=answer_text,
            audio_data=audio_data,
            job_description=job_description,
            question=question
        )
        
        if not analysis_result:
            raise HTTPException(status_code=500, detail="Failed to analyze quick practice")
        
        # 检查是否已存在该面试的分析结果
        existing_analysis = db.query(AnalysisModel).filter(AnalysisModel.interview_id == interview_id).first()
        
        if existing_analysis:
            # 更新现有记录
            existing_analysis.analysis_type = "quick_practice"
            existing_analysis.quick_practice_data = analysis_result
            existing_analysis.overall_score = analysis_result.get("feedback", {}).get("overall_score", 0) / 10  # 转换为0-10分制
            db.commit()
            db.refresh(existing_analysis)
            return existing_analysis
        else:
            # 创建新记录
            new_analysis = AnalysisModel(
                interview_id=interview_id,
                analysis_type="quick_practice",
                quick_practice_data=analysis_result,
                overall_score=analysis_result.get("feedback", {}).get("overall_score", 0) / 10  # 转换为0-10分制
            )
            db.add(new_analysis)
            db.commit()
            db.refresh(new_analysis)
            return new_analysis
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing quick practice: {str(e)}")

@router.put("/{analysis_id}", response_model=AnalysisSchema)
def update_analysis(analysis_id: int, analysis: AnalysisCreate, db: Session = Depends(get_db)):
    """更新分析结果"""
    db_analysis = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()
    if db_analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # 更新字段
    if analysis.overall:
        db_analysis.overall_score = analysis.overall.score
        db_analysis.strengths = analysis.overall.strengths
        db_analysis.weaknesses = analysis.overall.weaknesses
        db_analysis.suggestions = analysis.overall.suggestions
    
    if analysis.speech:
        db_analysis.speech_clarity = analysis.speech.clarity
        db_analysis.speech_pace = analysis.speech.pace
        db_analysis.speech_emotion = analysis.speech.emotion
    
    if analysis.visual:
        db_analysis.facial_expressions = analysis.visual.facial_expressions
        db_analysis.eye_contact = analysis.visual.eye_contact
        db_analysis.body_language = analysis.visual.body_language
    
    if analysis.content:
        db_analysis.content_relevance = analysis.content.relevance
        db_analysis.content_structure = analysis.content.structure
        db_analysis.key_points = analysis.content.key_points
    
    db.commit()
    db.refresh(db_analysis)
    return db_analysis

@router.delete("/{analysis_id}", response_model=AnalysisSchema)
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """删除分析结果"""
    db_analysis = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()
    if db_analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    db.delete(db_analysis)
    db.commit()
    return db_analysis