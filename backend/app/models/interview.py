from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum

class FileType(str, enum.Enum):
    VIDEO = "video"
    AUDIO = "audio"

class Interview(Base):
    __tablename__ = "interviews"

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