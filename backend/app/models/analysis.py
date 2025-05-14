from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), unique=True, nullable=False)
    
    # 综合评分
    overall_score = Column(Float)
    strengths = Column(JSON)  # 优势列表
    weaknesses = Column(JSON)  # 需改进项列表
    suggestions = Column(JSON)  # 建议列表
    
    # 语音分析
    speech_clarity = Column(Float)  # 语音清晰度
    speech_pace = Column(Float)  # 语速
    speech_emotion = Column(String(50))  # 主要情感
    speech_logic = Column(Float)  # 语言逻辑性
    
    # 视觉分析
    facial_expressions = Column(JSON)  # 面部表情分布
    eye_contact = Column(Float)  # 眼神接触评分
    body_language = Column(JSON)  # 肢体语言评分
    
    # 内容分析
    content_relevance = Column(Float)  # 内容相关性
    content_structure = Column(Float)  # 结构清晰度
    key_points = Column(JSON)  # 关键点列表
    
    # 专业能力评估
    professional_knowledge = Column(Float)  # 专业知识水平
    skill_matching = Column(Float)  # 技能匹配度
    logical_thinking = Column(Float)  # 逻辑思维能力
    innovation_ability = Column(Float)  # 创新能力
    stress_handling = Column(Float)  # 应变抗压能力
    
    # STAR结构评分
    situation_score = Column(Float)  # 情境描述评分
    task_score = Column(Float)  # 任务目标评分
    action_score = Column(Float)  # 行动措施评分
    result_score = Column(Float)  # 结果成效评分
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    interview = relationship("Interview", back_populates="analysis")