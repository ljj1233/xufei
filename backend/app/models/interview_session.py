from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum

class SessionStatus(str, enum.Enum):
    """面试会话状态"""
    PREPARING = "preparing"      # 准备中
    IN_PROGRESS = "in_progress"  # 进行中
    PAUSED = "paused"           # 暂停
    COMPLETED = "completed"     # 已完成
    CANCELLED = "cancelled"     # 已取消

class QuestionType(str, enum.Enum):
    """问题类型"""
    SELF_INTRO = "self_introduction"     # 自我介绍
    TECHNICAL = "technical"              # 技术问题
    BEHAVIORAL = "behavioral"            # 行为问题
    SCENARIO = "scenario"                # 情景问题
    CASE_STUDY = "case_study"            # 案例分析
    CODING = "coding"                    # 编程题
    SYSTEM_DESIGN = "system_design"      # 系统设计

class InterviewSession(Base):
    """面试会话模型 - 支持模拟面试练习"""
    __tablename__ = "interview_sessions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_position_id = Column(Integer, ForeignKey("job_positions.id"), nullable=False)
    
    # 会话基本信息
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(Enum(SessionStatus), default=SessionStatus.PREPARING)
    
    # 时间信息
    planned_duration = Column(Integer, default=1800)  # 计划时长(秒)，默认30分钟
    actual_duration = Column(Integer)  # 实际时长(秒)
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    
    # 配置信息
    enable_real_time_feedback = Column(Boolean, default=True)  # 是否启用实时反馈
    question_count = Column(Integer, default=5)  # 问题数量
    difficulty_level = Column(String(20), default="medium")  # 难度等级: easy, medium, hard
    
    # 综合评分（会话结束后计算）
    overall_score = Column(Float)
    completion_rate = Column(Float)  # 完成度
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    user = relationship("User", back_populates="interview_sessions")
    job_position = relationship("JobPosition", back_populates="interview_sessions")
    questions = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan")
    real_time_feedback = relationship("RealTimeFeedback", back_populates="session", cascade="all, delete-orphan")
    final_analysis = relationship("SessionAnalysis", back_populates="session", uselist=False, cascade="all, delete-orphan")

class InterviewQuestion(Base):
    """面试问题模型"""
    __tablename__ = "interview_questions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    
    # 问题信息
    question_text = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    expected_duration = Column(Integer, default=180)  # 期望回答时长(秒)，默认3分钟
    difficulty = Column(String(20), default="medium")
    
    # 问题顺序和状态
    order_index = Column(Integer, nullable=False)
    is_answered = Column(Boolean, default=False)
    
    # 回答信息
    answer_text = Column(Text)  # 语音转文本的回答
    answer_duration = Column(Integer)  # 实际回答时长(秒)
    answer_started_at = Column(DateTime(timezone=True))
    answer_ended_at = Column(DateTime(timezone=True))
    
    # 评分
    content_score = Column(Float)  # 内容评分
    delivery_score = Column(Float)  # 表达评分
    relevance_score = Column(Float)  # 相关性评分
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    session = relationship("InterviewSession", back_populates="questions")
    feedback_items = relationship("RealTimeFeedback", back_populates="question", cascade="all, delete-orphan")

class RealTimeFeedback(Base):
    """实时反馈模型"""
    __tablename__ = "real_time_feedback"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("interview_questions.id"), nullable=True)
    
    # 反馈时间点
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    session_time = Column(Integer)  # 会话开始后的秒数
    
    # 反馈类型和内容
    feedback_type = Column(String(50), nullable=False)  # speech, visual, content, general
    feedback_category = Column(String(50))  # clarity, pace, eye_contact, posture, etc.
    
    # 反馈内容
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="info")  # info, warning, error
    score = Column(Float)  # 当前评分
    
    # 是否已显示给用户
    is_displayed = Column(Boolean, default=False)
    display_duration = Column(Integer, default=3)  # 显示时长(秒)
    
    # 关联关系
    session = relationship("InterviewSession", back_populates="real_time_feedback")
    question = relationship("InterviewQuestion", back_populates="feedback_items")

class SessionAnalysis(Base):
    """会话分析结果模型"""
    __tablename__ = "session_analyses"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), unique=True, nullable=False)
    
    # 综合评分
    overall_score = Column(Float, nullable=False)
    strengths = Column(JSON)  # 优势列表
    weaknesses = Column(JSON)  # 需改进项列表
    suggestions = Column(JSON)  # 改进建议列表
    
    # 核心能力指标（5项核心能力）
    professional_knowledge = Column(Float)  # 专业知识水平
    skill_matching = Column(Float)  # 技能匹配度
    communication_ability = Column(Float)  # 语言表达能力
    logical_thinking = Column(Float)  # 逻辑思维能力
    innovation_ability = Column(Float)  # 创新能力
    stress_handling = Column(Float)  # 应变抗压能力
    
    # 语音分析
    speech_clarity = Column(Float)  # 语音清晰度
    speech_pace = Column(Float)  # 语速
    speech_emotion = Column(String(50))  # 主要情感
    speech_logic = Column(Float)  # 语言逻辑性
    
    # 视觉分析（如果有视频）
    facial_expressions = Column(JSON)  # 面部表情分布
    eye_contact = Column(Float)  # 眼神接触评分
    body_language = Column(JSON)  # 肢体语言评分
    confidence_level = Column(Float)  # 自信度
    
    # 内容分析
    content_relevance = Column(Float)  # 内容相关性
    content_structure = Column(Float)  # 结构清晰度
    key_points = Column(JSON)  # 关键点列表
    
    # STAR结构评分
    situation_score = Column(Float)  # 情境描述评分
    task_score = Column(Float)  # 任务目标评分
    action_score = Column(Float)  # 行动措施评分
    result_score = Column(Float)  # 结果成效评分
    
    # 个性化学习路径推荐
    recommended_resources = Column(JSON)  # 推荐学习资源
    improvement_plan = Column(JSON)  # 改进计划
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    session = relationship("InterviewSession", back_populates="final_analysis")