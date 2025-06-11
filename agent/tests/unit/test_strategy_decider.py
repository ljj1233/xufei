# -*- coding: utf-8 -*-
"""
策略决策器单元测试
"""
import pytest
from src.nodes.strategy_decider import StrategyDecider
from src.core.workflow.state import GraphState, TaskType

@pytest.fixture
def strategy_decider():
    """返回一个策略决策器的实例"""
    return StrategyDecider()

def test_quick_interview_strategy(strategy_decider):
    """
    测试 'quick' 模式下的策略选择。
    预期：只选择 content 和 speech 分析。
    """
    # 1. 准备状态
    state = GraphState()
    state.task_type = TaskType.INTERVIEW_ANALYSIS
    state.input = {
        "mode": "quick",
        "interview_data": {
            "audio": "path/to/audio.wav",
            "video": "path/to/video.mp4",
            "text": "这是面试文本记录。"
        }
    }
    # 模拟任务解析器可能执行的操作
    state.add_resource("transcript", "这是面试文本记录。")
    state.add_resource("audio_file", "path/to/audio.wav")
    state.add_resource("video_file", "path/to/video.mp4")

    # 2. 执行决策
    updated_state = strategy_decider.execute(state)

    # 3. 断言结果
    strategies = updated_state.get_strategies()
    assert isinstance(strategies, list)
    assert "content_analysis" in strategies
    assert "speech_analysis" in strategies
    assert "visual_analysis" not in strategies, "在 'quick' 模式下不应包含视觉分析"
    assert len(strategies) == 2

def test_full_interview_strategy(strategy_decider):
    """
    测试 'full' 模式下的策略选择。
    预期：选择 content, speech, 和 visual 分析。
    """
    # 1. 准备状态
    state = GraphState()
    state.task_type = TaskType.INTERVIEW_ANALYSIS
    state.input = {
        "mode": "full",
        "interview_data": {
            "audio": "path/to/audio.wav",
            "video": "path/to/video.mp4",
            "text": "这是面试文本记录。"
        }
    }
    state.add_resource("transcript", "这是面试文本记录。")
    state.add_resource("audio_file", "path/to/audio.wav")
    state.add_resource("video_file", "path/to/video.mp4")

    # 2. 执行决策
    updated_state = strategy_decider.execute(state)

    # 3. 断言结果
    strategies = updated_state.get_strategies()
    assert "content_analysis" in strategies
    assert "speech_analysis" in strategies
    assert "visual_analysis" in strategies
    assert len(strategies) == 3

def test_default_mode_is_full_strategy(strategy_decider):
    """
    测试未指定模式时，应默认为 'full' 模式。
    预期：选择 content, speech, 和 visual 分析。
    """
    # 1. 准备状态
    state = GraphState()
    state.task_type = TaskType.INTERVIEW_ANALYSIS
    state.input = {
        # 未指定 mode
        "interview_data": {
            "audio": "path/to/audio.wav",
            "video": "path/to/video.mp4",
            "text": "这是面试文本记录。"
        }
    }
    state.add_resource("transcript", "这是面试文本记录。")
    state.add_resource("audio_file", "path/to/audio.wav")
    state.add_resource("video_file", "path/to/video.mp4")

    # 2. 执行决策
    updated_state = strategy_decider.execute(state)

    # 3. 断言结果
    strategies = updated_state.get_strategies()
    assert "content_analysis" in strategies
    assert "speech_analysis" in strategies
    assert "visual_analysis" in strategies, "默认模式应为 'full'，包含视觉分析"
    assert len(strategies) == 3

def test_quick_mode_without_video_resource(strategy_decider):
    """
    测试 'quick' 模式下，当本身就没有视频资源时的情况。
    预期：只选择 content 和 speech 分析。
    """
    # 1. 准备状态
    state = GraphState()
    state.task_type = TaskType.INTERVIEW_ANALYSIS
    state.input = {
        "mode": "quick",
        "interview_data": {
            "audio": "path/to/audio.wav",
            "text": "这是面试文本记录。"
        }
    }
    state.add_resource("transcript", "这是面试文本记录。")
    state.add_resource("audio_file", "path/to/audio.wav")
    # 没有 video_file 资源

    # 2. 执行决策
    updated_state = strategy_decider.execute(state)

    # 3. 断言结果
    strategies = updated_state.get_strategies()
    assert "content_analysis" in strategies
    assert "speech_analysis" in strategies
    assert "visual_analysis" not in strategies
    assert len(strategies) == 2
