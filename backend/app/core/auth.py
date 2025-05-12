from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.security import verify_token
from app.db.base import get_db
from app.models.user import User

# OAuth2密码流认证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

# 获取当前用户
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 验证令牌
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # 获取用户
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user

# 获取当前管理员用户
async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user