from typing import Dict, Any, Optional, List
import os
import json
from .xunfei_service import XunfeiService
from sqlalchemy.orm import Session
from app.models.interview import Interview
from app.models.analysis import Analysis
from app.models.job_position import JobPosition

class AnalysisService:
    """面试分析服务"""
    
    def __init__(self, db: Optional[Session] = None, xunfei_service: Optional[XunfeiService] = None):
        """初始化分析服务
        
        Args:
            db: 数据库会话
            xunfei_service: 讯飞服务实例，如果为None则创建新实例
        """
        from .xunfei_service import xunfei_service as default_service
        self.xunfei_service = xunfei_service or default_service
        self.db = db
    
    def analyze_interview(self, interview_id: int) -> Dict[str, Any]:
        """分析面试
        
        Args:
            interview_id: 面试ID
            
        Returns:
            分析结果字典
        """
        # 获取面试信息
        interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError(f"面试不存在: ID {interview_id}")
            
        # 获取职位信息
        job_position = self.db.query(JobPosition).filter(JobPosition.id == interview.job_position_id).first()
        if not job_position:
            raise ValueError(f"职位不存在: ID {interview.job_position_id}")
        
        # 读取音频/视频文件
        file_path = interview.file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"面试文件不存在: {file_path}")
        
        with open(file_path, "rb") as f:
            audio_data = f.read()
        
        # 语音识别
        speech_text = self.xunfei_service.speech_recognition(audio_data)
        
        # 情感分析
        emotion_analysis = self.xunfei_service.emotion_analysis(audio_data)
        
        # 分析语音
        speech_analysis = self._analyze_speech(speech_text, emotion_analysis)
        
        # 分析视觉表现（如果有视频）
        visual_analysis = self._analyze_visual(file_path)
        
        # 分析内容
        content_analysis = self._analyze_content(speech_text, job_position)
        
        # 生成综合分析
        overall_analysis = self._generate_overall_analysis(
            speech_analysis, visual_analysis, content_analysis
        )
        
        # 合并所有分析结果
        analysis_result = {
            "speech_text": speech_text,
            **speech_analysis,
            **visual_analysis,
            **content_analysis,
            **overall_analysis
        }
        
        # 保存分析结果到数据库
        db_analysis = Analysis(
            interview_id=interview_id,
            overall_score=overall_analysis["overall_score"],
            strengths=overall_analysis["strengths"],
            weaknesses=overall_analysis["weaknesses"],
            suggestions=overall_analysis["suggestions"],
            speech_clarity=speech_analysis["speech_clarity"],
            speech_pace=speech_analysis["speech_pace"],
            speech_emotion=speech_analysis["speech_emotion"],
            speech_logic=speech_analysis["speech_logic"],
            facial_expressions=visual_analysis["facial_expressions"],
            eye_contact=visual_analysis["eye_contact"],
            body_language=visual_analysis["body_language"],
            content_relevance=content_analysis["content_relevance"],
            content_structure=content_analysis["content_structure"],
            key_points=content_analysis["key_points"],
            professional_knowledge=content_analysis["professional_knowledge"],
            skill_matching=content_analysis["skill_matching"],
            logical_thinking=content_analysis["logical_thinking"],
            innovation_ability=content_analysis["innovation_ability"],
            stress_handling=content_analysis["stress_handling"],
            situation_score=content_analysis["situation_score"],
            task_score=content_analysis["task_score"],
            action_score=content_analysis["action_score"],
            result_score=content_analysis["result_score"]
        )
        
        self.db.add(db_analysis)
        self.db.commit()
        self.db.refresh(db_analysis)
        
        return analysis_result
    
    def get_analysis(self, interview_id: int) -> Analysis:
        """获取面试分析结果
        
        Args:
            interview_id: 面试ID
            
        Returns:
            分析结果对象
        """
        analysis = self.db.query(Analysis).filter(Analysis.interview_id == interview_id).first()
        if not analysis:
            raise ValueError(f"分析结果不存在: 面试ID {interview_id}")
        return analysis
    
    def _analyze_speech(self, transcript: str, emotion_result: Dict[str, Any]) -> Dict[str, Any]:
        """分析语音表现
        
        Args:
            transcript: 语音识别文本
            emotion_result: 情感分析结果
            
        Returns:
            语音分析结果
        """
        speech_clarity = self._calculate_speech_clarity(transcript)
        speech_pace = self._calculate_speech_pace(transcript)
        speech_logic = self._calculate_speech_logic(transcript)
        
        return {
            "speech_clarity": speech_clarity,
            "speech_pace": speech_pace,
            "speech_emotion": emotion_result.get("emotion", "中性"),
            "speech_logic": speech_logic
        }
    
    def _analyze_visual(self, file_path: str) -> Dict[str, Any]:
        """分析视觉表现
        
        Args:
            file_path: 视频文件路径
            
        Returns:
            视觉分析结果
        """
        # 简化实现，实际应用中可能需要视频分析API
        return {
            "facial_expressions": {"微笑": 60, "专注": 40},
            "eye_contact": 85.0,
            "body_language": {"自信": 80, "放松": 20}
        }
    
    def _analyze_content(self, transcript: str, job_position: JobPosition) -> Dict[str, Any]:
        """分析内容
        
        Args:
            transcript: 语音识别文本
            job_position: 职位信息
            
        Returns:
            内容分析结果
        """
        content_relevance = self._calculate_content_relevance(transcript, job_position)
        content_structure = self._calculate_content_structure(transcript)
        key_points = self._extract_key_points(transcript)
        
        professional_skills = self._evaluate_professional_skills(transcript, job_position)
        star_structure = self._evaluate_star_structure(transcript)
        
        return {
            "content_relevance": content_relevance,
            "content_structure": content_structure,
            "key_points": key_points,
            **professional_skills,
            **star_structure
        }
    
    def _calculate_speech_clarity(self, transcript: str) -> float:
        """计算语音清晰度
        
        Args:
            transcript: 语音识别文本
            
        Returns:
            清晰度得分
        """
        # 简化实现，实际应用中可能需要更复杂的算法
        return 90.0
    
    def _calculate_speech_pace(self, transcript: str) -> float:
        """计算语速
        
        Args:
            transcript: 语音识别文本
            
        Returns:
            语速得分
        """
        # 简化实现，实际应用中可能需要更复杂的算法
        return 75.0
    
    def _calculate_speech_logic(self, transcript: str) -> float:
        """计算语言逻辑性
        
        Args:
            transcript: 语音识别文本
            
        Returns:
            逻辑性得分
        """
        # 简化实现，实际应用中可能需要更复杂的算法
        return 85.0
    
    def _calculate_content_relevance(self, transcript: str, job_position: JobPosition) -> float:
        """计算内容相关性
        
        Args:
            transcript: 语音识别文本
            job_position: 职位信息
            
        Returns:
            相关性得分
        """
        # 简化实现，实际应用中可能需要更复杂的算法
        return 90.0
    
    def _calculate_content_structure(self, transcript: str) -> float:
        """计算内容结构性
        
        Args:
            transcript: 语音识别文本
            
        Returns:
            结构性得分
        """
        # 简化实现，实际应用中可能需要更复杂的算法
        return 85.0
    
    def _extract_key_points(self, transcript: str) -> List[str]:
        """提取关键点
        
        Args:
            transcript: 语音识别文本
            
        Returns:
            关键点列表
        """
        # 简化实现，实际应用中可能需要更复杂的算法
        return ["项目经验", "技术能力", "团队协作"]
    
    def _evaluate_professional_skills(self, transcript: str, job_position: JobPosition) -> Dict[str, float]:
        """评估专业能力
        
        Args:
            transcript: 语音识别文本
            job_position: 职位信息
            
        Returns:
            专业能力评估结果
        """
        # 简化实现，实际应用中可能需要更复杂的算法
        return {
            "professional_knowledge": 88.0,
            "skill_matching": 85.0,
            "logical_thinking": 87.0,
            "innovation_ability": 80.0,
            "stress_handling": 82.0
        }
    
    def _evaluate_star_structure(self, transcript: str) -> Dict[str, float]:
        """评估STAR结构
        
        Args:
            transcript: 语音识别文本
            
        Returns:
            STAR结构评估结果
        """
        # 简化实现，实际应用中可能需要更复杂的算法
        return {
            "situation_score": 85.0,
            "task_score": 88.0,
            "action_score": 90.0,
            "result_score": 85.0
        }
    
    def _generate_overall_analysis(self, speech_analysis: Dict[str, Any], 
                                  visual_analysis: Dict[str, Any], 
                                  content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成综合分析
        
        Args:
            speech_analysis: 语音分析结果
            visual_analysis: 视觉分析结果
            content_analysis: 内容分析结果
            
        Returns:
            综合分析结果
        """
        # 计算综合得分
        overall_score = self._calculate_overall_score(speech_analysis, visual_analysis, content_analysis)
        
        # 识别优势
        strengths = self._identify_strengths(speech_analysis, visual_analysis, content_analysis)
        
        # 识别弱点
        weaknesses = self._identify_weaknesses(speech_analysis, visual_analysis, content_analysis)
        
        # 生成建议
        suggestions = self._generate_suggestions(speech_analysis, visual_analysis, content_analysis, overall_score)
        
        return {
            "overall_score": overall_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "suggestions": suggestions
        }
    
    def _calculate_overall_score(self, speech_analysis: Dict[str, Any], 
                               visual_analysis: Dict[str, Any], 
                               content_analysis: Dict[str, Any]) -> float:
        """计算综合得分
        
        Args:
            speech_analysis: 语音分析结果
            visual_analysis: 视觉分析结果
            content_analysis: 内容分析结果
            
        Returns:
            综合得分
        """
        # 加权平均计算综合得分
        weights = {
            "speech": 0.3,
            "visual": 0.2,
            "content": 0.5
        }
        
        speech_score = (speech_analysis["speech_clarity"] + speech_analysis["speech_pace"] + 
                       speech_analysis["speech_logic"]) / 3
        
        visual_score = visual_analysis["eye_contact"]
        
        content_score = (content_analysis["professional_knowledge"] + content_analysis["skill_matching"] + 
                        content_analysis["logical_thinking"] + content_analysis["innovation_ability"] + 
                        content_analysis["stress_handling"]) / 5
        
        overall = (
            speech_score * weights["speech"] +
            visual_score * weights["visual"] +
            content_score * weights["content"]
        )
        
        return round(overall, 1)
    
    def _identify_strengths(self, speech_analysis: Dict[str, Any], 
                          visual_analysis: Dict[str, Any], 
                          content_analysis: Dict[str, Any]) -> List[str]:
        """识别优势
        
        Args:
            speech_analysis: 语音分析结果
            visual_analysis: 视觉分析结果
            content_analysis: 内容分析结果
            
        Returns:
            优势列表
        """
        strengths = []
        
        # 识别语音优势
        if speech_analysis["speech_clarity"] >= 85:
            strengths.append("表达清晰")
        
        # 识别视觉优势
        if visual_analysis["eye_contact"] >= 85:
            strengths.append("眼神交流良好")
        
        # 识别内容优势
        if content_analysis["professional_knowledge"] >= 85:
            strengths.append("专业知识扎实")
        
        if content_analysis["logical_thinking"] >= 85:
            strengths.append("逻辑思维能力强")
        
        return strengths
    
    def _identify_weaknesses(self, speech_analysis: Dict[str, Any], 
                           visual_analysis: Dict[str, Any], 
                           content_analysis: Dict[str, Any]) -> List[str]:
        """识别弱点
        
        Args:
            speech_analysis: 语音分析结果
            visual_analysis: 视觉分析结果
            content_analysis: 内容分析结果
            
        Returns:
            弱点列表
        """
        weaknesses = []
        
        # 识别语音弱点
        if speech_analysis["speech_clarity"] < 70:
            weaknesses.append("表达不够清晰")
        
        # 识别视觉弱点
        if visual_analysis["eye_contact"] < 70:
            weaknesses.append("眼神接触不足")
        
        # 识别内容弱点
        if content_analysis["innovation_ability"] < 75:
            weaknesses.append("创新性表现一般")
        
        # 确保至少有一个弱点
        if not weaknesses:
            weaknesses.append("技术细节不够深入")
        
        return weaknesses
    
    def _generate_suggestions(self, speech_analysis: Dict[str, Any], 
                            visual_analysis: Dict[str, Any], 
                            content_analysis: Dict[str, Any],
                            overall_score: float) -> List[str]:
        """生成建议
        
        Args:
            speech_analysis: 语音分析结果
            visual_analysis: 视觉分析结果
            content_analysis: 内容分析结果
            overall_score: 综合得分
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # 基于语音分析生成建议
        if speech_analysis["speech_clarity"] < 70:
            suggestions.append("提高语言表达的清晰度，注意发音和语速")
        
        # 基于视觉分析生成建议
        if visual_analysis["eye_contact"] < 70:
            suggestions.append("增加眼神接触，展示自信")
        
        # 基于内容分析生成建议
        if content_analysis["innovation_ability"] < 75:
            suggestions.append("准备更多创新性案例，展示解决问题的创新思维")
        
        # 基于综合得分生成建议
        if overall_score < 70:
            suggestions.append("建议系统性提升专业能力和面试技巧")
        elif overall_score < 80:
            suggestions.append("整体表现良好，可以在细节方面进一步提升")
        
        # 确保至少有一个建议
        if not suggestions:
            suggestions.append("可以准备更多技术案例，展示实际解决问题的能力")
        
        return suggestions
    
    def _calculate_professional_score(self, speech_text: str, interview_data: Dict[str, Any]) -> float:
        """计算专业能力得分"""
        # 简化实现，实际中可能需要NLP模型分析专业术语使用情况等
        return 80.0  # 示例得分
    
    def _calculate_skill_match_score(self, speech_text: str, interview_data: Dict[str, Any]) -> float:
        """计算技能匹配度得分"""
        # 简化实现，实际中可能需要比对职位要求和回答内容
        return 75.0  # 示例得分
    
    def _calculate_expression_score(self, speech_assessment: Dict, emotion_analysis: Dict) -> float:
        """计算表达能力得分"""
        # 基于语音评测和情感分析计算表达能力得分
        fluency = speech_assessment.get("fluency", 0)
        clarity = speech_assessment.get("clarity", 0)
        return (fluency + clarity) / 2  # 简化计算
    
    def _calculate_logical_score(self, speech_text: str) -> float:
        """计算逻辑思维得分"""
        # 简化实现，实际中可能需要分析语言结构和逻辑关系
        return 85.0  # 示例得分
    
    def _calculate_innovation_score(self, speech_text: str) -> float:
        """计算创新能力得分"""
        # 简化实现，实际中可能需要分析回答的独特性和创新性
        return 70.0  # 示例得分
    
    def _calculate_pressure_score(self, emotion_analysis: Dict) -> float:
        """计算抗压能力得分"""
        # 基于情感分析计算抗压能力得分
        # 简化实现，实际中可能需要分析情绪波动和稳定性
        return 80.0  # 示例得分
    
    def _generate_improvement_suggestions(self, speech_text: str, speech_assessment: Dict,
                                        emotion_analysis: Dict, overall_score: float) -> list:
        """生成改进建议"""
        suggestions = []
        
        # 基于语音评测生成建议
        if speech_assessment.get("fluency", 100) < 70:
            suggestions.append("提高语言流畅度，减少停顿和重复")
        
        if speech_assessment.get("clarity", 100) < 70:
            suggestions.append("提高发音清晰度，注意语速控制")
        
        # 基于情感分析生成建议
        if emotion_analysis.get("confidence", 100) < 60:
            suggestions.append("增强自信心，保持积极的情绪状态")
        
        # 基于综合得分生成建议
        if overall_score < 60:
            suggestions.append("建议系统性提升专业能力和面试技巧")
        elif overall_score < 80:
            suggestions.append("整体表现良好，可以在细节方面进一步提升")
        
        return suggestions

# 创建服务实例
analysis_service = AnalysisService() 