# agent/services/async_xunfei_service.py

from typing import Dict, Optional, Any, List
import hashlib
import base64
import hmac
import json
import asyncio
import aiohttp
import logging
from urllib.parse import urlencode
import datetime
import time

from wsgiref.handlers import format_date_time
from ..core.system.config import AgentConfig

logger = logging.getLogger(__name__)

class AsyncXunFeiService:
    """讯飞服务的异步实现
    
    封装与讯飞开放平台API的异步交互
    
    Args:
        config: 配置对象，如果为None则创建默认配置
        max_concurrent_requests: 最大并发请求数，默认为1
    """
    
    def __init__(self, config: Optional[AgentConfig] = None, max_concurrent_requests: int = 1):
        """初始化讯飞服务
        
        Args:
            config: 配置对象，如果为None则创建默认配置
            max_concurrent_requests: 最大并发请求数，控制API调用的并发数量
        """
        self.config = config or AgentConfig()
        
        # 从配置中加载讯飞语音识别API参数
        self.xunfei_app_id = self.config.get_service_config("xunfei", "app_id", "")
        self.xunfei_api_key = self.config.get_service_config("xunfei", "api_key", "")
        self.xunfei_api_secret = self.config.get_service_config("xunfei", "api_secret", "")
        
        # 从配置中加载星火大模型API参数 - 星火需要单独的凭证
        self.spark_app_id = self.config.get_service_config("xunfei", "spark_app_id", "")
        self.spark_api_key = self.config.get_service_config("xunfei", "spark_api_key", "")
        self.spark_api_secret = self.config.get_service_config("xunfei", "spark_api_secret", "")
        
        # 讯飞语音识别API URL
        self.ise_url = self.config.get_service_config("xunfei", "ise_url", "https://api.xfyun.cn/v1/service/v1/ise")
        self.iat_url = self.config.get_service_config("xunfei", "iat_url", "https://api.xfyun.cn/v1/service/v1/iat")
        self.emotion_url = self.config.get_service_config("xunfei", "emotion_url", "https://api.xfyun.cn/v1/service/v1/emotion")
        
        # 星火API URL（默认使用Lite版本）- 使用正确的Lite版本URL
        self.spark_api_url = self.config.get_service_config("xunfei", "spark_api_url", "wss://spark-api.xf-yun.com/v1.1/chat")
        
        # 创建一个信号量，限制并发请求数量
        self.max_concurrent_requests = max_concurrent_requests
        self.api_semaphore = asyncio.Semaphore(max_concurrent_requests)
        logger.info(f"初始化讯飞服务，最大并发请求数: {max_concurrent_requests}")
        
        # 检查语音识别配置
        if not self.xunfei_app_id or not self.xunfei_api_key or not self.xunfei_api_secret:
            logger.warning("讯飞语音识别API配置不完整，语音转文本功能可能无法正常工作")
        else:
            logger.info(f"讯飞语音识别API配置完成，APPID: {self.xunfei_app_id[:4] if len(self.xunfei_app_id) > 4 else '****'}")
        
        # 检查星火配置
        if not self.spark_app_id or not self.spark_api_key or not self.spark_api_secret:
            logger.warning("讯飞星火大模型API配置不完整，星火对话功能可能无法正常工作")
        else:
            logger.info(f"讯飞星火大模型API配置完成，APPID: {self.spark_app_id[:4] if len(self.spark_app_id) > 4 else '****'}")
            logger.info(f"星火API URL: {self.spark_api_url} (星火Lite版本)")
    
    async def _create_auth_params(self, url: str, is_spark: bool = False) -> Dict:
        """生成讯飞API鉴权参数(异步版本)
        
        Args:
            url: API URL
            is_spark: 是否为星火API
            
        Returns:
            Dict: 鉴权参数
        """
        # 根据API类型选择不同的凭证
        api_key = self.spark_api_key if is_spark else self.xunfei_api_key
        api_secret = self.spark_api_secret if is_spark else self.xunfei_api_secret
        
        now = int(time.time())
        signature_origin = f'host: {url}\ndate: {now}\nGET /v1/iat HTTP/1.1'
        signature_sha = hmac.new(
            api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
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
        # 获取信号量，限制并发请求
        logger.debug(f"等待信号量，当前可用: {self.api_semaphore._value}/{self.max_concurrent_requests}")
        async with self.api_semaphore:
            logger.debug(f"获取到信号量，开始语音识别请求，剩余可用: {self.api_semaphore._value}/{self.max_concurrent_requests}")
            url = self.iat_url
            
            # 检查音频数据大小
            audio_size_kb = len(audio_data) / 1024
            logger.info(f"音频数据大小: {audio_size_kb:.2f} KB")
            
            # 如果音频大于1MB，尝试压缩或截断
            max_size = 1024 * 1024  # 1MB
            if len(audio_data) > max_size:
                logger.warning(f"警告: 音频数据大小({audio_size_kb:.2f}KB)超过1MB，可能会导致请求失败")
                # 这里可以添加音频压缩逻辑，但为简单起见，我们只截断数据
                audio_data = audio_data[:max_size]
                logger.info(f"已截断音频数据至 {len(audio_data)/1024:.2f} KB")
            
            # 获取当前时间戳
            cur_time = str(int(time.time()))
            
            # 构建API参数 - 简化参数，只保留必要的字段
            api_params = {
                "engine_type": "iat",    # 必需，表示语音识别服务
                "aue": "raw",            # 音频编码，raw代表原始PCM或WAV格式
                "format": "wav",         # 音频格式
                "sample_rate": 16000,    # 采样率
                "channel": 1,            # 声道数，1代表单声道
                "language": "zh_cn"      # 语言，使用zh_cn而不是cn
            }
            
            # 转换为JSON并进行Base64编码，作为X-Param头
            x_param = base64.b64encode(json.dumps(api_params).encode('utf-8')).decode('utf-8')
            
            # 计算CheckSum: MD5(API_SECRET + curTime + x_param)
            md5 = hashlib.md5()
            # 使用讯飞语音识别API的密钥，不是星火的
            md5.update((self.xunfei_api_secret + cur_time + x_param).encode('utf-8'))
            check_sum = md5.hexdigest()
            
            # 设置标准的讯飞WebAPI头信息
            headers = {
                'X-Appid': self.xunfei_app_id,  # 使用讯飞语音识别API的APPID
                'X-CurTime': cur_time,
                'X-Param': x_param,
                'X-CheckSum': check_sum,
                'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
                'Accept': 'application/json'
            }
            
            # Base64编码音频数据
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # 构建请求数据 - 只包含audio参数
            data = {
                'audio': audio_base64
            }
            
            # 将数据进行urlencode
            form_data = urlencode(data)
            
            try:
                logger.info(f"正在发送请求到讯飞语音识别API: {url}")
                logger.info(f"请求头: host=api.xfyun.cn, X-Appid={self.xunfei_app_id[:4] if len(self.xunfei_app_id) > 4 else '****'}, X-CurTime={cur_time}")
                logger.info(f"请求参数: {json.dumps(api_params, ensure_ascii=False)}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, data=form_data) as response:
                        # 检查HTTP状态码
                        status_code = response.status
                        resp_text = await response.text()
                        logger.info(f"响应状态码: {status_code}")
                        logger.info(f"响应内容类型: {response.headers.get('Content-Type', 'unknown')}")
                        logger.info(f"响应JSON: {resp_text}")
                        
                        if status_code != 200:
                            logger.error(f"HTTP错误: {status_code} - {resp_text}")
                            return ''
                        
                        # 尝试解析JSON响应
                        try:
                            result = json.loads(resp_text)
                            
                            if result.get('code') == '0':
                                logger.info("语音识别成功")
                                return result.get('data', '')
                            else:
                                error_code = result.get('code', '未知')
                                error_desc = result.get('desc', '未知错误')
                                logger.error(f"语音识别失败: {error_desc} (错误码: {error_code})")
                                
                                # 增加错误码说明
                                error_info = {
                                    "10105": "应用未授权或IP地址不在白名单中",
                                    "10106": "参数不合法，请检查X-Param格式",
                                    "10107": "音频文件格式有问题",
                                    "10110": "无效的token请求"
                                }
                                
                                if error_code in error_info:
                                    logger.error(f"错误详情: {error_info[error_code]}")
                                    
                                    # 特别处理10105错误
                                    if error_code == "10105":
                                        logger.error("请检查讯飞控制台中是否将当前服务器IP添加到白名单")
                                
                                logger.error(f"完整响应: {json.dumps(result, ensure_ascii=False)}")
                                return ''
                        except Exception as e:
                            logger.error(f"解析响应失败: {e}")
                            logger.error(f"原始响应: {resp_text}")
                            return ''
            except Exception as e:
                logger.error(f"语音识别请求异常: {e}")
                return ''
            finally:
                logger.debug(f"语音识别请求完成，释放信号量，当前可用: {self.api_semaphore._value + 1}/{self.max_concurrent_requests}")
    
    async def speech_assessment(self, audio_data: bytes) -> Dict:
        """异步语音评测服务
        
        评估语音的清晰度、流畅度等
        
        Args:
            audio_data: 音频数据
            
        Returns:
            Dict: 评测结果
        """
        logger.debug(f"等待信号量，当前可用: {self.api_semaphore._value}/{self.max_concurrent_requests}")
        async with self.api_semaphore:
            logger.debug(f"获取到信号量，开始语音评测请求，剩余可用: {self.api_semaphore._value}/{self.max_concurrent_requests}")
            url = self.ise_url
            # 使用讯飞语音识别API凭证，不是星火的
            auth_params = await self._create_auth_params(url, is_spark=False)
            
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
            finally:
                logger.debug(f"语音评测请求完成，释放信号量，当前可用: {self.api_semaphore._value + 1}/{self.max_concurrent_requests}")
    
    async def emotion_analysis(self, audio_data: bytes) -> Dict:
        """异步情感分析服务
        
        分析语音中的情感
        
        Args:
            audio_data: 音频数据
            
        Returns:
            Dict: 情感分析结果
        """
        logger.debug(f"等待信号量，当前可用: {self.api_semaphore._value}/{self.max_concurrent_requests}")
        async with self.api_semaphore:
            logger.debug(f"获取到信号量，开始情感分析请求，剩余可用: {self.api_semaphore._value}/{self.max_concurrent_requests}")
            url = self.emotion_url
            # 使用讯飞语音识别API凭证，不是星火的
            auth_params = await self._create_auth_params(url, is_spark=False)
            
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
            finally:
                logger.debug(f"情感分析请求完成，释放信号量，当前可用: {self.api_semaphore._value + 1}/{self.max_concurrent_requests}")
            
    async def chat_spark(self, messages: List[Dict[str, str]], 
                         temperature: float = 0.5, 
                         max_tokens: int = 2048) -> Dict[str, any]:
        """修复鉴权逻辑的星火对话方法"""
        logger.debug(f"等待信号量，当前可用: {self.api_semaphore._value}/{self.max_concurrent_requests}")
        async with self.api_semaphore:
            logger.debug(f"获取到信号量，开始星火对话请求，剩余可用: {self.api_semaphore._value}/{self.max_concurrent_requests}")
            try:
                # 1. 基础配置
                spark_api_url = self.spark_api_url
                host = "spark-api.xf-yun.com"
                path = "/v1.1/chat"
                logger.info(f'星火对话请求开始，使用app_id: {self.spark_app_id[:4]}****')
                
                # 构造正确的请求体
                request_body = {
                    "header": {
                        "app_id": self.spark_app_id,
                        "uid": f"user_{int(time.time())}"  # 生成唯一用户ID
                    },
                    "parameter": {
                        "chat": {
                            "domain": "lite",  # 关键修正：使用正确的domain
                            "temperature": temperature,
                            "max_tokens": max_tokens
                        }
                    },
                    "payload": {
                        "message": {
                            "text": [
                                # 系统角色提示
                                {"role": "system", "content": "你现在扮演一个专业的面试官,请用面试官的口吻和我说话。"},
                                # 用户消息（从参数中获取content）
                                {"role": "user", "content": messages[0]["content"] if messages else "你好"}
                            ]
                        }
                    }
                }
                
                # 3. 生成标准鉴权参数（关键修复）
                current_time = format_date_time(time.mktime(datetime.datetime.now().timetuple()))
                signature_origin = f"host: {host}\ndate: {current_time}\nGET {path} HTTP/1.1"
                
                # 4. 计算 HMAC-SHA256 签名
                signature = base64.b64encode(
                    hmac.new(
                        self.spark_api_secret.encode('utf-8'),
                        signature_origin.encode('utf-8'),
                        digestmod=hashlib.sha256
                    ).digest()
                ).decode()
                
                # 5. 构造授权头
                authorization = base64.b64encode(
                    f'api_key="{self.spark_api_key}", algorithm="hmac-sha256", '
                    f'headers="host date request-line", signature="{signature}"'
                    .encode('utf-8')
                ).decode()
                
                # 6. 拼接完整 URL
                url_params = {
                    "authorization": authorization,
                    "date": current_time,
                    "host": host
                }
                url = f"{spark_api_url}?{urlencode(url_params)}"
                
                # 7. WebSocket 连接（优化错误处理）
                response = {"status": "error", "content": "", "error": ""}
                logger.debug(f'星火对话请求体: {json.dumps(request_body, ensure_ascii=False)}')
                
                # 用于拼接完整回答内容的变量
                full_content = ""
                token_usage = {}
                
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.ws_connect(url, timeout=aiohttp.ClientTimeout(total=30)) as ws:
                            logger.info("WebSocket连接已建立，发送请求数据...")
                            await ws.send_str(json.dumps(request_body))
                            
                            async for msg in ws:
                                if msg.type == aiohttp.WSMsgType.TEXT:
                                    result = json.loads(msg.data)
                                    logger.debug(f"收到响应: {result}")
                                    
                                    if result["header"]["code"] == 0:
                                        # 检查payload和choices是否存在
                                        if "payload" in result and "choices" in result["payload"]:
                                            # 获取当前回答片段
                                            if "text" in result["payload"]["choices"]:
                                                text_list = result["payload"]["choices"]["text"]
                                                if text_list and len(text_list) > 0:
                                                    content_piece = text_list[0].get("content", "")
                                                    
                                                    # 拼接内容片段
                                                    full_content += content_piece
                                                    logger.debug(f"收到内容片段: 「{content_piece}」")
                                                    logger.debug(f"当前拼接结果: 「{full_content}」")
                                        
                                        # 如果是最后一条消息，完成拼接
                                        if result["header"]["status"] == 2:
                                            logger.info("接收到最终响应，内容拼接完成")
                                            # 记录token使用情况
                                            if "payload" in result and "usage" in result["payload"]:
                                                if "text" in result["payload"]["usage"]:
                                                    token_usage = result["payload"]["usage"]["text"]
                                                    logger.info(f"Token使用: 提问={token_usage.get('prompt_tokens', 0)}, "
                                                                f"回答={token_usage.get('completion_tokens', 0)}, "
                                                                f"总计={token_usage.get('total_tokens', 0)}")
                                            
                                            response["status"] = "success"
                                            response["content"] = full_content
                                            response["token_usage"] = token_usage
                                            break
                                    else:
                                        error_code = result["header"]["code"]
                                        error_msg = result["header"]["message"]
                                        logger.error(f"星火对话错误: Code {error_code}: {error_msg}")
                                        response["error"] = f"Code {error_code}: {error_msg}"
                                        break
                    except aiohttp.ClientError as e:
                        logger.error(f"WebSocket 连接失败: {str(e)}")
                        response["error"] = f"WebSocket 连接失败: {str(e)}"
                    except json.JSONDecodeError:
                        logger.error("无效的响应格式")
                        response["error"] = "无效的响应格式"
                    except Exception as e:
                        logger.error(f"处理WebSocket响应时发生错误: {str(e)}")
                        response["error"] = f"处理响应错误: {str(e)}"
                
                logger.info(f'星火对话响应状态: {response.get("status")}')
                logger.info(f'星火对话响应内容: {response.get("content", "")[:50]}...')
                return response
                
            except Exception as e:
                logger.error(f"星火对话异常: {str(e)}")
                return {"status": "error", "content": "", "error": str(e)}
            finally:
                logger.debug(f"星火对话请求完成，释放信号量，当前可用: {self.api_semaphore._value + 1}/{self.max_concurrent_requests}")