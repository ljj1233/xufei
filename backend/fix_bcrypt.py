#!/usr/bin/env python3
"""
修复bcrypt和passlib版本兼容性问题

这个脚本会卸载当前的bcrypt和passlib，然后安装兼容的版本。
当出现以下警告时使用此脚本：
WARNING:passlib.handlers.bcrypt:(trapped) error reading bcrypt version
"""

import subprocess
import sys
import os
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(command):
    """运行shell命令并返回退出码"""
    try:
        logger.info(f"执行命令: {command}")
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        logger.info(f"命令输出: {result.stdout}")
        return 0
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败 (返回码 {e.returncode}): {e.stderr}")
        return e.returncode

def fix_bcrypt_passlib():
    """修复bcrypt和passlib版本兼容性问题"""
    # 显示当前版本
    logger.info("=== 当前安装的版本 ===")
    run_command("pip show bcrypt")
    run_command("pip show passlib")
    
    # 卸载当前版本
    logger.info("=== 卸载当前版本 ===")
    run_command("pip uninstall -y bcrypt passlib")
    
    # 安装兼容版本
    logger.info("=== 安装兼容版本 ===")
    run_command("pip install bcrypt==3.2.0")
    run_command("pip install passlib==1.7.4")
    
    # 检查安装结果
    logger.info("=== 安装后的版本 ===")
    result_bcrypt = run_command("pip show bcrypt")
    result_passlib = run_command("pip show passlib")
    
    if result_bcrypt == 0 and result_passlib == 0:
        logger.info("修复完成！")
        return True
    else:
        logger.error("修复失败，请手动安装兼容版本")
        return False

if __name__ == "__main__":
    logger.info("开始修复bcrypt和passlib版本兼容性问题...")
    success = fix_bcrypt_passlib()
    sys.exit(0 if success else 1) 