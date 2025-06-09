#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行所有测试的主脚本

此脚本用于运行所有测试，包括MCP工具测试和其他测试
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
        logging.FileHandler('all_tests.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_test_script(script_name):
    """运行测试脚本"""
    logger.info(f"运行测试脚本: {script_name}")
    
    try:
        # 使用Python运行测试脚本
        result = subprocess.run(
            ['python', script_name],
            capture_output=True,
            text=True,
            check=False
        )
        
        # 输出测试结果
        logger.info(f"测试脚本结果 ({script_name}):")
        logger.info(result.stdout)
        
        if result.returncode != 0:
            logger.error(f"测试脚本失败 ({script_name}):")
            logger.error(result.stderr)
            return False
        
        return True
    except Exception as e:
        logger.error(f"运行测试脚本时出错 ({script_name}): {str(e)}")
        return False

def run_all_tests():
    """运行所有测试"""
    start_time = time.time()
    logger.info("开始运行所有测试...")
    
    # 测试脚本列表
    test_scripts = [
        'tests/run_mcp_tool_tests.py',  # MCP工具测试
        'tests/test_real_memory_tool.py'  # 实际Memory Tool测试
    ]
    
    results = {}
    all_passed = True
    
    for script in test_scripts:
        success = run_test_script(script)
        results[script] = "通过" if success else "失败"
        all_passed = all_passed and success
    
    # 输出测试摘要
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info("\n=== 所有测试结果摘要 ===")
    for script, result in results.items():
        logger.info(f"{script}: {result}")
    logger.info(f"总耗时: {duration:.2f}秒")
    logger.info(f"总体结果: {'全部通过' if all_passed else '部分失败'}")
    
    return all_passed

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)