from pydantic import BaseModel
from typing import Optional

class FileUploadResponse(BaseModel):
    """文件上传响应"""
    filename: str
    file_path: str
    file_type: str
    size: int
    duration: Optional[float] = None