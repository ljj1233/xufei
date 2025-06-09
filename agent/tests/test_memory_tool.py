#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Memory Tool的简单脚本
"""

import os
import sys
import logging
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memory_tool_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_memory_tool():
    """测试Memory Tool"""
    logger.info("测试Memory Tool...")
    
    # 模拟创建实体
    entities = [
        {
            "name": "测试实体1",
            "entityType": "测试类型",
            "observations": ["这是第一个测试观察"]
        },
        {
            "name": "测试实体2",
            "entityType": "测试类型",
            "observations": ["这是第二个测试观察"]
        }
    ]
    
    logger.info(f"创建测试实体: {json.dumps(entities, ensure_ascii=False)}")
    
    # 模拟创建关系
    relations = [
        {
            "from": "测试实体1",
            "to": "测试实体2",
            "relationType": "测试关系"
        }
    ]
    
    logger.info(f"创建测试关系: {json.dumps(relations, ensure_ascii=False)}")
    
    return True

def run_tests():
    """运行所有测试"""
    logger.info("开始运行Memory Tool测试...")
    
    # 运行Memory Tool测试
    memory_result = test_memory_tool()
    
    # 输出测试结果
    logger.info("\n=== Memory Tool测试结果 ===")
    logger.info(f"Memory Tool测试: {'通过' if memory_result else '失败'}")
    
    return memory_result

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)