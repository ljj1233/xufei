from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """应用配置类
    
    包含应用所需的所有配置参数
    """
    # 应用基本配置
    PROJECT_NAME: str = "多模态面试评测智能体"
    API_V1_STR: str = "/api/v1"
    
    # MySQL数据库配置
    MYSQL_SERVER: str = os.getenv("MYSQL_SERVER", "localhost")
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "password")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "interview_analysis")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")
    
    # 服务器配置
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    
    DATABASE_URI: Optional[str] = None
    DB_ECHO: bool = False  # 控制是否打印SQL语句，默认关闭

    # 数据库连接池配置
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))  # 连接池大小
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))  # 最大溢出连接数
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))  # 连接池等待超时时间，单位秒
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    # 多模态处理配置
    UPLOAD_FOLDER: str = "uploads"
    ALLOWED_EXTENSIONS: List[str] = ["mp4", "avi", "mov", "mp3", "wav"]
    MAX_CONTENT_LENGTH: int = 100 * 1024 * 1024  # 100MB
    
    # 模型配置
    TEXT_MODEL: str = "bert-base-chinese"
    
    model_config = dict(case_sensitive=True)
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        self.DATABASE_URI = f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_SERVER}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

settings = Settings()