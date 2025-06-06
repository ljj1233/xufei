"""
WebSocket连接管理器

管理WebSocket连接和消息发送
"""

import logging
import json
from typing import Dict, Any, List, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    WebSocket连接管理器
    
    管理WebSocket连接和消息发送
    """
    
    def __init__(self):
        """初始化连接管理器"""
        # 活跃连接字典: {client_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        logger.info("WebSocket连接管理器初始化完成")
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        接受WebSocket连接
        
        Args:
            websocket: WebSocket连接
            client_id: 客户端ID
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"客户端已连接: client_id={client_id}")
        
        # 发送连接成功消息
        await self.send_message(client_id, "CONNECTED", {"message": "WebSocket连接已建立"})
    
    def disconnect(self, client_id: str) -> None:
        """
        断开WebSocket连接
        
        Args:
            client_id: 客户端ID
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"客户端已断开连接: client_id={client_id}")
    
    async def send_message(self, client_id: str, event_type: str, data: Any) -> bool:
        """
        向指定客户端发送消息
        
        Args:
            client_id: 客户端ID
            event_type: 事件类型
            data: 消息数据
            
        Returns:
            是否发送成功
        """
        if client_id in self.active_connections:
            try:
                message = {
                    "type": event_type,
                    "data": data
                }
                await self.active_connections[client_id].send_json(message)
                logger.debug(f"消息已发送: client_id={client_id}, type={event_type}")
                return True
            except Exception as e:
                logger.error(f"发送消息失败: client_id={client_id}, error={str(e)}")
                return False
        else:
            logger.warning(f"客户端不存在或未连接: client_id={client_id}")
            return False
    
    async def broadcast(self, event_type: str, data: Any) -> None:
        """
        广播消息给所有连接的客户端
        
        Args:
            event_type: 事件类型
            data: 消息数据
        """
        message = {
            "type": event_type,
            "data": data
        }
        
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败: client_id={client_id}, error={str(e)}")
                disconnected_clients.append(client_id)
        
        # 清理断开的连接
        for client_id in disconnected_clients:
            self.disconnect(client_id)
        
        if disconnected_clients:
            logger.info(f"已清理 {len(disconnected_clients)} 个断开的连接")
        
        logger.info(f"广播消息已发送: type={event_type}, recipients={len(self.active_connections)}")
    
    def get_connection_count(self) -> int:
        """
        获取当前连接数
        
        Returns:
            当前连接数
        """
        return len(self.active_connections)
    
    def is_connected(self, client_id: str) -> bool:
        """
        检查客户端是否已连接
        
        Args:
            client_id: 客户端ID
            
        Returns:
            是否已连接
        """
        return client_id in self.active_connections 