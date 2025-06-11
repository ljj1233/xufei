from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SessionStatusEnum(str, Enum):
    PREPARING = "preparing"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class QuestionTypeEnum(str, Enum):
    SELF_INTRO = "self_introduction"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SCENARIO = "scenario"
    CASE_STUDY = "case_study"
    CODING = "coding"
    SYSTEM_DESIGN = "system_design"

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class InterviewModeEnum(str, Enum):
    QUICK = "quick"
    FULL = "full"

# 创建面试会话的请求模型
class InterviewSessionCreate(BaseModel):
    job_position_id: int = Field(..., description="职位ID")
    title: str = Field(..., min_length=1, max_length=200, description="面试标题")
    description: Optional[str] = Field(None, max_length=1000, description="面试描述")
    planned_duration: int = Field(1800, ge=300, le=7200, description="计划时长(秒)，默认30分钟")
    question_count: int = Field(5, ge=1, le=20, description="问题数量，默认5个")
    difficulty_level: DifficultyLevel = Field(DifficultyLevel.MEDIUM, description="难度等级")
    enable_real_time_feedback: bool = Field(True, description="是否启用实时反馈")
    mode: InterviewModeEnum = Field(InterviewModeEnum.FULL, description="面试模式，'quick'为快速面试，'full'为完整面试")

# 面试会话响应模型
class InterviewSessionResponse(BaseModel):
    id: int
    user_id: int
    job_position_id: int
    title: str
    description: Optional[str]
    status: SessionStatusEnum
    planned_duration: int
    actual_duration: Optional[int]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    enable_real_time_feedback: bool
    question_count: int
    difficulty_level: str
    mode: InterviewModeEnum
    overall_score: Optional[float]
    completion_rate: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# 面试问题响应模型
class InterviewQuestionResponse(BaseModel):
    id: int
    session_id: int
    question_text: str
    question_type: QuestionTypeEnum
    expected_duration: int
    difficulty: str
    order_index: int
    is_answered: bool
    answer_text: Optional[str]
    answer_duration: Optional[int]
    answer_started_at: Optional[datetime]
    answer_ended_at: Optional[datetime]
    content_score: Optional[float]
    delivery_score: Optional[float]
    relevance_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True

# 实时反馈响应模型
class RealTimeFeedbackResponse(BaseModel):
    id: int
    session_id: int
    question_id: Optional[int]
    timestamp: datetime
    session_time: int
    feedback_type: str
    feedback_category: Optional[str]
    message: str
    severity: str
    score: Optional[float]
    is_displayed: bool
    display_duration: int

    class Config:
        from_attributes = True

# 会话分析结果响应模型
class SessionAnalysisResponse(BaseModel):
    id: int
    session_id: int
    overall_score: float
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    
    # 核心能力指标
    professional_knowledge: Optional[float]
    skill_matching: Optional[float]
    communication_ability: Optional[float]
    logical_thinking: Optional[float]
    innovation_ability: Optional[float]
    stress_handling: Optional[float]
    
    # 语音分析
    speech_clarity: Optional[float]
    speech_pace: Optional[float]
    speech_emotion: Optional[str]
    speech_logic: Optional[float]
    
    # 视觉分析
    facial_expressions: Optional[Dict[str, Any]]
    eye_contact: Optional[float]
    body_language: Optional[Dict[str, Any]]
    confidence_level: Optional[float]
    
    # 内容分析
    content_relevance: Optional[float]
    content_structure: Optional[float]
    key_points: Optional[List[str]]
    
    # STAR结构评分
    situation_score: Optional[float]
    task_score: Optional[float]
    action_score: Optional[float]
    result_score: Optional[float]
    
    # 个性化学习路径推荐
    recommended_resources: Optional[List[Dict[str, Any]]]
    improvement_plan: Optional[Dict[str, Any]]
    
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# 问题回答提交模型
class QuestionAnswerSubmit(BaseModel):
    answer_text: str = Field(..., min_length=1, description="回答文本")
    answer_duration: int = Field(..., ge=0, description="回答时长(秒)")

# 实时数据提交模型
class RealTimeDataSubmit(BaseModel):
    type: str = Field(..., description="数据类型: audio, video, text")
    data: Dict[str, Any] = Field(..., description="实时数据内容")
    timestamp: Optional[datetime] = Field(None, description="数据时间戳")

# 面试会话统计模型
class InterviewSessionStats(BaseModel):
    total_sessions: int
    completed_sessions: int
    average_score: float
    average_duration: int
    completion_rate: float
    most_common_weaknesses: List[str]
    improvement_trends: Dict[str, float]

# 学习资源推荐模型
class LearningResource(BaseModel):
    type: str = Field(..., description="资源类型")
    title: str = Field(..., description="资源标题")
    description: str = Field(..., description="资源描述")
    url: Optional[str] = Field(None, description="资源链接")
    priority: str = Field(..., description="优先级: high, medium, low")
    estimated_time: Optional[int] = Field(None, description="预估学习时间(分钟)")

# 能力雷达图数据模型
class AbilityRadarData(BaseModel):
    professional_knowledge: float = Field(..., ge=0, le=10, description="专业知识")
    skill_matching: float = Field(..., ge=0, le=10, description="技能匹配度")
    communication_ability: float = Field(..., ge=0, le=10, description="沟通能力")
    logical_thinking: float = Field(..., ge=0, le=10, description="逻辑思维")
    innovation_ability: float = Field(..., ge=0, le=10, description="创新能力")
    stress_handling: float = Field(..., ge=0, le=10, description="抗压能力")

# 面试报告模型
class InterviewReport(BaseModel):
    session_info: InterviewSessionResponse
    analysis: SessionAnalysisResponse
    questions: List[InterviewQuestionResponse]
    radar_data: AbilityRadarData
    learning_recommendations: List[LearningResource]
    feedback_summary: Dict[str, Any]

# WebSocket消息模型
class WebSocketMessage(BaseModel):
    type: str = Field(..., description="消息类型")
    data: Dict[str, Any] = Field(..., description="消息数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")

# 实时反馈项模型
class FeedbackItem(BaseModel):
    type: str = Field(..., description="反馈类型")
    category: str = Field(..., description="反馈分类")
    message: str = Field(..., description="反馈消息")
    severity: str = Field(..., description="严重程度")
    score: Optional[float] = Field(None, description="评分")
    session_time: int = Field(..., description="会话时间")
    suggestions: Optional[List[str]] = Field(None, description="改进建议")

# 面试进度模型
class InterviewProgress(BaseModel):
    session_id: int
    current_question_index: int
    total_questions: int
    elapsed_time: int
    remaining_time: int
    completion_percentage: float
    current_scores: Dict[str, float]

# 面试设置模型
class InterviewSettings(BaseModel):
    enable_real_time_feedback: bool = True
    feedback_frequency: int = Field(5, ge=1, le=30, description="反馈频率(秒)")
    auto_next_question: bool = False
    max_answer_time: int = Field(300, ge=60, le=600, description="最大回答时间(秒)")
    enable_video_analysis: bool = True
    enable_audio_analysis: bool = True
    language: str = Field("zh-CN", description="语言设置")