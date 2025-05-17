from pydantic import BaseModel
from typing import Optional, Dict, Any, Union
from datetime import datetime

class InterviewBase(BaseModel):
    """面试基础模型"""
    title: str
    description: Optional[str] = None

class InterviewCreate(InterviewBase):
    """面试创建模型"""
    job_position_id: Optional[int] = None

class InterviewInDB(InterviewBase):
    """数据库中的面试模型"""
    id: int
    file_path: str
    file_type: str
    duration: Optional[float] = None
    created_at: datetime
    user_id: int
    job_position_id: Optional[int] = None
    
    model_config = dict(from_attributes=True, arbitrary_types_allowed=True)

class Interview(InterviewInDB):
    """面试响应模型"""
    # 使用字符串类型注解代替ForwardRef
    analysis: Optional[Dict[str, Any]] = None
    job_position: Optional[Dict[str, Any]] = None