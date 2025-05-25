from typing import Dict, Any, List, Optional
import asyncio
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.interview_session import (
    InterviewSession, InterviewQuestion, RealTimeFeedback, 
    SessionAnalysis, SessionStatus, QuestionType
)
from app.models.job_position import JobPosition, TechField, PositionType
from app.services.xunfei_service import xunfei_service
from ai_agent.core.agent import InterviewAgent

class InterviewSessionService:
    """模拟面试会话服务"""
    
    def __init__(self):
        self.agent = InterviewAgent()
        self.active_sessions = {}  # 存储活跃会话的实时分析状态
    
    def create_session(self, db: Session, user_id: int, job_position_id: int, 
                      title: str, description: str = None, 
                      planned_duration: int = 1800, question_count: int = 5,
                      difficulty_level: str = "medium") -> InterviewSession:
        """创建新的面试会话"""
        
        # 创建会话
        session = InterviewSession(
            user_id=user_id,
            job_position_id=job_position_id,
            title=title,
            description=description,
            planned_duration=planned_duration,
            question_count=question_count,
            difficulty_level=difficulty_level,
            status=SessionStatus.PREPARING
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # 生成面试问题
        self._generate_questions(db, session)
        
        return session
    
    def _generate_questions(self, db: Session, session: InterviewSession):
        """根据职位和难度生成面试问题"""
        job_position = db.query(JobPosition).filter(JobPosition.id == session.job_position_id).first()
        
        # 根据技术领域和岗位类型生成问题
        questions_data = self._get_questions_by_position(job_position, session.question_count, session.difficulty_level)
        
        for i, question_data in enumerate(questions_data):
            question = InterviewQuestion(
                session_id=session.id,
                question_text=question_data["text"],
                question_type=question_data["type"],
                expected_duration=question_data["duration"],
                difficulty=question_data["difficulty"],
                order_index=i + 1
            )
            db.add(question)
        
        db.commit()
    
    def _get_questions_by_position(self, job_position: JobPosition, count: int, difficulty: str) -> List[Dict]:
        """根据职位生成问题列表"""
        questions = []
        
        # 自我介绍（必有）
        questions.append({
            "text": "请先做一个简单的自我介绍，包括您的教育背景、技能特长和职业目标。",
            "type": QuestionType.SELF_INTRO,
            "duration": 120,
            "difficulty": "easy"
        })
        
        # 根据技术领域生成专业问题
        if job_position.tech_field == TechField.AI:
            questions.extend(self._get_ai_questions(job_position.position_type, difficulty, count - 1))
        elif job_position.tech_field == TechField.BIGDATA:
            questions.extend(self._get_bigdata_questions(job_position.position_type, difficulty, count - 1))
        elif job_position.tech_field == TechField.IOT:
            questions.extend(self._get_iot_questions(job_position.position_type, difficulty, count - 1))
        elif job_position.tech_field == TechField.SYSTEM:
            questions.extend(self._get_system_questions(job_position.position_type, difficulty, count - 1))
        
        return questions[:count]
    
    def _get_ai_questions(self, position_type: PositionType, difficulty: str, count: int) -> List[Dict]:
        """获取AI领域问题"""
        questions = []
        
        if position_type == PositionType.TECHNICAL:
            questions.extend([
                {
                    "text": "请解释深度学习中的反向传播算法原理，并说明梯度消失问题及其解决方案。",
                    "type": QuestionType.TECHNICAL,
                    "duration": 300,
                    "difficulty": difficulty
                },
                {
                    "text": "假设你需要设计一个图像识别系统，请描述你的技术选型和架构设计思路。",
                    "type": QuestionType.SYSTEM_DESIGN,
                    "duration": 400,
                    "difficulty": difficulty
                },
                {
                    "text": "请用Python实现一个简单的线性回归模型，并解释关键代码。",
                    "type": QuestionType.CODING,
                    "duration": 600,
                    "difficulty": difficulty
                }
            ])
        elif position_type == PositionType.PRODUCT:
            questions.extend([
                {
                    "text": "如何评估一个AI产品的用户体验？请提出具体的评估指标和方法。",
                    "type": QuestionType.BEHAVIORAL,
                    "duration": 240,
                    "difficulty": difficulty
                },
                {
                    "text": "描述一个你认为成功的AI产品案例，分析其成功因素。",
                    "type": QuestionType.CASE_STUDY,
                    "duration": 300,
                    "difficulty": difficulty
                }
            ])
        
        return questions[:count]
    
    def _get_bigdata_questions(self, position_type: PositionType, difficulty: str, count: int) -> List[Dict]:
        """获取大数据领域问题"""
        questions = [
            {
                "text": "请解释Hadoop生态系统的核心组件及其作用。",
                "type": QuestionType.TECHNICAL,
                "duration": 300,
                "difficulty": difficulty
            },
            {
                "text": "如何设计一个处理TB级数据的实时分析系统？",
                "type": QuestionType.SYSTEM_DESIGN,
                "duration": 400,
                "difficulty": difficulty
            }
        ]
        return questions[:count]
    
    def _get_iot_questions(self, position_type: PositionType, difficulty: str, count: int) -> List[Dict]:
        """获取物联网领域问题"""
        questions = [
            {
                "text": "请描述物联网系统的典型架构层次，并解释各层的功能。",
                "type": QuestionType.TECHNICAL,
                "duration": 300,
                "difficulty": difficulty
            },
            {
                "text": "如何保证物联网设备的数据安全和隐私保护？",
                "type": QuestionType.SCENARIO,
                "duration": 240,
                "difficulty": difficulty
            }
        ]
        return questions[:count]
    
    def _get_system_questions(self, position_type: PositionType, difficulty: str, count: int) -> List[Dict]:
        """获取智能系统领域问题"""
        questions = [
            {
                "text": "请设计一个智能推荐系统的架构，包括数据流和算法选择。",
                "type": QuestionType.SYSTEM_DESIGN,
                "duration": 400,
                "difficulty": difficulty
            },
            {
                "text": "如何评估和优化智能系统的性能？",
                "type": QuestionType.TECHNICAL,
                "duration": 300,
                "difficulty": difficulty
            }
        ]
        return questions[:count]
    
    def start_session(self, db: Session, session_id: int) -> Dict[str, Any]:
        """开始面试会话"""
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            raise ValueError("会话不存在")
        
        if session.status != SessionStatus.PREPARING:
            raise ValueError("会话状态不正确")
        
        # 更新会话状态
        session.status = SessionStatus.IN_PROGRESS
        session.started_at = datetime.utcnow()
        db.commit()
        
        # 初始化实时分析状态
        self.active_sessions[session_id] = {
            "start_time": datetime.utcnow(),
            "current_question_index": 0,
            "real_time_scores": {
                "speech_clarity": 0.0,
                "eye_contact": 0.0,
                "confidence": 0.0
            }
        }
        
        # 获取第一个问题
        first_question = db.query(InterviewQuestion).filter(
            and_(InterviewQuestion.session_id == session_id, InterviewQuestion.order_index == 1)
        ).first()
        
        return {
            "session_id": session_id,
            "status": session.status,
            "current_question": {
                "id": first_question.id,
                "text": first_question.question_text,
                "type": first_question.question_type,
                "expected_duration": first_question.expected_duration
            } if first_question else None
        }
    
    async def process_real_time_data(self, session_id: int, data_type: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理实时数据并生成反馈"""
        if session_id not in self.active_sessions:
            return []
        
        feedback_items = []
        current_time = datetime.utcnow()
        session_start = self.active_sessions[session_id]["start_time"]
        session_time = int((current_time - session_start).total_seconds())
        
        if data_type == "audio":
            feedback_items.extend(await self._process_audio_data(session_id, data, session_time))
        elif data_type == "video":
            feedback_items.extend(await self._process_video_data(session_id, data, session_time))
        elif data_type == "text":
            feedback_items.extend(await self._process_text_data(session_id, data, session_time))
        
        return feedback_items
    
    async def _process_audio_data(self, session_id: int, audio_data: Dict, session_time: int) -> List[Dict[str, Any]]:
        """处理音频数据"""
        feedback_items = []
        
        # 语音清晰度检测
        if "clarity_score" in audio_data:
            clarity = audio_data["clarity_score"]
            if clarity < 0.6:
                feedback_items.append({
                    "type": "speech",
                    "category": "clarity",
                    "message": "建议说话更清晰一些，注意发音准确性",
                    "severity": "warning",
                    "score": clarity,
                    "session_time": session_time
                })
        
        # 语速检测
        if "pace_score" in audio_data:
            pace = audio_data["pace_score"]
            if pace < 0.4:
                feedback_items.append({
                    "type": "speech",
                    "category": "pace",
                    "message": "语速偏慢，可以适当加快语速",
                    "severity": "info",
                    "score": pace,
                    "session_time": session_time
                })
            elif pace > 0.8:
                feedback_items.append({
                    "type": "speech",
                    "category": "pace",
                    "message": "语速偏快，建议放慢语速以便面试官理解",
                    "severity": "warning",
                    "score": pace,
                    "session_time": session_time
                })
        
        return feedback_items
    
    async def _process_video_data(self, session_id: int, video_data: Dict, session_time: int) -> List[Dict[str, Any]]:
        """处理视频数据"""
        feedback_items = []
        
        # 眼神接触检测
        if "eye_contact_score" in video_data:
            eye_contact = video_data["eye_contact_score"]
            if eye_contact < 0.5:
                feedback_items.append({
                    "type": "visual",
                    "category": "eye_contact",
                    "message": "建议多与摄像头保持眼神接触，展现自信",
                    "severity": "info",
                    "score": eye_contact,
                    "session_time": session_time
                })
        
        # 姿态检测
        if "posture_score" in video_data:
            posture = video_data["posture_score"]
            if posture < 0.6:
                feedback_items.append({
                    "type": "visual",
                    "category": "posture",
                    "message": "注意保持良好的坐姿，身体略向前倾显示专注",
                    "severity": "info",
                    "score": posture,
                    "session_time": session_time
                })
        
        return feedback_items
    
    async def _process_text_data(self, session_id: int, text_data: Dict, session_time: int) -> List[Dict[str, Any]]:
        """处理文本数据（语音转文本结果）"""
        feedback_items = []
        
        text_content = text_data.get("text", "")
        
        # 检测STAR结构
        if len(text_content) > 50:  # 只对较长回答进行结构分析
            star_analysis = self._analyze_star_structure(text_content)
            if star_analysis["missing_elements"]:
                missing = ", ".join(star_analysis["missing_elements"])
                feedback_items.append({
                    "type": "content",
                    "category": "structure",
                    "message": f"建议补充STAR结构中的{missing}部分",
                    "severity": "info",
                    "score": star_analysis["completeness"],
                    "session_time": session_time
                })
        
        # 检测专业术语使用
        if "keywords" in text_data:
            keyword_density = len(text_data["keywords"]) / max(len(text_content.split()), 1)
            if keyword_density < 0.05:
                feedback_items.append({
                    "type": "content",
                    "category": "technical_terms",
                    "message": "可以适当使用更多专业术语来展示技术深度",
                    "severity": "info",
                    "score": keyword_density,
                    "session_time": session_time
                })
        
        return feedback_items
    
    def _analyze_star_structure(self, text: str) -> Dict[str, Any]:
        """分析文本的STAR结构完整性"""
        text_lower = text.lower()
        
        # STAR关键词检测
        situation_keywords = ["情况", "背景", "当时", "项目中", "在...时候"]
        task_keywords = ["任务", "目标", "需要", "要求", "负责"]
        action_keywords = ["行动", "做了", "采用", "实施", "解决", "使用"]
        result_keywords = ["结果", "效果", "成功", "完成", "提升", "改善"]
        
        elements = {
            "situation": any(keyword in text_lower for keyword in situation_keywords),
            "task": any(keyword in text_lower for keyword in task_keywords),
            "action": any(keyword in text_lower for keyword in action_keywords),
            "result": any(keyword in text_lower for keyword in result_keywords)
        }
        
        missing_elements = [k for k, v in elements.items() if not v]
        completeness = sum(elements.values()) / 4.0
        
        return {
            "elements": elements,
            "missing_elements": missing_elements,
            "completeness": completeness
        }
    
    def answer_question(self, db: Session, question_id: int, answer_text: str, 
                       answer_duration: int) -> Dict[str, Any]:
        """提交问题回答"""
        question = db.query(InterviewQuestion).filter(InterviewQuestion.id == question_id).first()
        if not question:
            raise ValueError("问题不存在")
        
        # 更新问题回答
        question.answer_text = answer_text
        question.answer_duration = answer_duration
        question.is_answered = True
        question.answer_ended_at = datetime.utcnow()
        
        # 使用AI智能体分析回答
        analysis_result = self.agent.analyze_text_response(
            question=question.question_text,
            answer=answer_text,
            question_type=question.question_type.value
        )
        
        # 更新评分
        question.content_score = analysis_result.get("content_score", 0.0)
        question.delivery_score = analysis_result.get("delivery_score", 0.0)
        question.relevance_score = analysis_result.get("relevance_score", 0.0)
        
        db.commit()
        
        # 检查是否还有下一个问题
        next_question = db.query(InterviewQuestion).filter(
            and_(
                InterviewQuestion.session_id == question.session_id,
                InterviewQuestion.order_index == question.order_index + 1
            )
        ).first()
        
        return {
            "question_completed": True,
            "scores": {
                "content": question.content_score,
                "delivery": question.delivery_score,
                "relevance": question.relevance_score
            },
            "next_question": {
                "id": next_question.id,
                "text": next_question.question_text,
                "type": next_question.question_type,
                "expected_duration": next_question.expected_duration
            } if next_question else None
        }
    
    def complete_session(self, db: Session, session_id: int) -> Dict[str, Any]:
        """完成面试会话并生成最终分析"""
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            raise ValueError("会话不存在")
        
        # 更新会话状态
        session.status = SessionStatus.COMPLETED
        session.ended_at = datetime.utcnow()
        if session.started_at:
            session.actual_duration = int((session.ended_at - session.started_at).total_seconds())
        
        # 计算完成度
        questions = db.query(InterviewQuestion).filter(InterviewQuestion.session_id == session_id).all()
        answered_count = sum(1 for q in questions if q.is_answered)
        session.completion_rate = answered_count / len(questions) if questions else 0.0
        
        # 生成最终分析
        final_analysis = self._generate_final_analysis(db, session, questions)
        
        # 保存分析结果
        session_analysis = SessionAnalysis(
            session_id=session_id,
            **final_analysis
        )
        
        db.add(session_analysis)
        db.commit()
        
        # 清理活跃会话状态
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        return final_analysis
    
    def _generate_final_analysis(self, db: Session, session: InterviewSession, 
                               questions: List[InterviewQuestion]) -> Dict[str, Any]:
        """生成最终分析结果"""
        
        # 计算各项评分
        answered_questions = [q for q in questions if q.is_answered]
        
        if not answered_questions:
            return self._get_default_analysis()
        
        # 计算平均分
        avg_content = sum(q.content_score or 0 for q in answered_questions) / len(answered_questions)
        avg_delivery = sum(q.delivery_score or 0 for q in answered_questions) / len(answered_questions)
        avg_relevance = sum(q.relevance_score or 0 for q in answered_questions) / len(answered_questions)
        
        # 核心能力评分
        professional_knowledge = avg_content * 0.8 + avg_relevance * 0.2
        communication_ability = avg_delivery * 0.7 + avg_content * 0.3
        logical_thinking = avg_content * 0.6 + avg_relevance * 0.4
        
        # 综合评分
        overall_score = (professional_knowledge + communication_ability + logical_thinking) / 3.0
        
        # 生成优势和建议
        strengths, weaknesses, suggestions = self._generate_feedback(
            overall_score, avg_content, avg_delivery, avg_relevance, session.completion_rate
        )
        
        # 个性化学习路径推荐
        recommended_resources = self._generate_learning_recommendations(
            session, avg_content, avg_delivery, avg_relevance
        )
        
        return {
            "overall_score": round(overall_score * 10, 1),  # 转换为10分制
            "professional_knowledge": round(professional_knowledge * 10, 1),
            "communication_ability": round(communication_ability * 10, 1),
            "logical_thinking": round(logical_thinking * 10, 1),
            "skill_matching": round(avg_relevance * 10, 1),
            "innovation_ability": round(avg_content * 0.8 * 10, 1),
            "stress_handling": round(session.completion_rate * 10, 1),
            "content_relevance": round(avg_relevance * 10, 1),
            "content_structure": round(avg_content * 10, 1),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "suggestions": suggestions,
            "recommended_resources": recommended_resources,
            "key_points": [q.question_text[:50] + "..." for q in answered_questions[:3]]
        }
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """获取默认分析结果（当没有回答任何问题时）"""
        return {
            "overall_score": 0.0,
            "professional_knowledge": 0.0,
            "communication_ability": 0.0,
            "logical_thinking": 0.0,
            "skill_matching": 0.0,
            "innovation_ability": 0.0,
            "stress_handling": 0.0,
            "content_relevance": 0.0,
            "content_structure": 0.0,
            "strengths": [],
            "weaknesses": ["未完成面试问题", "需要提高参与度"],
            "suggestions": ["建议完整参与模拟面试", "多练习回答常见面试问题"],
            "recommended_resources": [],
            "key_points": []
        }
    
    def _generate_feedback(self, overall_score: float, content: float, delivery: float, 
                          relevance: float, completion_rate: float) -> tuple:
        """生成反馈建议"""
        strengths = []
        weaknesses = []
        suggestions = []
        
        # 根据评分生成反馈
        if content >= 0.8:
            strengths.append("回答内容丰富，专业知识扎实")
        elif content < 0.6:
            weaknesses.append("回答内容需要更加充实")
            suggestions.append("建议多准备相关专业知识和案例")
        
        if delivery >= 0.8:
            strengths.append("表达清晰流畅，逻辑性强")
        elif delivery < 0.6:
            weaknesses.append("表达能力有待提升")
            suggestions.append("建议多练习口语表达和逻辑组织")
        
        if relevance >= 0.8:
            strengths.append("回答切题，针对性强")
        elif relevance < 0.6:
            weaknesses.append("回答与问题相关性不够")
            suggestions.append("建议仔细理解问题后再回答")
        
        if completion_rate < 0.8:
            weaknesses.append("面试完成度不高")
            suggestions.append("建议合理安排时间，完整回答所有问题")
        
        # 确保至少有一些反馈
        if not strengths:
            strengths.append("积极参与面试练习")
        
        if not suggestions:
            suggestions.append("继续保持，多加练习")
        
        return strengths, weaknesses, suggestions
    
    def _generate_learning_recommendations(self, session: InterviewSession, 
                                         content: float, delivery: float, 
                                         relevance: float) -> List[Dict[str, Any]]:
        """生成个性化学习路径推荐"""
        recommendations = []
        
        # 根据薄弱环节推荐学习资源
        if content < 0.7:
            recommendations.append({
                "type": "knowledge",
                "title": "专业知识提升课程",
                "description": "针对您的技术领域，推荐相关的在线课程和学习资料",
                "priority": "high"
            })
        
        if delivery < 0.7:
            recommendations.append({
                "type": "communication",
                "title": "表达能力训练",
                "description": "口语表达和逻辑思维训练课程",
                "priority": "medium"
            })
        
        if relevance < 0.7:
            recommendations.append({
                "type": "interview_skills",
                "title": "面试技巧专项训练",
                "description": "如何准确理解和回答面试问题",
                "priority": "high"
            })
        
        # 通用推荐
        recommendations.append({
            "type": "practice",
            "title": "模拟面试练习",
            "description": "定期进行模拟面试，提升面试经验",
            "priority": "medium"
        })
        
        return recommendations

# 创建全局服务实例
interview_session_service = InterviewSessionService()