from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

class AnalysisBase(BaseModel):
    """分析结果基础模型"""
    interview_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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

class AnalysisInDB(AnalysisBase):
    """数据库中的分析结果模型"""
    id: int
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
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

class Analysis(AnalysisInDB):
    """分析结果响应模型"""
    speech: Optional[SpeechAnalysis] = None
    visual: Optional[VisualAnalysis] = None
    content: Optional[ContentAnalysis] = None
    overall: Optional[OverallAnalysis] = None
    
    def __init__(self, **data):
        super().__init__(**data)
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
    
    def _parse_json(self, json_str):
        if not json_str:
            return None
        if isinstance(json_str, (dict, list)):
            return json_str
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return None