from typing import Dict, Any, List, Optional
import asyncio
import base64
import numpy as np
from datetime import datetime
import logging

from ai_agent.core.agent import InterviewAgent
from ai_agent.core.models import AnalysisResult
from backend.app.core.config import settings

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
        visual_features: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """分析问题回答"""
        try:
            if session_id not in self.active_sessions:
                logger.warning(f"Session {session_id} not active for analysis")
                return None
            
            # 调用AI智能体分析问题回答
            result = await self.agent.analyze_question_answer(
                session_id=str(session_id),
                question_id=question_id,
                answer_text=answer_text,
                audio_features=audio_features,
                visual_features=visual_features
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze question answer: {str(e)}")
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