#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试运行脚本

运行所有测试并生成报告
"""

import os
import sys
import pytest
import time
import logging
import argparse
from pathlib import Path
import traceback

# 添加项目根目录到系统路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_run.log'),
        logging.StreamHandler(sys.stdout)  # 明确使用stdout而不是默认stderr
    ]
)

# 添加异常处理
def safe_log(logger_obj, level, msg, *args, **kwargs):
    """安全的日志记录函数，忽略日志写入错误"""
    try:
        if level == "info":
            logger_obj.info(msg, *args, **kwargs)
        elif level == "error":
            logger_obj.error(msg, *args, **kwargs)
        elif level == "warning":
            logger_obj.warning(msg, *args, **kwargs)
        elif level == "debug":
            logger_obj.debug(msg, *args, **kwargs)
    except Exception:
        # 忽略日志写入错误
        pass

logger = logging.getLogger(__name__)

def run_unit_tests(verbose=True):
    """运行单元测试
    
    Args:
        verbose: 是否显示详细输出
    
    Returns:
        int: 测试结果代码（0表示成功）
    """
    safe_log(logger, "info", "运行单元测试...")
    try:
        args = ['unit', '-v'] if verbose else ['unit']
        return pytest.main(args)
    except Exception as e:
        safe_log(logger, "error", f"运行单元测试时出错: {e}")
        safe_log(logger, "error", traceback.format_exc())
        return 1

def run_integration_tests(verbose=True):
    """运行集成测试
    
    Args:
        verbose: 是否显示详细输出
    
    Returns:
        int: 测试结果代码（0表示成功）
    """
    safe_log(logger, "info", "运行集成测试...")
    try:
        args = ['integration', '-v'] if verbose else ['integration']
        return pytest.main(args)
    except Exception as e:
        safe_log(logger, "error", f"运行集成测试时出错: {e}")
        safe_log(logger, "error", traceback.format_exc())
        return 1

def run_performance_tests(verbose=True):
    """运行性能测试
    
    Args:
        verbose: 是否显示详细输出
    
    Returns:
        int: 测试结果代码（0表示成功）
    """
    safe_log(logger, "info", "运行性能测试...")
    try:
        args = ['performance', '-v'] if verbose else ['performance']
        return pytest.main(args)
    except Exception as e:
        safe_log(logger, "error", f"运行性能测试时出错: {e}")
        safe_log(logger, "error", traceback.format_exc())
        return 1

def run_mcp_tests(verbose=True):
    """运行MCP测试
    
    Args:
        verbose: 是否显示详细输出
    
    Returns:
        int: 测试结果代码（0表示成功）
    """
    safe_log(logger, "info", "运行MCP测试...")
    try:
        args = ['test_mcp_integration.py', 'test_mcp_rag_integration.py', '-v'] if verbose else ['test_mcp_integration.py', 'test_mcp_rag_integration.py']
        return pytest.main(args)
    except Exception as e:
        safe_log(logger, "error", f"运行MCP测试时出错: {e}")
        safe_log(logger, "error", traceback.format_exc())
        return 1

def run_custom_tests(test_paths, verbose=True):
    """运行自定义测试
    
    Args:
        test_paths: 测试文件或目录路径列表
        verbose: 是否显示详细输出
    
    Returns:
        int: 测试结果代码（0表示成功）
    """
    safe_log(logger, "info", f"运行自定义测试: {test_paths}...")
    try:
        args = test_paths + ['-v'] if verbose else test_paths
        return pytest.main(args)
    except Exception as e:
        safe_log(logger, "error", f"运行自定义测试时出错: {e}")
        safe_log(logger, "error", traceback.format_exc())
        return 1

def run_all_tests(verbose=True):
    """运行所有测试
    
    Args:
        verbose: 是否显示详细输出
    
    Returns:
        bool: 测试是否全部通过
    """
    safe_log(logger, "info", "开始运行所有测试...")
    start_time = time.time()
    
    # 运行各类测试
    results = {}
    
    # 运行单元测试
    results["unit"] = run_unit_tests(verbose)
    
    # 运行集成测试
    results["integration"] = run_integration_tests(verbose)
    
    # 运行性能测试
    results["performance"] = run_performance_tests(verbose)
    
    # 运行MCP测试
    results["mcp"] = run_mcp_tests(verbose)
    
    # 运行内容分析器测试
    results["content"] = run_custom_tests(['test_content_analyzer.py'], verbose)
    
    # 运行工作流测试
    results["workflow"] = run_custom_tests(['test_integration_workflow.py'], verbose)
    
    # 输出结果摘要
    elapsed = time.time() - start_time
    safe_log(logger, "info", f"测试完成，耗时: {elapsed:.2f}秒")
    
    for test_type, result in results.items():
        status = "通过" if result == 0 else "失败"
        safe_log(logger, "info", f"{test_type} 测试: {status}")
    
    # 检查是否所有测试都通过
    all_passed = all(result == 0 for result in results.values())
    
    if all_passed:
        safe_log(logger, "info", "所有测试通过！")
    else:
        safe_log(logger, "error", "部分测试失败，请查看日志获取详细信息")
    
    return all_passed

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行测试")
    parser.add_argument("--unit", action="store_true", help="只运行单元测试")
    parser.add_argument("--integration", action="store_true", help="只运行集成测试")
    parser.add_argument("--performance", action="store_true", help="只运行性能测试")
    parser.add_argument("--mcp", action="store_true", help="只运行MCP测试")
    parser.add_argument("--content", action="store_true", help="只运行内容分析器测试")
    parser.add_argument("--workflow", action="store_true", help="只运行工作流测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细输出")
    
    args = parser.parse_args()
    
    # 如果没有指定任何测试类型，默认运行所有测试
    if not any([args.unit, args.integration, args.performance, args.mcp, args.content, args.workflow, args.all]):
        args.all = True
    
    success = True
    
    if args.all:
        success = run_all_tests(args.verbose)
    else:
        if args.unit:
            success = run_unit_tests(args.verbose) == 0 and success
        if args.integration:
            success = run_integration_tests(args.verbose) == 0 and success
        if args.performance:
            success = run_performance_tests(args.verbose) == 0 and success
        if args.mcp:
            success = run_mcp_tests(args.verbose) == 0 and success
        if args.content:
            success = run_custom_tests(['test_content_analyzer.py'], args.verbose) == 0 and success
        if args.workflow:
            success = run_custom_tests(['test_integration_workflow.py'], args.verbose) == 0 and success
    
    sys.exit(0 if success else 1) 