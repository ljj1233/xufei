# -*- coding: utf-8 -*-
"""
性能测试模块

包含基准测试和性能监控功能
"""

import unittest
import time
import logging
import statistics
from typing import Dict, List, Any
import json
import os
from pathlib import Path
import uuid

from agent.src.core.workflow.state import GraphState, TaskType, TaskStatus
from agent.src.nodes.analyzer_executor import AnalyzerExecutor
from agent.src.core.analyzer_adapter import create_adapter

logger = logging.getLogger(__name__)

class PerformanceTest(unittest.TestCase):
    """性能测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.executor = AnalyzerExecutor()
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # 加载测试数据
        self.test_data = self._load_test_data()
    
    def _load_test_data(self) -> Dict[str, Any]:
        """加载测试数据
        
        Returns:
            Dict[str, Any]: 测试数据
        """
        # 这里应该实际加载测试数据，但简化起见，使用模拟数据
        return {
            "speech": [{"name": f"speech_test_{i}", "audio_file": f"test_audio_{i}.wav"} for i in range(5)],
            "visual": [{"name": f"visual_test_{i}", "video_file": f"test_video_{i}.mp4"} for i in range(5)],
            "content": [{"name": f"content_test_{i}", "transcript": f"这是测试文本内容 {i}"} for i in range(5)]
        }
    
    def test_speech_analysis_performance(self):
        """测试语音分析性能"""
        results = []
        
        for test_case in self.test_data["speech"]:
            start_time = time.time()
            
            # 创建测试状态
            state = GraphState()
            state.task_state.tasks = [{
                "id": str(uuid.uuid4()),  # 添加唯一ID
                "task_type": TaskType.SPEECH_ANALYSIS,
                "status": TaskStatus.PENDING,
                "data": test_case
            }]
            
            # 执行分析
            result = self.executor.execute(state)
            
            # 记录性能指标
            elapsed = time.time() - start_time
            results.append({
                "case": test_case["name"],
                "elapsed": elapsed,
                "success": result.error is None,
                "score": result.analysis_state.results[0].score if result.analysis_state.results else 0
            })
        
        # 计算统计指标
        elapsed_times = [r["elapsed"] for r in results]
        stats = {
            "mean": statistics.mean(elapsed_times),
            "median": statistics.median(elapsed_times),
            "std": statistics.stdev(elapsed_times) if len(elapsed_times) > 1 else 0,
            "min": min(elapsed_times),
            "max": max(elapsed_times)
        }
        
        # 保存结果
        self._save_results("speech_performance", results, stats)
        
        # 验证性能要求
        self.assertLess(stats["mean"], 2.0, "语音分析平均耗时超过2秒")
        self.assertLess(stats["max"], 5.0, "语音分析最大耗时超过5秒")
    
    def test_visual_analysis_performance(self):
        """测试视觉分析性能"""
        results = []
        
        for test_case in self.test_data["visual"]:
            start_time = time.time()
            
            # 创建测试状态
            state = GraphState()
            state.task_state.tasks = [{
                "id": str(uuid.uuid4()),  # 添加唯一ID
                "task_type": TaskType.VISUAL_ANALYSIS,
                "status": TaskStatus.PENDING,
                "data": test_case
            }]
            
            # 执行分析
            result = self.executor.execute(state)
            
            # 记录性能指标
            elapsed = time.time() - start_time
            results.append({
                "case": test_case["name"],
                "elapsed": elapsed,
                "success": result.error is None,
                "score": result.analysis_state.results[0].score if result.analysis_state.results else 0
            })
        
        # 计算统计指标
        elapsed_times = [r["elapsed"] for r in results]
        stats = {
            "mean": statistics.mean(elapsed_times),
            "median": statistics.median(elapsed_times),
            "std": statistics.stdev(elapsed_times) if len(elapsed_times) > 1 else 0,
            "min": min(elapsed_times),
            "max": max(elapsed_times)
        }
        
        # 保存结果
        self._save_results("visual_performance", results, stats)
        
        # 验证性能要求
        self.assertLess(stats["mean"], 3.0, "视觉分析平均耗时超过3秒")
        self.assertLess(stats["max"], 8.0, "视觉分析最大耗时超过8秒")
    
    def test_content_analysis_performance(self):
        """测试内容分析性能"""
        results = []
        
        for test_case in self.test_data["content"]:
            start_time = time.time()
            
            # 创建测试状态
            state = GraphState()
            state.task_state.tasks = [{
                "id": str(uuid.uuid4()),  # 添加唯一ID
                "task_type": TaskType.CONTENT_ANALYSIS,
                "status": TaskStatus.PENDING,
                "data": test_case
            }]
            
            # 执行分析
            result = self.executor.execute(state)
            
            # 记录性能指标
            elapsed = time.time() - start_time
            results.append({
                "case": test_case["name"],
                "elapsed": elapsed,
                "success": result.error is None,
                "score": result.analysis_state.results[0].score if result.analysis_state.results else 0
            })
        
        # 计算统计指标
        elapsed_times = [r["elapsed"] for r in results]
        stats = {
            "mean": statistics.mean(elapsed_times),
            "median": statistics.median(elapsed_times),
            "std": statistics.stdev(elapsed_times) if len(elapsed_times) > 1 else 0,
            "min": min(elapsed_times),
            "max": max(elapsed_times)
        }
        
        # 保存结果
        self._save_results("content_performance", results, stats)
        
        # 验证性能要求
        self.assertLess(stats["mean"], 1.0, "内容分析平均耗时超过1秒")
        self.assertLess(stats["max"], 3.0, "内容分析最大耗时超过3秒")
    
    def test_concurrent_performance(self):
        """测试并发性能"""
        results = []
        
        # 创建混合任务
        tasks = []
        for test_case in self.test_data["speech"][:2]:
            tasks.append({
                "id": str(uuid.uuid4()),  # 添加唯一ID
                "task_type": TaskType.SPEECH_ANALYSIS,
                "status": TaskStatus.PENDING,
                "data": test_case
            })
        
        for test_case in self.test_data["visual"][:2]:
            tasks.append({
                "id": str(uuid.uuid4()),  # 添加唯一ID
                "task_type": TaskType.VISUAL_ANALYSIS,
                "status": TaskStatus.PENDING,
                "data": test_case
            })
        
        for test_case in self.test_data["content"][:2]:
            tasks.append({
                "id": str(uuid.uuid4()),  # 添加唯一ID
                "task_type": TaskType.CONTENT_ANALYSIS,
                "status": TaskStatus.PENDING,
                "data": test_case
            })
        
        # 执行并发测试
        start_time = time.time()
        
        state = GraphState()
        state.task_state.tasks = tasks
        state.task_state.parallel_execution = True
        
        result = self.executor.execute(state)
        
        elapsed = time.time() - start_time
        
        # 记录性能指标
        results.append({
            "total_tasks": len(tasks),
            "elapsed": elapsed,
            "success": result.error is None,
            "completed_tasks": len(result.analysis_state.results)
        })
        
        # 保存结果
        self._save_results("concurrent_performance", results, {})
        
        # 验证性能要求
        self.assertLess(elapsed, 10.0, "并发执行总耗时超过10秒")
        self.assertEqual(len(result.analysis_state.results), len(tasks), "并发执行任务完成数量不匹配")
    
    def _save_results(self, test_name: str, results: List[Dict], stats: Dict):
        """保存测试结果
        
        Args:
            test_name: 测试名称
            results: 测试结果列表
            stats: 统计指标
        """
        output = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": results,
            "statistics": stats
        }
        
        result_file = self.results_dir / f"{test_name}_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"性能测试结果已保存到: {result_file}")


if __name__ == '__main__':
    unittest.main() 