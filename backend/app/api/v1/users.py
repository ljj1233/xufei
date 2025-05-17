from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.auth import get_current_user, get_current_admin
from app.db.base import get_db
from app.models.user import User
from pydantic import BaseModel, EmailStr
from datetime import timedelta

router = APIRouter()

# 请求模型
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    email: EmailStr = None
    password: str = None

class Token(BaseModel):
    access_token: str
    token_type: str

# 用户注册
@router.post("/register", response_model=Token)
async def register(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    # 检查用户名是否已存在
    logging.debug(f"尝试注册用户: {user_in.username}")
    print(f"尝试注册用户: {user_in.username}")
    if db.query(User).filter(User.username == user_in.username).first():
        logging.warning(f"用户名已存在: {user_in.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被注册"
        )
    print(f"尝试注册邮箱: {user_in.email}")
    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 创建新用户
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password)
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        logging.info(f"用户注册成功: {user.username} (ID: {user.id})")
    except Exception as e:
        db.rollback()
        logging.error(f"用户注册失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册过程中发生错误"
        )
    print(f"用户注册成功: {user.username} (ID: {user.id})")
    # 生成访问令牌
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# 用户登录
@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: Session = Depends(get_db)) -> Any:
    # 验证用户
    user = db.query(User).filter(User.username == user_in.username).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    # 生成访问令牌
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# 获取当前用户信息
@router.get("/me", response_model=dict)
async def get_user_info(current_user: User = Depends(get_current_user)) -> Any:
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin
    }

# 更新用户信息
@router.put("/me", response_model=dict)
async def update_user_info(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    # 更新邮箱
    if user_in.email and user_in.email != current_user.email:
        if db.query(User).filter(User.email == user_in.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
        current_user.email = user_in.email
    
    # 更新密码
    if user_in.password:
        current_user.hashed_password = get_password_hash(user_in.password)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin
    }

# 管理员接口：获取所有用户列表
@router.get("/all", response_model=list[dict])
async def get_all_users(current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)) -> Any:
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "created_at": user.created_at
        }
        for user in users
    ]

# 管理员接口：更改用户状态
@router.put("/status/{user_id}", response_model=dict)
async def update_user_status(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "is_active": user.is_active
    }