# -*- coding: utf-8 -*-
"""
集成测试模块

测试各个组件之间的交互
"""

import unittest
import logging
from typing import Dict, Any
import json
from pathlib import Path

from agent.src.core.workflow.state import GraphState, TaskType, TaskStatus
from agent.src.nodes.task_parser import TaskParser
from agent.src.nodes.strategy_decider import StrategyDecider
from agent.src.nodes.task_planner import TaskPlanner
from agent.src.nodes.analyzer_executor import AnalyzerExecutor
from agent.src.nodes.result_integrator import ResultIntegrator
from agent.src.nodes.feedback_generator import FeedbackGenerator

logger = logging.getLogger(__name__)

class IntegrationTest(unittest.TestCase):
    """集成测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.task_parser = TaskParser()
        self.strategy_decider = StrategyDecider()
        self.task_planner = TaskPlanner()
        self.analyzer_executor = AnalyzerExecutor()
        self.result_integrator = ResultIntegrator()
        self.feedback_generator = FeedbackGenerator()
        
        # 加载测试数据
        self.test_data = self._load_test_data()
    
    def _load_test_data(self) -> Dict[str, Any]:
        """加载测试数据
        
        Returns:
            Dict[str, Any]: 测试数据
        """
        data_file = Path(__file__).parent / "data" / "test_data.json"
        if not data_file.exists():
            return {
                "user_scenarios": []
            }
        
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        if not self.test_data["user_scenarios"]:
            self.skipTest("没有测试数据")
            return
            
        for scenario in self.test_data["user_scenarios"]:
            # 1. 任务解析
            state = GraphState()
            state.user_context.interview_data = scenario["interview_data"]
            state = self.task_parser.execute(state)
            
            self.assertIsNotNone(state.get_tasks(), "任务解析失败")
            self.assertGreaterEqual(len(state.get_tasks()), 0, "未生成任何任务")
            
            # 2. 策略决策
            state = self.strategy_decider.execute(state)
            
            self.assertIsNotNone(state.get_strategies(), "策略决策失败")
            
            # 3. 任务规划
            state = self.task_planner.execute(state)
            
            # 确保有任务计划
            tasks = state.get_tasks()
            self.assertIsNotNone(tasks, "任务规划失败")
            
            # 4. 分析执行
            state = self.analyzer_executor.execute(state)
            
            # 5. 结果整合
            state = self.result_integrator.execute(state)
            
            self.assertIsNotNone(state.get_result(), "结果整合失败")
            
            # 6. 反馈生成
            state = self.feedback_generator.execute(state)
            
            feedback = state.get_feedback()
            self.assertIsNotNone(feedback, "反馈生成失败")
            self.assertGreater(len(feedback), 0, "反馈内容为空")
    
    def test_error_handling(self):
        """测试错误处理"""
        # 创建无效的测试数据
        invalid_data = {
            "interview_data": {
                "audio": None,
                "video": None,
                "text": ""
            }
        }
        
        # 1. 任务解析
        state = GraphState()
        state.user_context.interview_data = invalid_data["interview_data"]
        # 手动设置错误以模拟错误状态
        state.set_error("测试错误：空输入数据")
        
        # 验证错误处理
        self.assertIsNotNone(state.error, "未检测到错误")
    
    def test_parallel_execution(self):
        """测试并行执行"""
        # 创建多任务测试数据
        multi_task_data = {
            "interview_data": {
                "audio": "test_audio.wav",
                "video": "test_video.mp4",
                "text": "测试文本内容"
            }
        }
        
        # 1. 任务解析
        state = GraphState()
        state.user_context.interview_data = multi_task_data["interview_data"]
        state = self.task_parser.execute(state)
        
        # 2. 设置并行执行
        state.set_parallel_execution(True)
        
        # 3. 执行分析
        state = self.analyzer_executor.execute(state)
    
    def test_state_persistence(self):
        """测试状态持久化"""
        # 创建测试数据
        test_data = {
            "interview_data": {
                "audio": "test_audio.wav",
                "video": "test_video.mp4",
                "text": "测试文本内容"
            }
        }
        
        # 1. 执行完整流程
        state = GraphState()
        state.user_context.interview_data = test_data["interview_data"]
        
        # 保存任务类型
        state.task_type = TaskType.INTERVIEW_ANALYSIS
        
        # 执行各个节点
        state = self.task_parser.execute(state)
        state = self.strategy_decider.execute(state)
        state = self.task_planner.execute(state)
        state = self.analyzer_executor.execute(state)
        state = self.result_integrator.execute(state)
        state = self.feedback_generator.execute(state)
        
        # 验证状态变化
        self.assertEqual(state.task_status, TaskStatus.FEEDBACK_GENERATED, "最终状态不正确")
        self.assertIsNotNone(state.get_result(), "最终状态缺少分析结果")
        self.assertIsNotNone(state.get_feedback(), "最终状态缺少反馈内容")


if __name__ == '__main__':
    unittest.main() 