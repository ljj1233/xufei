# agent/services/openai_service.py

from typing import Dict, List, Optional, Any, Union
import logging
import json
import asyncio
from openai import AsyncOpenAI
from ..core.system.config import AgentConfig

logger = logging.getLogger(__name__)

class OpenAIService:
    """OpenAI API服务
    
    封装与OpenAI API的交互
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化OpenAI服务
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        self.config = config or AgentConfig()
        
        # 从配置中加载OpenAI API参数
        self.api_key = self.config.get_service_config("openai", "api_key", "")
        self.api_base = self.config.get_service_config("openai", "api_base", None)
        self.default_model = self.config.get_service_config("openai", "default_model", "Qwen/Qwen2.5-7B-Instruct")
        
        # 初始化客户端
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
        
        # 检查必要的配置是否存在
        if not self.api_key:
            logger.warning("OpenAI API配置不完整，某些功能可能无法正常工作")
    
    async def chat_completion(self, 
                             messages: List[Dict[str, str]], 
                             model: Optional[str] = None, 
                             temperature: float = 0.7,
                             max_tokens: int = 1000,
                             stream: bool = False) -> Dict[str, Any]:
        """异步获取聊天完成结果
        
        Args:
            messages: 对话历史消息列表
            model: 模型名称，如果为None则使用默认模型
            temperature: 采样温度
            max_tokens: 最大生成的令牌数量
            stream: 是否使用流式响应
            
        Returns:
            Dict: 完成结果
        """
        try:
            # 使用提供的模型或默认模型
            model_name = model or self.default_model
            
            logger.info(f"请求OpenAI API, 模型: {model_name}, 温度: {temperature}, 最大token: {max_tokens}")
            
            # 发送请求
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            # 处理流式响应
            if stream:
                collected_content = []
                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        collected_content.append(content)
                        yield content
                
                # 返回完整内容
                return {
                    "content": "".join(collected_content),
                    "role": "assistant",
                    "status": "success"
                }
            else:
                # 处理非流式响应
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    logger.info(f"OpenAI API返回成功，内容长度: {len(content)}")
                    return {
                        "content": content,
                        "role": "assistant",
                        "status": "success",
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens
                        } if hasattr(response, 'usage') else {}
                    }
                else:
                    logger.warning("OpenAI API返回空结果")
                    return {
                        "content": "",
                        "status": "error",
                        "error": "API返回空结果"
                    }
        
        except Exception as e:
            logger.error(f"OpenAI API请求异常: {e}")
            return {
                "content": "",
                "status": "error",
                "error": str(e)
            }
    
    async def function_calling(self, 
                              messages: List[Dict[str, str]], 
                              functions: List[Dict[str, Any]],
                              model: Optional[str] = None,
                              temperature: float = 0.7) -> Dict[str, Any]:
        """异步使用函数调用功能
        
        Args:
            messages: 对话历史消息列表
            functions: 可用函数的定义列表
            model: 模型名称，如果为None则使用默认模型
            temperature: 采样温度
            
        Returns:
            Dict: 函数调用结果
        """
        try:
            # 使用提供的模型或默认模型
            model_name = model or self.default_model
            
            logger.info(f"请求OpenAI API函数调用, 模型: {model_name}, 函数数量: {len(functions)}")
            
            # 发送请求
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                functions=functions,
                function_call="auto",
                temperature=temperature
            )
            
            # 解析响应
            if response.choices and len(response.choices) > 0:
                message = response.choices[0].message
                
                # 检查是否有函数调用
                if message.function_call:
                    function_name = message.function_call.name
                    function_args = json.loads(message.function_call.arguments)
                    
                    logger.info(f"函数调用成功: {function_name}")
                    
                    return {
                        "type": "function_call",
                        "function_name": function_name,
                        "arguments": function_args,
                        "status": "success",
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens
                        } if hasattr(response, 'usage') else {}
                    }
                else:
                    # 没有函数调用，返回普通内容
                    content = message.content
                    
                    logger.info("函数调用API返回普通内容")
                    
                    return {
                        "type": "content",
                        "content": content,
                        "status": "success",
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens
                        } if hasattr(response, 'usage') else {}
                    }
            else:
                logger.warning("OpenAI API返回空结果")
                return {
                    "type": "error",
                    "content": "",
                    "status": "error",
                    "error": "API返回空结果"
                }
        
        except Exception as e:
            logger.error(f"OpenAI API函数调用请求异常: {e}")
            return {
                "type": "error",
                "content": "",
                "status": "error",
                "error": str(e)
            }
    
    async def create_embedding(self, text: Union[str, List[str]], model: str = "text-embedding-ada-002") -> Dict[str, Any]:
        """异步创建文本嵌入向量
        
        Args:
            text: 输入文本或文本列表
            model: 模型名称
            
        Returns:
            Dict: 嵌入结果
        """
        try:
            logger.info(f"请求OpenAI嵌入API, 模型: {model}")
            
            # 发送请求
            response = await self.client.embeddings.create(
                model=model,
                input=text
            )
            
            # 解析响应
            if response.data and len(response.data) > 0:
                # 提取嵌入向量
                embeddings = [item.embedding for item in response.data]
                
                # 如果只有一个文本，返回单个嵌入向量
                if isinstance(text, str) or (isinstance(text, list) and len(text) == 1):
                    embedding = embeddings[0] if embeddings else []
                    logger.info(f"嵌入创建成功，维度: {len(embedding)}")
                    return {
                        "embedding": embedding,
                        "status": "success",
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "total_tokens": response.usage.total_tokens
                        } if hasattr(response, 'usage') else {}
                    }
                # 如果有多个文本，返回多个嵌入向量
                else:
                    logger.info(f"多个嵌入创建成功，数量: {len(embeddings)}")
                    return {
                        "embeddings": embeddings,
                        "status": "success",
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "total_tokens": response.usage.total_tokens
                        } if hasattr(response, 'usage') else {}
                    }
            else:
                logger.warning("OpenAI API返回空嵌入结果")
                return {
                    "embedding": [],
                    "status": "error",
                    "error": "API返回空嵌入结果"
                }
        
        except Exception as e:
            logger.error(f"OpenAI API嵌入请求异常: {e}")
            return {
                "embedding": [],
                "status": "error",
                "error": str(e)
            } 