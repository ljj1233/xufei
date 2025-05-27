# -*- coding: utf-8 -*-
"""
自动化测试运行脚本

运行所有测试用例并生成报告
"""

import unittest
import logging
import time
import json
from pathlib import Path
import sys
import os

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent.parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_run.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_tests():
    """运行所有测试用例"""
    # 创建测试结果目录
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    # 记录开始时间
    start_time = time.time()
    
    # 收集所有测试用例
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(
        start_dir=str(Path(__file__).parent),
        pattern="test_*.py"
    )
    
    # 运行测试
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_result = test_runner.run(test_suite)
    
    # 记录结束时间
    end_time = time.time()
    
    # 生成测试报告
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration": end_time - start_time,
        "total_tests": test_result.testsRun,
        "failures": len(test_result.failures),
        "errors": len(test_result.errors),
        "skipped": len(test_result.skipped),
        "success_rate": (test_result.testsRun - len(test_result.failures) - len(test_result.errors)) / test_result.testsRun * 100
    }
    
    # 保存测试报告
    report_file = results_dir / f"test_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 记录失败和错误详情
    if test_result.failures or test_result.errors:
        details_file = results_dir / f"test_details_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(details_file, "w", encoding="utf-8") as f:
            f.write("=== 测试失败详情 ===\n\n")
            for failure in test_result.failures:
                f.write(f"失败: {failure[0]}\n")
                f.write(f"原因: {failure[1]}\n\n")
            
            f.write("=== 测试错误详情 ===\n\n")
            for error in test_result.errors:
                f.write(f"错误: {error[0]}\n")
                f.write(f"原因: {error[1]}\n\n")
    
    # 输出测试结果摘要
    logger.info("=== 测试结果摘要 ===")
    logger.info(f"总测试数: {report['total_tests']}")
    logger.info(f"失败数: {report['failures']}")
    logger.info(f"错误数: {report['errors']}")
    logger.info(f"跳过数: {report['skipped']}")
    logger.info(f"成功率: {report['success_rate']:.2f}%")
    logger.info(f"总耗时: {report['duration']:.2f}秒")
    logger.info(f"详细报告已保存到: {report_file}")
    
    # 返回测试是否全部通过
    return len(test_result.failures) == 0 and len(test_result.errors) == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1) 