from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """访问令牌"""
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """令牌载荷"""
    sub: Optional[int] = None