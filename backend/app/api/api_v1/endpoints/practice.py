"""
面试练习相关API接口

提供面试练习模式相关的功能，包括获取练习题目、提交答案录音和查看参考答案等
"""

import logging
import os
import uuid
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Body, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.interview import InterviewQuestion
from agent.services.question_service import QuestionGenerationService

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/practice/{position_id}", response_model=List[Dict[str, Any]])
async def get_practice_questions(
    position_id: int, 
    count: Optional[int] = Query(6, description="需要获取的题目数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定职位的面试练习题目
    
    Args:
        position_id: 职位ID
        count: 题目数量，默认为6道
        
    Returns:
        题目列表，每个题目包含问题内容、技能标签、建议回答时长
    """
    try:
        logger.info(f"用户{current_user.id}请求职位{position_id}的练习题目，数量={count}")
        
        # 实例化问题生成服务
        question_service = QuestionGenerationService(db=db)
        
        # 获取题目
        questions = await question_service.generate_questions_for_position(position_id, count)
        
        # 从返回结果中移除参考答案，避免直接展示给用户
        for q in questions:
            # 保存答案长度信息，但不返回具体内容
            answer_length = len(q.get("reference_answer", "")) if q.get("reference_answer") else 0
            q["has_reference_answer"] = answer_length > 0
            q["reference_answer_length"] = answer_length
            
            # 移除参考答案
            if "reference_answer" in q:
                del q["reference_answer"]
        
        logger.info(f"成功返回{len(questions)}道练习题目")
        return questions
        
    except Exception as e:
        logger.error(f"获取练习题目时出错: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取练习题目失败: {str(e)}"
        )

@router.get("/questions/{question_id}/answer", response_model=Dict[str, Any])
async def get_question_answer(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定题目的参考答案
    
    Args:
        question_id: 题目ID
        
    Returns:
        包含参考答案的字典
    """
    try:
        logger.info(f"用户{current_user.id}请求题目{question_id}的参考答案")
        
        # 查询题目
        question = db.query(InterviewQuestion).filter(InterviewQuestion.id == question_id).first()
        
        if not question:
            logger.warning(f"题目{question_id}不存在")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在"
            )
        
        # 返回参考答案
        result = {
            "id": question.id,
            "question": question.content,
            "reference_answer": question.reference_answer
        }
        
        logger.info(f"成功返回题目{question_id}的参考答案")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取参考答案时出错: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取参考答案失败: {str(e)}"
        )

@router.post("/practice/upload_audio", response_model=Dict[str, Any])
async def upload_practice_audio(
    file: UploadFile = File(...),
    question_id: int = Form(...),
    position_id: int = Form(...),
    current_user: User = Depends(get_current_user)
):
    """
    上传练习回答的音频文件
    
    Args:
        file: 音频文件
        question_id: 题目ID
        position_id: 职位ID
        
    Returns:
        上传结果
    """
    try:
        logger.info(f"用户{current_user.id}上传题目{question_id}的回答音频")
        
        # 确保上传目录存在
        upload_dir = os.path.join("uploads", "practice", str(current_user.id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成文件名
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # 这里只保存文件，不进行复杂分析
        # 如果需要，可以添加简单的音频分析逻辑
        
        logger.info(f"成功保存音频文件: {file_path}")
        return {
            "success": True,
            "file_path": file_path,
            "message": "音频上传成功"
        }
        
    except Exception as e:
        logger.error(f"上传音频文件时出错: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传音频失败: {str(e)}"
        ) 