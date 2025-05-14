from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any, Union, ForwardRef
from datetime import datetime
import json

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
    
    class Config:
        orm_mode = True

class Interview(InterviewInDB):
    """面试响应模型"""
    # 添加与分析结果的关系
    analysis: Optional['Analysis'] = None
    # 添加与职位的关系
    job_position: Optional['JobPosition'] = None

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
    # 转换为更易用的结构
    speech: Optional[SpeechAnalysis] = None
    visual: Optional[VisualAnalysis] = None
    content: Optional[ContentAnalysis] = None
    overall: Optional[OverallAnalysis] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # 构建语音分析结果
        if any([self.speech_clarity, self.speech_pace, self.speech_emotion]):
            self.speech = SpeechAnalysis(
                clarity=self.speech_clarity or 0.0,
                pace=self.speech_pace or 0.0,
                emotion=self.speech_emotion or ""
            )
        
        # 构建视觉分析结果
        if any([self.facial_expressions, self.eye_contact, self.body_language]):
            self.visual = VisualAnalysis(
                facial_expressions=self._parse_json(self.facial_expressions) or {},
                eye_contact=self.eye_contact or 0.0,
                body_language=self._parse_json(self.body_language) or {}
            )
        
        # 构建内容分析结果
        if any([self.content_relevance, self.content_structure, self.key_points]):
            self.content = ContentAnalysis(
                relevance=self.content_relevance or 0.0,
                structure=self.content_structure or 0.0,
                key_points=self._parse_json(self.key_points) or []
            )
        
        # 构建综合分析结果
        if any([self.overall_score, self.strengths, self.weaknesses, self.suggestions]):
            self.overall = OverallAnalysis(
                score=self.overall_score or 0.0,
                strengths=self._parse_json(self.strengths) or [],
                weaknesses=self._parse_json(self.weaknesses) or [],
                suggestions=self._parse_json(self.suggestions) or []
            )
    
    def _parse_json(self, json_str):
        """解析JSON字符串为Python对象"""
        if not json_str:
            return None
        if isinstance(json_str, (dict, list)):
            return json_str
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return None

# 文件上传响应
class FileUploadResponse(BaseModel):
    """文件上传响应"""
    filename: str
    file_path: str
    file_type: str
    size: int
    duration: Optional[float] = None

# 职位相关模型
from enum import Enum

class TechField(str, Enum):
    """技术领域枚举"""
    AI = "artificial_intelligence"
    BIGDATA = "big_data"
    IOT = "internet_of_things"
    SYSTEM = "intelligent_system"

class PositionType(str, Enum):
    """岗位类型枚举"""
    TECHNICAL = "technical"  # 技术岗
    OPERATION = "operation"  # 运维测试岗
    PRODUCT = "product"      # 产品岗

class JobPositionBase(BaseModel):
    """职位基础模型"""
    title: str
    tech_field: TechField
    position_type: PositionType
    required_skills: str
    job_description: str
    evaluation_criteria: str

class JobPositionCreate(JobPositionBase):
    """职位创建模型"""
    pass

class JobPositionInDB(JobPositionBase):
    """数据库中的职位模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class JobPosition(JobPositionInDB):
    """职位响应模型"""
    pass

# 令牌模型
class Token(BaseModel):
    """访问令牌"""
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """令牌载荷"""
    sub: Optional[int] = None