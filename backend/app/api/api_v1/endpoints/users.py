from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.database import get_db
from app.db.models import User
from app.models import schemas
from app.utils.auth import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.utils.auth import get_current_active_user
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


router = APIRouter()


@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """注册新用户
    
    创建新用户账号
    
    Args:
        user: 用户创建信息
        db: 数据库会话
        
    Returns:
        User: 创建的用户信息
    """
    # 检查邮箱是否已存在
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被使用"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录
    
    验证用户凭据并返回访问令牌
    
    Args:
        form_data: 表单数据，包含用户名和密码
        db: 数据库会话
        
    Returns:
        Token: 访问令牌
    """
    # 查找用户
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证密码
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息
    
    返回当前登录用户的详细信息
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 用户信息
    """
    return current_user


# 这个函数需要在auth.py中定义，这里只是引用
def get_current_active_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """获取当前活跃用户
    
    从令牌中获取当前用户
    
    Args:
        db: 数据库会话
        token: 访问令牌
        
    Returns:
        User: 当前用户
    """
    # 这个函数的实现应该在auth.py中
    pass