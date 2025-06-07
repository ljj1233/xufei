from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum

class FileType(str, enum.Enum):
    VIDEO = "video"
    AUDIO = "audio"

class Interview(Base):
    __tablename__ = "interviews"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_position_id = Column(Integer, ForeignKey("job_positions.id"), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(String(500))
    file_path = Column(String(255), nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    duration = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    user = relationship("User", back_populates="interviews")
    job_position = relationship("JobPosition", back_populates="interviews")
    analysis = relationship("Analysis", back_populates="interview", uselist=False)

class InterviewQuestion(Base):
    """面试问题模型，用于存储生成的面试问题及其相关信息"""
    __tablename__ = "interview_questions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("job_positions.id"), nullable=False)
    content = Column(Text, nullable=False, comment="问题内容")
    skill_tags = Column(String(255), comment="考察的技能点，逗号分隔")
    suggested_duration_seconds = Column(Integer, default=120, comment="建议回答时长(秒)")
    reference_answer = Column(Text, comment="参考答案")
    difficulty = Column(Integer, default=3, comment="难度等级，1-5")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    job_position = relationship("JobPosition", back_populates="questions")