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

# 创建一个模拟的InterviewAgent类，用于测试
class InterviewAgent:
    """模拟的面试智能体，用于测试"""
    
    def __init__(self):
        self.config = {"model": "test_model"}
    
    def analyze_audio(self, audio_data):
        """模拟音频分析"""
        return {
            "speech_rate": 150,
            "clarity": 0.8,
            "confidence": 0.75,
            "emotion": "neutral",
            "transcript": "这是一段模拟的文字转录",
            "score": 0.8
        }
    
    def analyze_video(self, video_data):
        """模拟视频分析"""
        return {
            "eye_contact": 0.7,
            "facial_expression": "neutral",
            "posture": "good",
            "engagement": 0.8,
            "score": 0.75
        }
    
    def analyze_content(self, text):
        """模拟内容分析"""
        return {
            "relevance": 0.8,
            "coherence": 0.75,
            "depth": 0.7,
            "structure": "good",
            "score": 0.75
        }

class InterviewSessionService:
    """模拟面试会话服务"""
    
    def __init__(self):
        self.agent = InterviewAgent()
        self.active_sessions = {}  # 存储活跃会话的实时分析状态
    
    def create_session(self, db: Session, user_id: int, job_position_id: int, 
                      title: str, description: str = None, 
                      planned_duration: int = 1800, question_count: int = 5,
                      difficulty_level: str = "medium", 
                      enable_real_time_feedback: bool = True,
                      mode: str = "full") -> InterviewSession:
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
            enable_real_time_feedback=enable_real_time_feedback,
            mode=mode,
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
        
        # 根据技术领域、岗位类型和面试模式生成问题
        questions_data = self._get_questions_by_position(
            job_position, 
            session.question_count, 
            session.difficulty_level,
            session.mode  # 传递面试模式
        )
        
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
    
    def _get_questions_by_position(self, job_position: JobPosition, count: int, difficulty: str, mode: str = "full") -> List[Dict]:
        """根据职位生成问题列表
        
        Args:
            job_position: 职位信息
            count: 问题数量
            difficulty: 难度级别
            mode: 面试模式（"quick"或"full"）
            
        Returns:
            问题列表
        """
        questions = []
        
        # 自我介绍（必有）- 在quick模式下更短，在full模式下更全面
        if mode == "quick":
            questions.append({
                "text": "请简单介绍一下自己的专业背景和核心技能。",
                "type": QuestionType.SELF_INTRO,
                "duration": 60,  # 缩短为1分钟
                "difficulty": "easy"
            })
        else:
            questions.append({
                "text": "请先做一个简单的自我介绍，包括您的教育背景、技能特长和职业目标。",
                "type": QuestionType.SELF_INTRO,
                "duration": 120,
                "difficulty": "easy"
            })
        
        # 根据技术领域和面试模式生成专业问题
        if job_position.tech_field == TechField.AI:
            questions.extend(self._get_ai_questions(job_position.position_type, difficulty, count - 1, mode))
        elif job_position.tech_field == TechField.BIGDATA:
            questions.extend(self._get_bigdata_questions(job_position.position_type, difficulty, count - 1, mode))
        elif job_position.tech_field == TechField.IOT:
            questions.extend(self._get_iot_questions(job_position.position_type, difficulty, count - 1, mode))
        elif job_position.tech_field == TechField.SYSTEM:
            questions.extend(self._get_system_questions(job_position.position_type, difficulty, count - 1, mode))
        
        # 如果是快速模式，可能需要减少问题数量
        if mode == "quick" and len(questions) > min(4, count):
            # 保留自我介绍和最多3个技术问题
            questions = questions[:min(4, count)]
        
        return questions[:count]
    
    def _get_ai_questions(self, position_type: PositionType, difficulty: str, count: int, mode: str = "full") -> List[Dict]:
        """获取AI领域问题"""
        quick_questions = [
            {
                "text": "简述一下深度学习与传统机器学习的主要区别。",
                "type": QuestionType.TECHNICAL,
                "duration": 120,  # 2分钟
                "difficulty": difficulty
            },
            {
                "text": "你最熟悉的一种深度学习框架是什么？请简述其优缺点。",
                "type": QuestionType.TECHNICAL,
                "duration": 120,
                "difficulty": difficulty
            }
        ]
        
        full_questions = [
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
        ]
        
        if position_type == PositionType.PRODUCT:
            quick_product_questions = [
                {
                    "text": "简述一个你认为成功的AI产品案例。",
                    "type": QuestionType.CASE_STUDY,
                    "duration": 120,
                    "difficulty": difficulty
                }
            ]
            
            full_product_questions = [
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
            ]
            
            if mode == "quick":
                quick_questions.extend(quick_product_questions)
            else:
                full_questions.extend(full_product_questions)
        
        # 根据模式返回不同问题集
        if mode == "quick":
            return quick_questions[:count]
        else:
            return full_questions[:count]
    
    def _get_bigdata_questions(self, position_type: PositionType, difficulty: str, count: int, mode: str = "full") -> List[Dict]:
        """获取大数据领域问题"""
        quick_questions = [
            {
                "text": "简述Hadoop的核心组件及其作用。",
                "type": QuestionType.TECHNICAL,
                "duration": 120,
                "difficulty": difficulty
            },
            {
                "text": "你使用过哪些大数据处理框架？简述其中一个的优势。",
                "type": QuestionType.TECHNICAL,
                "duration": 120,
                "difficulty": difficulty
            }
        ]
        
        full_questions = [
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
            },
            {
                "text": "在处理大数据时，你是如何优化查询性能的？请给出具体案例。",
                "type": QuestionType.BEHAVIORAL,
                "duration": 300,
                "difficulty": difficulty
            }
        ]
        
        # 根据模式返回不同问题集
        if mode == "quick":
            return quick_questions[:count]
        else:
            return full_questions[:count]
    
    def _get_iot_questions(self, position_type: PositionType, difficulty: str, count: int, mode: str = "full") -> List[Dict]:
        """获取物联网领域问题"""
        quick_questions = [
            {
                "text": "简述物联网系统的典型架构层次。",
                "type": QuestionType.TECHNICAL,
                "duration": 120,
                "difficulty": difficulty
            },
            {
                "text": "物联网设备面临哪些主要的安全挑战？",
                "type": QuestionType.TECHNICAL,
                "duration": 120,
                "difficulty": difficulty
            }
        ]
        
        full_questions = [
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
            },
            {
                "text": "描述一个你参与过的物联网项目，重点说明你解决的技术挑战。",
                "type": QuestionType.BEHAVIORAL,
                "duration": 300,
                "difficulty": difficulty
            }
        ]
        
        # 根据模式返回不同问题集
        if mode == "quick":
            return quick_questions[:count]
        else:
            return full_questions[:count]
    
    def _get_system_questions(self, position_type: PositionType, difficulty: str, count: int, mode: str = "full") -> List[Dict]:
        """获取智能系统领域问题"""
        quick_questions = [
            {
                "text": "简述一个智能推荐系统的基本架构。",
                "type": QuestionType.TECHNICAL,
                "duration": 120,
                "difficulty": difficulty
            },
            {
                "text": "你使用过哪些方法评估智能系统的性能？",
                "type": QuestionType.TECHNICAL,
                "duration": 120,
                "difficulty": difficulty
            }
        ]
        
        full_questions = [
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
            },
            {
                "text": "描述一个你参与开发的智能系统项目，重点说明你的贡献和项目成果。",
                "type": QuestionType.BEHAVIORAL,
                "duration": 300,
                "difficulty": difficulty
            }
        ]
        
        # 根据模式返回不同问题集
        if mode == "quick":
            return quick_questions[:count]
        else:
            return full_questions[:count]
    
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
        """完成面试会话并生成分析报告"""
        # 获取会话
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        
        if not session:
            raise ValueError(f"会话不存在: ID {session_id}")
        
        if session.status not in [SessionStatus.IN_PROGRESS, SessionStatus.PAUSED]:
            raise ValueError(f"会话状态不允许完成: {session.status}")
        
        # 获取所有问题
        questions = db.query(InterviewQuestion).filter(
            InterviewQuestion.session_id == session_id
        ).order_by(InterviewQuestion.order_index).all()
        
        # 计算完成度
        answered_questions = [q for q in questions if q.is_answered]
        completion_rate = len(answered_questions) / len(questions) if questions else 0
        
        # 更新会话状态
        session.status = SessionStatus.COMPLETED
        session.ended_at = datetime.now()
        session.actual_duration = int((session.ended_at - session.started_at).total_seconds()) if session.started_at else 0
        session.completion_rate = completion_rate
        
        # 生成最终分析
        final_analysis = self._generate_final_analysis(db, session, questions)
        session.overall_score = final_analysis.overall_score
        
        # 保存更新
        db.commit()
        
        # 格式化返回结果
        return {
            "session_id": session.id,
            "completion_rate": completion_rate,
            "overall_score": final_analysis.overall_score,
            **{k: getattr(final_analysis, k) for k in [
                'strengths', 'weaknesses', 'suggestions', 
                'professional_knowledge', 'skill_matching',
                'communication_ability', 'logical_thinking',
                'innovation_ability', 'stress_handling'
            ] if hasattr(final_analysis, k)}
        }
    
    def _generate_final_analysis(self, db: Session, session: InterviewSession, 
                              questions: List[InterviewQuestion]) -> Dict[str, Any]:
        """生成最终分析报告
        
        考虑会话的模式，快速面试(quick)和完整面试(full)采用不同的分析策略
        """
        # 获取会话模式
        session_mode = session.mode
        
        # 计算各项指标
        content_scores = []
        delivery_scores = []
        relevance_scores = []
        
        for q in questions:
            if q.is_answered:
                if q.content_score:
                    content_scores.append(q.content_score)
                if q.delivery_score:
                    delivery_scores.append(q.delivery_score)
                if q.relevance_score:
                    relevance_scores.append(q.relevance_score)
        
        # 计算平均分
        avg_content = sum(content_scores) / len(content_scores) if content_scores else 0
        avg_delivery = sum(delivery_scores) / len(delivery_scores) if delivery_scores else 0
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
        
        # 计算总分 - 根据模式调整权重
        if session_mode == "quick":
            # 快速面试模式：内容占比更高，不考虑视觉分析
            overall_score = avg_content * 0.6 + avg_delivery * 0.4
        else:
            # 完整面试模式：综合考虑内容、表达和相关性
            overall_score = avg_content * 0.5 + avg_delivery * 0.3 + avg_relevance * 0.2
        
        # 生成反馈
        strengths, weaknesses = self._generate_feedback(
            overall_score=overall_score,
            content=avg_content,
            delivery=avg_delivery,
            relevance=avg_relevance,
            completion_rate=session.completion_rate
        )
        
        # 生成建议
        suggestions = [
            "在面试前做更充分的准备，熟悉岗位职责和公司背景",
            "练习使用STAR法则回答行为面试问题",
            "提高语言的逻辑性和条理性",
            "保持适当的语速和音量"
        ]
        
        # 生成学习资源推荐
        learning_recommendations = self._generate_learning_recommendations(
            session=session,
            content=avg_content,
            delivery=avg_delivery,
            relevance=avg_relevance
        )
        
        # 创建分析结果
        analysis = SessionAnalysis(
            session_id=session.id,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            
            # 核心能力指标 - 快速模式与完整模式有不同的计算方式
            professional_knowledge=avg_content * 1.2,
            skill_matching=avg_relevance * 1.1,
            communication_ability=avg_delivery * 1.2,
            logical_thinking=avg_content * 0.9,
            innovation_ability=avg_content * 0.8,
            stress_handling=avg_delivery * 0.9,
            
            # 语音分析平均分
            speech_clarity=avg_delivery * 1.1,
            speech_pace=avg_delivery * 0.9,
            speech_emotion="自信" if avg_delivery > 7 else "中性" if avg_delivery > 5 else "紧张",
            speech_logic=avg_content * 1.1,
            
            # 视觉分析 - 仅在完整模式下有效
            facial_expressions={"专注": 60, "微笑": 30, "思考": 10} if session_mode == "full" else None,
            eye_contact=75.0 if session_mode == "full" else None,
            body_language={"自信": 70, "放松": 30} if session_mode == "full" else None,
            
            # 内容分析
            content_relevance=avg_relevance,
            content_structure=avg_content * 0.9,
            key_points=["沟通技巧", "团队协作", "问题解决能力"],
            
            # STAR结构评分
            situation_score=avg_content * 0.95,
            task_score=avg_content * 0.90,
            action_score=avg_content * 1.05,
            result_score=avg_content * 1.10,
            
            # 个性化学习推荐
            recommended_resources=learning_recommendations
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        return analysis
    
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
        
        return strengths, weaknesses
    
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