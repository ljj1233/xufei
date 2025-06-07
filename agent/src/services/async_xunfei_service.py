# agent/services/async_xunfei_service.py

from typing import Dict, Optional, Any
import time
import hashlib
import base64
import hmac
import json
import asyncio
import aiohttp
import logging

from ..core.system.config import AgentConfig

logger = logging.getLogger(__name__)

class AsyncXunFeiService:
    """讯飞服务的异步实现
    
    封装与讯飞开放平台API的异步交互
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
        self.spark_url = self.config.get_service_config("xunfei", "spark_url", "wss://spark-api.xfyun.cn/v1.1/chat")
        
        # 检查必要的配置是否存在
        if not self.app_id or not self.api_key or not self.api_secret:
            logger.warning("讯飞API配置不完整，某些功能可能无法正常工作")
    
    async def _create_auth_params(self, url: str) -> Dict:
        """生成讯飞API鉴权参数(异步版本)
        
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
    
    async def speech_recognition(self, audio_data: bytes) -> str:
        """异步语音识别服务
        
        将音频数据转换为文本
        
        Args:
            audio_data: 音频数据
            
        Returns:
            str: 识别结果文本
        """
        url = self.iat_url
        auth_params = await self._create_auth_params(url)
        
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
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    result = await response.json()
                    
                    if result.get('code') == '0':
                        logger.info("语音识别成功")
                        return result.get('data', '')
                    else:
                        logger.error(f"语音识别失败: {result.get('desc', '未知错误')}")
                        return ''
        except Exception as e:
            logger.error(f"语音识别请求异常: {e}")
            return ''
    
    async def speech_assessment(self, audio_data: bytes) -> Dict:
        """异步语音评测服务
        
        评估语音的清晰度、流畅度等
        
        Args:
            audio_data: 音频数据
            
        Returns:
            Dict: 评测结果
        """
        url = self.ise_url
        auth_params = await self._create_auth_params(url)
        
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
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    result = await response.json()
                    
                    if result.get('code') == '0':
                        logger.info("语音评测成功")
                        return {
                            'clarity': result.get('clarity', 0),  # 清晰度
                            'fluency': result.get('fluency', 0),  # 流畅度
                            'integrity': result.get('integrity', 0),  # 完整度
                            'speed': result.get('speed', 0)  # 语速
                        }
                    else:
                        logger.error(f"语音评测失败: {result.get('desc', '未知错误')}")
                        return {}
        except Exception as e:
            logger.error(f"语音评测请求异常: {e}")
            return {}
    
    async def emotion_analysis(self, audio_data: bytes) -> Dict:
        """异步情感分析服务
        
        分析语音中的情感
        
        Args:
            audio_data: 音频数据
            
        Returns:
            Dict: 情感分析结果
        """
        url = self.emotion_url
        auth_params = await self._create_auth_params(url)
        
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
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    result = await response.json()
                    
                    if result.get('code') == '0':
                        logger.info("情感分析成功")
                        return {
                            'emotion': result.get('emotion', '中性'),  # 情感类型
                            'confidence': result.get('confidence', 0.0)  # 置信度
                        }
                    else:
                        logger.error(f"情感分析失败: {result.get('desc', '未知错误')}")
                        return {}
        except Exception as e:
            logger.error(f"情感分析请求异常: {e}")
            return {}
            
    async def chat_spark(self, messages: list, temperature: float = 0.7, domain: str = "generalv1.5", max_tokens: int = 2048) -> Dict:
        """与讯飞星火大模型进行异步对话
        
        Args:
            messages: 对话历史
            temperature: 温度参数
            domain: 模型版本
            max_tokens: 最大生成token数
            
        Returns:
            Dict: 对话结果
        """
        try:
            # 构造请求体
            data = {
                "header": {
                    "app_id": self.app_id,
                    "uid": "12345678"
                },
                "parameter": {
                    "chat": {
                        "domain": domain,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                },
                "payload": {
                    "message": {
                        "text": messages
                    }
                }
            }
            
            # 生成鉴权信息
            current_time = str(int(time.time()))
            signature_origin = f'{self.api_key}{current_time}{json.dumps(data)}'
            signature_sha = hmac.new(
                self.api_secret.encode('utf-8'),
                signature_origin.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            signature = base64.b64encode(signature_sha).decode(encoding='utf-8')
            
            # 构造请求URL
            url = f"{self.spark_url}?appid={self.app_id}&timestamp={current_time}&signature={signature}"
            
            logger.info(f"使用星火API URL: {self.spark_url}")
            
            # 发送WebSocket请求
            response = {}
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url) as ws:
                    await ws.send_str(json.dumps(data))
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            result = json.loads(msg.data)
                            
                            if result.get("header", {}).get("code") == 0:
                                response = {
                                    "content": result.get("payload", {}).get("text", ""),
                                    "status": "success"
                                }
                                if result.get("header", {}).get("status") == 2:  # 2表示最后一条消息
                                    break
                            else:
                                logger.error(f"星火对话失败: {result}")
                                response = {
                                    "content": "",
                                    "status": "error",
                                    "error": result.get("header", {}).get("message", "未知错误")
                                }
                                break
                                
            logger.info(f"星火对话完成: {response}")
            return response
            
        except Exception as e:
            logger.error(f"星火对话请求异常: {e}")
            return {
                "content": "",
                "status": "error",
                "error": str(e)
            } 