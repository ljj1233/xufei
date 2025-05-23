# ai_agent/tests/conftest.py

import os
import pytest
from unittest.mock import patch, MagicMock

from ai_agent.core.config import AgentConfig


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
    config = AgentConfig()
    # 设置一些通用配置
    config.set_config("log_level", "INFO")
    return config