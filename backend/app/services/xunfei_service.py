from typing import Dict, Optional, Any
import time
import hashlib
import base64
import hmac
import json
import requests
import uuid
from datetime import datetime
import websocket
import logging
from urllib.parse import urlparse
from ..core.xunfei_config import xunfei_settings

# 配置日志
logger = logging.getLogger(__name__)

class XunfeiService:
    def __init__(self):
        """初始化讯飞服务"""
        self.app_id = xunfei_settings.XUNFEI_APPID
        self.api_key = xunfei_settings.XUNFEI_API_KEY
        self.api_secret = xunfei_settings.XUNFEI_API_SECRET
        
        # 获取讯飞星火大模型URL
        self.spark_url = xunfei_settings.XUNFEI_SPARK_URL
        
        logger.info("讯飞服务初始化完成")
    
    def _create_auth_params(self, url: str) -> Dict[str, str]:
        """创建认证参数"""
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        path = parsed_url.path
        
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # 拼接字符串
        signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
        
        # 进行hmac-sha256加密
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        
        signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        
        return {
            "authorization": authorization,
            "date": date,
            "host": host
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
            return {
                'emotion': data.get('emotion', 'neutral'),  # 情感类型
                'confidence': data.get('confidence', 0.5)  # 置信度
            }
        return {}
    
    def spark_assessment(self, text: str, criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """使用讯飞星火大模型进行评分
        
        Args:
            text: 需要评分的文本
            criteria: 评分标准，如果不提供则使用默认标准
            
        Returns:
            Dict[str, Any]: 评分结果
        """
        if not text:
            logger.warning("评分文本为空")
            return {
                "score": 0,
                "feedback": "无法评分空文本",
                "aspects": {}
            }
            
        try:
            # 默认评分标准
            default_criteria = {
                "relevance": "回答与问题的相关性",
                "structure": "回答的结构性和逻辑性",
                "professionalism": "专业知识水平",
                "clarity": "表达清晰度"
            }
            
            # 使用提供的标准或默认标准
            eval_criteria = criteria or default_criteria
            
            # 构建评分提示
            prompt = f"""
            请对以下面试回答进行评分和分析。评分标准如下：
            {json.dumps(eval_criteria, ensure_ascii=False)}
            
            每项评分使用0-100分制，并提供简短的改进建议。
            
            面试回答内容：
            {text}
            
            请以JSON格式返回结果，格式如下：
            {{
                "overall_score": 总分(0-100),
                "feedback": "总体评价",
                "aspects": {{
                    "方面1": {{"score": 分数, "feedback": "建议"}},
                    "方面2": {{"score": 分数, "feedback": "建议"}},
                    ...
                }}
            }}
            """
            
            # 准备请求参数
            request_data = {
                "header": {
                    "app_id": self.app_id,
                    "uid": str(uuid.uuid4())
                },
                "parameter": {
                    "chat": {
                        "domain": "generalv3",  # 使用通用领域模型
                        "temperature": 0.3,  # 低温度以获得更确定的评分
                        "max_tokens": 1024
                    }
                },
                "payload": {
                    "message": {
                        "text": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    }
                }
            }
            
            # 发送WebSocket请求
            logger.info("调用讯飞星火大模型进行评分分析")
            
            # 使用HTTP请求替代WebSocket（简化实现）
            # 注意：实际使用时应根据讯飞API的要求选择合适的请求方式
            response = self._call_spark_api(request_data)
            
            if not response or "payload" not in response:
                logger.error("星火大模型API返回无效响应")
                return {
                    "score": 50,
                    "feedback": "评分服务暂时不可用，请稍后再试",
                    "aspects": {}
                }
                
            # 解析响应
            try:
                content = response["payload"]["message"]["content"][0]["content"]
                
                # 提取JSON结果
                import re
                json_match = re.search(r'({.*})', content, re.DOTALL)
                if json_match:
                    assessment_result = json.loads(json_match.group(1))
                else:
                    assessment_result = json.loads(content)
                
                logger.info(f"评分分析完成: 总分={assessment_result.get('overall_score', 0)}")
                return assessment_result
                
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                logger.error(f"解析评分结果失败: {e}")
                return {
                    "score": 50,
                    "feedback": "评分结果解析失败，请稍后再试",
                    "aspects": {}
                }
                
        except Exception as e:
            logger.error(f"调用星火大模型评分服务失败: {e}")
            return {
                "score": 50,
                "feedback": "评分服务出现错误，请稍后再试",
                "aspects": {}
            }
    
    def _call_spark_api(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """调用星火大模型API
        
        Args:
            request_data: 请求数据
            
        Returns:
            Dict[str, Any]: API响应
        """
        # 这里应实现实际的API调用
        # 由于讯飞星火API通常使用WebSocket，这里提供一个简化的HTTP实现示例
        # 实际使用时应根据讯飞API文档进行适配
        
        try:
            # 使用HTTP API示例（实际可能需要WebSocket）
            # 这里假设有一个HTTP接口可用
            http_url = self.spark_url.replace("wss://", "https://").replace("/v1.1/chat", "/api/chat")
            
            # 构建认证头
            timestamp = str(int(time.time()))
            signature_origin = self.api_key + timestamp + self.api_secret
            signature = hashlib.md5(signature_origin.encode('utf-8')).hexdigest()
            
            headers = {
                "Content-Type": "application/json",
                "X-Appid": self.app_id,
                "X-Timestamp": timestamp,
                "X-Signature": signature
            }
            
            # 发送请求
            response = requests.post(http_url, headers=headers, json=request_data)
            
            if response.status_code != 200:
                logger.error(f"星火API请求失败: {response.status_code} - {response.text}")
                return {}
                
            return response.json()
            
        except Exception as e:
            logger.error(f"调用星火API失败: {e}")
            return {}


# 创建单例实例
xunfei_service = XunfeiService()