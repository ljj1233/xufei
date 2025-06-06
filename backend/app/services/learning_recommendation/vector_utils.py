"""
向量处理工具

提供文本向量化和向量相似度计算功能
"""

import os
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Union
import requests
import json
import time
from pathlib import Path

from app.services.learning_recommendation.logging_config import setup_logger, log_function

# 设置日志
logger = setup_logger("app.services.learning_recommendation.vector_utils")

class VectorUtils:
    """
    向量处理工具类，提供文本向量化和向量相似度计算功能
    """
    
    def __init__(self, 
                embedding_model: str = "text-embedding-ada-002", 
                api_key: Optional[str] = None,
                cache_dir: str = "data/embeddings_cache"):
        """
        初始化向量处理工具
        
        Args:
            embedding_model: 嵌入模型名称
            api_key: OpenAI API密钥，如不提供，将尝试从环境变量OPENAI_API_KEY获取
            cache_dir: 向量缓存目录
        """
        self.embedding_model = embedding_model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.cache_dir = cache_dir
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
        logger.info("向量处理工具初始化完成", extra={'request_id': 'system', 'user_id': 'system'})
    
    @log_function(logger)
    def compute_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        计算文本的向量嵌入
        
        Args:
            text: 输入文本
            use_cache: 是否使用缓存
            
        Returns:
            文本的向量表示
        """
        if not text.strip():
            logger.warning("尝试对空文本进行向量化", extra={'request_id': 'auto', 'user_id': 'system'})
            return [0.0] * 1536  # 返回零向量，维度与OpenAI的嵌入模型匹配
        
        # 生成缓存键
        cache_key = self._generate_cache_key(text)
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        # 如果启用缓存并且缓存文件存在，则从缓存加载
        if use_cache and os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cached_data = json.load(f)
                logger.info(f"从缓存加载向量嵌入: {cache_key}", 
                          extra={'request_id': 'auto', 'user_id': 'system'})
                return cached_data["embedding"]
            except Exception as e:
                logger.error(f"从缓存加载向量嵌入失败: {str(e)}", exc_info=True,
                            extra={'request_id': 'auto', 'user_id': 'system'})
        
        # 如果没有缓存或加载失败，则计算新的向量嵌入
        try:
            # 调用OpenAI API计算向量嵌入
            embedding = self._call_openai_embedding_api(text)
            
            # 缓存结果
            if use_cache:
                self._cache_embedding(cache_path, embedding, text)
                
            return embedding
        except Exception as e:
            logger.error(f"计算向量嵌入失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'auto', 'user_id': 'system'})
            
            # 在出错时返回全零向量
            return [0.0] * 1536
    
    @log_function(logger)
    def compute_embeddings_batch(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """
        批量计算多个文本的向量嵌入
        
        Args:
            texts: 输入文本列表
            use_cache: 是否使用缓存
            
        Returns:
            文本向量列表
        """
        results = []
        
        # 分批处理，避免API限制
        batch_size = 20
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            # 对批次中的每个文本计算嵌入
            batch_results = []
            for text in batch:
                embedding = self.compute_embedding(text, use_cache)
                batch_results.append(embedding)
                
            results.extend(batch_results)
            
            # 如果不是最后一批，添加短暂延迟避免API限制
            if i + batch_size < len(texts):
                time.sleep(0.5)
                
        return results
    
    @log_function(logger)
    def compute_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量之间的余弦相似度
        
        Args:
            vec1: 第一个向量
            vec2: 第二个向量
            
        Returns:
            余弦相似度 (-1到1之间)
        """
        try:
            # 转换为numpy数组
            arr1 = np.array(vec1)
            arr2 = np.array(vec2)
            
            # 计算余弦相似度
            dot_product = np.dot(arr1, arr2)
            norm1 = np.linalg.norm(arr1)
            norm2 = np.linalg.norm(arr2)
            
            # 避免除零错误
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"计算向量相似度失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'auto', 'user_id': 'system'})
            return 0.0
    
    @log_function(logger)
    def compute_similarity_batch(self, query_vec: List[float], candidate_vecs: List[List[float]]) -> List[Dict[str, Any]]:
        """
        计算查询向量与多个候选向量的相似度，并返回排序结果
        
        Args:
            query_vec: 查询向量
            candidate_vecs: 候选向量列表
            
        Returns:
            按相似度排序的结果列表，每项包含索引和相似度分数
        """
        results = []
        
        for i, vec in enumerate(candidate_vecs):
            similarity = self.compute_similarity(query_vec, vec)
            results.append({
                "index": i,
                "similarity": similarity
            })
            
        # 按相似度降序排序
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results
    
    def _generate_cache_key(self, text: str) -> str:
        """生成文本的缓存键"""
        import hashlib
        # 使用MD5哈希作为缓存键
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _cache_embedding(self, cache_path: str, embedding: List[float], text: str) -> None:
        """缓存向量嵌入"""
        try:
            cache_data = {
                "model": self.embedding_model,
                "text": text[:100] + "..." if len(text) > 100 else text,  # 只保存部分文本以节省空间
                "embedding": embedding,
                "created_at": time.time()
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
                
            logger.debug(f"向量嵌入已缓存: {os.path.basename(cache_path)}", 
                        extra={'request_id': 'auto', 'user_id': 'system'})
        except Exception as e:
            logger.error(f"缓存向量嵌入失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'auto', 'user_id': 'system'})
    
    def _call_openai_embedding_api(self, text: str) -> List[float]:
        """调用OpenAI API计算向量嵌入"""
        if not self.api_key:
            raise ValueError("未提供OpenAI API密钥")
            
        # 准备API请求
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": self.embedding_model,
            "input": text
        }
        
        # 发送请求
        response = requests.post(url, headers=headers, json=data)
        
        # 检查响应状态
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code} - {response.text}")
            
        # 解析响应
        result = response.json()
        embedding = result["data"][0]["embedding"]
        
        return embedding

# 创建默认向量工具实例
vector_utils = VectorUtils()

# 导出函数，方便直接调用
compute_embedding = vector_utils.compute_embedding
compute_embeddings_batch = vector_utils.compute_embeddings_batch
compute_similarity = vector_utils.compute_similarity
compute_similarity_batch = vector_utils.compute_similarity_batch 