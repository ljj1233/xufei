from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum

class TechField(str, enum.Enum):
    AI = "artificial_intelligence"
    BIGDATA = "big_data"
    IOT = "internet_of_things"
    SYSTEM = "intelligent_system"

class PositionType(str, enum.Enum):
    TECHNICAL = "technical"  # 技术岗
    OPERATION = "operation"  # 运维测试岗
    PRODUCT = "product"      # 产品岗

class JobPosition(Base):
    __tablename__ = "job_positions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)  # 职位名称
    tech_field = Column(Enum(TechField), nullable=False)  # 技术领域
    position_type = Column(Enum(PositionType), nullable=False)  # 岗位类型
    required_skills = Column(String(500), nullable=False)  # 所需技能
    job_description = Column(String(1000), nullable=False)  # 岗位描述
    evaluation_criteria = Column(String(500), nullable=False)  # 评估标准
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    interviews = relationship("Interview", back_populates="job_position")