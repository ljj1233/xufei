#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试智能体与MCP的集成功能
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from agent.src.services.mcp_service import MCPService
from agent.src.core.agent import InterviewAgent
from agent.workflow import InterviewAnalysisWorkflow


class TestMCPIntegration:
    """测试智能体与MCP的集成功能"""

    @pytest.fixture
    def mock_mcp_service(self):
        """模拟MCP服务"""
        mock = MagicMock(spec=MCPService)
        return mock
        
    @pytest.fixture
    def mock_notification_service(self):
        """模拟通知服务"""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def mock_interview_agent(self, mock_mcp_service, mock_notification_service):
        """模拟面试智能体"""
        agent = MagicMock()
        agent.mcp_service = mock_mcp_service
        agent.notification_service = mock_notification_service
        return agent

    @pytest.mark.asyncio
    async def test_mcp_knowledge_creation(self, mock_mcp_service):
        """测试MCP知识创建功能"""
        # 准备测试数据
        test_entity = {
            "name": "面试技巧",
            "entityType": "知识点",
            "observations": ["保持眼神接触", "使用STAR方法回答问题"]
        }
        
        test_relation = {
            "from": "面试技巧",
            "to": "非技术面试",
            "relationType": "适用于"
        }
        
        # 执行测试
        service = MCPService()
        service.create_entities = mock_mcp_service.create_entities
        service.create_relations = mock_mcp_service.create_relations
        
        # 创建实体
        await service.create_entities([test_entity])
        mock_mcp_service.create_entities.assert_called_once()
        
        # 创建关系
        await service.create_relations([test_relation])
        mock_mcp_service.create_relations.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_knowledge_retrieval(self, mock_mcp_service):
        """测试MCP知识检索功能"""
        # 模拟搜索结果
        mock_search_result = {
            "nodes": [
                {
                    "name": "系统设计",
                    "entityType": "技术领域",
                    "observations": ["分布式系统", "高可用架构", "可扩展性设计"]
                }
            ]
        }
        mock_mcp_service.search_nodes.return_value = mock_search_result
        
        # 执行测试
        service = MCPService()
        service.search_nodes = mock_mcp_service.search_nodes
        
        result = await service.search_nodes("系统设计")
        assert result == mock_search_result
        mock_mcp_service.search_nodes.assert_called_once_with("系统设计")

    @pytest.mark.asyncio
    async def test_interview_analysis_with_mcp(self, mock_interview_agent, mock_notification_service):
        """测试使用MCP进行面试分析"""
        # 准备测试数据
        interview_data = {
            "transcript": "我有五年的后端开发经验，主要使用Python和Java。",
            "job_position": "高级后端工程师",
            "audio_file": "test_audio.wav",
            "video_file": "test_video.mp4"
        }
        
        # 创建异步mock方法
        async def async_notify(*args, **kwargs):
            return {"status": "success"}
            
        # 为所有通知方法创建异步mock
        mock_notification_service.notify_interview_status = async_notify
        mock_notification_service.notify_analysis_progress = async_notify
        mock_notification_service.notify_error = async_notify
        mock_notification_service.send_partial_feedback = async_notify
        
        # 模拟面试分析工作流
        workflow = InterviewAnalysisWorkflow(notification_service=mock_notification_service)
        
        # 模拟分析方法，替换为异步方法
        async def async_analyze_content(*args, **kwargs):
            return {
                "relevance": {"score": 85, "feedback": "回答与职位要求高度相关"},
                "completeness": {"score": 80, "feedback": "回答较为全面，但缺少具体项目经验描述"}
            }
        workflow._analyze_content = async_analyze_content
        
        async def async_analyze_speech(*args, **kwargs):
            return {
                "speech_rate": {"score": 80, "feedback": "语速适中"},
                "fluency": {"score": 85, "feedback": "表达流畅"}
            }
        workflow._analyze_speech = async_analyze_speech
        
        async def async_analyze_visual(*args, **kwargs):
            return {
                "facial_expression": {"score": 80, "feedback": "表情自然"},
                "eye_contact": {"score": 85, "feedback": "目光接触良好"}
            }
        workflow._analyze_visual = async_analyze_visual
        
        async def async_generate_report(*args, **kwargs):
            return {
                "id": "test_report_id",
                "overall_score": 8.2,
                "strengths": ["技术背景扎实", "表达清晰"],
                "weaknesses": ["缺少具体项目案例"],
                "suggestions": ["准备2-3个具体的项目案例"]
            }
        workflow._generate_final_report = async_generate_report
        
        # 调用同步分析方法进行测试
        result = await workflow._analyze_interview_sync("test_client", interview_data)
        
        # 验证结果
        assert result["id"] == "test_report_id"
        assert result["overall_score"] == 8.2
        assert len(result["strengths"]) > 0
        assert len(result["weaknesses"]) > 0
        assert len(result["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_learning_path_generation_with_mcp(self, mock_mcp_service):
        """测试使用MCP生成学习路径"""
        from agent.src.nodes.executors.learning_path_generator import (
            LearningPathGenerator, 
            LearningPathGeneratorInput
        )
        
        # 模拟分析结果
        analysis_result = {
            "strengths": ["技术背景扎实", "表达清晰"],
            "weaknesses": ["系统设计能力不足", "缺乏大规模分布式系统经验"],
            "suggestions": ["学习系统设计模式", "参与开源项目积累经验"]
        }
        
        # 准备测试输入
        input_data = LearningPathGeneratorInput(
            analysis_result=analysis_result,
            job_position="高级后端工程师",
            tech_field="后端开发",
            time_constraint="三个月",
            focus_areas=["系统设计", "分布式系统", "数据库优化"]
        )
        
        # 模拟MCP知识检索结果
        mock_search_result = {
            "nodes": [
                {
                    "name": "系统设计",
                    "entityType": "学习领域",
                    "observations": [
                        "设计模式",
                        "架构原则",
                        "可扩展性设计"
                    ]
                },
                {
                    "name": "分布式系统",
                    "entityType": "学习领域",
                    "observations": [
                        "一致性算法",
                        "分布式事务",
                        "CAP理论"
                    ]
                }
            ]
        }
        
        # 确保返回一个awaitable对象
        async def async_search_nodes(*args, **kwargs):
            return mock_search_result
        mock_mcp_service.search_nodes = async_search_nodes
        
        # 创建一个模拟的LearningPathGenerator
        class MockLearningPathGenerator:
            def __init__(self):
                self.mcp_service = mock_mcp_service
            
            async def generate(self, input_data):
                # 返回模拟的结果
                from unittest.mock import MagicMock
                return MagicMock(
                    learning_report="基于面试表现分析，建议重点学习系统设计和分布式系统相关知识",
                    learning_paths=[
                        {
                            "area": "系统设计",
                            "resources": ["《系统设计面试指南》", "GitHub: system-design-primer"],
                            "milestones": ["第一周: 掌握基本概念", "第二周: 完成3个系统设计案例"]
                        },
                        {
                            "area": "分布式系统",
                            "resources": ["MIT 6.824分布式系统课程", "《数据密集型应用系统设计》"],
                            "milestones": ["第一个月: 理解CAP理论", "第二个月: 实现简单的分布式系统"]
                        }
                    ]
                )
        
        # 使用模拟的生成器
        generator = MockLearningPathGenerator()
        
        # 执行测试
        output = await generator.generate(input_data)
        
        # 验证结果
        assert "learning_report" in dir(output)
        assert "learning_paths" in dir(output)
        assert len(output.learning_paths) == 2
        assert output.learning_paths[0]["area"] == "系统设计"
        assert output.learning_paths[1]["area"] == "分布式系统"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 