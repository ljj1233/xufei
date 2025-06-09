#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行MCP工具测试的脚本

此脚本用于测试FileSystem Tool和Memory Tool等MCP工具的功能
"""

import os
import sys
import time
import logging
import subprocess
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_tool_tests.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# MCP工具测试文件
MCP_TOOL_TEST_FILES = [
    'test_mcp_tools.py',
    'test_memory_tool.py',
    'test_memory_mcp.py'
]

def run_single_test(test_file):
    """运行单个测试文件"""
    test_path = Path(__file__).parent / test_file
    if not test_path.exists():
        logger.error(f"测试文件不存在: {test_path}")
        return False
    
    logger.info(f"运行测试: {test_file}")
    
    try:
        # 使用Python运行测试
        result = subprocess.run(
            ['python', str(test_path)],
            capture_output=True,
            text=True,
            check=False
        )
        
        # 输出测试结果
        logger.info(f"测试结果 ({test_file}):")
        logger.info(result.stdout)
        
        if result.returncode != 0:
            logger.error(f"测试失败 ({test_file}):")
            logger.error(result.stderr)
            return False
        
        return True
    except Exception as e:
        logger.error(f"运行测试时出错 ({test_file}): {str(e)}")
        return False

def run_all_mcp_tool_tests():
    """运行所有MCP工具测试"""
    start_time = time.time()
    logger.info("开始运行MCP工具测试...")
    
    results = {}
    all_passed = True
    
    for test_file in MCP_TOOL_TEST_FILES:
        success = run_single_test(test_file)
        results[test_file] = "通过" if success else "失败"
        all_passed = all_passed and success
    
    # 输出测试摘要
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info("\n=== MCP工具测试结果摘要 ===")
    for test_file, result in results.items():
        logger.info(f"{test_file}: {result}")
    logger.info(f"总耗时: {duration:.2f}秒")
    logger.info(f"总体结果: {'全部通过' if all_passed else '部分失败'}")
    
    return all_passed

if __name__ == '__main__':
    success = run_all_mcp_tool_tests()
    sys.exit(0 if success else 1)