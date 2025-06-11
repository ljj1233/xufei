# -*- coding: utf-8 -*-
"""
单元测试运行脚本

此脚本解决了在不同目录下运行 pytest 时可能出现的导入问题。
它将项目根目录添加到系统路径中，然后调用 pytest。
"""
import sys
import os
import pytest

def main():
    """设置路径并运行指定的单元测试"""
    # 将此脚本所在的目录（即 agent/ 目录）添加到 sys.path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print(f"Project root added to sys.path: {project_root}")
    print("Current sys.path:", sys.path)

    # 指定要运行的测试文件
    test_file = os.path.join(project_root, "tests", "unit", "test_strategy_decider.py")
    
    # 调用 pytest
    # 使用 -s 选项显示测试中的打印语句，方便调试
    # 使用 -v 选项获取更详细的输出
    exit_code = pytest.main(["-s", "-v", test_file])
    
    # 退出并返回 pytest 的退出码
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
