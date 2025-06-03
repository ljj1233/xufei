from typing import Dict, Optional
import time
import hashlib
import base64
import hmac
import json
import requests
from ..core.xunfei_config import xunfei_settings

class XunfeiService:
    def __init__(self):
        self.app_id = xunfei_settings.XUNFEI_APPID
        self.api_key = xunfei_settings.XUNFEI_API_KEY
        self.api_secret = xunfei_settings.XUNFEI_API_SECRET

    def _create_auth_params(self, url: str) -> Dict:
        """生成讯飞API鉴权参数"""
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
        """语音识别服务"""
        url = xunfei_settings.XUNFEI_IAT_URL
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
        
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        
        if result.get('code') == '0':
            if isinstance(result.get('data'), dict) and 'result' in result.get('data'):
                return result.get('data').get('result', '')
            return result.get('data', '')
        return ''

    def speech_assessment(self, audio_data: bytes) -> Dict:
        """语音评测服务"""
        url = xunfei_settings.XUNFEI_ISE_URL
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
        
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        
        if result.get('code') == '0':
            data = result.get('data', {})
            return {
                'clarity': data.get('clarity', 0),  # 清晰度
                'fluency': data.get('fluency', 0),  # 流畅度
                'integrity': data.get('integrity', 0),  # 完整度
                'speed': data.get('speed', 0),  # 语速
                'pronunciation': data.get('pronunciation', 0)  # 发音
            }
        return {}

    def emotion_analysis(self, audio_data: bytes) -> Dict:
        """情感分析服务"""
        url = xunfei_settings.XUNFEI_EMOTION_URL
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
        
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        
        if result.get('code') == '0':
            data = result.get('data', {})
            emotion_data = data.get('emotion', {})
            if isinstance(emotion_data, dict):
                return emotion_data
            return {
                'positive': data.get('positive', 0),  # 积极情绪
                'neutral': data.get('neutral', 0),  # 中性情绪
                'negative': data.get('negative', 0),  # 消极情绪
                'emotion': data.get('emotion', ''),  # 情感类型
                'confidence': data.get('confidence', 0)  # 置信度
            }
        return {}

xunfei_service = XunfeiService()