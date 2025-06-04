# agent/services/modelscope_service.py

from typing import Dict, List, Optional, Any, Union, Tuple
import logging
import numpy as np
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

from ..core.system.config import AgentConfig

logger = logging.getLogger(__name__)

class ModelScopeService:
    """ModelScope服务
    
    封装与ModelScope模型的交互
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化ModelScope服务
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        self.config = config or AgentConfig()
        
        # 从配置中加载参数
        self.cache_dir = self.config.get_service_config("modelscope", "cache_dir", None)
        self.max_workers = self.config.get_service_config("modelscope", "max_workers", 2)
        
        # 线程池用于并行处理
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # 初始化模型字典
        self._models = {}
        self._pipelines = {}
        
        # 延迟导入，避免启动时依赖问题
        self._modelscope_imported = False
        
        logger.info("ModelScope服务初始化完成")
    
    def _ensure_modelscope_imported(self):
        """确保ModelScope已导入"""
        if not self._modelscope_imported:
            try:
                import modelscope
                from modelscope.pipelines import pipeline
                from modelscope.utils.constant import Tasks
                
                self.modelscope = modelscope
                self.pipeline = pipeline
                self.Tasks = Tasks
                self._modelscope_imported = True
                logger.info("ModelScope库导入成功")
                
            except ImportError as e:
                logger.error(f"导入ModelScope失败: {e}")
                raise ImportError("ModelScope库未安装，请使用pip install modelscope安装")
    
    def _get_or_create_pipeline(self, task: str, model_id: str) -> Any:
        """获取或创建管道
        
        Args:
            task: 任务类型
            model_id: 模型ID
            
        Returns:
            管道实例
        """
        self._ensure_modelscope_imported()
        
        # 创建管道标识
        pipeline_key = f"{task}:{model_id}"
        
        # 检查是否已存在
        if pipeline_key not in self._pipelines:
            logger.info(f"创建新管道: {pipeline_key}")
            try:
                # 创建新管道
                task_enum = getattr(self.Tasks, task.upper()) if hasattr(self.Tasks, task.upper()) else task
                pipe = self.pipeline(
                    task=task_enum,
                    model=model_id,
                    model_revision="master",
                    cache_dir=self.cache_dir
                )
                self._pipelines[pipeline_key] = pipe
            except Exception as e:
                logger.error(f"创建管道失败: {e}")
                raise
        
        return self._pipelines[pipeline_key]
    
    async def run_pipeline(self, 
                         task: str, 
                         model_id: str, 
                         inputs: Union[str, Dict, List],
                         **kwargs) -> Dict[str, Any]:
        """异步运行ModelScope管道
        
        Args:
            task: 任务类型
            model_id: 模型ID
            inputs: 输入数据
            **kwargs: 其他参数
            
        Returns:
            Dict: 处理结果
        """
        try:
            # 将同步管道在线程池中运行
            loop = asyncio.get_event_loop()
            start_time = time.time()
            
            result = await loop.run_in_executor(
                self.executor,
                lambda: self._run_pipeline_sync(task, model_id, inputs, **kwargs)
            )
            
            elapsed = time.time() - start_time
            logger.info(f"管道运行完成: {task}, 用时: {elapsed:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"运行管道失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _run_pipeline_sync(self, 
                         task: str, 
                         model_id: str, 
                         inputs: Union[str, Dict, List],
                         **kwargs) -> Dict[str, Any]:
        """同步运行ModelScope管道
        
        Args:
            task: 任务类型
            model_id: 模型ID
            inputs: 输入数据
            **kwargs: 其他参数
            
        Returns:
            Dict: 处理结果
        """
        try:
            # 获取管道
            pipe = self._get_or_create_pipeline(task, model_id)
            
            # 运行管道
            result = pipe(inputs, **kwargs)
            
            # 处理结果
            return self._process_result(task, result)
            
        except Exception as e:
            logger.error(f"同步运行管道失败: {task}, {model_id}, 错误: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _process_result(self, task: str, result: Any) -> Dict[str, Any]:
        """处理管道结果
        
        Args:
            task: 任务类型
            result: 管道返回结果
            
        Returns:
            Dict: 处理后的结果
        """
        # 根据不同任务类型处理结果
        if task.lower() == "text_embedding" or task.lower() == "sentence_embedding":
            # 处理嵌入向量结果
            if isinstance(result, dict) and "text_embedding" in result:
                embedding = result["text_embedding"].tolist() if isinstance(result["text_embedding"], np.ndarray) else result["text_embedding"]
                return {
                    "embedding": embedding,
                    "status": "success"
                }
            else:
                return {
                    "embedding": [],
                    "status": "error",
                    "error": "无效的嵌入结果"
                }
                
        elif task.lower() == "text_classification" or task.lower() == "sentiment_analysis":
            # 处理文本分类/情感分析结果
            if isinstance(result, dict) and "scores" in result and "labels" in result:
                return {
                    "labels": result["labels"],
                    "scores": result["scores"],
                    "status": "success"
                }
            else:
                return {
                    "labels": [],
                    "scores": [],
                    "status": "error",
                    "error": "无效的分类结果"
                }
                
        elif task.lower() == "text_generation":
            # 处理文本生成结果
            if isinstance(result, dict) and "text" in result:
                return {
                    "text": result["text"],
                    "status": "success"
                }
            else:
                return {
                    "text": "",
                    "status": "error",
                    "error": "无效的生成结果"
                }
                
        elif task.lower() == "token_classification" or task.lower() == "named_entity_recognition":
            # 处理命名实体识别结果
            if isinstance(result, dict) and "entities" in result:
                return {
                    "entities": result["entities"],
                    "status": "success"
                }
            else:
                return {
                    "entities": [],
                    "status": "error",
                    "error": "无效的实体识别结果"
                }
                
        # 默认情况下，直接返回结果
        return {
            "result": result,
            "status": "success"
        }
    
    async def create_embedding(self, text: Union[str, List[str]], model_id: str = "damo/nlp_bert_embedding_chinese_base") -> Dict[str, Any]:
        """创建文本嵌入向量
        
        Args:
            text: 输入文本或文本列表
            model_id: 模型ID
            
        Returns:
            Dict: 嵌入结果
        """
        # 处理单个文本
        if isinstance(text, str):
            return await self.run_pipeline("text_embedding", model_id, text)
        
        # 处理文本列表
        else:
            results = []
            for t in text:
                result = await self.run_pipeline("text_embedding", model_id, t)
                if result.get("status") == "success" and "embedding" in result:
                    results.append(result["embedding"])
            
            if len(results) == len(text):
                return {
                    "embeddings": results,
                    "status": "success"
                }
            else:
                return {
                    "embeddings": results,
                    "status": "partial",
                    "error": f"仅完成了 {len(results)}/{len(text)} 个嵌入"
                }
    
    async def sentiment_analysis(self, text: str, model_id: str = "damo/nlp_structbert_sentiment-classification_chinese-base") -> Dict[str, Any]:
        """情感分析
        
        Args:
            text: 输入文本
            model_id: 模型ID
            
        Returns:
            Dict: 情感分析结果
        """
        return await self.run_pipeline("sentiment_analysis", model_id, text)
    
    async def named_entity_recognition(self, text: str, model_id: str = "damo/nlp_structbert_named-entity-recognition_chinese-base") -> Dict[str, Any]:
        """命名实体识别
        
        Args:
            text: 输入文本
            model_id: 模型ID
            
        Returns:
            Dict: 实体识别结果
        """
        return await self.run_pipeline("named_entity_recognition", model_id, text)
    
    async def text_classification(self, text: str, model_id: str, labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """文本分类
        
        Args:
            text: 输入文本
            model_id: 模型ID
            labels: 可选的标签列表
            
        Returns:
            Dict: 分类结果
        """
        kwargs = {}
        if labels:
            kwargs["candidate_labels"] = labels
            
        return await self.run_pipeline("text_classification", model_id, text, **kwargs)
        
    def release_resources(self):
        """释放资源"""
        # 清空管道和模型
        self._pipelines = {}
        self._models = {}
        
        # 关闭线程池
        self.executor.shutdown(wait=False)
        
        logger.info("ModelScope资源已释放") 