# ai_agent/examples/langgraph_agent_example.py

"""
基于LangGraph的智能面试代理示例

该示例展示了如何使用基于LangGraph框架重构的智能面试评测代理。
"""

import os
import sys
import json
import time
from typing import Dict, Any, Optional
import logging

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ai_agent.core.intelligent_agent import IntelligentInterviewAgent
from ai_agent.core.state import TaskType, TaskPriority

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def print_result(result: Dict[str, Any]):
    """打印分析结果"""
    print("\n" + "=" * 50)
    print("分析结果:")
    print("=" * 50)
    
    if "error" in result:
        print(f"错误: {result['error']}")
        return
    
    # 打印综合评分
    if "overall_score" in result:
        print(f"综合评分: {result['overall_score']:.2f}/10.0")
    
    # 打印各维度评分
    if "dimension_scores" in result:
        print("\n各维度评分:")
        for dimension, score in result["dimension_scores"].items():
            print(f"  - {dimension}: {score:.2f}/10.0")
    
    # 打印优势
    if "strengths" in result:
        print("\n优势:")
        for strength in result["strengths"]:
            print(f"  - {strength}")
    
    # 打印不足
    if "weaknesses" in result:
        print("\n不足:")
        for weakness in result["weaknesses"]:
            print(f"  - {weakness}")
    
    # 打印建议
    if "suggestions" in result:
        print("\n改进建议:")
        for suggestion in result["suggestions"]:
            print(f"  - {suggestion}")
    
    print("=" * 50)


def stream_callback(partial_result: Dict[str, Any]):
    """流式回调函数"""
    # 打印部分结果
    if "current_task" in partial_result:
        print(f"当前任务: {partial_result['current_task']}")
    
    if "progress" in partial_result:
        print(f"进度: {partial_result['progress']:.1f}%")
    
    if "partial_analysis" in partial_result:
        analysis = partial_result["partial_analysis"]
        print(f"部分分析: {analysis[:100]}..." if len(analysis) > 100 else analysis)


def simulate_speech_data():
    """模拟语音数据"""
    return {
        "audio_path": "simulated_audio.wav",
        "duration": 120,  # 2分钟
        "sample_rate": 16000,
        "features": {
            "pitch": [220.0, 230.0, 225.0, 215.0],  # 模拟音高数据
            "energy": [0.8, 0.9, 0.85, 0.75],  # 模拟能量数据
            "speech_rate": 4.5,  # 每秒音节数
            "pause_count": 15,  # 停顿次数
        }
    }


def simulate_vision_data():
    """模拟视觉数据"""
    return {
        "video_path": "simulated_video.mp4",
        "duration": 120,  # 2分钟
        "resolution": "1280x720",
        "features": {
            "face_expressions": ["neutral", "smile", "neutral", "concerned"],  # 模拟表情数据
            "eye_contact": 0.75,  # 眼神接触比例
            "posture_changes": 8,  # 姿势变化次数
            "hand_gestures": 12,  # 手势次数
        }
    }


def simulate_content_data():
    """模拟内容数据"""
    return {
        "transcript": "您好，我是张三，今天来应聘软件工程师职位。我有5年的Python开发经验，"
                     "主要负责后端API开发和数据处理。在上一家公司，我负责了电商平台的订单系统重构，"
                     "将处理速度提升了30%。我熟悉微服务架构，并且有丰富的数据库优化经验。"
                     "我认为自己最大的优势是解决问题的能力和团队协作精神。"
                     "我的不足可能是前端技术相对薄弱，但我正在学习React和Vue来弥补这一点。",
        "question": "请介绍一下你自己和你的技术背景",
        "interview_position": "软件工程师",
        "keywords": ["Python", "API", "数据处理", "微服务", "数据库优化"]
    }


def main():
    """主函数"""
    try:
        # 创建智能面试代理
        agent = IntelligentInterviewAgent(user_id="test_user", session_id="test_session")
        
        print("智能面试评测代理已初始化")
        
        # 准备模拟数据
        speech_data = simulate_speech_data()
        vision_data = simulate_vision_data()
        content_data = simulate_content_data()
        
        # 组合多模态数据
        multimodal_data = {
            "speech": speech_data,
            "vision": vision_data,
            "content": content_data,
            "context": {
                "interview_type": "technical",
                "position": "软件工程师",
                "company": "科技有限公司",
                "stage": "初试"
            }
        }
        
        print("\n开始综合分析...")
        
        # 方式1：同步分析
        result = agent.analyze(multimodal_data)
        print_result(result)
        
        # 方式2：流式分析
        print("\n开始流式分析...")
        final_result = agent.analyze_stream(multimodal_data, callback=stream_callback)
        print_result(final_result)
        
        # 方式3：创建任务
        print("\n创建分析任务...")
        task_id = agent.create_task(
            task_type="COMPREHENSIVE_ANALYSIS",
            data=multimodal_data,
            priority="HIGH"
        )
        print(f"任务已创建，ID: {task_id}")
        
        # 获取智能体状态
        state = agent.get_state()
        print(f"\n智能体当前状态: {state['agent_state']}")
        
        # 重置智能体
        agent.reset()
        print("智能体已重置")
        
    except Exception as e:
        logger.error(f"示例运行出错: {e}", exc_info=True)


if __name__ == "__main__":
    main()