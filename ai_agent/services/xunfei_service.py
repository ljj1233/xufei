# ai_agent/services/xunfei_service.py

from typing import Dict, Optional
import time
import hashlib
import base64
import hmac
import json
import requests

from ..core.config import AgentConfig


class XunFeiService:
    """讯飞服务
    
    封装与讯飞开放平台API的交互
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化讯飞服务
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        self.config = config or AgentConfig()
        
        # 从配置中加载讯飞API参数
        self.app_id = self.config.get_service_config("xunfei", "app_id", "")
        self.api_key = self.config.get_service_config("xunfei", "api_key", "")
        self.api_secret = self.config.get_service_config("xunfei", "api_secret", "")
        
        # 讯飞API URL
        self.ise_url = self.config.get_service_config("xunfei", "ise_url", "https://api.xfyun.cn/v1/service/v1/ise")
        self.iat_url = self.config.get_service_config("xunfei", "iat_url", "https://api.xfyun.cn/v1/service/v1/iat")
        self.emotion_url = self.config.get_service_config("xunfei", "emotion_url", "https://api.xfyun.cn/v1/service/v1/emotion")
        
        # 检查必要的配置是否存在
        if not self.app_id or not self.api_key or not self.api_secret:
            print("警告: 讯飞API配置不完整，某些功能可能无法正常工作")
    
    def _create_auth_params(self, url: str) -> Dict:
        """生成讯飞API鉴权参数
        
        Args:
            url: API URL
            
        Returns:
            Dict: 鉴权参数
        """
        now = int(time.time())
        signature_origin = f'host: {url}\ndate: {now}\nGET /v1/iat HTTP/1.1'
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        return {
            'authorization': authorization,
            'date': str(now),
            'host': url
        }
    
    def speech_recognition(self, audio_data: bytes) -> str:
        """语音识别服务
        
        将音频数据转换为文本
        
        Args:
            audio_data: 音频数据
            
        Returns:
            str: 识别结果文本
        """
        url = self.iat_url
        auth_params = self._create_auth_params(url)
        
        headers = {
            'authorization': auth_params['authorization'],
            'date': auth_params['date'],
            'host': auth_params['host'],
            'content-type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'audio': base64.b64encode(audio_data).decode('utf-8')
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            result = response.json()
            
            if result.get('code') == '0':
                return result.get('data', '')
            else:
                print(f"语音识别失败: {result.get('desc', '未知错误')}")
                return ''
        except Exception as e:
            print(f"语音识别请求异常: {e}")
            return ''
    
    def speech_assessment(self, audio_data: bytes) -> Dict:
        """语音评测服务
        
        评估语音的清晰度、流畅度等
        
        Args:
            audio_data: 音频数据
            
        Returns:
            Dict: 评测结果
        """
        url = self.ise_url
        auth_params = self._create_auth_params(url)
        
        headers = {
            'authorization': auth_params['authorization'],
            'date': auth_params['date'],
            'host': auth_params['host'],
            'content-type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'audio': base64.b64encode(audio_data).decode('utf-8'),
            'category': 'read_sentence',  # 评测模式
            'language': 'cn'  # 语言
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            result = response.json()
            
            if result.get('code') == '0':
                return {
                    'clarity': result.get('clarity', 0),  # 清晰度
                    'fluency': result.get('fluency', 0),  # 流畅度
                    'integrity': result.get('integrity', 0),  # 完整度
                    'speed': result.get('speed', 0)  # 语速
                }
            else:
                print(f"语音评测失败: {result.get('desc', '未知错误')}")
                return {}
        except Exception as e:
            print(f"语音评测请求异常: {e}")
            return {}
    
    def emotion_analysis(self, audio_data: bytes) -> Dict:
        """情感分析服务
        
        分析语音中的情感
        
        Args:
            audio_data: 音频数据
            
        Returns:
            Dict: 情感分析结果
        """
        url = self.emotion_url
        auth_params = self._create_auth_params(url)
        
        headers = {
            'authorization': auth_params['authorization'],
            'date': auth_params['date'],
            'host': auth_params['host'],
            'content-type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'audio': base64.b64encode(audio_data).decode('utf-8')
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            result = response.json()
            
            if result.get('code') == '0':
                return {
                    'emotion': result.get('emotion', '中性'),  # 情感类型
                    'confidence': result.get('confidence', 0.0)  # 置信度
                }
            else:
                print(f"情感分析失败: {result.get('desc', '未知错误')}")
                return {}
        except Exception as e:
            print(f"情感分析请求异常: {e}")
            return {}