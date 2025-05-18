#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试运行脚本

此脚本用于运行所有测试用例，并生成测试报告
"""

import pytest
import os
import sys

def main():
    """运行所有测试并生成报告"""
    print("开始运行测试...\
")
    
    # 确保当前工作目录是项目根目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 运行测试并生成覆盖率报告
    args = [
        "tests/",  # 测试目录
        "-v",  # 详细输出
        "--cov=app",  # 覆盖率报告范围
        "--cov-report=term",  # 终端输出覆盖率
        "--cov-report=html:coverage_reports",  # HTML格式覆盖率报告
    ]
    
    # 如果指定了特定测试文件，则只运行该文件
    if len(sys.argv) > 1:
        args = [sys.argv[1]] + args[1:]
    
    exit_code = pytest.main(args)
    
    if exit_code == 0:
        print("\n✅ 所有测试通过!")
        print("覆盖率报告已生成到 coverage_reports 目录")
    else:
        print("\n❌ 测试失败，请检查错误信息")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())