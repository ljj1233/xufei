"""
学习推荐模块的数据模型

定义职位、技能、学习资源等相关的数据结构
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from enum import Enum


class ResourceType(str, Enum):
    """学习资源类型枚举"""
    ARTICLE = "article"
    VIDEO = "video"
    COURSE = "course"
    TUTORIAL = "tutorial"
    PROJECT = "project"
    BOOK = "book"
    COMMUNITY = "community"
    TOOL = "tool"
    OTHER = "other"


class DifficultyLevel(str, Enum):
    """难度级别枚举"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TimeCommitment(str, Enum):
    """时间投入枚举"""
    SHORT = "short"  # <1小时
    MEDIUM = "medium"  # 1-5小时
    LONG = "long"  # >5小时


class Skill(BaseModel):
    """技能模型"""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    parent_skill_id: Optional[str] = None
    related_skills: List[str] = Field(default_factory=list)


class JobPosition(BaseModel):
    """职位模型"""
    id: str
    title: str
    description: Optional[str] = None
    required_skills: Dict[str, float] = Field(default_factory=dict)  # 技能ID到权重的映射
    recommended_skills: Dict[str, float] = Field(default_factory=dict)  # 推荐技能的映射


class LearningResource(BaseModel):
    """学习资源模型"""
    id: str
    title: str
    description: str
    resource_type: ResourceType
    url: HttpUrl
    source: str
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    difficulty: DifficultyLevel
    time_commitment: TimeCommitment
    tags: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)  # 相关技能ID
    rating: Optional[float] = None  # 0-5分的评分
    review_count: int = 0
    job_relevance: List[str] = Field(default_factory=list)  # 相关职位ID


class UserPreferences(BaseModel):
    """用户学习偏好模型"""
    user_id: str
    preferred_resource_types: List[ResourceType] = Field(default_factory=list)
    preferred_difficulty: Optional[DifficultyLevel] = None
    time_availability: Optional[str] = None  # 'limited', 'moderate', 'abundant'
    learning_style: Optional[str] = None  # 'visual', 'auditory', 'reading', 'kinesthetic'
    known_skills: List[str] = Field(default_factory=list)  # 用户已掌握的技能ID


class LearningGoal(BaseModel):
    """学习目标模型"""
    skill: str  # 技能ID
    name: str  # 技能名称
    priority_score: float  # 优先级评分
    term_type: Optional[str] = None  # 'short', 'mid', 'long'
    resources: List[Dict[str, Any]] = Field(default_factory=list)  # 推荐的学习资源


class LearningPath(BaseModel):
    """学习路径模型"""
    id: str
    user_id: str
    job_position: Dict[str, Any]
    created_at: datetime
    goals: Dict[str, List[LearningGoal]]  # 按term_type分组的目标
    summary: str 