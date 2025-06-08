# agent/tests/conftest.py

import os
import pytest
from unittest.mock import patch, MagicMock


class MockAgentConfig:
    """模拟的代理配置类"""
    def __init__(self):
        self.config = {}
        
    def set_config(self, key, value):
        """设置配置项"""
        self.config[key] = value
        
    def get_config(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)


class MockContentFilterService:
    """模拟的内容过滤服务"""
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = MockContentFilterService()
        return cls._instance
    
    def filter_text(self, text):
        """模拟过滤文本"""
        return MagicMock(
            filtered_text=text,
            has_sensitive_content=False,
            sensitive_word_count=0,
            sensitive_categories=[],
            highest_severity="low"
        )


class MockNotificationService:
    """模拟的通知服务"""
    async def notify_interview_status(self, client_id, status, message):
        """模拟通知面试状态"""
        pass
    
    async def notify_analysis_progress(self, client_id, progress, message, data=None):
        """模拟通知分析进度"""
        pass
    
    async def send_partial_feedback(self, client_id, feedback_type, feedback_data):
        """模拟发送部分反馈"""
        pass
    
    async def notify_task_status(self, client_id, task_id, status, data=None):
        """模拟通知任务状态"""
        pass
    
    async def notify_error(self, client_id, error_type, error_message):
        """模拟通知错误"""
        pass


@pytest.fixture(scope="session")
def base_test_dir():
    """返回测试数据目录路径"""
    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 测试数据目录
    test_data_dir = os.path.join(current_dir, "test_data")
    # 确保目录存在
    os.makedirs(test_data_dir, exist_ok=True)
    return test_data_dir


@pytest.fixture(scope="session")
def sample_audio_path(base_test_dir):
    """返回示例音频文件路径"""
    return os.path.join(base_test_dir, "sample_audio.wav")


@pytest.fixture
def mock_agent_config():
    """创建模拟的代理配置"""
    config = MockAgentConfig()
    # 设置一些通用配置
    config.set_config("log_level", "INFO")
    return config


@pytest.fixture
def mock_content_filter_service():
    """创建模拟的内容过滤服务"""
    return MockContentFilterService()


@pytest.fixture
def mock_notification_service():
    """创建模拟的通知服务"""
    return MockNotificationService()