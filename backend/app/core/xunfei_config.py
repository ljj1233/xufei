from pydantic_settings import BaseSettings
from typing import Optional

class XunFeiSettings(BaseSettings):
    """讯飞API配置"""
    XUNFEI_APPID: str = ""
    XUNFEI_API_KEY: str = ""
    XUNFEI_API_SECRET: str = ""
    
    # 语音评测服务配置
    XUNFEI_ISE_URL: str = "https://api.xfyun.cn/v1/service/v1/ise"
    # 语音识别服务配置
    XUNFEI_IAT_URL: str = "https://api.xfyun.cn/v1/service/v1/iat"
    # 情感分析服务配置
    XUNFEI_EMOTION_URL: str = "https://api.xfyun.cn/v1/service/v1/emotion"
    
    model_config = dict(env_file=".env", case_sensitive=True, extra="allow")

xunfei_settings = XunFeiSettings()