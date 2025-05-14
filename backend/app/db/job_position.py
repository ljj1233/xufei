from sqlalchemy import Column, Integer, String, Text, DateTime, ARRAY, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional

from app.db.database import Base


class JobPosition(Base):
    """职位模型
    
    存储面试职位信息
    """
    __tablename__ = "job_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)  # 存储为JSON字符串
    company = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    interviews = relationship("Interview", back_populates="job_position")