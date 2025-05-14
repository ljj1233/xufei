from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class TechField(str, Enum):
    AI = "artificial_intelligence"
    BIGDATA = "big_data"
    IOT = "internet_of_things"
    SYSTEM = "intelligent_system"

class PositionType(str, Enum):
    TECHNICAL = "technical"
    OPERATION = "operation"
    PRODUCT = "product"

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
        from_attributes = True
        arbitrary_types_allowed = True

class JobPosition(JobPositionInDB):
    """职位响应模型"""
    pass