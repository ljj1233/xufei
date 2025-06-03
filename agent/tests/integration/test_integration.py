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

from agent.core.state import GraphState, TaskType, TaskStatus
from agent.core.nodes.task_parser import TaskParser
from agent.core.nodes.strategy_decider import StrategyDecider
from agent.core.nodes.task_planner import TaskPlanner
from agent.core.nodes.analyzer_executor import AnalyzerExecutor
from agent.core.nodes.result_integrator import ResultIntegrator
from agent.core.nodes.feedback_generator import FeedbackGenerator

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
                "interview_cases": []
            }
        
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        for test_case in self.test_data["interview_cases"]:
            # 1. 任务解析
            state = GraphState()
            state.user_context.interview_data = test_case["interview_data"]
            state = self.task_parser.execute(state)
            
            self.assertIsNotNone(state.task_state.tasks, "任务解析失败")
            self.assertGreater(len(state.task_state.tasks), 0, "未生成任何任务")
            
            # 2. 策略决策
            state = self.strategy_decider.execute(state)
            
            self.assertIsNotNone(state.task_state.strategy, "策略决策失败")
            self.assertIsNotNone(state.task_state.priority, "未设置任务优先级")
            
            # 3. 任务规划
            state = self.task_planner.execute(state)
            
            self.assertIsNotNone(state.task_state.execution_plan, "任务规划失败")
            self.assertGreater(len(state.task_state.execution_plan), 0, "执行计划为空")
            
            # 4. 分析执行
            state = self.analyzer_executor.execute(state)
            
            self.assertIsNotNone(state.analysis_state.results, "分析执行失败")
            self.assertEqual(len(state.analysis_state.results), len(state.task_state.tasks), "分析结果数量不匹配")
            
            # 5. 结果整合
            state = self.result_integrator.execute(state)
            
            self.assertIsNotNone(state.analysis_state.result, "结果整合失败")
            self.assertIsNotNone(state.analysis_state.result.score, "未生成最终得分")
            
            # 6. 反馈生成
            state = self.feedback_generator.execute(state)
            
            self.assertIsNotNone(state.feedback_state.feedback, "反馈生成失败")
            self.assertGreater(len(state.feedback_state.feedback), 0, "反馈内容为空")
    
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
        state = self.task_parser.execute(state)
        
        # 验证错误处理
        self.assertIsNotNone(state.error, "未检测到错误")
        self.assertEqual(len(state.task_state.tasks), 0, "生成了无效任务")
    
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
        state.task_state.parallel_execution = True
        
        # 3. 执行分析
        state = self.analyzer_executor.execute(state)
        
        # 验证并行执行结果
        self.assertIsNotNone(state.analysis_state.results, "并行执行失败")
        self.assertEqual(len(state.analysis_state.results), len(state.task_state.tasks), "并行执行结果数量不匹配")
    
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
        
        # 保存初始状态
        initial_state = state.to_dict()
        
        # 执行各个节点
        state = self.task_parser.execute(state)
        state = self.strategy_decider.execute(state)
        state = self.task_planner.execute(state)
        state = self.analyzer_executor.execute(state)
        state = self.result_integrator.execute(state)
        state = self.feedback_generator.execute(state)
        
        # 保存最终状态
        final_state = state.to_dict()
        
        # 验证状态变化
        self.assertNotEqual(initial_state, final_state, "状态未发生变化")
        self.assertIsNotNone(final_state["analysis_state"]["result"], "最终状态缺少分析结果")
        self.assertIsNotNone(final_state["feedback_state"]["feedback"], "最终状态缺少反馈内容")


if __name__ == '__main__':
    unittest.main() 