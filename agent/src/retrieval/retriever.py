# agent/retrieval/retriever.py

from typing import List, Dict, Any, Optional, Union, Tuple
import logging
import asyncio
import time
from abc import ABC, abstractmethod

from ..core.system.config import AgentConfig

logger = logging.getLogger(__name__)

class Retriever(ABC):
    """检索器基类
    
    所有检索器的基类，定义基本接口
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化检索器
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        self.config = config or AgentConfig()
        self.name = "base_retriever"
    
    @abstractmethod
    async def retrieve(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """执行检索
        
        Args:
            query: 查询文本
            **kwargs: 其他参数
            
        Returns:
            List[Dict[str, Any]]: 检索结果列表
        """
        pass
    
    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """添加文档到检索器
        
        Args:
            documents: 文档列表，每个文档是一个字典，包含文本和元数据
            
        Returns:
            bool: 是否成功添加
        """
        pass


class VectorRetriever(Retriever):
    """向量检索器
    
    基于向量数据库的检索器
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化向量检索器
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        super().__init__(config)
        self.name = "vector_retriever"
        self.top_k = self.config.get_retriever_config("vector", "top_k", 5)
        self.score_threshold = self.config.get_retriever_config("vector", "score_threshold", 0.5)
        self.embedding_model = self.config.get_retriever_config("vector", "embedding_model", "openai")
        
        # 延迟导入向量数据库，避免启动时依赖问题
        self._vector_db_imported = False
        self._vector_db = None
    
    def _ensure_vector_db_imported(self):
        """确保向量数据库已导入"""
        if not self._vector_db_imported:
            try:
                from .vector_db import VectorDatabase
                
                # 初始化向量数据库
                self._vector_db = VectorDatabase(self.config)
                self._vector_db_imported = True
                
            except ImportError as e:
                logger.error(f"导入向量数据库失败: {e}")
                raise
    
    async def retrieve(self, query: str, top_k: Optional[int] = None, score_threshold: Optional[float] = None, **kwargs) -> List[Dict[str, Any]]:
        """执行向量检索
        
        Args:
            query: 查询文本
            top_k: 返回的结果数量
            score_threshold: 相似度阈值
            **kwargs: 其他参数
            
        Returns:
            List[Dict[str, Any]]: 检索结果列表
        """
        self._ensure_vector_db_imported()
        
        # 使用参数或默认值
        k = top_k or self.top_k
        threshold = score_threshold or self.score_threshold
        
        try:
            start_time = time.time()
            
            # 执行向量检索
            results = await self._vector_db.search(query, k, threshold)
            
            elapsed = time.time() - start_time
            logger.info(f"向量检索完成, 用时: {elapsed:.2f}s, 结果数量: {len(results)}")
            
            return results
            
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """添加文档到向量数据库
        
        Args:
            documents: 文档列表，每个文档是一个字典，包含文本和元数据
            
        Returns:
            bool: 是否成功添加
        """
        self._ensure_vector_db_imported()
        
        try:
            result = await self._vector_db.add_documents(documents)
            return result
            
        except Exception as e:
            logger.error(f"添加文档到向量数据库失败: {e}")
            return False


class KeywordRetriever(Retriever):
    """关键词检索器
    
    基于关键词匹配的检索器
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化关键词检索器
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        super().__init__(config)
        self.name = "keyword_retriever"
        self.max_results = self.config.get_retriever_config("keyword", "max_results", 10)
        self.min_score = self.config.get_retriever_config("keyword", "min_score", 0.3)
        
        # 存储文档
        self.documents = []
        
        # 初始化词典
        self.keyword_index = {}
    
    async def retrieve(self, query: str, max_results: Optional[int] = None, min_score: Optional[float] = None, **kwargs) -> List[Dict[str, Any]]:
        """执行关键词检索
        
        Args:
            query: 查询文本
            max_results: 最大结果数
            min_score: 最小分数阈值
            **kwargs: 其他参数
            
        Returns:
            List[Dict[str, Any]]: 检索结果列表
        """
        # 使用参数或默认值
        limit = max_results or self.max_results
        threshold = min_score or self.min_score
        
        try:
            start_time = time.time()
            
            # 提取查询中的关键词
            keywords = self._extract_keywords(query)
            
            # 如果没有关键词，返回空结果
            if not keywords:
                return []
            
            # 对每个文档评分
            scored_docs = []
            for doc_id, doc in enumerate(self.documents):
                score = self._score_document(doc, keywords)
                if score >= threshold:
                    scored_docs.append((doc_id, score))
            
            # 按分数排序
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            # 准备结果
            results = []
            for doc_id, score in scored_docs[:limit]:
                doc = self.documents[doc_id]
                results.append({
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "score": score,
                    "source": "keyword"
                })
            
            elapsed = time.time() - start_time
            logger.info(f"关键词检索完成, 用时: {elapsed:.2f}s, 结果数量: {len(results)}")
            
            return results
            
        except Exception as e:
            logger.error(f"关键词检索失败: {e}")
            return []
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """添加文档到关键词检索器
        
        Args:
            documents: 文档列表，每个文档是一个字典，包含文本和元数据
            
        Returns:
            bool: 是否成功添加
        """
        try:
            # 添加文档并更新索引
            start_idx = len(self.documents)
            self.documents.extend(documents)
            
            # 更新索引
            for i, doc in enumerate(documents, start=start_idx):
                keywords = self._extract_keywords(doc["text"])
                for kw in keywords:
                    if kw not in self.keyword_index:
                        self.keyword_index[kw] = []
                    self.keyword_index[kw].append(i)
            
            return True
            
        except Exception as e:
            logger.error(f"添加文档到关键词检索器失败: {e}")
            return False
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取文本中的关键词
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 关键词列表
        """
        # 简单实现，以空格分词并去除停用词
        # 在实际应用中，这里可以使用更复杂的分词和关键词提取算法
        stop_words = {"的", "了", "是", "在", "我", "你", "他", "她", "它", "这", "那", "和", "与", "或", "但", "如果", "因为", "所以", "而且", "如何", "什么", "为什么", "怎么", "哪里", "谁", "何时", "为何"}
        words = [word.lower() for word in text.split() if word.lower() not in stop_words]
        return words
    
    def _score_document(self, doc: Dict[str, Any], keywords: List[str]) -> float:
        """计算文档与关键词的匹配分数
        
        Args:
            doc: 文档
            keywords: 关键词列表
            
        Returns:
            float: 匹配分数
        """
        # 简单实现，计算关键词出现的比例
        doc_text = doc["text"].lower()
        matches = sum(1 for kw in keywords if kw.lower() in doc_text)
        return matches / len(keywords) if keywords else 0


class HybridRetriever(Retriever):
    """混合检索器
    
    结合多种检索方法的混合检索器
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化混合检索器
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        super().__init__(config)
        self.name = "hybrid_retriever"
        self.max_results = self.config.get_retriever_config("hybrid", "max_results", 10)
        self.vector_weight = self.config.get_retriever_config("hybrid", "vector_weight", 0.7)
        self.keyword_weight = self.config.get_retriever_config("hybrid", "keyword_weight", 0.3)
        
        # 初始化检索器
        self.vector_retriever = VectorRetriever(config)
        self.keyword_retriever = KeywordRetriever(config)
    
    async def retrieve(self, query: str, max_results: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """执行混合检索
        
        Args:
            query: 查询文本
            max_results: 最大结果数
            **kwargs: 其他参数
            
        Returns:
            List[Dict[str, Any]]: 检索结果列表
        """
        # 使用参数或默认值
        limit = max_results or self.max_results
        
        try:
            start_time = time.time()
            
            # 并行执行向量和关键词检索
            vector_results_task = self.vector_retriever.retrieve(query, top_k=limit)
            keyword_results_task = self.keyword_retriever.retrieve(query, max_results=limit)
            
            vector_results, keyword_results = await asyncio.gather(
                vector_results_task,
                keyword_results_task
            )
            
            # 合并和重新排序结果
            merged_results = self._merge_results(vector_results, keyword_results, limit)
            
            elapsed = time.time() - start_time
            logger.info(f"混合检索完成, 用时: {elapsed:.2f}s, 结果数量: {len(merged_results)}")
            
            return merged_results
            
        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            return []
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """添加文档到所有检索器
        
        Args:
            documents: 文档列表，每个文档是一个字典，包含文本和元数据
            
        Returns:
            bool: 是否成功添加
        """
        try:
            # 并行添加文档
            vector_task = self.vector_retriever.add_documents(documents)
            keyword_task = self.keyword_retriever.add_documents(documents)
            
            vector_result, keyword_result = await asyncio.gather(
                vector_task,
                keyword_task
            )
            
            # 只有全部成功，才返回成功
            return vector_result and keyword_result
            
        except Exception as e:
            logger.error(f"向混合检索器添加文档失败: {e}")
            return False
    
    def _merge_results(self, vector_results: List[Dict[str, Any]], keyword_results: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """合并向量和关键词检索结果
        
        Args:
            vector_results: 向量检索结果
            keyword_results: 关键词检索结果
            limit: 结果数量限制
            
        Returns:
            List[Dict[str, Any]]: 合并后的结果
        """
        # 创建文档ID到结果的映射
        result_map = {}
        
        # 处理向量检索结果
        for result in vector_results:
            doc_id = result.get("metadata", {}).get("doc_id")
            if doc_id:
                if doc_id not in result_map:
                    result_map[doc_id] = {
                        "text": result["text"],
                        "metadata": result["metadata"],
                        "vector_score": result["score"],
                        "keyword_score": 0.0,
                        "sources": ["vector"]
                    }
                else:
                    result_map[doc_id]["vector_score"] = result["score"]
                    if "vector" not in result_map[doc_id]["sources"]:
                        result_map[doc_id]["sources"].append("vector")
        
        # 处理关键词检索结果
        for result in keyword_results:
            doc_id = result.get("metadata", {}).get("doc_id")
            if doc_id:
                if doc_id not in result_map:
                    result_map[doc_id] = {
                        "text": result["text"],
                        "metadata": result["metadata"],
                        "vector_score": 0.0,
                        "keyword_score": result["score"],
                        "sources": ["keyword"]
                    }
                else:
                    result_map[doc_id]["keyword_score"] = result["score"]
                    if "keyword" not in result_map[doc_id]["sources"]:
                        result_map[doc_id]["sources"].append("keyword")
        
        # 计算最终分数
        results = []
        for doc_id, result in result_map.items():
            score = (
                self.vector_weight * result["vector_score"] +
                self.keyword_weight * result["keyword_score"]
            )
            results.append({
                "text": result["text"],
                "metadata": result["metadata"],
                "score": score,
                "vector_score": result["vector_score"],
                "keyword_score": result["keyword_score"],
                "sources": result["sources"]
            })
        
        # 按最终分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:limit] 