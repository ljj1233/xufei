# agent/retrieval/document_processor.py

from typing import List, Dict, Any, Optional, Union, Tuple, Iterator
import logging
import re
import uuid
from pathlib import Path
import json
import os
import time

from ..core.system.config import AgentConfig

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """文档处理器
    
    处理和分割文档，准备用于向量化和检索
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化文档处理器
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        self.config = config or AgentConfig()
        
        # 从配置中加载参数
        self.chunk_size = self.config.get_retriever_config("document", "chunk_size", 1000)
        self.chunk_overlap = self.config.get_retriever_config("document", "chunk_overlap", 200)
        self.separator = self.config.get_retriever_config("document", "separator", "\n")
    
    def process_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """处理文本
        
        将文本分割成块，并添加元数据
        
        Args:
            text: 输入文本
            metadata: 元数据
            
        Returns:
            List[Dict[str, Any]]: 处理后的文档块列表
        """
        # 分割文本
        chunks = self._split_text(text)
        
        # 准备元数据
        if metadata is None:
            metadata = {}
        
        # 为每个块创建文档
        documents = []
        for i, chunk in enumerate(chunks):
            # 复制元数据，避免修改原始对象
            chunk_metadata = metadata.copy()
            
            # 添加块信息
            chunk_metadata["chunk_index"] = i
            chunk_metadata["chunk_count"] = len(chunks)
            
            # 如果没有文档ID，生成一个
            if "doc_id" not in chunk_metadata:
                chunk_metadata["doc_id"] = str(uuid.uuid4())
            
            # 创建文档
            document = {
                "text": chunk,
                "metadata": chunk_metadata
            }
            
            documents.append(document)
        
        logger.info(f"文本处理完成，生成了 {len(documents)} 个文档块")
        return documents
    
    def _split_text(self, text: str) -> List[str]:
        """将文本分割成块
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 文本块列表
        """
        # 如果文本长度小于块大小，直接返回
        if len(text) <= self.chunk_size:
            return [text]
        
        # 按分隔符分割文本
        segments = text.split(self.separator)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for segment in segments:
            # 如果当前段太长，进一步分割
            if len(segment) > self.chunk_size:
                # 先处理当前块
                if current_chunk:
                    chunks.append(self.separator.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # 分割长段
                sub_segments = self._split_long_segment(segment)
                chunks.extend(sub_segments)
                continue
            
            # 如果添加当前段会超出块大小，保存当前块并开始新块
            if current_length + len(segment) > self.chunk_size and current_chunk:
                chunks.append(self.separator.join(current_chunk))
                
                # 开始新块，考虑重叠
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap // len(self.separator))
                current_chunk = current_chunk[overlap_start:]
                current_length = sum(len(s) for s in current_chunk) + len(self.separator) * (len(current_chunk) - 1)
            
            # 添加当前段到当前块
            current_chunk.append(segment)
            current_length += len(segment) + len(self.separator)
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(self.separator.join(current_chunk))
        
        return chunks
    
    def _split_long_segment(self, segment: str) -> List[str]:
        """分割过长的段落
        
        Args:
            segment: 输入段落
            
        Returns:
            List[str]: 分割后的段落列表
        """
        # 尝试按句子分割
        sentences = re.split(r'(?<=[.!?])\s+', segment)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            # 如果单个句子超过块大小，按单词分割
            if len(sentence) > self.chunk_size:
                # 先处理当前块
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # 分割长句子
                words = sentence.split()
                sub_chunk = []
                sub_length = 0
                
                for word in words:
                    if sub_length + len(word) + 1 > self.chunk_size and sub_chunk:
                        chunks.append(" ".join(sub_chunk))
                        sub_chunk = []
                        sub_length = 0
                    
                    sub_chunk.append(word)
                    sub_length += len(word) + 1
                
                if sub_chunk:
                    chunks.append(" ".join(sub_chunk))
                
                continue
            
            # 如果添加当前句子会超出块大小，保存当前块并开始新块
            if current_length + len(sentence) + 1 > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
            
            # 添加当前句子到当前块
            current_chunk.append(sentence)
            current_length += len(sentence) + 1
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def process_file(self, file_path: Union[str, Path], metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """处理文件
        
        读取文件内容并处理
        
        Args:
            file_path: 文件路径
            metadata: 元数据
            
        Returns:
            List[Dict[str, Any]]: 处理后的文档块列表
        """
        try:
            # 确保路径是Path对象
            path = Path(file_path) if isinstance(file_path, str) else file_path
            
            # 读取文件内容
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            
            # 准备元数据
            if metadata is None:
                metadata = {}
            
            # 添加文件信息
            metadata["file_path"] = str(path)
            metadata["file_name"] = path.name
            metadata["file_type"] = path.suffix
            metadata["file_size"] = path.stat().st_size
            metadata["created_at"] = time.time()
            
            # 处理文本
            return self.process_text(text, metadata)
            
        except Exception as e:
            logger.error(f"处理文件失败: {e}")
            return []
    
    def process_directory(self, dir_path: Union[str, Path], glob_pattern: str = "**/*.{txt,md,py,js,html,css,json}", metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """处理目录
        
        处理目录中的所有匹配文件
        
        Args:
            dir_path: 目录路径
            glob_pattern: 文件匹配模式
            metadata: 元数据
            
        Returns:
            List[Dict[str, Any]]: 处理后的文档块列表
        """
        try:
            # 确保路径是Path对象
            path = Path(dir_path) if isinstance(dir_path, str) else dir_path
            
            # 准备元数据
            if metadata is None:
                metadata = {}
            
            # 添加目录信息
            base_metadata = metadata.copy()
            base_metadata["dir_path"] = str(path)
            base_metadata["dir_name"] = path.name
            
            # 查找匹配的文件
            all_documents = []
            
            # 替换大括号为实际的文件扩展名
            if "{" in glob_pattern and "}" in glob_pattern:
                # 提取扩展名列表
                ext_pattern = re.search(r'{(.*?)}', glob_pattern)
                if ext_pattern:
                    exts = ext_pattern.group(1).split(",")
                    base_pattern = glob_pattern.split("{")[0]
                    
                    for ext in exts:
                        pattern = f"{base_pattern}{ext}"
                        for file_path in path.glob(pattern):
                            if file_path.is_file():
                                # 处理文件
                                file_metadata = base_metadata.copy()
                                documents = self.process_file(file_path, file_metadata)
                                all_documents.extend(documents)
            else:
                # 直接使用模式
                for file_path in path.glob(glob_pattern):
                    if file_path.is_file():
                        # 处理文件
                        file_metadata = base_metadata.copy()
                        documents = self.process_file(file_path, file_metadata)
                        all_documents.extend(documents)
            
            logger.info(f"目录处理完成，处理了 {len(all_documents)} 个文档块")
            return all_documents
            
        except Exception as e:
            logger.error(f"处理目录失败: {e}")
            return []
    
    def process_json(self, json_data: Union[str, Dict, List], metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """处理JSON数据
        
        Args:
            json_data: JSON数据，可以是字符串、字典或列表
            metadata: 元数据
            
        Returns:
            List[Dict[str, Any]]: 处理后的文档块列表
        """
        try:
            # 解析JSON
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
            
            # 准备元数据
            if metadata is None:
                metadata = {}
            
            # 添加JSON信息
            metadata["data_type"] = "json"
            metadata["created_at"] = time.time()
            
            # 将JSON转换为文本
            text = json.dumps(data, ensure_ascii=False, indent=2)
            
            # 处理文本
            return self.process_text(text, metadata)
            
        except Exception as e:
            logger.error(f"处理JSON失败: {e}")
            return [] 