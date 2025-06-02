from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 使用字符串引用模型名称，避免循环导入问题
    interviews = relationship("Interview", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    interview_sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
