"""
WebSocket路由处理器

处理WebSocket连接和消息
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.services.websocket_manager import ConnectionManager
from app.models.user import User
from app.db.database import get_db
from sqlalchemy.orm import Session

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter()

# 创建连接管理器实例
manager = ConnectionManager()

# OAuth2密码授权
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 验证WebSocket连接的用户
async def get_current_user_ws(token: str, db: Session) -> User:
    """
    验证WebSocket连接的用户
    
    Args:
        token: 访问令牌
        db: 数据库会话
        
    Returns:
        当前用户
        
    Raises:
        HTTPException: 如果令牌无效或用户不存在
    """
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            logger.warning("WebSocket连接验证失败: 令牌中无用户名")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
            )
    except Exception as e:
        logger.warning(f"WebSocket连接验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
        )
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        logger.warning(f"WebSocket连接验证失败: 用户不存在 - {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    
    return user

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, token: Optional[str] = None):
    """
    WebSocket终端点
    
    处理WebSocket连接和消息
    
    Args:
        websocket: WebSocket连接
        client_id: 客户端ID
        token: 访问令牌（可选）
    """
    # 验证连接（如果提供了令牌）
    if token:
        try:
            db = next(get_db())
            user = await get_current_user_ws(token, db)
            logger.info(f"WebSocket连接已验证: client_id={client_id}, user={user.username}")
        except HTTPException as e:
            logger.warning(f"WebSocket连接验证失败: client_id={client_id}, error={e.detail}")
            await websocket.close(code=status.HTTP_401_UNAUTHORIZED)
            return
    
    # 接受连接
    await manager.connect(websocket, client_id)
    
    try:
        # 持续接收消息
        while True:
            # 接收消息
            data = await websocket.receive_json()
            logger.info(f"收到WebSocket消息: client_id={client_id}, data={data}")
            
            # 处理消息（可以根据需要扩展）
            if data.get("type") == "ping":
                await manager.send_message(client_id, "pong", {
                    "message": "pong",
                    "timestamp": data.get("timestamp")
                })
            
    except WebSocketDisconnect:
        # 断开连接
        manager.disconnect(client_id)
        logger.info(f"WebSocket连接已断开: client_id={client_id}")
    except Exception as e:
        # 处理其他异常
        manager.disconnect(client_id)
        logger.error(f"WebSocket连接发生错误: client_id={client_id}, error={str(e)}")

@router.get("/ws/connections/count")
async def get_connection_count():
    """
    获取当前WebSocket连接数
    
    Returns:
        当前连接数
    """
    count = manager.get_connection_count()
    logger.info(f"当前WebSocket连接数: {count}")
    return {"count": count} 