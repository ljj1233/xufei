"""
Celery应用配置

定义Celery应用实例和相关配置
"""

import os
import logging
from celery import Celery
from app.core.config import settings

# 配置日志
logger = logging.getLogger(__name__)

# 创建Celery实例
celery_app = Celery(
    "interview_analysis",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

# 配置Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    task_time_limit=3600,  # 任务执行时间限制（秒）
    worker_hijack_root_logger=False,  # 不覆盖根日志记录器
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)

# 自动发现任务
celery_app.autodiscover_tasks(["app.services.tasks"])

# 启动时记录日志
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    logger.info("Celery应用已配置完成")

# Celery任务基类
class BaseTask(celery_app.Task):
    """
    Celery任务基类，提供通用的日志记录和错误处理
    """
    
    def on_success(self, retval, task_id, args, kwargs):
        """任务成功完成时的回调"""
        logger.info(f"任务 {self.name}[{task_id}] 成功完成: {retval}")
        return super().on_success(retval, task_id, args, kwargs)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        logger.error(f"任务 {self.name}[{task_id}] 失败: {exc}")
        return super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """任务重试时的回调"""
        logger.warning(f"任务 {self.name}[{task_id}] 重试中: {exc}")
        return super().on_retry(exc, task_id, args, kwargs, einfo)
    
    def before_start(self, task_id, args, kwargs):
        """任务开始前的回调"""
        logger.info(f"任务 {self.name}[{task_id}] 开始执行")
        return super().before_start(task_id, args, kwargs) 