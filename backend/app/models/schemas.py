# 此文件用于向后兼容，实际模型已移至app.schemas包
# 重定向导入以保持现有代码兼容性

from app.schemas.user import UserBase, UserCreate, UserUpdate, UserInDB, User
from app.schemas.interview import InterviewBase, InterviewCreate, InterviewInDB, Interview
from app.schemas.analysis import AnalysisBase, SpeechAnalysis, VisualAnalysis, ContentAnalysis, OverallAnalysis, AnalysisCreate, AnalysisInDB, Analysis
from app.schemas.job_position import JobPositionBase, JobPositionCreate, JobPositionInDB, JobPosition, TechField, PositionType
from app.schemas.token import Token, TokenPayload
from app.schemas.file import FileUploadResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

# 用户相关模型
class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    username: str

class UserCreate(UserBase):
    """用户创建模型"""
    password: str

class UserUpdate(BaseModel):
    """用户更新模型"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserStatusUpdate(BaseModel):
    """用户状态更新模型"""
    is_active: bool

class UserAdminUpdate(BaseModel):
    """用户管理员权限更新模型"""
    is_admin: bool

class User(BaseModel):
    """用户响应模型"""
    id: int
    email: EmailStr
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

# Token相关模型
class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token数据模型"""
    sub: Optional[str] = None

# 导出所有模型
__all__ = [
    # 用户模型
    'UserBase', 'UserCreate', 'UserUpdate', 'UserInDB', 'User',
    # 面试模型
    'InterviewBase', 'InterviewCreate', 'InterviewInDB', 'Interview',
    # 分析模型
    'AnalysisBase', 'SpeechAnalysis', 'VisualAnalysis', 'ContentAnalysis', 
    'OverallAnalysis', 'AnalysisCreate', 'AnalysisInDB', 'Analysis',
    # 职位模型
    'JobPositionBase', 'JobPositionCreate', 'JobPositionInDB', 'JobPosition',
    'TechField', 'PositionType',
    # 令牌模型
    'Token', 'TokenPayload',
    # 文件模型
    'FileUploadResponse'
]