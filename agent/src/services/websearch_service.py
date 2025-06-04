# agent/services/websearch_service.py

from typing import Dict, List, Optional, Any
import logging
import aiohttp
import asyncio
import json
import re
import time
from urllib.parse import quote

from ..core.system.config import AgentConfig

logger = logging.getLogger(__name__)

class WebSearchService:
    """Web搜索服务
    
    提供网络搜索功能，支持多个搜索引擎
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化Web搜索服务
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        self.config = config or AgentConfig()
        
        # 从配置中加载参数
        self.serper_api_key = self.config.get_service_config("websearch", "serper_api_key", "")
        self.serpapi_api_key = self.config.get_service_config("websearch", "serpapi_api_key", "")
        self.bing_api_key = self.config.get_service_config("websearch", "bing_api_key", "")
        self.default_engine = self.config.get_service_config("websearch", "default_engine", "serper")
        self.max_results = self.config.get_service_config("websearch", "max_results", 5)
        self.request_timeout = self.config.get_service_config("websearch", "request_timeout", 30)
        
        self.serper_url = "https://google.serper.dev/search"
        self.serpapi_url = "https://serpapi.com/search"
        self.bing_url = "https://api.bing.microsoft.com/v7.0/search"
        
        # 检查API密钥
        if self.default_engine == "serper" and not self.serper_api_key:
            logger.warning("Serper API密钥未配置，搜索功能可能无法正常工作")
        elif self.default_engine == "serpapi" and not self.serpapi_api_key:
            logger.warning("SerpAPI API密钥未配置，搜索功能可能无法正常工作")
        elif self.default_engine == "bing" and not self.bing_api_key:
            logger.warning("Bing API密钥未配置，搜索功能可能无法正常工作")
    
    async def search(self, 
                    query: str, 
                    engine: Optional[str] = None, 
                    num_results: Optional[int] = None,
                    language: str = "zh",
                    country: str = "cn") -> Dict[str, Any]:
        """执行网络搜索
        
        Args:
            query: 搜索查询
            engine: 搜索引擎，可选值：serper, serpapi, bing
            num_results: 结果数量
            language: 语言代码
            country: 国家代码
            
        Returns:
            Dict: 搜索结果
        """
        # 使用指定的引擎或默认引擎
        search_engine = engine or self.default_engine
        result_limit = num_results or self.max_results
        
        logger.info(f"执行Web搜索: '{query}', 引擎: {search_engine}, 结果数量: {result_limit}")
        
        try:
            if search_engine == "serper":
                search_results = await self._search_serper(query, result_limit, language, country)
            elif search_engine == "serpapi":
                search_results = await self._search_serpapi(query, result_limit, language, country)
            elif search_engine == "bing":
                search_results = await self._search_bing(query, result_limit, language, country)
            else:
                logger.error(f"不支持的搜索引擎: {search_engine}")
                search_results = {
                    "status": "error",
                    "error": f"不支持的搜索引擎: {search_engine}"
                }
            
            return search_results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "results": []
            }
    
    async def _search_serper(self, query: str, num_results: int, language: str, country: str) -> Dict[str, Any]:
        """使用Serper API搜索
        
        Args:
            query: 搜索查询
            num_results: 结果数量
            language: 语言代码
            country: 国家代码
            
        Returns:
            Dict: 搜索结果
        """
        if not self.serper_api_key:
            return {"status": "error", "error": "Serper API密钥未配置", "results": []}
        
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "gl": country,
            "hl": language,
            "num": num_results
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.serper_url,
                    headers=headers,
                    json=payload,
                    timeout=self.request_timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Serper API错误: {response.status}, {error_text}")
                        return {
                            "status": "error",
                            "error": f"API返回错误: {response.status}",
                            "results": []
                        }
                    
                    data = await response.json()
                    
                    # 处理搜索结果
                    processed_results = self._process_serper_results(data, num_results)
                    
                    return {
                        "status": "success",
                        "engine": "serper",
                        "results": processed_results
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"Serper API请求错误: {e}")
            return {
                "status": "error",
                "error": f"API请求错误: {str(e)}",
                "results": []
            }
    
    def _process_serper_results(self, data: Dict, limit: int) -> List[Dict]:
        """处理Serper API结果
        
        Args:
            data: API返回的数据
            limit: 结果数量限制
            
        Returns:
            List[Dict]: 处理后的结果列表
        """
        results = []
        
        # 处理自然结果
        if "organic" in data:
            for item in data["organic"][:limit]:
                result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "organic",
                    "position": item.get("position", 0)
                }
                results.append(result)
        
        # 处理知识面板
        if "knowledgeGraph" in data and len(results) < limit:
            kg = data["knowledgeGraph"]
            if isinstance(kg, dict):
                result = {
                    "title": kg.get("title", ""),
                    "description": kg.get("description", ""),
                    "source": "knowledge_graph"
                }
                # 添加其他可能的字段
                if "attributes" in kg:
                    result["attributes"] = kg["attributes"]
                
                results.append(result)
        
        # 处理相关问题
        if "relatedSearches" in data and len(results) < limit:
            for item in data["relatedSearches"][:limit - len(results)]:
                result = {
                    "query": item.get("query", ""),
                    "source": "related_search"
                }
                results.append(result)
        
        return results[:limit]
    
    async def _search_serpapi(self, query: str, num_results: int, language: str, country: str) -> Dict[str, Any]:
        """使用SerpAPI搜索
        
        Args:
            query: 搜索查询
            num_results: 结果数量
            language: 语言代码
            country: 国家代码
            
        Returns:
            Dict: 搜索结果
        """
        if not self.serpapi_api_key:
            return {"status": "error", "error": "SerpAPI密钥未配置", "results": []}
        
        params = {
            "q": query,
            "api_key": self.serpapi_api_key,
            "engine": "google",
            "hl": language,
            "gl": country,
            "num": num_results
        }
        
        query_string = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
        url = f"{self.serpapi_url}?{query_string}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.request_timeout) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"SerpAPI错误: {response.status}, {error_text}")
                        return {
                            "status": "error",
                            "error": f"API返回错误: {response.status}",
                            "results": []
                        }
                    
                    data = await response.json()
                    
                    # 处理搜索结果
                    processed_results = self._process_serpapi_results(data, num_results)
                    
                    return {
                        "status": "success",
                        "engine": "serpapi",
                        "results": processed_results
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"SerpAPI请求错误: {e}")
            return {
                "status": "error",
                "error": f"API请求错误: {str(e)}",
                "results": []
            }
    
    def _process_serpapi_results(self, data: Dict, limit: int) -> List[Dict]:
        """处理SerpAPI结果
        
        Args:
            data: API返回的数据
            limit: 结果数量限制
            
        Returns:
            List[Dict]: 处理后的结果列表
        """
        results = []
        
        # 处理自然结果
        if "organic_results" in data:
            for item in data["organic_results"][:limit]:
                result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "organic",
                    "position": item.get("position", 0)
                }
                results.append(result)
        
        # 处理知识图谱
        if "knowledge_graph" in data and len(results) < limit:
            kg = data["knowledge_graph"]
            if isinstance(kg, dict):
                result = {
                    "title": kg.get("title", ""),
                    "description": kg.get("description", ""),
                    "source": "knowledge_graph"
                }
                # 添加其他可能的字段
                if "attributes" in kg:
                    result["attributes"] = kg["attributes"]
                
                results.append(result)
        
        # 处理相关问题
        if "related_questions" in data and len(results) < limit:
            for item in data["related_questions"][:limit - len(results)]:
                result = {
                    "question": item.get("question", ""),
                    "answer": item.get("answer", ""),
                    "source": "related_question"
                }
                results.append(result)
        
        return results[:limit]
    
    async def _search_bing(self, query: str, num_results: int, language: str, country: str) -> Dict[str, Any]:
        """使用Bing API搜索
        
        Args:
            query: 搜索查询
            num_results: 结果数量
            language: 语言代码
            country: 国家代码
            
        Returns:
            Dict: 搜索结果
        """
        if not self.bing_api_key:
            return {"status": "error", "error": "Bing API密钥未配置", "results": []}
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.bing_api_key
        }
        
        params = {
            "q": query,
            "count": num_results,
            "setLang": language,
            "cc": country,
            "mkt": f"{language}-{country}"
        }
        
        query_string = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
        url = f"{self.bing_url}?{query_string}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=self.request_timeout) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Bing API错误: {response.status}, {error_text}")
                        return {
                            "status": "error",
                            "error": f"API返回错误: {response.status}",
                            "results": []
                        }
                    
                    data = await response.json()
                    
                    # 处理搜索结果
                    processed_results = self._process_bing_results(data, num_results)
                    
                    return {
                        "status": "success",
                        "engine": "bing",
                        "results": processed_results
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"Bing API请求错误: {e}")
            return {
                "status": "error",
                "error": f"API请求错误: {str(e)}",
                "results": []
            }
    
    def _process_bing_results(self, data: Dict, limit: int) -> List[Dict]:
        """处理Bing API结果
        
        Args:
            data: API返回的数据
            limit: 结果数量限制
            
        Returns:
            List[Dict]: 处理后的结果列表
        """
        results = []
        
        # 处理网页结果
        if "webPages" in data and "value" in data["webPages"]:
            for item in data["webPages"]["value"][:limit]:
                result = {
                    "title": item.get("name", ""),
                    "link": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "web",
                    "id": item.get("id", "")
                }
                results.append(result)
        
        # 处理实体结果
        if "entities" in data and "value" in data["entities"] and len(results) < limit:
            for item in data["entities"]["value"][:limit - len(results)]:
                result = {
                    "title": item.get("name", ""),
                    "description": item.get("description", ""),
                    "source": "entity"
                }
                if "image" in item and "thumbnailUrl" in item["image"]:
                    result["image"] = item["image"]["thumbnailUrl"]
                    
                results.append(result)
        
        # 处理相关搜索
        if "relatedSearches" in data and "value" in data["relatedSearches"] and len(results) < limit:
            for item in data["relatedSearches"]["value"][:limit - len(results)]:
                result = {
                    "text": item.get("text", ""),
                    "displayText": item.get("displayText", ""),
                    "source": "related_search"
                }
                results.append(result)
        
        return results[:limit]
    
    async def multi_engine_search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """使用多个搜索引擎执行搜索，并合并结果
        
        Args:
            query: 搜索查询
            num_results: 每个引擎的结果数量
            
        Returns:
            Dict: 合并后的搜索结果
        """
        engines = []
        
        # 添加配置了API密钥的搜索引擎
        if self.serper_api_key:
            engines.append("serper")
        if self.serpapi_api_key:
            engines.append("serpapi")
        if self.bing_api_key:
            engines.append("bing")
        
        # 如果没有配置任何API密钥，返回错误
        if not engines:
            return {
                "status": "error",
                "error": "未配置任何搜索引擎API密钥",
                "results": []
            }
        
        # 并行执行搜索
        tasks = [self.search(query, engine, num_results) for engine in engines]
        search_results = await asyncio.gather(*tasks)
        
        # 合并结果
        all_results = []
        for result in search_results:
            if result.get("status") == "success" and "results" in result:
                all_results.extend(result["results"])
        
        # 去除重复项（基于URL或标题）
        unique_results = self._remove_duplicates(all_results)
        
        return {
            "status": "success",
            "engine": "multi",
            "results": unique_results[:num_results],
            "total_engines": len(engines),
            "engines_used": engines
        }
    
    def _remove_duplicates(self, results: List[Dict]) -> List[Dict]:
        """移除重复的搜索结果
        
        Args:
            results: 搜索结果列表
            
        Returns:
            List[Dict]: 去重后的结果列表
        """
        unique_results = []
        urls = set()
        titles = set()
        
        for result in results:
            url = result.get("link", "")
            title = result.get("title", "")
            
            # 如果URL和标题都没有出现过，添加到结果中
            if (not url or url not in urls) and (not title or title not in titles):
                if url:
                    urls.add(url)
                if title:
                    titles.add(title)
                unique_results.append(result)
        
        return unique_results
    
    def extract_search_query(self, question: str) -> str:
        """从问题中提取搜索查询
        
        Args:
            question: 问题文本
            
        Returns:
            str: 优化后的搜索查询
        """
        # 移除不必要的词语
        stop_words = ["你能", "请", "能否", "帮我", "告诉我", "查询", "搜索", "寻找", "查找", "了解", "获取", "吗", "呢"]
        query = question
        
        for word in stop_words:
            query = query.replace(word, "")
        
        # 移除标点符号
        query = re.sub(r'[^\w\s]', '', query)
        
        # 移除多余的空格
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query 