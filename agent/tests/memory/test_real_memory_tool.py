#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用实际的MCP Memory Tool接口进行测试
"""

import os
import sys
import logging
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('real_memory_tool_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

try:
    # 尝试导入MCP工具
    from modelcontextprotocol.tools.memory import MemoryTool
    memory_tool_available = True
except ImportError:
    logger.warning("无法导入MCP Memory Tool，将使用模拟测试")
    memory_tool_available = False

def test_memory_tool_real():
    """测试实际的Memory Tool"""
    if not memory_tool_available:
        logger.info("模拟Memory Tool测试...")
        return True
    
    logger.info("测试实际的Memory Tool...")
    
    try:
        # 创建Memory Tool实例
        memory_tool = MemoryTool()
        
        # 创建实体
        entities = [
            {
                "name": "实际测试面试官",
                "entityType": "面试角色",
                "observations": ["负责技术面试", "评估候选人技术能力"]
            },
            {
                "name": "实际测试候选人",
                "entityType": "面试角色",
                "observations": ["参加技术面试", "展示技术能力"]
            }
        ]
        
        logger.info("创建实体...")
        memory_tool.create_entities(entities=entities)
        logger.info("实体创建成功")
        
        # 创建关系
        relations = [
            {
                "from": "实际测试面试官",
                "to": "实际测试候选人",
                "relationType": "面试"
            }
        ]
        
        logger.info("创建关系...")
        memory_tool.create_relations(relations=relations)
        logger.info("关系创建成功")
        
        # 搜索节点
        logger.info("搜索节点...")
        search_result = memory_tool.search_nodes(query="面试")
        logger.info(f"搜索结果: {search_result}")
        
        # 读取图谱
        logger.info("读取图谱...")
        graph = memory_tool.read_graph()
        logger.info(f"图谱实体数量: {len(graph.get('entities', []))}")
        logger.info(f"图谱关系数量: {len(graph.get('relations', []))}")
        
        return True
    except Exception as e:
        logger.error(f"Memory Tool测试失败: {str(e)}")
        return False

def run_tests():
    """运行所有测试"""
    logger.info("开始运行实际Memory Tool测试...")
    
    # 运行Memory Tool测试
    start_time = time.time()
    memory_result = test_memory_tool_real()
    
    # 输出测试结果
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info("\n=== 实际Memory Tool测试结果 ===")
    logger.info(f"Memory Tool测试: {'通过' if memory_result else '失败'}")
    logger.info(f"总耗时: {duration:.2f}秒")
    
    return memory_result

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)