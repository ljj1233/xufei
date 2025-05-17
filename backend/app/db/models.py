from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class User(Base):
    """用户模型
    
    存储系统用户信息
    """
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    interviews = relationship("Interview", back_populates="user")
    

class Interview(Base):
    """面试记录模型
    
    存储面试视频/音频记录及其基本信息
    """
    __tablename__ = "interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    file_path = Column(String)  # 视频/音频文件路径
    file_type = Column(String)  # 文件类型：video或audio
    duration = Column(Float, nullable=True)  # 时长（秒）
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_position_id = Column(Integer, ForeignKey("job_positions.id"), nullable=True)
    
    # 关系
    user = relationship("User", back_populates="interviews")
    analysis = relationship("InterviewAnalysis", back_populates="interview", uselist=False)
    job_position = relationship("JobPosition", back_populates="interviews")
    

class InterviewAnalysis(Base):
    """面试分析结果模型
    
    存储面试的多模态分析结果
    """
    __tablename__ = "interview_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), unique=True)
    
    # 语音分析
    speech_clarity = Column(Float, nullable=True)  # 语音清晰度评分
    speech_pace = Column(Float, nullable=True)  # 语速评分
    speech_emotion = Column(String, nullable=True)  # 语音情感
    
    # 视觉分析（如果是视频）
    facial_expressions = Column(Text, nullable=True)  # 面部表情分析JSON
    eye_contact = Column(Float, nullable=True)  # 眼神接触评分
    body_language = Column(Text, nullable=True)  # 肢体语言分析JSON
    
    # 内容分析
    content_relevance = Column(Float, nullable=True)  # 内容相关性评分
    content_structure = Column(Float, nullable=True)  # 内容结构评分
    key_points = Column(Text, nullable=True)  # 关键点JSON
    
    # 综合评分
    overall_score = Column(Float, nullable=True)  # 综合评分
    strengths = Column(Text, nullable=True)  # 优势JSON
    weaknesses = Column(Text, nullable=True)  # 劣势JSON
    suggestions = Column(Text, nullable=True)  # 建议JSON
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    interview = relationship("Interview", back_populates="analysis")