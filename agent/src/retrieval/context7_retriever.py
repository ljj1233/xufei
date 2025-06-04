# agent/retrieval/context7_retriever.py

from typing import List, Dict, Any, Optional, Union
import logging
import json
import asyncio
from abc import ABC

from ..core.system.config import AgentConfig
from .retriever import Retriever

logger = logging.getLogger(__name__)

class Context7Retriever(Retriever):
    """Context7检索器
    
    使用Context7 MCP获取外部库文档
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化Context7检索器
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        super().__init__(config)
        self.name = "context7_retriever"
        
        # MCP客户端
        self._mcp_client = None
        self._initialized = False
        
        # 缓存
        self._library_cache = {}
    
    async def _ensure_initialized(self):
        """确保MCP客户端已初始化"""
        if not self._initialized:
            try:
                # 导入MCP客户端
                from ..utils.mcp_client import MCPClient
                
                # 初始化客户端
                self._mcp_client = MCPClient()
                self._initialized = True
                logger.info("Context7 MCP客户端初始化成功")
                
            except ImportError as e:
                logger.error(f"导入MCP客户端失败: {e}")
                raise
    
    async def resolve_library_id(self, library_name: str) -> str:
        """解析库名称为Context7兼容的库ID
        
        Args:
            library_name: 库名称
            
        Returns:
            str: Context7兼容的库ID
        """
        await self._ensure_initialized()
        
        try:
            # 调用MCP resolve-library-id函数
            result = await self._mcp_client.call(
                "github.com/upstash/context7-mcp",
                "resolve-library-id",
                {"libraryName": library_name}
            )
            
            if isinstance(result, dict) and "context7CompatibleLibraryID" in result:
                library_id = result["context7CompatibleLibraryID"]
                logger.info(f"解析库名称 '{library_name}' 为 '{library_id}'")
                return library_id
            else:
                logger.error(f"解析库名称失败: {result}")
                return ""
                
        except Exception as e:
            logger.error(f"解析库名称异常: {e}")
            return ""
    
    async def get_library_docs(self, library_id: str, tokens: int = 6000, topic: Optional[str] = None) -> Dict[str, Any]:
        """获取库文档
        
        Args:
            library_id: Context7兼容的库ID
            tokens: 最大令牌数
            topic: 主题过滤器
            
        Returns:
            Dict: 文档结果
        """
        await self._ensure_initialized()
        
        # 检查缓存
        cache_key = f"{library_id}:{tokens}:{topic or 'all'}"
        if cache_key in self._library_cache:
            logger.info(f"从缓存获取库文档: {cache_key}")
            return self._library_cache[cache_key]
        
        try:
            # 准备参数
            params = {
                "context7CompatibleLibraryID": library_id,
                "tokens": tokens
            }
            
            if topic:
                params["topic"] = topic
            
            # 调用MCP get-library-docs函数
            result = await self._mcp_client.call(
                "github.com/upstash/context7-mcp",
                "get-library-docs",
                params
            )
            
            # 缓存结果
            self._library_cache[cache_key] = result
            
            logger.info(f"获取库文档成功: {library_id}, 大小: {len(str(result))} 字节")
            return result
                
        except Exception as e:
            logger.error(f"获取库文档异常: {e}")
            return {"error": str(e)}
    
    async def retrieve(self, query: str, library_name: Optional[str] = None, library_id: Optional[str] = None, tokens: int = 6000, topic: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """执行库文档检索
        
        Args:
            query: 查询文本
            library_name: 库名称，如果提供，将解析为库ID
            library_id: Context7兼容的库ID，优先于library_name
            tokens: 最大令牌数
            topic: 主题过滤器
            **kwargs: 其他参数
            
        Returns:
            List[Dict[str, Any]]: 检索结果列表
        """
        try:
            # 确定库ID
            target_library_id = library_id
            if not target_library_id and library_name:
                target_library_id = await self.resolve_library_id(library_name)
            
            if not target_library_id:
                logger.error("未提供有效的库ID或库名称")
                return []
            
            # 获取文档
            docs_result = await self.get_library_docs(target_library_id, tokens, topic)
            
            if "error" in docs_result:
                logger.error(f"检索文档失败: {docs_result['error']}")
                return []
            
            # 提取文档内容
            if "content" in docs_result:
                content = docs_result["content"]
                
                # 将文档内容转换为检索结果格式
                result = {
                    "text": content,
                    "metadata": {
                        "doc_id": target_library_id,
                        "library_id": target_library_id,
                        "topic": topic,
                        "tokens": tokens
                    },
                    "score": 1.0,  # 直接检索不计算相似度分数
                    "source": "context7"
                }
                
                logger.info(f"Context7检索成功: {target_library_id}")
                return [result]
            else:
                logger.warning(f"文档结果中没有内容: {docs_result}")
                return []
            
        except Exception as e:
            logger.error(f"Context7检索异常: {e}")
            return []
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Context7检索器不支持添加文档
        
        Args:
            documents: 文档列表
            
        Returns:
            bool: 始终返回False
        """
        logger.warning("Context7检索器不支持添加文档")
        return False 