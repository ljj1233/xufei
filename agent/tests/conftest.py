import pytest
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class MockNotificationService:
    """模拟通知服务"""
    
    def __init__(self):
        """初始化模拟通知服务"""
        self.notifications = []
    
    def send_progress(self, message: str, percent: int) -> None:
        """发送进度通知
        
        Args:
            message: 进度消息
            percent: 进度百分比
        """
        logger.info(f"进度通知: {percent}% - {message}")
        self.notifications.append({
            "type": "progress",
            "message": message,
            "percent": percent
        })
    
    async def notify_interview_status(self, client_id: str, status: str, message: str) -> None:
        """通知面试状态
        
        Args:
            client_id: 客户端ID
            status: 状态
            message: 消息
        """
        logger.info(f"面试状态通知: {status} - {message}")
        self.notifications.append({
            "type": "interview_status",
            "client_id": client_id,
            "status": status,
            "message": message
        })
    
    async def notify_analysis_progress(self, client_id: str, stage: str, message: str) -> None:
        """通知分析进度
        
        Args:
            client_id: 客户端ID
            stage: 阶段
            message: 消息
        """
        logger.info(f"分析进度通知: {stage} - {message}")
        self.notifications.append({
            "type": "analysis_progress",
            "client_id": client_id,
            "stage": stage,
            "message": message
        })
    
    async def send_partial_feedback(self, client_id: str, feedback_type: str, feedback_data: Dict[str, Any]) -> None:
        """发送部分反馈
        
        Args:
            client_id: 客户端ID
            feedback_type: 反馈类型
            feedback_data: 反馈数据
        """
        logger.info(f"部分反馈: {feedback_type}")
        self.notifications.append({
            "type": "partial_feedback",
            "client_id": client_id,
            "feedback_type": feedback_type,
            "feedback_data": feedback_data
        })
    
    async def notify_task_status(self, client_id: str, task_id: str, status: str, details: Dict[str, Any]) -> None:
        """通知任务状态
        
        Args:
            client_id: 客户端ID
            task_id: 任务ID
            status: 状态
            details: 详情
        """
        logger.info(f"任务状态通知: {task_id} - {status}")
        self.notifications.append({
            "type": "task_status",
            "client_id": client_id,
            "task_id": task_id,
            "status": status,
            "details": details
        })
    
    async def notify_error(self, client_id: str, error_type: str, error_message: str) -> None:
        """通知错误
        
        Args:
            client_id: 客户端ID
            error_type: 错误类型
            error_message: 错误消息
        """
        logger.info(f"错误通知: {error_type} - {error_message}")
        self.notifications.append({
            "type": "error",
            "client_id": client_id,
            "error_type": error_type,
            "error_message": error_message
        })

class MockContentFilterService:
    """模拟内容过滤服务"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = MockContentFilterService()
        return cls._instance
    
    def __init__(self):
        """初始化模拟内容过滤服务"""
        self.filtered_contents = {}
    
    def filter_text(self, text: str) -> Any:
        """过滤文本内容
        
        Args:
            text: 需要过滤的文本
            
        Returns:
            Any: 过滤结果
        """
        from dataclasses import dataclass
        
        @dataclass
        class FilterResult:
            filtered_text: str
            has_sensitive_content: bool
            sensitive_word_count: int
            sensitive_categories: list
            highest_severity: str
            
        # 简单过滤，只替换少数敏感词
        filtered_text = text
        if text and isinstance(text, str):
            for word in ["敏感词1", "敏感词2"]:
                if word in text:
                    filtered_text = filtered_text.replace(word, "***")
        
        # 创建过滤结果对象
        result = FilterResult(
            filtered_text=filtered_text,
            has_sensitive_content=False,
            sensitive_word_count=0,
            sensitive_categories=[],
            highest_severity="low"
        )
        
        # 记录过滤结果
        self.filtered_contents[text] = result
        
        return result
    
    def filter_audio(self, audio_data: bytes) -> Any:
        """过滤音频内容
        
        Args:
            audio_data: 音频数据
            
        Returns:
            Any: 过滤结果
        """
        from dataclasses import dataclass
        
        @dataclass
        class FilterResult:
            filtered_text: str
            has_sensitive_content: bool
            sensitive_word_count: int
            sensitive_categories: list
            highest_severity: str
            
        # 简单返回一个默认的过滤结果
        result = FilterResult(
            filtered_text="",
            has_sensitive_content=False,
            sensitive_word_count=0,
            sensitive_categories=[],
            highest_severity="low"
        )
        
        return result