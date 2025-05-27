# ai_agent/core/nodes/task_parser.py

"""
任务解析节点

该节点负责解析用户输入，确定需要执行的任务类型和优先级。
它是工作流的第一个节点，接收用户输入并将其转换为结构化的任务。
"""

import uuid
from typing import Dict, Any, List, Tuple
from datetime import datetime

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

from ...core.state import GraphState, Task, TaskType, TaskPriority, TaskStatus
import logging

logger = logging.getLogger(__name__)


class ParsedTask(BaseModel):
    """解析后的任务模型"""
    task_type: str = Field(description="任务类型，可以是'SPEECH_ANALYSIS'、'VISION_ANALYSIS'、'CONTENT_ANALYSIS'或'COMPREHENSIVE_ANALYSIS'")
    priority: str = Field(description="任务优先级，可以是'LOW'、'MEDIUM'、'HIGH'或'CRITICAL'")
    data: Dict[str, Any] = Field(description="任务相关数据")


class TaskParser:
    """任务解析器节点"""
    
    def __init__(self):
        """初始化任务解析器"""
        self.parser = PydanticOutputParser(pydantic_object=ParsedTask)
        
        self.prompt_template = PromptTemplate(
            template="""你是一个面试评测系统的任务解析器。
            请分析以下用户输入，并确定需要执行的任务类型和优先级。
            
            用户输入: {input}
            
            请根据输入内容，确定以下信息：
            1. 任务类型：是语音分析(SPEECH_ANALYSIS)、视觉分析(VISION_ANALYSIS)、内容分析(CONTENT_ANALYSIS)还是综合分析(COMPREHENSIVE_ANALYSIS)？
            2. 任务优先级：根据紧急程度和重要性，确定优先级(LOW/MEDIUM/HIGH/CRITICAL)
            3. 提取任务相关的关键数据
            
            {format_instructions}
            """,
            input_variables=["input"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    def _parse_input(self, input_data: Dict[str, Any]) -> ParsedTask:
        """解析用户输入
        
        Args:
            input_data: 用户输入数据
            
        Returns:
            解析后的任务
        """
        # 在实际实现中，这里会调用LLM进行解析
        # 目前使用简化的逻辑进行演示
        
        # 提取输入文本
        input_text = input_data.get("text", "")
        
        # 根据输入文本中的关键词确定任务类型
        task_type = "COMPREHENSIVE_ANALYSIS"  # 默认为综合分析
        if "语音" in input_text or "声音" in input_text or "audio" in input_text.lower():
            task_type = "SPEECH_ANALYSIS"
        elif "视频" in input_text or "图像" in input_text or "video" in input_text.lower() or "image" in input_text.lower():
            task_type = "VISION_ANALYSIS"
        elif "内容" in input_text or "文本" in input_text or "text" in input_text.lower() or "content" in input_text.lower():
            task_type = "CONTENT_ANALYSIS"
        
        # 确定优先级
        priority = "MEDIUM"  # 默认为中等优先级
        if "紧急" in input_text or "立即" in input_text or "urgent" in input_text.lower():
            priority = "HIGH"
        elif "重要" in input_text or "关键" in input_text or "critical" in input_text.lower():
            priority = "CRITICAL"
        
        # 提取任务数据
        data = {
            "original_input": input_text,
            "timestamp": datetime.now().isoformat(),
        }
        
        # 如果输入中包含文件路径，添加到数据中
        if "file" in input_data:
            data["file_path"] = input_data["file"]
        
        return ParsedTask(task_type=task_type, priority=priority, data=data)
    
    def _create_task(self, parsed_task: ParsedTask) -> Task:
        """根据解析结果创建任务
        
        Args:
            parsed_task: 解析后的任务
            
        Returns:
            创建的任务
        """
        task_id = str(uuid.uuid4())
        
        # 转换任务类型
        task_type_map = {
            "SPEECH_ANALYSIS": TaskType.SPEECH_ANALYSIS,
            "VISION_ANALYSIS": TaskType.VISION_ANALYSIS,
            "CONTENT_ANALYSIS": TaskType.CONTENT_ANALYSIS,
            "COMPREHENSIVE_ANALYSIS": TaskType.COMPREHENSIVE_ANALYSIS,
        }
        task_type = task_type_map.get(parsed_task.task_type, TaskType.CUSTOM)
        
        # 转换优先级
        priority_map = {
            "LOW": TaskPriority.LOW,
            "MEDIUM": TaskPriority.MEDIUM,
            "HIGH": TaskPriority.HIGH,
            "CRITICAL": TaskPriority.CRITICAL,
        }
        priority = priority_map.get(parsed_task.priority, TaskPriority.MEDIUM)
        
        # 创建任务
        return Task(
            id=task_id,
            type=task_type,
            priority=priority,
            status=TaskStatus.PENDING,
            data=parsed_task.data,
            created_at=datetime.now(),
        )
    
    def parse(self, state: GraphState) -> GraphState:
        logger.info(f"任务解析节点开始，输入状态: {state}")
        try:
            # 假设有任务解析主流程
            parsed_tasks = self._parse_tasks(state)
            logger.info(f"任务解析完成，解析结果: {parsed_tasks}")
            state.task_state.tasks = parsed_tasks
            return state
        except Exception as e:
            logger.error(f"任务解析异常: {e}")
            state.error = str(e)
            return state