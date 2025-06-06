"""
资源管理服务

负责管理学习资源的增删改查和向量索引
"""

import os
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import time
import pandas as pd
from pathlib import Path

from app.services.learning_recommendation.logging_config import setup_logger, log_function
from app.services.learning_recommendation.models import LearningResource, ResourceType, DifficultyLevel, TimeCommitment
from app.services.learning_recommendation.vector_utils import compute_embedding, compute_similarity, compute_embeddings_batch

# 设置日志
logger = setup_logger("app.services.learning_recommendation.resource_management")

class ResourceManagementService:
    """资源管理服务，负责学习资源的CRUD和向量索引"""
    
    def __init__(self, 
                resources_file: str = "data/learning_resources.json",
                vector_index_file: str = "data/vector_index.json"):
        """
        初始化资源管理服务
        
        Args:
            resources_file: 资源数据文件路径
            vector_index_file: 向量索引文件路径
        """
        self.resources_file = resources_file
        self.vector_index_file = vector_index_file
        self.resources = {}  # 资源字典，键为资源ID
        self.vector_index = {}  # 向量索引，键为资源ID
        
        # 加载资源和向量索引
        self._load_resources()
        self._load_vector_index()
        
        logger.info("资源管理服务初始化完成", extra={'request_id': 'system', 'user_id': 'system'})
    
    @log_function(logger)
    def _load_resources(self) -> None:
        """从文件加载资源数据"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.resources_file), exist_ok=True)
            
            if os.path.exists(self.resources_file):
                with open(self.resources_file, 'r', encoding='utf-8') as f:
                    self.resources = json.load(f)
                logger.info(f"成功从 {self.resources_file} 加载学习资源数据，共 {len(self.resources)} 条资源", 
                           extra={'request_id': 'system', 'user_id': 'system'})
            else:
                # 创建空的资源文件
                self.resources = {}
                self._save_resources()
                logger.info("创建了空的学习资源数据文件", extra={'request_id': 'system', 'user_id': 'system'})
        except Exception as e:
            logger.error(f"加载学习资源数据失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'system', 'user_id': 'system'})
            # 初始化空字典
            self.resources = {}
    
    @log_function(logger)
    def _save_resources(self) -> None:
        """保存资源数据到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.resources_file), exist_ok=True)
            
            with open(self.resources_file, 'w', encoding='utf-8') as f:
                json.dump(self.resources, f, ensure_ascii=False, indent=2)
                
            logger.info(f"学习资源数据已保存到 {self.resources_file}，共 {len(self.resources)} 条资源",
                       extra={'request_id': 'system', 'user_id': 'system'})
        except Exception as e:
            logger.error(f"保存学习资源数据失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'system', 'user_id': 'system'})
    
    @log_function(logger)
    def _load_vector_index(self) -> None:
        """从文件加载向量索引"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.vector_index_file), exist_ok=True)
            
            if os.path.exists(self.vector_index_file):
                with open(self.vector_index_file, 'r', encoding='utf-8') as f:
                    self.vector_index = json.load(f)
                logger.info(f"成功从 {self.vector_index_file} 加载向量索引，共 {len(self.vector_index)} 条索引", 
                           extra={'request_id': 'system', 'user_id': 'system'})
            else:
                # 创建空的向量索引文件
                self.vector_index = {}
                self._save_vector_index()
                logger.info("创建了空的向量索引文件", extra={'request_id': 'system', 'user_id': 'system'})
        except Exception as e:
            logger.error(f"加载向量索引失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'system', 'user_id': 'system'})
            # 初始化空字典
            self.vector_index = {}
    
    @log_function(logger)
    def _save_vector_index(self) -> None:
        """保存向量索引到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.vector_index_file), exist_ok=True)
            
            with open(self.vector_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.vector_index, f, ensure_ascii=False, indent=2)
                
            logger.info(f"向量索引已保存到 {self.vector_index_file}，共 {len(self.vector_index)} 条索引",
                       extra={'request_id': 'system', 'user_id': 'system'})
        except Exception as e:
            logger.error(f"保存向量索引失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'system', 'user_id': 'system'})
    
    @log_function(logger)
    def add_resource(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加学习资源
        
        Args:
            resource_data: 资源数据
            
        Returns:
            添加的资源
        """
        try:
            # 生成唯一ID
            resource_id = resource_data.get("id") or f"res_{str(uuid.uuid4())[:8]}"
            
            # 确保必要的字段存在
            if "title" not in resource_data:
                raise ValueError("缺少必要的字段: title")
            if "url" not in resource_data:
                raise ValueError("缺少必要的字段: url")
                
            # 设置默认值
            current_time = datetime.now().isoformat()
            resource = {
                "id": resource_id,
                "title": resource_data["title"],
                "description": resource_data.get("description", ""),
                "url": resource_data["url"],
                "resource_type": resource_data.get("resource_type", ResourceType.ARTICLE),
                "source": resource_data.get("source", ""),
                "author": resource_data.get("author", ""),
                "published_date": resource_data.get("published_date", ""),
                "difficulty": resource_data.get("difficulty", DifficultyLevel.INTERMEDIATE),
                "time_commitment": resource_data.get("time_commitment", TimeCommitment.MEDIUM),
                "tags": resource_data.get("tags", []),
                "skills": resource_data.get("skills", []),
                "rating": resource_data.get("rating", 0),
                "review_count": resource_data.get("review_count", 0),
                "job_relevance": resource_data.get("job_relevance", []),
                "created_at": current_time,
                "updated_at": current_time
            }
            
            # 存储资源
            self.resources[resource_id] = resource
            self._save_resources()
            
            # 为资源计算向量表示并更新索引
            self._update_resource_vector(resource_id)
            
            logger.info(f"成功添加学习资源: {resource_id} - {resource['title']}", 
                       extra={'request_id': 'auto', 'user_id': 'system'})
            
            return resource
        except Exception as e:
            logger.error(f"添加学习资源失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'auto', 'user_id': 'system'})
            raise
    
    @log_function(logger)
    def get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        获取学习资源
        
        Args:
            resource_id: 资源ID
            
        Returns:
            资源数据，如不存在返回None
        """
        if resource_id in self.resources:
            return self.resources[resource_id]
        else:
            logger.warning(f"尝试获取不存在的学习资源: {resource_id}", 
                          extra={'request_id': 'auto', 'user_id': 'system'})
            return None
    
    @log_function(logger)
    def update_resource(self, resource_id: str, resource_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新学习资源
        
        Args:
            resource_id: 资源ID
            resource_data: 要更新的资源数据
            
        Returns:
            更新后的资源，如不存在返回None
        """
        if resource_id not in self.resources:
            logger.warning(f"尝试更新不存在的学习资源: {resource_id}", 
                          extra={'request_id': 'auto', 'user_id': 'system'})
            return None
            
        try:
            # 获取原资源
            resource = self.resources[resource_id]
            
            # 更新字段
            for key, value in resource_data.items():
                if key not in ["id", "created_at"]:  # 保护这些字段不被更新
                    resource[key] = value
                    
            # 更新时间戳
            resource["updated_at"] = datetime.now().isoformat()
            
            # 保存更新
            self.resources[resource_id] = resource
            self._save_resources()
            
            # 如果标题或描述更新了，重新计算向量
            if "title" in resource_data or "description" in resource_data:
                self._update_resource_vector(resource_id)
            
            logger.info(f"成功更新学习资源: {resource_id}", 
                       extra={'request_id': 'auto', 'user_id': 'system'})
                       
            return resource
        except Exception as e:
            logger.error(f"更新学习资源 {resource_id} 失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'auto', 'user_id': 'system'})
            raise
    
    @log_function(logger)
    def delete_resource(self, resource_id: str) -> bool:
        """
        删除学习资源
        
        Args:
            resource_id: 资源ID
            
        Returns:
            是否删除成功
        """
        if resource_id not in self.resources:
            logger.warning(f"尝试删除不存在的学习资源: {resource_id}", 
                          extra={'request_id': 'auto', 'user_id': 'system'})
            return False
            
        try:
            # 删除资源
            del self.resources[resource_id]
            self._save_resources()
            
            # 删除向量索引
            if resource_id in self.vector_index:
                del self.vector_index[resource_id]
                self._save_vector_index()
            
            logger.info(f"成功删除学习资源: {resource_id}", 
                       extra={'request_id': 'auto', 'user_id': 'system'})
            return True
        except Exception as e:
            logger.error(f"删除学习资源 {resource_id} 失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'auto', 'user_id': 'system'})
            return False
    
    @log_function(logger)
    def list_resources(self, 
                     filters: Optional[Dict[str, Any]] = None, 
                     sort_by: str = "created_at", 
                     sort_desc: bool = True,
                     limit: int = 100,
                     offset: int = 0) -> List[Dict[str, Any]]:
        """
        列出学习资源
        
        Args:
            filters: 过滤条件
            sort_by: 排序字段
            sort_desc: 是否降序排序
            limit: 返回结果数量限制
            offset: 结果偏移量
            
        Returns:
            资源列表
        """
        try:
            # 获取所有资源值
            resources = list(self.resources.values())
            
            # 应用过滤条件
            if filters:
                resources = self._apply_filters(resources, filters)
                
            # 应用排序
            if sort_by in resources[0] if resources else False:
                resources.sort(key=lambda x: x.get(sort_by, ""), reverse=sort_desc)
            
            # 应用分页
            paginated_resources = resources[offset:offset+limit]
            
            logger.info(f"列出学习资源: 返回 {len(paginated_resources)}/{len(resources)} 条记录", 
                       extra={'request_id': 'auto', 'user_id': 'system'})
            
            return paginated_resources
        except Exception as e:
            logger.error(f"列出学习资源失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'auto', 'user_id': 'system'})
            return []
    
    @log_function(logger)
    def search_resources(self, 
                       query: str,
                       filters: Optional[Dict[str, Any]] = None,
                       top_k: int = 10) -> List[Dict[str, Any]]:
        """
        搜索学习资源
        
        Args:
            query: 搜索查询
            filters: 过滤条件
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        try:
            # 计算查询向量
            query_vector = compute_embedding(query)
            
            # 获取所有资源ID和向量
            resource_ids = list(self.vector_index.keys())
            resource_vectors = [self.vector_index[rid]["vector"] for rid in resource_ids]
            
            if not resource_vectors:
                logger.warning("没有可搜索的资源向量", 
                              extra={'request_id': 'auto', 'user_id': 'system'})
                return []
            
            # 计算相似度并排序
            similarities = []
            for i, rid in enumerate(resource_ids):
                if rid in self.resources:  # 确保资源存在
                    similarity = compute_similarity(query_vector, resource_vectors[i])
                    similarities.append({
                        "id": rid,
                        "similarity": similarity,
                        "resource": self.resources[rid]
                    })
            
            # 排序
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            # 应用过滤条件
            if filters:
                filtered_results = []
                for item in similarities:
                    if self._match_filters(item["resource"], filters):
                        filtered_results.append(item)
                similarities = filtered_results
            
            # 限制结果数量
            results = similarities[:top_k]
            
            # 提取资源数据
            resources = [item["resource"] for item in results]
            
            logger.info(f"搜索学习资源: 查询 '{query}'，返回 {len(resources)} 条结果", 
                       extra={'request_id': 'auto', 'user_id': 'system'})
            
            return resources
        except Exception as e:
            logger.error(f"搜索学习资源失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'auto', 'user_id': 'system'})
            return []
    
    @log_function(logger)
    def bulk_import_resources(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量导入学习资源
        
        Args:
            resources: 资源列表
            
        Returns:
            导入结果统计
        """
        stats = {
            "total": len(resources),
            "imported": 0,
            "failed": 0,
            "errors": []
        }
        
        for resource_data in resources:
            try:
                self.add_resource(resource_data)
                stats["imported"] += 1
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append({
                    "resource": resource_data.get("title", "未知标题"),
                    "error": str(e)
                })
        
        logger.info(f"批量导入学习资源: 总计 {stats['total']}，成功 {stats['imported']}，失败 {stats['failed']}", 
                   extra={'request_id': 'auto', 'user_id': 'system'})
        
        return stats
    
    @log_function(logger)
    def import_resources_from_csv(self, csv_file: str) -> Dict[str, Any]:
        """
        从CSV文件导入学习资源
        
        Args:
            csv_file: CSV文件路径
            
        Returns:
            导入结果统计
        """
        try:
            # 读取CSV文件
            df = pd.read_csv(csv_file)
            
            # 转换为字典列表
            resources = df.to_dict(orient="records")
            
            # 批量导入
            return self.bulk_import_resources(resources)
        except Exception as e:
            logger.error(f"从CSV文件导入学习资源失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'auto', 'user_id': 'system'})
            return {
                "total": 0,
                "imported": 0,
                "failed": 0,
                "errors": [{"resource": csv_file, "error": str(e)}]
            }
    
    @log_function(logger)
    def reindex_all_resources(self) -> Dict[str, Any]:
        """
        重建所有资源的向量索引
        
        Returns:
            索引结果统计
        """
        stats = {
            "total": len(self.resources),
            "indexed": 0,
            "failed": 0,
            "errors": []
        }
        
        # 清空现有索引
        self.vector_index = {}
        
        # 为每个资源重建索引
        for resource_id in self.resources:
            try:
                self._update_resource_vector(resource_id)
                stats["indexed"] += 1
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append({
                    "id": resource_id,
                    "title": self.resources[resource_id].get("title", "未知标题"),
                    "error": str(e)
                })
        
        # 保存索引
        self._save_vector_index()
        
        logger.info(f"重建资源向量索引: 总计 {stats['total']}，成功 {stats['indexed']}，失败 {stats['failed']}", 
                   extra={'request_id': 'auto', 'user_id': 'system'})
        
        return stats
    
    def _update_resource_vector(self, resource_id: str) -> None:
        """为资源计算向量表示并更新索引"""
        if resource_id not in self.resources:
            logger.warning(f"尝试为不存在的资源计算向量: {resource_id}", 
                          extra={'request_id': 'auto', 'user_id': 'system'})
            return
            
        resource = self.resources[resource_id]
        
        # 构建用于向量化的文本
        vector_text = f"{resource['title']}. {resource['description']}"
        if resource.get("tags"):
            tags_text = " ".join(resource["tags"])
            vector_text += f" 标签: {tags_text}"
            
        # 计算向量
        vector = compute_embedding(vector_text)
        
        # 更新索引
        self.vector_index[resource_id] = {
            "vector": vector,
            "updated_at": time.time()
        }
        
        # 定期保存索引
        # 为避免频繁IO，这里可以采用计数器或时间间隔来控制保存频率
        # 简化示例中每次都保存
        self._save_vector_index()
    
    def _apply_filters(self, resources: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """应用过滤条件"""
        filtered_resources = []
        for resource in resources:
            if self._match_filters(resource, filters):
                filtered_resources.append(resource)
        return filtered_resources
    
    def _match_filters(self, resource: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查资源是否匹配过滤条件"""
        for key, value in filters.items():
            # 处理特殊过滤条件
            if key == "tags" and isinstance(value, list):
                # 检查是否包含任一标签
                if not any(tag in resource.get("tags", []) for tag in value):
                    return False
            elif key == "skills" and isinstance(value, list):
                # 检查是否包含任一技能
                if not any(skill in resource.get("skills", []) for skill in value):
                    return False
            elif key == "job_relevance" and isinstance(value, list):
                # 检查是否与任一职位相关
                if not any(job in resource.get("job_relevance", []) for job in value):
                    return False
            elif key == "difficulty" and value in [d.value for d in DifficultyLevel]:
                # 精确匹配难度
                if resource.get("difficulty") != value:
                    return False
            elif key == "resource_type" and value in [rt.value for rt in ResourceType]:
                # 精确匹配资源类型
                if resource.get("resource_type") != value:
                    return False
            elif key == "search_text" and isinstance(value, str):
                # 文本搜索
                search_text = value.lower()
                title = resource.get("title", "").lower()
                description = resource.get("description", "").lower()
                if search_text not in title and search_text not in description:
                    return False
            else:
                # 默认精确匹配
                if key in resource and resource[key] != value:
                    return False
        return True 