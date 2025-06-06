"""
Celery工作者入口脚本

用于启动Celery工作者进程
"""

import os
import logging
from app.celery_app import celery_app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("启动Celery工作者")
    
    # 设置默认的队列优先级
    celery_app.conf.update(
        task_routes={
            "app.services.tasks.analysis_tasks.quick_analysis": {"queue": "high_priority"},
            "app.services.tasks.analysis_tasks.detailed_analysis": {"queue": "default"},
            "app.services.tasks.analysis_tasks.*": {"queue": "default"},
        }
    )
    
    # 启动Celery工作者
    celery_app.worker_main(
        argv=[
            "worker",
            "--loglevel=info",
            "--concurrency=4",  # 并发工作者数量
            "-Q", "high_priority,default",  # 监听的队列
        ]
    ) 