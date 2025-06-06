"""
通知服务

处理系统通知和实时反馈
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from app.services.websocket_manager import ConnectionManager

# 配置日志
logger = logging.getLogger(__name__)

class NotificationService:
    """
    通知服务
    
    处理系统通知和实时反馈
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        """
        初始化通知服务
        
        Args:
            connection_manager: WebSocket连接管理器
        """
        self.manager = connection_manager
        logger.info("通知服务初始化完成")
        
    async def notify_analysis_progress(self, client_id: str, progress: float, status: str, details: Optional[Dict[str, Any]] = None):
        """
        通知客户端分析进度
        
        Args:
            client_id: 客户端ID
            progress: 进度百分比 (0-100)
            status: 当前状态描述
            details: 详细信息
        """
        await self.manager.send_message(client_id, "ANALYSIS_PROGRESS", {
            "progress": progress,
            "status": status,
            "details": details or {}
        })
        logger.info(f"已发送进度通知: client_id={client_id}, progress={progress}, status={status}")
        
    async def send_partial_feedback(self, client_id: str, feedback_type: str, feedback_content: Dict[str, Any]):
        """
        发送部分分析结果的实时反馈
        
        Args:
            client_id: 客户端ID
            feedback_type: 反馈类型 (如 'speech', 'visual', 'content')
            feedback_content: 反馈内容
        """
        await self.manager.send_message(client_id, "FEEDBACK", {
            "type": feedback_type,
            "content": feedback_content
        })
        logger.info(f"已发送部分反馈: client_id={client_id}, type={feedback_type}")
        
    async def notify_interview_status(self, client_id: str, status: str, message: str):
        """
        通知面试状态变化
        
        Args:
            client_id: 客户端ID
            status: 状态码
            message: 状态消息
        """
        await self.manager.send_message(client_id, "INTERVIEW_STATUS", {
            "status": status,
            "message": message
        })
        logger.info(f"已通知状态变化: client_id={client_id}, status={status}, message={message}")
        
    async def notify_error(self, client_id: str, error_code: str, error_message: str):
        """
        通知错误信息
        
        Args:
            client_id: 客户端ID
            error_code: 错误代码
            error_message: 错误消息
        """
        await self.manager.send_message(client_id, "ERROR", {
            "code": error_code,
            "message": error_message
        })
        logger.error(f"已通知错误: client_id={client_id}, code={error_code}, message={error_message}")
        
    async def broadcast_system_notification(self, title: str, message: str, notification_type: str = "info"):
        """
        广播系统通知
        
        Args:
            title: 通知标题
            message: 通知内容
            notification_type: 通知类型 (info, warning, error, success)
        """
        await self.manager.broadcast("SYSTEM_NOTIFICATION", {
            "title": title,
            "message": message,
            "type": notification_type
        })
        logger.info(f"已广播系统通知: title={title}, type={notification_type}")
        
    async def notify_task_status(self, client_id: str, task_id: str, status: str, result: Optional[Dict[str, Any]] = None):
        """
        通知任务状态
        
        Args:
            client_id: 客户端ID
            task_id: 任务ID
            status: 任务状态
            result: 任务结果
        """
        await self.manager.send_message(client_id, "TASK_STATUS", {
            "task_id": task_id,
            "status": status,
            "result": result or {}
        })
        logger.info(f"已通知任务状态: client_id={client_id}, task_id={task_id}, status={status}") 