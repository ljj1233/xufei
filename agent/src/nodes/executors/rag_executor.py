# agent/nodes/executors/rag_executor.py

from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import asyncio
import time
import json
from pydantic import BaseModel, Field

from ...core.system.config import AgentConfig
from ...retrieval import HybridRetriever, Context7Retriever, DocumentProcessor
from ...services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class RAGExecutorInput(BaseModel):
    """RAG执行器输入"""
    query: str = Field(..., description="查询文本")
    context: Optional[Dict[str, Any]] = Field(default=None, description="上下文信息")
    library_name: Optional[str] = Field(default=None, description="库名称")
    library_id: Optional[str] = Field(default=None, description="Context7库ID")
    max_results: int = Field(default=5, description="最大结果数量")
    use_web_search: bool = Field(default=False, description="是否使用网络搜索")
    use_context7: bool = Field(default=False, description="是否使用Context7")

class RAGExecutorOutput(BaseModel):
    """RAG执行器输出"""
    query: str = Field(..., description="查询文本")
    context: List[Dict[str, Any]] = Field(default_factory=list, description="检索到的上下文")
    answer: Optional[str] = Field(default=None, description="生成的回答")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="来源信息")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

class RAGExecutor:
    """RAG执行器
    
    执行检索增强生成
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化RAG执行器
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        self.config = config or AgentConfig()
        
        # 初始化检索器
        self.hybrid_retriever = None
        self.context7_retriever = None
        self.document_processor = None
        
        # 初始化LLM服务
        self.openai_service = None
        
        # 从配置中加载参数
        self.max_results = self.config.get_rag_config("max_results", 5)
        self.context_window = self.config.get_rag_config("context_window", 4000)
        self.answer_template = self.config.get_rag_config("answer_template", 
            "根据提供的上下文，回答以下问题：\n\n问题：{query}\n\n上下文：\n{context}\n\n回答："
        )
    
    def _ensure_retrievers_initialized(self):
        """确保检索器已初始化"""
        if self.hybrid_retriever is None:
            self.hybrid_retriever = HybridRetriever(self.config)
            logger.info("混合检索器初始化完成")
        
        if self.context7_retriever is None:
            self.context7_retriever = Context7Retriever(self.config)
            logger.info("Context7检索器初始化完成")
        
        if self.document_processor is None:
            self.document_processor = DocumentProcessor(self.config)
            logger.info("文档处理器初始化完成")
    
    def _ensure_llm_initialized(self):
        """确保LLM服务已初始化"""
        if self.openai_service is None:
            self.openai_service = OpenAIService(self.config)
            logger.info("OpenAI服务初始化完成")
    
    async def _retrieve_context(self, query: str, max_results: int = 5, use_context7: bool = False, library_name: Optional[str] = None, library_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """检索上下文
        
        Args:
            query: 查询文本
            max_results: 最大结果数量
            use_context7: 是否使用Context7
            library_name: 库名称
            library_id: Context7库ID
            
        Returns:
            List[Dict[str, Any]]: 检索结果
        """
        self._ensure_retrievers_initialized()
        
        # 创建检索任务列表
        retrieval_tasks = []
        
        # 添加混合检索任务
        retrieval_tasks.append(self.hybrid_retriever.retrieve(query, max_results=max_results))
        
        # 如果使用Context7，添加Context7检索任务
        if use_context7 and (library_name or library_id):
            retrieval_tasks.append(self.context7_retriever.retrieve(
                query, 
                library_name=library_name,
                library_id=library_id,
                tokens=6000
            ))
        
        # 并行执行检索任务
        results = await asyncio.gather(*retrieval_tasks)
        
        # 合并结果
        all_results = []
        for result_list in results:
            all_results.extend(result_list)
        
        # 按分数排序
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # 限制结果数量
        return all_results[:max_results]
    
    async def _generate_answer(self, query: str, context: List[Dict[str, Any]]) -> str:
        """生成回答
        
        Args:
            query: 查询文本
            context: 上下文
            
        Returns:
            str: 生成的回答
        """
        self._ensure_llm_initialized()
        
        # 准备上下文文本
        context_text = ""
        for i, item in enumerate(context):
            context_text += f"[{i+1}] {item['text']}\n\n"
        
        # 准备提示
        prompt = self.answer_template.format(
            query=query,
            context=context_text
        )
        
        # 准备消息
        messages = [
            {"role": "system", "content": "你是一个专业的面试辅导助手，使用中文回答问题，基于提供的上下文信息。如果上下文中没有相关信息，请明确说明并提供一般性建议。"},
            {"role": "user", "content": prompt}
        ]
        
        # 生成回答
        result = await self.openai_service.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        if result.get("status") == "success" and "content" in result:
            return result["content"]
        else:
            logger.error(f"生成回答失败: {result.get('error', '未知错误')}")
            return "抱歉，我无法生成回答。请重试。"
    
    async def _prepare_sources(self, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """准备来源信息
        
        Args:
            context: 上下文
            
        Returns:
            List[Dict[str, Any]]: 来源信息
        """
        sources = []
        
        for item in context:
            source = {
                "text": item["text"][:100] + "..." if len(item["text"]) > 100 else item["text"],
                "score": item.get("score", 0),
                "source": item.get("source", "unknown")
            }
            
            # 添加元数据
            metadata = item.get("metadata", {})
            if "file_path" in metadata:
                source["file_path"] = metadata["file_path"]
            if "file_name" in metadata:
                source["file_name"] = metadata["file_name"]
            if "library_id" in metadata:
                source["library_id"] = metadata["library_id"]
            
            sources.append(source)
        
        return sources
    
    async def execute(self, input_data: Union[Dict[str, Any], RAGExecutorInput]) -> RAGExecutorOutput:
        """执行RAG
        
        Args:
            input_data: 输入数据
            
        Returns:
            RAGExecutorOutput: 输出数据
        """
        # 确保输入是RAGExecutorInput类型
        if isinstance(input_data, dict):
            input_data = RAGExecutorInput(**input_data)
        
        start_time = time.time()
        logger.info(f"开始执行RAG: {input_data.query}")
        
        try:
            # 检索上下文
            context = await self._retrieve_context(
                query=input_data.query,
                max_results=input_data.max_results,
                use_context7=input_data.use_context7,
                library_name=input_data.library_name,
                library_id=input_data.library_id
            )
            
            # 生成回答
            answer = await self._generate_answer(input_data.query, context)
            
            # 准备来源信息
            sources = await self._prepare_sources(context)
            
            # 准备元数据
            metadata = {
                "execution_time": time.time() - start_time,
                "context_count": len(context),
                "query_length": len(input_data.query),
                "answer_length": len(answer)
            }
            
            # 创建输出
            output = RAGExecutorOutput(
                query=input_data.query,
                context=context,
                answer=answer,
                sources=sources,
                metadata=metadata
            )
            
            logger.info(f"RAG执行完成，用时: {metadata['execution_time']:.2f}s")
            return output
            
        except Exception as e:
            logger.error(f"RAG执行异常: {e}")
            
            # 创建错误输出
            output = RAGExecutorOutput(
                query=input_data.query,
                context=[],
                answer=f"抱歉，执行过程中出现错误: {str(e)}",
                sources=[],
                metadata={"error": str(e), "execution_time": time.time() - start_time}
            )
            
            return output
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """添加文档到检索器
        
        Args:
            documents: 文档列表
            
        Returns:
            bool: 是否成功添加
        """
        self._ensure_retrievers_initialized()
        
        try:
            # 添加到混合检索器
            result = await self.hybrid_retriever.add_documents(documents)
            
            logger.info(f"添加文档结果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"添加文档异常: {e}")
            return False
    
    async def process_and_add_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """处理并添加文本
        
        Args:
            text: 文本内容
            metadata: 元数据
            
        Returns:
            bool: 是否成功添加
        """
        self._ensure_retrievers_initialized()
        
        try:
            # 处理文本
            documents = self.document_processor.process_text(text, metadata)
            
            # 添加文档
            return await self.add_documents(documents)
            
        except Exception as e:
            logger.error(f"处理并添加文本异常: {e}")
            return False
    
    async def process_and_add_file(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """处理并添加文件
        
        Args:
            file_path: 文件路径
            metadata: 元数据
            
        Returns:
            bool: 是否成功添加
        """
        self._ensure_retrievers_initialized()
        
        try:
            # 处理文件
            documents = self.document_processor.process_file(file_path, metadata)
            
            # 添加文档
            return await self.add_documents(documents)
            
        except Exception as e:
            logger.error(f"处理并添加文件异常: {e}")
            return False 