from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

class AnalysisBase(BaseModel):
    """分析结果基础模型"""
    interview_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# 新增的快速练习PLUS评价体系模型
class ContentQualityAnalysis(BaseModel):
    """内容质量分析"""
    relevance: float = Field(..., description="回答相关性评分(0-10)")
    relevance_review: str = Field(default="", description="回答相关性评价")
    depth_and_detail: float = Field(..., description="细节与深度评分(0-10)")
    depth_review: str = Field(default="", description="细节与深度评价")
    professionalism: float = Field(..., description="专业性评分(0-10)")
    matched_keywords: List[str] = Field(default_factory=list, description="匹配的关键词")
    professional_style_review: str = Field(default="", description="专业风格评价")

class CognitiveSkillsAnalysis(BaseModel):
    """思维能力分析"""
    logical_structure: float = Field(..., description="逻辑结构评分(0-10)")
    structure_review: str = Field(default="", description="逻辑结构评价")
    clarity_of_thought: float = Field(..., description="思维清晰度评分(0-10)")
    clarity_review: str = Field(default="", description="思维清晰度评价")

class CommunicationSkillsAnalysis(BaseModel):
    """沟通技巧分析"""
    fluency: float = Field(..., description="语言流畅度评分(0-10)")
    fluency_details: Dict[str, Any] = Field(default_factory=dict, description="流畅度详情")
    speech_rate: float = Field(..., description="语速评分(0-10)")
    speech_rate_details: Dict[str, Any] = Field(default_factory=dict, description="语速详情")
    vocal_energy: float = Field(..., description="声音能量评分(0-10)")
    vocal_energy_details: Dict[str, Any] = Field(default_factory=dict, description="声音能量详情")
    conciseness: float = Field(..., description="语言简洁性评分(0-10)")
    conciseness_review: str = Field(default="", description="语言简洁性评价")

class QuickPracticeFeedback(BaseModel):
    """快速练习反馈"""
    strengths: List[Dict[str, Any]] = Field(..., description="亮点列表")
    growth_areas: List[Dict[str, Any]] = Field(..., description="成长区域列表")
    content_quality_score: float = Field(..., description="内容质量模块得分(0-100)")
    cognitive_skills_score: float = Field(..., description="思维能力模块得分(0-100)")
    communication_skills_score: float = Field(..., description="沟通技巧模块得分(0-100)")
    overall_score: float = Field(..., description="总体得分(0-100)")

class QuickPracticeAnalysis(BaseModel):
    """快速练习PLUS分析结果"""
    content_quality: ContentQualityAnalysis
    cognitive_skills: CognitiveSkillsAnalysis
    communication_skills: Optional[CommunicationSkillsAnalysis] = None
    feedback: QuickPracticeFeedback

# 原有的分析模型
class SpeechAnalysis(BaseModel):
    """语音分析结果"""
    clarity: float = Field(..., description="语音清晰度评分(0-10)")
    pace: float = Field(..., description="语速评分(0-10)")
    emotion: str = Field(..., description="主要情感类型")
    fluency: float = Field(..., description="流利度评分(0-10)")

class VisualAnalysis(BaseModel):
    """视觉分析结果"""
    facial_expressions: Dict[str, Any] = Field(..., description="面部表情分析")
    eye_contact: float = Field(..., description="眼神接触评分(0-10)")
    body_language: Dict[str, Any] = Field(..., description="肢体语言分析")

class ContentAnalysis(BaseModel):
    """内容分析结果"""
    relevance: float = Field(..., description="内容相关性评分(0-10)")
    structure: float = Field(..., description="内容结构评分(0-10)")
    key_points: List[str] = Field(..., description="关键点列表")

class OverallAnalysis(BaseModel):
    """综合分析结果"""
    score: float = Field(..., description="综合评分(0-10)")
    strengths: List[str] = Field(..., description="优势列表")
    weaknesses: List[str] = Field(..., description="劣势列表")
    suggestions: List[str] = Field(..., description="建议列表")

class AnalysisCreate(AnalysisBase):
    """分析结果创建模型"""
    speech: Optional[SpeechAnalysis] = None
    visual: Optional[VisualAnalysis] = None
    content: Optional[ContentAnalysis] = None
    overall: Optional[OverallAnalysis] = None
    quick_practice: Optional[QuickPracticeAnalysis] = None
    analysis_type: str = Field(default="standard", description="分析类型: standard/quick_practice")

class AnalysisInDB(AnalysisBase):
    """数据库中的分析结果模型"""
    id: int
    analysis_type: str = "standard"
    
    # 标准分析字段
    speech_clarity: Optional[float] = None
    speech_pace: Optional[float] = None
    speech_emotion: Optional[str] = None
    facial_expressions: Optional[Dict[str, Any]] = None
    eye_contact: Optional[float] = None
    body_language: Optional[Dict[str, Any]] = None
    content_relevance: Optional[float] = None
    content_structure: Optional[float] = None
    key_points: Optional[List[str]] = None
    overall_score: Optional[float] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None
    
    # 快速练习PLUS分析字段
    quick_practice_data: Optional[Dict[str, Any]] = None
    
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

class Analysis(AnalysisInDB):
    """分析结果响应模型"""
    speech: Optional[SpeechAnalysis] = None
    visual: Optional[VisualAnalysis] = None
    content: Optional[ContentAnalysis] = None
    overall: Optional[OverallAnalysis] = None
    quick_practice: Optional[QuickPracticeAnalysis] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # 处理标准分析结果
        if self.analysis_type == "standard":
            if any([self.speech_clarity, self.speech_pace, self.speech_emotion]):
                self.speech = SpeechAnalysis(
                    clarity=self.speech_clarity or 0.0,
                    pace=self.speech_pace or 0.0,
                    emotion=self.speech_emotion or "",
                    fluency=0.0  # Assuming fluency is not provided in the input
                )
            if any([self.facial_expressions, self.eye_contact, self.body_language]):
                self.visual = VisualAnalysis(
                    facial_expressions=self._parse_json(self.facial_expressions) or {},
                    eye_contact=self.eye_contact or 0.0,
                    body_language=self._parse_json(self.body_language) or {}
                )
            if any([self.content_relevance, self.content_structure, self.key_points]):
                self.content = ContentAnalysis(
                    relevance=self.content_relevance or 0.0,
                    structure=self.content_structure or 0.0,
                    key_points=self._parse_json(self.key_points) or []
                )
            if any([self.overall_score, self.strengths, self.weaknesses, self.suggestions]):
                self.overall = OverallAnalysis(
                    score=self.overall_score or 0.0,
                    strengths=self._parse_json(self.strengths) or [],
                    weaknesses=self._parse_json(self.weaknesses) or [],
                    suggestions=self._parse_json(self.suggestions) or []
                )
        # 处理快速练习PLUS分析结果
        elif self.analysis_type == "quick_practice" and self.quick_practice_data:
            qp_data = self._parse_json(self.quick_practice_data)
            if qp_data:
                self.quick_practice = QuickPracticeAnalysis(**qp_data)
    
    def _parse_json(self, json_str):
        if not json_str:
            return None
        if isinstance(json_str, (dict, list)):
            return json_str
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return None