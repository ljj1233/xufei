# agent/__init__.py

"""
多模态面试评测智能体库

这是一个独立的AI智能体库，专门用于多模态面试评测系统的分析功能。
通过将AI功能从后端分离，实现了更清晰的架构和更灵活的调用方式。
"""

import logging
import os
import sys

# 将src目录添加到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logging.getLogger('agent').setLevel(logging.INFO)

# 暂时注释掉导入，防止导入错误
# from src.core import agent

__version__ = '0.1.0'

# 导出主要类和函数，方便用户直接从包导入
from .src.core.agent import InterviewAgent, AnalysisResult
from .src.core.system.config import AgentConfig