from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

# 用户相关模型
class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    username: str

class UserCreate(UserBase):
    """用户创建模型"""
    password: str

class UserInDB(UserBase):
    """数据库中的用户模型"""
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

class User(UserInDB):
    """用户响应模型"""
    pass

# 面试相关模型
class InterviewBase(BaseModel):
    """面试基础模型"""
    title: str
    description: Optional[str] = None

class InterviewCreate(InterviewBase):
    """面试创建模型"""
    pass

class InterviewInDB(InterviewBase):
    """数据库中的面试模型"""
    id: int
    file_path: str
    file_type: str
    duration: Optional[float] = None
    created_at: datetime
    user_id: int
    
    class Config:
        orm_mode = True

class Interview(InterviewInDB):
    """面试响应模型"""
    pass

# 分析结果相关模型
class AnalysisBase(BaseModel):
    """分析结果基础模型"""
    interview_id: int

class SpeechAnalysis(BaseModel):
    """语音分析结果"""
    clarity: float = Field(..., description="语音清晰度评分(0-10)")
    pace: float = Field(..., description="语速评分(0-10)")
    emotion: str = Field(..., description="主要情感类型")

class VisualAnalysis(BaseModel):
    """视觉分析结果"""
    facial_expressions: Dict[str, Any] = Field(..., description="面部表情分析")
    eye_contact: float = Field(..., description="眼神接触评分(0-10)")
    body_language: Dict[str, Any] = Field(..., description="肢体语言分析")

class ContentAnalysis(BaseModel):
    """内容分析结果"""
    relevance: float = Field(..., description="内容相关性评分(0-10)")
    structure: float = Field(..., description="内容结构评分(0-10)")
    key_points: List[str] = Field(..., description="关键点列表")

class OverallAnalysis(BaseModel):
    """综合分析结果"""
    score: float = Field(..., description="综合评分(0-10)")
    strengths: List[str] = Field(..., description="优势列表")
    weaknesses: List[str] = Field(..., description="劣势列表")
    suggestions: List[str] = Field(..., description="建议列表")

class AnalysisCreate(AnalysisBase):
    """分析结果创建模型"""
    speech: Optional[SpeechAnalysis] = None
    visual: Optional[VisualAnalysis] = None
    content: Optional[ContentAnalysis] = None
    overall: Optional[OverallAnalysis] = None

class AnalysisInDB(AnalysisBase):
    """数据库中的分析结果模型"""
    id: int
    speech_clarity: Optional[float] = None
    speech_pace: Optional[float] = None
    speech_emotion: Optional[str] = None
    facial_expressions: Optional[Dict[str, Any]] = None
    eye_contact: Optional[float] = None
    body_language: Optional[Dict[str, Any]] = None
    content_relevance: Optional[float] = None
    content_structure: Optional[float] = None
    key_points: Optional[List[str]] = None
    overall_score: Optional[float] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class Analysis(AnalysisInDB):
    """分析结果响应模型"""
    pass

# 文件上传响应
class FileUploadResponse(BaseModel):
    """文件上传响应"""
    filename: str
    file_path: str
    file_type: str
    size: int
    duration: Optional[float] = None

# 令牌模型
class Token(BaseModel):
    """访问令牌"""
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """令牌载荷"""
    sub: Optional[int] = None