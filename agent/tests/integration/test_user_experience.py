# -*- coding: utf-8 -*-
"""
用户体验测试模块

测试系统的易用性和响应性
"""

import unittest
import logging
import time
from typing import Dict, Any, List
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

class UserExperienceTest(unittest.TestCase):
    """用户体验测试类"""
    
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
        
        # 设置响应时间阈值（秒）
        self.response_thresholds = {
            "task_parser": 1.0,
            "strategy_decider": 1.0,
            "task_planner": 1.0,
            "analyzer_executor": 5.0,
            "result_integrator": 1.0,
            "feedback_generator": 2.0
        }
    
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
    
    def test_response_time(self):
        """测试响应时间"""
        for scenario in self.test_data["user_scenarios"]:
            state = GraphState()
            state.user_context.interview_data = scenario["interview_data"]
            
            # 测试各个节点的响应时间
            response_times = {}
            
            # 1. 任务解析
            start_time = time.time()
            state = self.task_parser.execute(state)
            response_times["task_parser"] = time.time() - start_time
            
            # 2. 策略决策
            start_time = time.time()
            state = self.strategy_decider.execute(state)
            response_times["strategy_decider"] = time.time() - start_time
            
            # 3. 任务规划
            start_time = time.time()
            state = self.task_planner.execute(state)
            response_times["task_planner"] = time.time() - start_time
            
            # 4. 分析执行
            start_time = time.time()
            state = self.analyzer_executor.execute(state)
            response_times["analyzer_executor"] = time.time() - start_time
            
            # 5. 结果整合
            start_time = time.time()
            state = self.result_integrator.execute(state)
            response_times["result_integrator"] = time.time() - start_time
            
            # 6. 反馈生成
            start_time = time.time()
            state = self.feedback_generator.execute(state)
            response_times["feedback_generator"] = time.time() - start_time
            
            # 验证响应时间
            for node, response_time in response_times.items():
                threshold = self.response_thresholds[node]
                self.assertLess(
                    response_time,
                    threshold,
                    f"{node} 响应时间 {response_time:.2f}秒 超过阈值 {threshold}秒"
                )
    
    def test_feedback_quality(self):
        """测试反馈质量"""
        for scenario in self.test_data["user_scenarios"]:
            state = GraphState()
            state.user_context.interview_data = scenario["interview_data"]
            
            # 执行完整流程
            state = self.task_parser.execute(state)
            state = self.strategy_decider.execute(state)
            state = self.task_planner.execute(state)
            state = self.analyzer_executor.execute(state)
            state = self.result_integrator.execute(state)
            state = self.feedback_generator.execute(state)
            
            # 验证反馈质量
            feedback = state.feedback_state.feedback
            
            # 1. 检查反馈完整性
            self.assertIsNotNone(feedback, "反馈为空")
            self.assertGreater(len(feedback), 0, "反馈内容为空")
            
            # 2. 检查反馈结构
            self.assertIn("overall_score", feedback, "缺少总体评分")
            self.assertIn("strengths", feedback, "缺少优点分析")
            self.assertIn("weaknesses", feedback, "缺少缺点分析")
            self.assertIn("suggestions", feedback, "缺少改进建议")
            
            # 3. 检查反馈内容质量
            self.assertGreater(len(feedback["strengths"]), 0, "优点分析为空")
            self.assertGreater(len(feedback["weaknesses"]), 0, "缺点分析为空")
            self.assertGreater(len(feedback["suggestions"]), 0, "改进建议为空")
            
            # 4. 检查反馈相关性
            self.assertIsInstance(feedback["overall_score"], (int, float), "评分格式错误")
            self.assertGreaterEqual(feedback["overall_score"], 0, "评分小于0")
            self.assertLessEqual(feedback["overall_score"], 10, "评分大于10")
    
    def test_error_messages(self):
        """测试错误提示"""
        # 测试各种错误情况
        error_cases = [
            {
                "name": "空输入",
                "interview_data": {
                    "audio": None,
                    "video": None,
                    "text": ""
                }
            },
            {
                "name": "无效文件",
                "interview_data": {
                    "audio": "nonexistent.wav",
                    "video": "nonexistent.mp4",
                    "text": "测试文本"
                }
            },
            {
                "name": "格式错误",
                "interview_data": {
                    "audio": "test.txt",
                    "video": "test.txt",
                    "text": "测试文本"
                }
            }
        ]
        
        for case in error_cases:
            state = GraphState()
            state.user_context.interview_data = case["interview_data"]
            
            # 执行流程
            state = self.task_parser.execute(state)
            
            # 验证错误提示
            self.assertIsNotNone(state.error, f"{case['name']} 未检测到错误")
            self.assertGreater(len(state.error), 0, f"{case['name']} 错误提示为空")
            self.assertIn("错误", state.error, f"{case['name']} 错误提示不明确")
    
    def test_progress_indication(self):
        """测试进度指示"""
        state = GraphState()
        state.user_context.interview_data = self.test_data["user_scenarios"][0]["interview_data"]
        
        # 执行流程并检查状态变化
        progress_states = []
        
        # 1. 任务解析
        state = self.task_parser.execute(state)
        progress_states.append({
            "stage": "task_parser",
            "tasks_count": len(state.task_state.tasks),
            "has_error": state.error is not None
        })
        
        # 2. 策略决策
        state = self.strategy_decider.execute(state)
        progress_states.append({
            "stage": "strategy_decider",
            "has_strategy": state.task_state.strategy is not None,
            "has_priority": state.task_state.priority is not None
        })
        
        # 3. 任务规划
        state = self.task_planner.execute(state)
        progress_states.append({
            "stage": "task_planner",
            "has_plan": state.task_state.execution_plan is not None,
            "plan_length": len(state.task_state.execution_plan)
        })
        
        # 4. 分析执行
        state = self.analyzer_executor.execute(state)
        progress_states.append({
            "stage": "analyzer_executor",
            "results_count": len(state.analysis_state.results),
            "has_error": state.error is not None
        })
        
        # 5. 结果整合
        state = self.result_integrator.execute(state)
        progress_states.append({
            "stage": "result_integrator",
            "has_result": state.analysis_state.result is not None,
            "has_score": state.analysis_state.result.score is not None
        })
        
        # 6. 反馈生成
        state = self.feedback_generator.execute(state)
        progress_states.append({
            "stage": "feedback_generator",
            "has_feedback": state.feedback_state.feedback is not None,
            "feedback_length": len(state.feedback_state.feedback)
        })
        
        # 验证进度状态
        for state in progress_states:
            self.assertIsNotNone(state, f"{state['stage']} 状态为空")
            self.assertGreater(len(state), 1, f"{state['stage']} 状态信息不完整")


if __name__ == '__main__':
    unittest.main() 