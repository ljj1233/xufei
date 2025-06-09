# agent/retrieval/vector_db.py

from typing import List, Dict, Any, Optional, Union, Tuple, Type
import logging
import os
import json
import asyncio
import time
import uuid
import numpy as np
from pathlib import Path

from ..core.system.config import AgentConfig

logger = logging.getLogger(__name__)

class VectorDatabase:
    """向量数据库
    
    管理文档嵌入向量的存储和检索
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化向量数据库
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        self.config = config or AgentConfig()
        
        # 从配置中加载参数
        self.db_type = self.config.get_db_config("vector", "db_type", "faiss")
        self.data_dir = self.config.get_db_config("vector", "data_dir", "data/vector_db")
        self.embedding_model = self.config.get_db_config("vector", "embedding_model", "openai")
        self.embedding_dim = self.config.get_db_config("vector", "embedding_dim", 1536)  # OpenAI默认维度
        self.distance_metric = self.config.get_db_config("vector", "distance_metric", "cosine")
        
        # 初始化数据存储
        self._documents = {}
        self._embeddings = {}
        self._metadata = {}
        self._index = None
        
        # 初始化嵌入服务
        self._embedding_service = None
        self._embedding_service_imported = False
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 初始化数据库
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        try:
            self._load_data()
            self._init_index()
            logger.info(f"向量数据库初始化完成，包含 {len(self._documents)} 个文档")
        except Exception as e:
            logger.error(f"初始化向量数据库失败: {e}")
            # 创建空数据库
            self._documents = {}
            self._embeddings = {}
            self._metadata = {}
            self._init_empty_index()
    
    def _init_index(self):
        """初始化索引"""
        if self.db_type == "faiss":
            self._init_faiss_index()
        else:
            logger.warning(f"不支持的数据库类型: {self.db_type}，使用内存索引")
            self._init_memory_index()
    
    def _init_empty_index(self):
        """初始化空索引"""
        if self.db_type == "faiss":
            self._init_empty_faiss_index()
        else:
            self._init_memory_index()
    
    def _init_faiss_index(self):
        """初始化FAISS索引"""
        try:
            import faiss
            
            # 如果有现有嵌入，则加载
            if self._embeddings:
                embeddings = np.array(list(self._embeddings.values()), dtype=np.float32)
                dim = embeddings.shape[1]
                
                if self.distance_metric == "cosine":
                    self._index = faiss.IndexFlatIP(dim)  # 内积索引（归一化后为余弦相似度）
                    # 归一化嵌入
                    faiss.normalize_L2(embeddings)
                else:
                    self._index = faiss.IndexFlatL2(dim)  # L2距离索引
                
                self._index.add(embeddings)
                logger.info(f"FAISS索引初始化完成，包含 {len(self._embeddings)} 个向量")
            else:
                self._init_empty_faiss_index()
                
        except ImportError as e:
            logger.error(f"导入FAISS失败: {e}，使用内存索引")
            self._init_memory_index()
    
    def _init_empty_faiss_index(self):
        """初始化空的FAISS索引"""
        try:
            import faiss
            
            if self.distance_metric == "cosine":
                self._index = faiss.IndexFlatIP(self.embedding_dim)  # 内积索引
            else:
                self._index = faiss.IndexFlatL2(self.embedding_dim)  # L2距离索引
                
            logger.info(f"创建了空的FAISS索引，维度: {self.embedding_dim}")
                
        except ImportError as e:
            logger.error(f"导入FAISS失败: {e}，使用内存索引")
            self._init_memory_index()
    
    def _init_memory_index(self):
        """初始化内存索引"""
        # 简单的内存索引，用于不支持FAISS的环境
        self._index = "memory"
        logger.info("使用内存索引")
    
    def _load_data(self):
        """加载数据"""
        # 加载文档
        docs_file = os.path.join(self.data_dir, "documents.json")
        if os.path.exists(docs_file):
            with open(docs_file, "r", encoding="utf-8") as f:
                self._documents = json.load(f)
        else:
            self._documents = {}
        
        # 加载元数据
        metadata_file = os.path.join(self.data_dir, "metadata.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)
        else:
            self._metadata = {}
        
        # 加载嵌入
        embeddings_file = os.path.join(self.data_dir, "embeddings.json")
        if os.path.exists(embeddings_file):
            with open(embeddings_file, "r", encoding="utf-8") as f:
                # 将嵌入从列表转换为numpy数组
                embeddings_dict = json.load(f)
                self._embeddings = {k: np.array(v, dtype=np.float32) for k, v in embeddings_dict.items()}
        else:
            self._embeddings = {}
    
    def _save_data(self):
        """保存数据"""
        # 保存文档
        docs_file = os.path.join(self.data_dir, "documents.json")
        with open(docs_file, "w", encoding="utf-8") as f:
            json.dump(self._documents, f, ensure_ascii=False)
        
        # 保存元数据
        metadata_file = os.path.join(self.data_dir, "metadata.json")
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, ensure_ascii=False)
        
        # 保存嵌入
        embeddings_file = os.path.join(self.data_dir, "embeddings.json")
        with open(embeddings_file, "w", encoding="utf-8") as f:
            # 将numpy数组转换为列表
            embeddings_dict = {k: v.tolist() for k, v in self._embeddings.items()}
            json.dump(embeddings_dict, f)
    
    def _ensure_embedding_service(self):
        """确保嵌入服务已初始化"""
        if not self._embedding_service_imported:
            # 尝试导入不同的嵌入服务
            try:
                if self.embedding_model == "openai":
                    from ..services.openai_service import OpenAIService
                    self._embedding_service = OpenAIService(self.config)
                elif self.embedding_model == "modelscope":
                    from ..services.modelscope_service import ModelScopeService
                    self._embedding_service = ModelScopeService(self.config)
                else:
                    raise ValueError(f"不支持的嵌入模型: {self.embedding_model}")
                
                self._embedding_service_imported = True
                logger.info(f"嵌入服务初始化成功，使用模型: {self.embedding_model}")
                
            except ImportError as e:
                logger.error(f"导入嵌入服务失败: {e}")
                raise
    
    async def create_embedding(self, text: str) -> np.ndarray:
        """创建文本的嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            np.ndarray: 嵌入向量
        """
        self._ensure_embedding_service()
        
        try:
            if self.embedding_model == "openai":
                result = await self._embedding_service.create_embedding(text)
                if result.get("status") == "success" and "embedding" in result:
                    embedding = np.array(result["embedding"], dtype=np.float32)
                    
                    # 对向量进行归一化（如果使用余弦相似度）
                    if self.distance_metric == "cosine":
                        norm = np.linalg.norm(embedding)
                        if norm > 0:
                            embedding = embedding / norm
                    
                    return embedding
                else:
                    logger.error(f"创建嵌入失败: {result.get('error', '未知错误')}")
                    raise ValueError(f"创建嵌入失败: {result.get('error', '未知错误')}")
            elif self.embedding_model == "modelscope":
                result = await self._embedding_service.create_embedding(text)
                if result.get("status") == "success" and "embedding" in result:
                    embedding = np.array(result["embedding"], dtype=np.float32)
                    
                    # 对向量进行归一化（如果使用余弦相似度）
                    if self.distance_metric == "cosine":
                        norm = np.linalg.norm(embedding)
                        if norm > 0:
                            embedding = embedding / norm
                    
                    return embedding
                else:
                    logger.error(f"创建嵌入失败: {result.get('error', '未知错误')}")
                    raise ValueError(f"创建嵌入失败: {result.get('error', '未知错误')}")
            else:
                raise ValueError(f"不支持的嵌入模型: {self.embedding_model}")
                
        except Exception as e:
            logger.error(f"创建嵌入异常: {e}")
            raise
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """添加文档到数据库
        
        Args:
            documents: 文档列表，每个文档是一个字典，包含文本和元数据
            
        Returns:
            bool: 是否成功添加
        """
        try:
            start_time = time.time()
            
            # 为每个文档生成ID（如果没有）
            for doc in documents:
                if "metadata" not in doc:
                    doc["metadata"] = {}
                
                if "doc_id" not in doc["metadata"]:
                    doc["metadata"]["doc_id"] = str(uuid.uuid4())
            
            # 创建嵌入向量
            embedding_tasks = [self.create_embedding(doc["text"]) for doc in documents]
            embeddings = await asyncio.gather(*embedding_tasks)
            
            # 更新索引
            new_ids = []
            for doc, embedding in zip(documents, embeddings):
                doc_id = doc["metadata"]["doc_id"]
                self._documents[doc_id] = doc["text"]
                self._metadata[doc_id] = doc["metadata"]
                self._embeddings[doc_id] = embedding
                new_ids.append(doc_id)
            
            # 更新索引
            self._update_index(new_ids)
            
            # 保存数据
            self._save_data()
            
            elapsed = time.time() - start_time
            logger.info(f"添加 {len(documents)} 个文档到向量数据库，用时: {elapsed:.2f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"添加文档到向量数据库失败: {e}")
            return False
    
    def _update_index(self, doc_ids: List[str]):
        """更新索引
        
        Args:
            doc_ids: 要更新的文档ID列表
        """
        if not doc_ids:
            return
        
        if isinstance(self._index, str) and self._index == "memory":
            # 内存索引不需要更新
            return
        
        try:
            import faiss
            
            # 获取嵌入
            embeddings = [self._embeddings[doc_id] for doc_id in doc_ids]
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # 如果使用余弦相似度，确保向量已归一化
            if self.distance_metric == "cosine":
                faiss.normalize_L2(embeddings_array)
            
            # 添加到索引
            self._index.add(embeddings_array)
            
        except Exception as e:
            logger.error(f"更新索引失败: {e}")
    
    async def search(self, query: str, top_k: int = 5, score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """搜索与查询最相似的文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            score_threshold: 相似度阈值
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        if not self._documents:
            return []
        
        try:
            # 创建查询嵌入
            query_embedding = await self.create_embedding(query)
            
            if isinstance(self._index, str) and self._index == "memory":
                # 使用内存索引进行搜索 - 确保这是异步的
                return await self._memory_search_async(query_embedding, top_k, score_threshold)
            else:
                # 使用FAISS索引进行搜索 - 确保这是异步的
                return await self._faiss_search_async(query_embedding, top_k, score_threshold)
                
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    async def _memory_search_async(self, query_embedding: np.ndarray, top_k: int, score_threshold: float) -> List[Dict[str, Any]]:
        """异步使用内存索引进行搜索
        
        Args:
            query_embedding: 查询嵌入
            top_k: 返回结果数量
            score_threshold: 相似度阈值
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        # 封装同步搜索代码到异步函数中
        def _sync_search():
            scores = {}
            
            for doc_id, embedding in self._embeddings.items():
                if self.distance_metric == "cosine":
                    # 计算余弦相似度
                    score = np.dot(query_embedding, embedding)
                else:
                    # 计算欧氏距离，并转换为相似度分数
                    dist = np.linalg.norm(query_embedding - embedding)
                    score = 1.0 / (1.0 + dist)
                
                scores[doc_id] = score
            
            # 按分数排序
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            # 过滤低于阈值的结果
            filtered_scores = [(doc_id, score) for doc_id, score in sorted_scores if score >= score_threshold]
            
            # 限制结果数量
            results = []
            for doc_id, score in filtered_scores[:top_k]:
                results.append({
                    "text": self._documents[doc_id],
                    "metadata": self._metadata[doc_id],
                    "score": float(score),
                    "source": "vector"
                })
            
            return results
        
        # 在异步运行同步代码
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_search)
    
    async def _faiss_search_async(self, query_embedding: np.ndarray, top_k: int, score_threshold: float) -> List[Dict[str, Any]]:
        """异步使用FAISS索引进行搜索
        
        Args:
            query_embedding: 查询嵌入
            top_k: 返回结果数量
            score_threshold: 相似度阈值
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        # 封装同步搜索代码到异步函数中
        def _sync_search():
            try:
                import faiss
                
                # 确保查询嵌入是2D数组
                query_array = query_embedding.reshape(1, -1).astype(np.float32)
                
                # 如果使用余弦相似度，确保向量已归一化
                if self.distance_metric == "cosine":
                    faiss.normalize_L2(query_array)
                
                # 执行搜索
                distances, indices = self._index.search(query_array, min(top_k, len(self._documents)))
                
                # 转换结果
                doc_ids = list(self._embeddings.keys())
                results = []
                
                for i, idx in enumerate(indices[0]):
                    if idx < 0 or idx >= len(doc_ids):
                        continue
                        
                    doc_id = doc_ids[idx]
                    
                    if self.distance_metric == "cosine":
                        # FAISS余弦相似度范围为[-1, 1]，转换为[0, 1]
                        score = float((distances[0][i] + 1) / 2)
                    else:
                        # 欧氏距离转换为相似度分数
                        score = float(1.0 / (1.0 + distances[0][i]))
                    
                    if score >= score_threshold:
                        results.append({
                            "text": self._documents[doc_id],
                            "metadata": self._metadata[doc_id],
                            "score": score,
                            "source": "vector"
                        })
                
                return results
            except Exception as e:
                logger.error(f"FAISS搜索失败: {e}")
                return []
        
        # 在异步运行同步代码
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_search) 