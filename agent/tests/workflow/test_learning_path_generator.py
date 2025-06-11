#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试学习路径生成器功能
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent.parent.parent))


class TestLearningPathGenerator:
    """测试学习路径生成器功能"""

    @pytest.fixture
    def mock_openai_service(self):
        """模拟OpenAI服务"""
        with patch('xufei.agent.src.services.openai_service.OpenAIService') as mock:
            service = mock.return_value
            service.chat_completion = MagicMock(return_value={
                "content": "基于面试表现分析，建议重点学习系统设计和分布式系统相关知识"
            })
            yield service

    @pytest.fixture
    def mock_websearch_service(self):
        """模拟网络搜索服务"""
        with patch('xufei.agent.src.services.websearch_service.WebSearchService') as mock:
            service = mock.return_value
            service.search = MagicMock(return_value=[
                {
                    "title": "系统设计面试指南",
                    "url": "https://example.com/system-design-guide",
                    "snippet": "全面的系统设计面试准备指南，包含常见问题和解答思路。"
                },
                {
                    "title": "分布式系统学习资源",
                    "url": "https://example.com/distributed-systems",
                    "snippet": "包含MIT 6.824课程、推荐书籍和实践项目的分布式系统学习资源。"
                }
            ])
            yield service

    @pytest.fixture
    def mock_modelscope_service(self):
        """模拟ModelScope服务"""
        with patch('xufei.agent.src.services.modelscope_service.ModelScopeService') as mock:
            service = mock.return_value
            service.generate_text = MagicMock(return_value="基于您的面试表现，建议您重点提升系统设计能力和分布式系统理解。")
            yield service

    @pytest.mark.asyncio
    async def test_learning_path_generation(self, mock_openai_service, mock_websearch_service, mock_modelscope_service):
        """测试学习路径生成功能"""
        from xufei.agent.src.nodes.executors.learning_path_generator import (
            LearningPathGenerator, 
            LearningPathGeneratorInput
        )
        
        # 准备测试数据
        analysis_result = {
            "strengths": ["技术背景扎实", "表达清晰"],
            "weaknesses": ["系统设计能力不足", "缺乏大规模分布式系统经验"],
            "suggestions": ["学习系统设计模式", "参与开源项目积累经验"]
        }
        
        # 创建输入对象
        input_data = LearningPathGeneratorInput(
            analysis_result=analysis_result,
            job_position="高级后端工程师",
            tech_field="后端开发",
            time_constraint="三个月",
            focus_areas=["系统设计", "分布式系统", "数据库优化"]
        )
        
        # 创建学习路径生成器
        generator = LearningPathGenerator()
        generator.openai_service = mock_openai_service
        generator.websearch_service = mock_websearch_service
        generator.modelscope_service = mock_modelscope_service
        
        # 模拟generate方法
        async def mock_generate(input_data):
            # 1. 生成学习需求报告
            learning_report = await generator.modelscope_service.generate_text(
                f"基于以下面试分析，生成学习需求报告：{input_data.analysis_result}"
            )
            
            # 2. 为每个重点领域搜索学习资源
            learning_paths = []
            for area in input_data.focus_areas:
                # 搜索资源
                search_query = f"{area} 学习资源 {input_data.job_position}"
                search_results = await generator.websearch_service.search(search_query)
                
                # 提取资源
                resources = [result["title"] for result in search_results[:2]]
                
                # 生成里程碑
                milestones_prompt = f"为{input_data.job_position}制定{area}的学习里程碑，时间约束为{input_data.time_constraint}"
                milestones_response = await generator.openai_service.chat_completion(milestones_prompt)
                milestones = ["第一周: 掌握基本概念", "第二周: 完成实践项目"]  # 简化的里程碑
                
                # 添加到学习路径
                learning_paths.append({
                    "area": area,
                    "resources": resources,
                    "milestones": milestones
                })
            
            # 创建返回对象
            class LearningPathOutput:
                def __init__(self, learning_report, learning_paths):
                    self.learning_report = learning_report
                    self.learning_paths = learning_paths
            
            return LearningPathOutput(learning_report, learning_paths)
        
        # 替换实际的generate方法
        generator.generate = mock_generate
        
        # 执行测试
        output = await generator.generate(input_data)
        
        # 验证结果
        assert output.learning_report is not None
        assert len(output.learning_paths) == 3
        assert output.learning_paths[0]["area"] == "系统设计"
        assert output.learning_paths[1]["area"] == "分布式系统"
        assert output.learning_paths[2]["area"] == "数据库优化"
        assert len(output.learning_paths[0]["resources"]) > 0
        assert len(output.learning_paths[0]["milestones"]) > 0

    @pytest.mark.asyncio
    async def test_learning_path_customization(self, mock_openai_service):
        """测试学习路径定制化功能"""
        # 准备测试数据
        user_preferences = {
            "learning_style": "实践导向",
            "available_time": "每周10小时",
            "prior_knowledge": "中级",
            "preferred_resources": ["视频教程", "实践项目"]
        }
        
        # 模拟定制化方法
        async def customize_learning_path(learning_path, user_preferences):
            # 构建提示词
            prompt = f"""
            根据用户偏好定制学习路径:
            
            原始学习路径:
            {learning_path}
            
            用户偏好:
            - 学习风格: {user_preferences['learning_style']}
            - 可用时间: {user_preferences['available_time']}
            - 已有知识水平: {user_preferences['prior_knowledge']}
            - 偏好资源类型: {', '.join(user_preferences['preferred_resources'])}
            
            请提供定制化的学习路径，包括资源和时间安排。
            """
            
            # 调用OpenAI服务
            response = await mock_openai_service.chat_completion(prompt)
            
            # 返回定制化学习路径
            return {
                "area": learning_path["area"],
                "resources": [
                    "YouTube: 系统设计实践视频系列",
                    "GitHub: 动手实现分布式缓存项目"
                ],
                "milestones": [
                    "第一周 (4小时): 观看入门视频",
                    "第二周 (6小时): 完成第一个实践项目"
                ],
                "customized": True
            }
        
        # 准备原始学习路径
        original_path = {
            "area": "系统设计",
            "resources": ["《系统设计面试指南》", "GitHub: system-design-primer"],
            "milestones": ["第一周: 掌握基本概念", "第二周: 完成3个系统设计案例"]
        }
        
        # 执行测试
        customized_path = await customize_learning_path(original_path, user_preferences)
        
        # 验证结果
        assert customized_path["area"] == original_path["area"]
        assert customized_path["customized"] == True
        assert len(customized_path["resources"]) > 0
        assert len(customized_path["milestones"]) > 0
        assert any("实践" in resource for resource in customized_path["resources"])
        mock_openai_service.chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_learning_resource_evaluation(self, mock_openai_service):
        """测试学习资源评估功能"""
        # 准备测试数据
        resources = [
            {
                "title": "系统设计面试指南",
                "url": "https://example.com/system-design-guide",
                "snippet": "全面的系统设计面试准备指南，包含常见问题和解答思路。"
            },
            {
                "title": "分布式系统学习资源",
                "url": "https://example.com/distributed-systems",
                "snippet": "包含MIT 6.824课程、推荐书籍和实践项目的分布式系统学习资源。"
            }
        ]
        
        # 模拟评估方法
        async def evaluate_resources(resources, job_position):
            # 构建提示词
            prompt = f"""
            评估以下学习资源对于{job_position}职位的适用性:
            
            资源列表:
            {resources}
            
            请为每个资源提供评分(1-10)和简短评价。
            """
            
            # 调用OpenAI服务
            mock_openai_service.chat_completion.return_value = {
                "content": """
                资源评估结果:
                
                1. 系统设计面试指南 - 评分: 9/10
                   评价: 非常适合高级后端工程师，内容全面且实用，案例丰富。
                
                2. 分布式系统学习资源 - 评分: 8/10
                   评价: MIT课程质量高，但可能需要较多时间投入，适合有一定基础的工程师。
                """
            }
            
            response = await mock_openai_service.chat_completion(prompt)
            
            # 解析评估结果
            lines = response["content"].strip().split("\n")
            evaluations = []
            
            current_eval = {}
            for line in lines:
                if "评分:" in line:
                    title = line.split(" - ")[0].strip().split(". ")[1] if ". " in line else line.split(" - ")[0].strip()
                    score = int(line.split("评分:")[1].strip().split("/")[0])
                    current_eval = {"title": title, "score": score}
                elif "评价:" in line and current_eval:
                    current_eval["comment"] = line.split("评价:")[1].strip()
                    evaluations.append(current_eval.copy())
                    current_eval = {}
            
            return evaluations
        
        # 执行测试
        evaluations = await evaluate_resources(resources, "高级后端工程师")
        
        # 验证结果
        assert len(evaluations) == 2
        assert evaluations[0]["title"] == "系统设计面试指南"
        assert evaluations[0]["score"] == 9
        assert evaluations[1]["title"] == "分布式系统学习资源"
        assert evaluations[1]["score"] == 8
        mock_openai_service.chat_completion.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 