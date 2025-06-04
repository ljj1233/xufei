from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    username: str

class UserCreate(UserBase):
    """用户创建模型"""
    password: str

class UserUpdate(BaseModel):
    """用户更新模型"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserStatusUpdate(BaseModel):
    """用户状态更新模型"""
    is_active: bool

class UserAdminUpdate(BaseModel):
    """用户管理员权限更新模型"""
    is_admin: bool

class UserInDB(UserBase):
    """数据库中的用户模型"""
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

class User(UserInDB):
    """用户响应模型"""
    pass