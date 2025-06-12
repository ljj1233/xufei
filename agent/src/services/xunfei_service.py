# agent/services/xunfei_service.py

from typing import Dict, Optional
import time
import hashlib
import base64
import hmac
import json
import requests
from urllib.parse import urlparse

from ..core.system.config import AgentConfig


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
        # 从URL中提取域名和路径
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        path = parsed_url.path or '/v1/iat'
        
        # 根据不同API构建适当的请求路径
        if 'ise' in path:
            request_line = 'POST /v1/ise HTTP/1.1'
        elif 'iat' in path:
            request_line = 'POST /v1/iat HTTP/1.1'
        elif 'emotion' in path:
            request_line = 'POST /v1/emotion HTTP/1.1'
        else:
            # 默认情况
            request_line = f'POST {path} HTTP/1.1'
        
        now = int(time.time())
        signature_origin = f'host: {host}\ndate: {now}\n{request_line}'
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
            'host': host
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
        
        # 确保URL使用正确的域名
        if 'xf-yun.cn' in url:
            url = url.replace('xf-yun.cn', 'xfyun.cn')
            print(f"已修正IAT URL: {url}")
        
        auth_params = self._create_auth_params(url)
        
        headers = {
            'authorization': auth_params['authorization'],
            'date': auth_params['date'],
            'host': auth_params['host'],
            'content-type': 'application/x-www-form-urlencoded; charset=utf-8',
            'Accept': 'application/json'
        }
        
        # 检查音频数据大小
        audio_size_kb = len(audio_data) / 1024
        print(f"音频数据大小: {audio_size_kb:.2f} KB")
        
        # 如果音频大于1MB，尝试压缩或截断
        max_size = 1024 * 1024  # 1MB
        if len(audio_data) > max_size:
            print(f"警告: 音频数据大小({audio_size_kb:.2f}KB)超过1MB，可能会导致请求失败")
            # 这里可以添加音频压缩逻辑，但为简单起见，我们只截断数据
            audio_data = audio_data[:max_size]
            print(f"已截断音频数据至 {len(audio_data)/1024:.2f} KB")
        
        # Base64编码音频数据
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # 构建请求参数 - 使用讯飞API要求的格式
        data = {
            'audio': audio_base64,
            'format': 'wav',      # 音频格式
            'rate': 16000,        # 采样率16k
            'channel': 1,         # 单声道
            'lang': 'cn',         # 中文
            'aue': 'raw',         # 原始编码
            'vad_eos': 10000      # 静音检测超时时间，默认5000ms
        }
        
        try:
            print(f"\n正在发送请求到讯飞语音识别API: {url}")
            print(f"请求头: host={auth_params['host']}, date={auth_params['date']}")
            print(f"请求参数: format={data['format']}, rate={data['rate']}, channel={data['channel']}, lang={data['lang']}")
            
            # 发送请求
            response = requests.post(url, headers=headers, data=data, timeout=30)
            
            # 输出详细的请求和响应信息
            print(f"请求URL: {url}")
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容类型: {response.headers.get('Content-Type', '未知')}")
            
            # 检查HTTP状态码
            if response.status_code != 200:
                print(f"HTTP错误: {response.status_code}")
                print(f"响应头: {dict(response.headers)}")
                print(f"响应内容: {response.text[:500]}")
                return ''
            
            # 尝试解析JSON响应
            try:
                result = response.json()
                print(f"响应JSON: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
                
                if result.get('code') == '0':
                    # 成功识别
                    text_result = result.get('data', '')
                    print(f"语音识别成功，文本长度: {len(text_result)}")
                    return text_result
                else:
                    # API返回错误
                    error_code = result.get('code', '未知')
                    error_desc = result.get('desc', '未知错误')
                    print(f"语音识别失败: {error_desc} (错误码: {error_code})")
                    print(f"完整响应: {json.dumps(result, ensure_ascii=False)}")
                    return ''
            except ValueError as e:
                # 非JSON响应
                print(f"响应不是有效的JSON: {e}")
                print(f"响应内容: {response.text[:500]}")
                return ''
                
        except requests.exceptions.Timeout:
            print("请求超时，讯飞API没有在指定时间内响应")
            return ''
        except requests.exceptions.ConnectionError as e:
            print(f"连接错误: {e}")
            return ''
        except Exception as e:
            print(f"语音识别请求异常: {e}")
            import traceback
            traceback.print_exc()
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
            'content-type': 'application/x-www-form-urlencoded; charset=utf-8',
            'Accept': 'application/json'
        }
        
        # 构建请求参数
        data = {
            'audio': base64.b64encode(audio_data).decode('utf-8'),
            'category': 'read_sentence',  # 评测模式
            'language': 'cn',  # 语言
            'format': 'wav',
            'sample_rate': 16000,
            'bits': 16,
            'channel': 1
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            
            # 检查HTTP状态码
            if response.status_code != 200:
                print(f"语音评测HTTP错误: {response.status_code} - {response.text}")
                return {}
            
            # 尝试解析JSON响应
            try:
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
            except ValueError:
                print(f"语音评测响应不是有效的JSON: {response.text[:200]}")
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
        
        # 确保URL使用正确的域名
        if 'xf-yun.cn' in url:
            url = url.replace('xf-yun.cn', 'xfyun.cn')
            print(f"已修正情感分析URL: {url}")
        
        auth_params = self._create_auth_params(url)
        
        headers = {
            'authorization': auth_params['authorization'],
            'date': auth_params['date'],
            'host': auth_params['host'],
            'content-type': 'application/x-www-form-urlencoded; charset=utf-8',
            'Accept': 'application/json'
        }
        
        # 检查音频数据大小
        audio_size_kb = len(audio_data) / 1024
        print(f"情感分析音频数据大小: {audio_size_kb:.2f} KB")
        
        # 如果音频大于1MB，尝试压缩或截断
        max_size = 1024 * 1024  # 1MB
        if len(audio_data) > max_size:
            print(f"警告: 音频数据大小({audio_size_kb:.2f}KB)超过1MB，可能会导致请求失败")
            # 这里可以添加音频压缩逻辑，但为简单起见，我们只截断数据
            audio_data = audio_data[:max_size]
            print(f"已截断音频数据至 {len(audio_data)/1024:.2f} KB")
        
        # 构建请求参数
        data = {
            'audio': base64.b64encode(audio_data).decode('utf-8'),
            'format': 'wav',
            'sample_rate': 16000,
            'bits': 16,
            'channel': 1
        }
        
        try:
            print(f"\n正在发送请求到讯飞情感分析API: {url}")
            print(f"请求头: host={auth_params['host']}, date={auth_params['date']}")
            print(f"请求参数: format={data['format']}, sample_rate={data['sample_rate']}, bits={data['bits']}, channel={data['channel']}")
            
            # 发送请求
            response = requests.post(url, headers=headers, data=data, timeout=30)
            
            # 输出详细的请求和响应信息
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容类型: {response.headers.get('Content-Type', '未知')}")
            
            # 检查HTTP状态码
            if response.status_code != 200:
                print(f"情感分析HTTP错误: {response.status_code}")
                print(f"响应头: {dict(response.headers)}")
                print(f"响应内容: {response.text[:500]}")
                return {}
            
            # 尝试解析JSON响应
            try:
                result = response.json()
                print(f"情感分析响应: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
                
                if result.get('code') == '0':
                    # 成功分析
                    emotion_type = result.get('emotion', '中性')
                    confidence = result.get('confidence', 0.0)
                    print(f"情感分析成功: 情感类型={emotion_type}, 置信度={confidence}")
                    return {
                        'emotion': emotion_type,  # 情感类型
                        'confidence': confidence  # 置信度
                    }
                else:
                    # API返回错误
                    error_code = result.get('code', '未知')
                    error_desc = result.get('desc', '未知错误')
                    print(f"情感分析失败: {error_desc} (错误码: {error_code})")
                    print(f"完整响应: {json.dumps(result, ensure_ascii=False)}")
                    return {}
            except ValueError as e:
                # 非JSON响应
                print(f"情感分析响应不是有效的JSON: {e}")
                print(f"响应内容: {response.text[:500]}")
                return {}
                
        except requests.exceptions.Timeout:
            print("请求超时，讯飞情感分析API没有在指定时间内响应")
            return {}
        except requests.exceptions.ConnectionError as e:
            print(f"连接错误: {e}")
            return {}
        except Exception as e:
            print(f"情感分析请求异常: {e}")
            import traceback
            traceback.print_exc()
            return {}