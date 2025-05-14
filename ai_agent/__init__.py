# ai_agent/__init__.py

"""
多模态面试评测智能体库

这是一个独立的AI智能体库，专门用于多模态面试评测系统的分析功能。
通过将AI功能从后端分离，实现了更清晰的架构和更灵活的调用方式。
"""

__version__ = '0.1.0'

# 导出主要类和函数，方便用户直接从包导入
from .core.agent import InterviewAgent, AnalysisResult
from .core.config import AgentConfig

# 设置默认日志级别
import logging
logging.getLogger('ai_agent').setLevel(logging.INFO)