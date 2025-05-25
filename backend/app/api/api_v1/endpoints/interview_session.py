from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import asyncio
import base64
from datetime import datetime

from app.db.database import get_db
from app.models.interview_session import InterviewSession, InterviewQuestion, RealTimeFeedback, SessionStatus
from app.models.user import User
from app.utils.auth import get_current_active_user
from app.services.interview_session_service import interview_session_service
from app.services.ai_agent_service import ai_agent_service
from app.schemas.interview_session import (
    InterviewSessionCreate, InterviewSessionResponse, 
    InterviewQuestionResponse, RealTimeFeedbackResponse,
    SessionAnalysisResponse
)

router = APIRouter()

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: int):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: int):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_feedback(self, session_id: int, feedback: Dict[str, Any]):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(feedback))
            except:
                self.disconnect(session_id)

manager = ConnectionManager()

@router.post("/", response_model=InterviewSessionResponse)
def create_interview_session(
    session_data: InterviewSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新的模拟面试会话"""
    try:
        session = interview_session_service.create_session(
            db=db,
            user_id=current_user.id,
            job_position_id=session_data.job_position_id,
            title=session_data.title,
            description=session_data.description,
            planned_duration=session_data.planned_duration,
            question_count=session_data.question_count,
            difficulty_level=session_data.difficulty_level
        )
        return session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建面试会话失败: {str(e)}"
        )

@router.get("/", response_model=List[InterviewSessionResponse])
def get_user_sessions(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户的面试会话列表"""
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return sessions

@router.get("/{session_id}", response_model=InterviewSessionResponse)
def get_session_detail(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取面试会话详情"""
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    return session

@router.post("/{session_id}/start")
def start_interview_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """开始面试会话"""
    # 验证会话所有权
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    try:
        result = interview_session_service.start_session(db, session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动面试会话失败: {str(e)}"
        )

@router.get("/{session_id}/questions", response_model=List[InterviewQuestionResponse])
def get_session_questions(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取面试会话的问题列表"""
    # 验证会话所有权
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == session_id
    ).order_by(InterviewQuestion.order_index).all()
    
    return questions

@router.post("/questions/{question_id}/answer")
def submit_question_answer(
    question_id: int,
    answer_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """提交问题回答"""
    # 验证问题所有权
    question = db.query(InterviewQuestion).join(InterviewSession).filter(
        InterviewQuestion.id == question_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="问题不存在")
    
    try:
        result = interview_session_service.answer_question(
            db=db,
            question_id=question_id,
            answer_text=answer_data.get("answer_text", ""),
            answer_duration=answer_data.get("answer_duration", 0)
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交回答失败: {str(e)}"
        )

@router.post("/{session_id}/complete", response_model=SessionAnalysisResponse)
def complete_interview_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """完成面试会话并生成分析报告"""
    # 验证会话所有权
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    try:
        analysis_result = interview_session_service.complete_session(db, session_id)
        return analysis_result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"完成面试会话失败: {str(e)}"
        )

@router.get("/{session_id}/analysis", response_model=SessionAnalysisResponse)
def get_session_analysis(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取面试会话分析结果"""
    # 验证会话所有权
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    if not session.final_analysis:
        raise HTTPException(status_code=404, detail="分析结果不存在，请先完成面试")
    
    return session.final_analysis

@router.get("/{session_id}/feedback", response_model=List[RealTimeFeedbackResponse])
def get_session_feedback(
    session_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取面试会话的实时反馈记录"""
    # 验证会话所有权
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    feedback_items = db.query(RealTimeFeedback).filter(
        RealTimeFeedback.session_id == session_id
    ).order_by(RealTimeFeedback.timestamp.desc()).offset(skip).limit(limit).all()
    
    return feedback_items

@router.websocket("/{session_id}/realtime")
async def websocket_realtime_feedback(
    websocket: WebSocket,
    session_id: int,
    db: Session = Depends(get_db)
):
    """WebSocket端点，用于实时反馈"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # 接收客户端数据
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理不同类型的实时数据
            data_type = message.get("type")
            data_content = message.get("data", {})
            
            if data_type in ["audio", "video", "text"]:
                # 处理实时数据并生成反馈
                feedback_items = await interview_session_service.process_real_time_data(
                    session_id, data_type, data_content
                )
                
                # 保存反馈到数据库
                for feedback_item in feedback_items:
                    db_feedback = RealTimeFeedback(
                        session_id=session_id,
                        feedback_type=feedback_item["type"],
                        feedback_category=feedback_item["category"],
                        message=feedback_item["message"],
                        severity=feedback_item["severity"],
                        score=feedback_item["score"],
                        session_time=feedback_item["session_time"]
                    )
                    db.add(db_feedback)
                
                db.commit()
                
                # 发送反馈给客户端
                if feedback_items:
                    await manager.send_feedback(session_id, {
                        "type": "feedback",
                        "items": feedback_items
                    })
            
            elif data_type == "heartbeat":
                # 心跳检测
                await manager.send_feedback(session_id, {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(session_id)

@router.delete("/{session_id}")
def delete_interview_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除面试会话"""
    # 验证会话所有权
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    # 只允许删除未开始或已完成的会话
    if session.status == SessionStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="无法删除进行中的面试会话")
    
    db.delete(session)
    db.commit()
    
    return {"message": "面试会话已删除"}

@router.post("/{session_id}/pause")
def pause_interview_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """暂停面试会话"""
    # 验证会话所有权
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    if session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="只能暂停进行中的面试会话")
    
    session.status = SessionStatus.PAUSED
    db.commit()
    
    return {"message": "面试会话已暂停", "status": session.status}

@router.post("/{session_id}/resume")
def resume_interview_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """恢复面试会话"""
    # 验证会话所有权
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    if session.status != SessionStatus.PAUSED:
        raise HTTPException(status_code=400, detail="只能恢复暂停的面试会话")
    
    session.status = SessionStatus.IN_PROGRESS
    db.commit()
    
    return {"message": "面试会话已恢复", "status": session.status}

@router.post("/{session_id}/upload-audio")
async def upload_audio_stream(
    session_id: int,
    audio_file: UploadFile = File(...),
    timestamp: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """上传音频流进行实时分析"""
    # 验证会话所有权
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    if session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="面试会话未在进行中")
    
    try:
        # 读取音频数据
        audio_data = await audio_file.read()
        
        # 调用AI智能体进行实时音频分析
        analysis_result = await ai_agent_service.analyze_audio_stream(
            session_id=session_id,
            audio_data=audio_data,
            timestamp=timestamp
        )
        
        # 如果有分析结果，保存反馈
        if analysis_result:
            feedback_items = ai_agent_service.generate_audio_feedback(analysis_result)
            
            for feedback_item in feedback_items:
                db_feedback = RealTimeFeedback(
                    session_id=session_id,
                    feedback_type="speech",
                    feedback_category=feedback_item.get("category", "general"),
                    message=feedback_item.get("message", ""),
                    severity=feedback_item.get("severity", "info"),
                    score=feedback_item.get("score", 5.0),
                    session_time=feedback_item.get("session_time", 0),
                    display_duration=feedback_item.get("display_duration", 3.0)
                )
                db.add(db_feedback)
            
            db.commit()
            
            # 通过WebSocket发送实时反馈
            await manager.send_feedback(session_id, {
                "type": "audio_feedback",
                "analysis": analysis_result,
                "feedback": feedback_items
            })
        
        return {"status": "success", "analysis": analysis_result}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"音频分析失败: {str(e)}"
        )

@router.post("/{session_id}/upload-video")
async def upload_video_frame(
    session_id: int,
    video_file: UploadFile = File(...),
    timestamp: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """上传视频帧进行实时分析"""
    # 验证会话所有权
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    if session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="面试会话未在进行中")
    
    try:
        # 读取视频帧数据
        frame_data = await video_file.read()
        
        # 调用AI智能体进行实时视频分析
        analysis_result = await ai_agent_service.analyze_video_frame(
            session_id=session_id,
            frame_data=frame_data,
            timestamp=timestamp
        )
        
        # 如果有分析结果，保存反馈
        if analysis_result:
            feedback_items = ai_agent_service.generate_video_feedback(analysis_result)
            
            for feedback_item in feedback_items:
                db_feedback = RealTimeFeedback(
                    session_id=session_id,
                    feedback_type="visual",
                    feedback_category=feedback_item.get("category", "general"),
                    message=feedback_item.get("message", ""),
                    severity=feedback_item.get("severity", "info"),
                    score=feedback_item.get("score", 5.0),
                    session_time=feedback_item.get("session_time", 0),
                    display_duration=feedback_item.get("display_duration", 3.0)
                )
                db.add(db_feedback)
            
            db.commit()
            
            # 通过WebSocket发送实时反馈
            await manager.send_feedback(session_id, {
                "type": "video_feedback",
                "analysis": analysis_result,
                "feedback": feedback_items
            })
        
        return {"status": "success", "analysis": analysis_result}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"视频分析失败: {str(e)}"
        )

@router.post("/{session_id}/analyze-answer")
async def analyze_question_answer(
    session_id: int,
    question_id: int,
    answer_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """分析问题回答"""
    # 验证会话所有权
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    # 验证问题存在
    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.id == question_id,
        InterviewQuestion.session_id == session_id
    ).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="问题不存在")
    
    try:
        # 调用AI智能体分析回答
        analysis_result = await ai_agent_service.analyze_question_answer(
            session_id=session_id,
            question_id=question_id,
            answer_text=answer_data.get("answer_text", ""),
            audio_features=answer_data.get("audio_features"),
            visual_features=answer_data.get("visual_features")
        )
        
        # 更新问题的分析结果
        question.answer_analysis = analysis_result
        question.answer_score = analysis_result.get("overall_scores", {}).get("total", 0)
        
        db.commit()
        
        return {"status": "success", "analysis": analysis_result}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"回答分析失败: {str(e)}"
        )

@router.get("/{session_id}/real-time-status")
async def get_real_time_status(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取实时分析状态"""
    # 验证会话所有权
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="面试会话不存在")
    
    try:
        # 获取AI智能体的实时状态
        status_info = ai_agent_service.get_real_time_status(session_id)
        
        return {
            "session_id": session_id,
            "is_analyzing": status_info.get("is_analyzing", False),
            "session_time": status_info.get("session_time", 0),
            "analysis_count": status_info.get("analysis_count", 0),
            "last_feedback_time": status_info.get("last_feedback_time")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态失败: {str(e)}"
        )