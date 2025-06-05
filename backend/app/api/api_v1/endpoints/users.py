from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
from pydantic import BaseModel

from app.db.database import get_db
from app.models.user import User
from app.models import schemas
from app.utils.auth import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.utils.auth import get_current_active_user
from app.core.auth import get_current_admin
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


router = APIRouter()


@router.post("/register", response_model=schemas.User, status_code=201)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """注册新用户
    
    创建新用户账号
    
    Args:
        user: 用户创建信息
        db: 数据库会话
        
    Returns:
        User: 创建的用户信息
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"尝试注册新用户: {user.username}, {user.email}")
    
    # 检查邮箱是否已存在
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        logger.warning(f"邮箱已被注册: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        logger.warning(f"用户名已被使用: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    try:
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
        logger.info(f"用户注册成功: {user.username}")
        return db_user
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册过程中发生错误: {str(e)}"
        )


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
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证密码
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
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


@router.put("/me", response_model=schemas.User)
def update_user(
    user_update: schemas.UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息
    
    更新当前登录用户的信息
    
    Args:
        user_update: 要更新的用户信息
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        User: 更新后的用户信息
    """
    # 检查邮箱是否已被其他用户使用
    if user_update.email and user_update.email != current_user.email:
        db_user = db.query(User).filter(User.email == user_update.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # 更新用户信息
    if user_update.email:
        current_user.email = user_update.email
    if user_update.password:
        current_user.hashed_password = get_password_hash(user_update.password)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.delete("/me", status_code=200)
def delete_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除当前用户
    
    删除当前登录用户的账号
    
    Args:
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        Dict: 操作结果
    """
    db.delete(current_user)
    db.commit()
    
    return {"message": "User deleted successfully"}


# 管理员API：获取所有用户
@router.get("/", response_model=List[schemas.User])
def get_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """获取所有用户（管理员专用）
    
    返回系统中的所有用户
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话
        current_user: 当前管理员用户
        
    Returns:
        List[User]: 用户列表
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

# 管理员API：获取特定用户
@router.get("/{user_id}", response_model=schemas.User)
def get_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """获取特定用户（管理员专用）
    
    根据用户ID获取用户信息
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前管理员用户
        
    Returns:
        User: 用户信息
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# 管理员API：更新用户状态
@router.patch("/{user_id}/status", response_model=schemas.User)
def update_user_status(
    user_id: int, 
    user_status: schemas.UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """更新用户状态（管理员专用）
    
    激活或停用用户账号
    
    Args:
        user_id: 用户ID
        user_status: 用户状态更新信息
        db: 数据库会话
        current_user: 当前管理员用户
        
    Returns:
        User: 更新后的用户信息
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 不允许停用最后一个管理员账号
    if user.is_admin and not user_status.is_active:
        admin_count = db.query(User).filter(User.is_admin == True, User.is_active == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last admin account"
            )
    
    user.is_active = user_status.is_active
    db.commit()
    db.refresh(user)
    return user

# 管理员API：授予或撤销管理员权限
@router.patch("/{user_id}/admin", response_model=schemas.User)
def update_user_admin(
    user_id: int, 
    user_admin: schemas.UserAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """更新用户管理员权限（管理员专用）
    
    授予或撤销用户的管理员权限
    
    Args:
        user_id: 用户ID
        user_admin: 用户管理员权限更新信息
        db: 数据库会话
        current_user: 当前管理员用户
        
    Returns:
        User: 更新后的用户信息
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 不允许撤销最后一个管理员的权限
    if user.is_admin and not user_admin.is_admin:
        admin_count = db.query(User).filter(User.is_admin == True, User.is_active == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove admin rights from the last admin account"
            )
    
    user.is_admin = user_admin.is_admin
    db.commit()
    db.refresh(user)
    return user

# 管理员API：删除用户
@router.delete("/{user_id}", status_code=200)
def delete_user_by_admin(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """删除用户（管理员专用）
    
    根据用户ID删除用户
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前管理员用户
        
    Returns:
        Dict: 操作结果
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 不允许删除最后一个管理员账号
    if user.is_admin:
        admin_count = db.query(User).filter(User.is_admin == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last admin account"
            )
    
    # 不允许删除自己
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

# 添加密码更改模型
class PasswordChange(BaseModel):
    """密码更改模型"""
    current_password: str
    new_password: str

# 更改密码
@router.post("/change-password", response_model=schemas.User)
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更改用户密码
    
    验证当前密码并设置新密码
    
    Args:
        password_data: 包含当前密码和新密码的数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        User: 更新后的用户信息
    """
    # 验证当前密码
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # 更新密码
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
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
    from app.utils.auth import get_current_active_user as _get_current_active_user
    return _get_current_active_user(db=db, token=token)