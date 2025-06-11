from typing import Dict, Any, List, Optional
import asyncio
import base64
import numpy as np
from datetime import datetime
import logging

# 创建模拟的AnalysisResult类
class AnalysisResult:
    """模拟的分析结果类，用于测试"""
    def __init__(self, data=None):
        self.data = data or {}
    
    @property
    def speech_analysis(self):
        return self.data.get("speech", {})
    
    @property
    def visual_analysis(self):
        return self.data.get("visual", {})
    
    @property
    def content_analysis(self):
        return self.data.get("content", {})

# 创建模拟的InterviewAgent类
class InterviewAgent:
    """模拟的面试智能体，用于测试"""
    
    def __init__(self):
        self.config = {"model": "test_model"}
    
    async def start_real_time_analysis(self, session_id, scenario, feedback_callback):
        """模拟开始实时分析"""
        return True
    
    async def stop_real_time_analysis(self, session_id):
        """模拟停止实时分析"""
        return True
    
    async def analyze_audio_stream(self, session_id, audio_data, timestamp):
        """模拟分析音频流"""
        return {
            "clarity": {"score": 7.5, "details": "清晰度良好"},
            "pace": {"score": 7.0, "words_per_minute": 150},
            "emotion": {"score": 6.5, "primary": "neutral"},
            "timestamp": timestamp
        }
    
    async def analyze_video_frame(self, session_id, frame_data, timestamp):
        """模拟分析视频帧"""
        return {
            "eye_contact": {"score": 7.0, "details": "良好的眼神交流"},
            "expression": {"score": 6.5, "primary": "neutral"},
            "posture": {"score": 7.5, "details": "坐姿端正"},
            "timestamp": timestamp
        }
    
    async def analyze_question_answer(self, session_id, question_id, answer_text, 
                                     audio_features=None, visual_features=None, mode="full"):
        """模拟分析问题回答"""
        return {
            "relevance": {"score": 7.5, "details": "回答与问题相关"},
            "structure": {"score": 7.0, "details": "结构清晰"},
            "depth": {"score": 6.5, "details": "深度适中"},
            "overall": {"score": 7.0}
        }
        
    async def analyze_quick_practice(self, session_id, question_id, answer_text, 
                                   audio_data=None, job_description="", question=""):
        """模拟快速练习PLUS分析"""
        # 这是一个新增的方法，用于支持快速练习PLUS功能
        
        # 内容质量分析
        content_quality = {
            "relevance": 7.5,
            "relevance_review": "回答高度相关，直接针对问题进行了回应",
            "depth_and_detail": 6.0,
            "depth_review": "回答包含了一些具体例子，但缺少具体数据支撑",
            "professionalism": 8.0,
            "matched_keywords": ["算法", "数据结构", "优化"],
            "professional_style_review": "使用了专业术语，表达专业"
        }
        
        # 思维能力分析
        cognitive_skills = {
            "logical_structure": 7.0,
            "structure_review": "总分总结构，逻辑较为清晰",
            "clarity_of_thought": 7.5,
            "clarity_review": "思路清晰，没有明显矛盾"
        }
        
        # 沟通技巧分析（如果提供了音频数据）
        communication_skills = None
        if audio_data:
            communication_skills = {
                "fluency": 7.0,
                "fluency_details": {
                    "filler_words_count": 3,
                    "unnatural_pauses_count": 1
                },
                "speech_rate": 7.5,
                "speech_rate_details": {
                    "words_per_minute": 160,
                    "pace_category": "适中"
                },
                "vocal_energy": 6.5,
                "vocal_energy_details": {
                    "pitch_std_dev": 15.0,
                    "pitch_category": "平稳有变化"
                },
                "conciseness": 6.5,
                "conciseness_review": "表达较为简洁，但有少量冗余"
            }
        
        # 反馈生成
        strengths = [
            {
                "category": "content_quality",
                "item": "relevance",
                "description": "回答的相关性极高，你的回答紧扣问题核心，展现了良好的理解能力。"
            },
            {
                "category": "cognitive_skills",
                "item": "clarity_of_thought",
                "description": "思维清晰，能够有条理地表达复杂概念。"
            }
        ]
        
        growth_areas = [
            {
                "category": "content_quality",
                "item": "depth_and_detail",
                "description": "回答缺乏具体的数据和例子支撑",
                "action_suggestion": "使用STAR法则，特别是在描述结果时加入具体数据"
            }
        ]
        
        if communication_skills:
            if communication_skills["fluency"] < 7.0:
                growth_areas.append({
                    "category": "communication_skills",
                    "item": "fluency",
                    "description": f"检测到{communication_skills['fluency_details']['filler_words_count']}次填充词",
                    "action_suggestion": "用有意的停顿代替填充词，增强表达的专业性"
                })
            else:
                strengths.append({
                    "category": "communication_skills",
                    "item": "fluency",
                    "description": "语言表达流畅，很少使用填充词。"
                })
        
        # 计算模块得分
        content_quality_score = (content_quality["relevance"] + content_quality["depth_and_detail"] + 
                                content_quality["professionalism"]) / 3 * 10
        
        cognitive_skills_score = (cognitive_skills["logical_structure"] + 
                                 cognitive_skills["clarity_of_thought"]) / 2 * 10
        
        communication_skills_score = 0
        if communication_skills:
            communication_skills_score = (communication_skills["fluency"] + 
                                         communication_skills["speech_rate"] + 
                                         communication_skills["vocal_energy"] + 
                                         communication_skills["conciseness"]) / 4 * 10
        
        # 计算总分
        weights = [0.4, 0.3, 0.3] if communication_skills else [0.6, 0.4, 0]
        overall_score = (content_quality_score * weights[0] + 
                         cognitive_skills_score * weights[1] + 
                         communication_skills_score * weights[2])
        
        feedback = {
            "strengths": strengths,
            "growth_areas": growth_areas,
            "content_quality_score": content_quality_score,
            "cognitive_skills_score": cognitive_skills_score,
            "communication_skills_score": communication_skills_score,
            "overall_score": overall_score
        }
        
        return {
            "content_quality": content_quality,
            "cognitive_skills": cognitive_skills,
            "communication_skills": communication_skills,
            "feedback": feedback
        }

from app.core.config import settings

logger = logging.getLogger(__name__)

class AIAgentService:
    """AI智能体服务类，负责协调多模态分析"""
    
    def __init__(self):
        self.agent = InterviewAgent()
        self.active_sessions: Dict[int, Dict[str, Any]] = {}
        
    async def start_session_analysis(self, session_id: int, scenario: str = "technical") -> bool:
        """开始会话的实时分析"""
        try:
            # 启动AI智能体的实时分析
            success = await self.agent.start_real_time_analysis(
                session_id=str(session_id),
                scenario=scenario,
                feedback_callback=self._handle_feedback
            )
            
            if success:
                self.active_sessions[session_id] = {
                    "start_time": datetime.now(),
                    "scenario": scenario,
                    "analysis_count": 0,
                    "last_feedback_time": None
                }
                logger.info(f"Started real-time analysis for session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to start session analysis: {str(e)}")
            return False
    
    async def stop_session_analysis(self, session_id: int) -> bool:
        """停止会话的实时分析"""
        try:
            # 停止AI智能体的实时分析
            success = await self.agent.stop_real_time_analysis(str(session_id))
            
            if success and session_id in self.active_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Stopped real-time analysis for session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to stop session analysis: {str(e)}")
            return False
    
    async def analyze_audio_stream(
        self, 
        session_id: int, 
        audio_data: bytes, 
        timestamp: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """分析音频流数据"""
        try:
            if session_id not in self.active_sessions:
                logger.warning(f"Session {session_id} not active for analysis")
                return None
            
            # 调用AI智能体分析音频流
            result = await self.agent.analyze_audio_stream(
                session_id=str(session_id),
                audio_data=audio_data,
                timestamp=timestamp or datetime.now().timestamp()
            )
            
            if result:
                self.active_sessions[session_id]["analysis_count"] += 1
                self.active_sessions[session_id]["last_feedback_time"] = datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze audio stream: {str(e)}")
            return None
    
    async def analyze_video_frame(
        self, 
        session_id: int, 
        frame_data: bytes, 
        timestamp: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """分析视频帧数据"""
        try:
            if session_id not in self.active_sessions:
                logger.warning(f"Session {session_id} not active for analysis")
                return None
            
            # 调用AI智能体分析视频帧
            result = await self.agent.analyze_video_frame(
                session_id=str(session_id),
                frame_data=frame_data,
                timestamp=timestamp or datetime.now().timestamp()
            )
            
            if result:
                self.active_sessions[session_id]["analysis_count"] += 1
                self.active_sessions[session_id]["last_feedback_time"] = datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze video frame: {str(e)}")
            return None
    
    async def analyze_question_answer(
        self,
        session_id: int,
        question_id: int,
        answer_text: str,
        audio_features: Optional[Dict[str, Any]] = None,
        visual_features: Optional[Dict[str, Any]] = None,
        mode: str = "full"
    ) -> Optional[Dict[str, Any]]:
        """分析问题回答"""
        try:
            # 验证会话存在且为活跃状态
            if session_id not in self.active_sessions:
                logger.warning(f"会话 {session_id} 未处于活跃分析状态，尝试分析问题 {question_id}")
            
            # 调用智能体分析问题回答
            result = await self.agent.analyze_question_answer(
                session_id=str(session_id),
                question_id=question_id,
                answer_text=answer_text,
                audio_features=audio_features,
                visual_features=visual_features,
                mode=mode  # 确保向智能体传递模式参数
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze question answer: {str(e)}")
            return None
            
    async def analyze_quick_practice(
        self,
        session_id: int,
        question_id: int,
        answer_text: str,
        audio_data: Optional[bytes] = None,
        job_description: str = "",
        question: str = ""
    ) -> Optional[Dict[str, Any]]:
        """分析快速练习回答 - 新增方法"""
        try:
            # 快速练习可以不需要活跃会话
            # 调用AI智能体分析快速练习
            result = await self.agent.analyze_quick_practice(
                session_id=str(session_id),
                question_id=question_id,
                answer_text=answer_text,
                audio_data=audio_data,
                job_description=job_description,
                question=question
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze quick practice: {str(e)}")
            return None
    
    def generate_audio_feedback(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据音频分析结果生成反馈"""
        feedback_items = []
        
        try:
            # 语音清晰度反馈
            if "clarity" in analysis_result:
                clarity_score = analysis_result["clarity"].get("score", 0)
                if clarity_score < 6.0:
                    feedback_items.append({
                        "category": "clarity",
                        "message": "语音清晰度需要改善，建议放慢语速并清晰发音",
                        "severity": "warning",
                        "score": clarity_score,
                        "session_time": analysis_result.get("timestamp", 0),
                        "display_duration": 4.0
                    })
                elif clarity_score >= 8.0:
                    feedback_items.append({
                        "category": "clarity",
                        "message": "语音清晰度很好，继续保持",
                        "severity": "success",
                        "score": clarity_score,
                        "session_time": analysis_result.get("timestamp", 0),
                        "display_duration": 2.0
                    })
            
            # 语速反馈
            if "pace" in analysis_result:
                pace_score = analysis_result["pace"].get("score", 0)
                pace_value = analysis_result["pace"].get("words_per_minute", 0)
                
                if pace_value < 120:
                    feedback_items.append({
                        "category": "pace",
                        "message": "语速偏慢，可以适当加快语速",
                        "severity": "info",
                        "score": pace_score,
                        "session_time": analysis_result.get("timestamp", 0),
                        "display_duration": 3.0
                    })
                elif pace_value > 200:
                    feedback_items.append({
                        "category": "pace",
                        "message": "语速偏快，建议放慢语速以便面试官理解",
                        "severity": "warning",
                        "score": pace_score,
                        "session_time": analysis_result.get("timestamp", 0),
                        "display_duration": 4.0
                    })
            
            # 情感状态反馈
            if "emotion" in analysis_result:
                emotion_data = analysis_result["emotion"]
                confidence = emotion_data.get("confidence", 0)
                
                if confidence < 0.3:
                    feedback_items.append({
                        "category": "confidence",
                        "message": "声音听起来不够自信，建议调整语调和音量",
                        "severity": "warning",
                        "score": confidence * 10,
                        "session_time": analysis_result.get("timestamp", 0),
                        "display_duration": 4.0
                    })
        
        except Exception as e:
            logger.error(f"Failed to generate audio feedback: {str(e)}")
        
        return feedback_items
    
    def generate_video_feedback(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据视频分析结果生成反馈"""
        feedback_items = []
        
        try:
            # 眼神接触反馈
            if "eye_contact" in analysis_result:
                eye_contact_score = analysis_result["eye_contact"].get("score", 0)
                if eye_contact_score < 6.0:
                    feedback_items.append({
                        "category": "eye_contact",
                        "message": "注意保持与摄像头的眼神接触",
                        "severity": "warning",
                        "score": eye_contact_score,
                        "session_time": analysis_result.get("timestamp", 0),
                        "display_duration": 3.0
                    })
                elif eye_contact_score >= 8.0:
                    feedback_items.append({
                        "category": "eye_contact",
                        "message": "眼神接触很好，继续保持",
                        "severity": "success",
                        "score": eye_contact_score,
                        "session_time": analysis_result.get("timestamp", 0),
                        "display_duration": 2.0
                    })
            
            # 面部表情反馈
            if "expression" in analysis_result:
                expression_data = analysis_result["expression"]
                dominant_emotion = expression_data.get("dominant_emotion", "")
                
                if dominant_emotion in ["sad", "angry", "fear"]:
                    feedback_items.append({
                        "category": "expression",
                        "message": "表情看起来有些紧张，尝试放松并保持微笑",
                        "severity": "info",
                        "score": expression_data.get("confidence", 5.0),
                        "session_time": analysis_result.get("timestamp", 0),
                        "display_duration": 3.0
                    })
                elif dominant_emotion == "happy":
                    feedback_items.append({
                        "category": "expression",
                        "message": "表情自然友好，很好",
                        "severity": "success",
                        "score": expression_data.get("confidence", 8.0),
                        "session_time": analysis_result.get("timestamp", 0),
                        "display_duration": 2.0
                    })
            
            # 姿态反馈
            if "posture" in analysis_result:
                posture_score = analysis_result["posture"].get("score", 0)
                if posture_score < 6.0:
                    feedback_items.append({
                        "category": "posture",
                        "message": "注意保持良好的坐姿，挺直背部",
                        "severity": "info",
                        "score": posture_score,
                        "session_time": analysis_result.get("timestamp", 0),
                        "display_duration": 3.0
                    })
        
        except Exception as e:
            logger.error(f"Failed to generate video feedback: {str(e)}")
        
        return feedback_items
    
    def get_real_time_status(self, session_id: int) -> Dict[str, Any]:
        """获取实时分析状态"""
        if session_id not in self.active_sessions:
            return {
                "is_analyzing": False,
                "session_time": 0,
                "analysis_count": 0,
                "last_feedback_time": None
            }
        
        session_data = self.active_sessions[session_id]
        start_time = session_data["start_time"]
        session_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "is_analyzing": True,
            "session_time": session_time,
            "analysis_count": session_data["analysis_count"],
            "last_feedback_time": session_data["last_feedback_time"].isoformat() if session_data["last_feedback_time"] else None
        }
    
    async def _handle_feedback(self, session_id: str, feedback_data: Dict[str, Any]):
        """处理AI智能体的反馈回调"""
        try:
            # 这里可以添加额外的反馈处理逻辑
            logger.info(f"Received feedback for session {session_id}: {feedback_data}")
        except Exception as e:
            logger.error(f"Failed to handle feedback: {str(e)}")

# 创建全局服务实例
ai_agent_service = AIAgentService()