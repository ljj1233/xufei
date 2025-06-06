"""
学习推荐模块的日志配置

配置结构化日志记录，支持不同级别的日志和多种输出方式
"""

import os
import logging
import logging.handlers
import functools
import time
import uuid
import json
import traceback
from typing import Callable, Dict, Any, Optional

# 创建日志目录
os.makedirs("logs", exist_ok=True)

def setup_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    设置和配置日志记录器
    
    Args:
        name: 记录器名称
        log_level: 日志记录级别
        
    Returns:
        已配置的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 创建文件处理器
    log_file = f"logs/{name.replace('.', '_')}_{time.strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(request_id)s - %(user_id)s - %(name)s - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S.%f'
    )
    
    # 设置格式化器
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logger.info("日志记录器已配置完成", extra={'request_id': 'system', 'user_id': 'system'})
    return logger

# 自定义过滤器，添加默认的额外字段
class ContextFilter(logging.Filter):
    """为日志记录添加上下文信息的过滤器"""
    
    def filter(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = 'unknown'
        if not hasattr(record, 'user_id'):
            record.user_id = 'anonymous'
        return True

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addFilter(ContextFilter())

# 创建日志装饰器
def log_function(logger: Optional[logging.Logger] = None):
    """
    函数日志记录装饰器
    
    Args:
        logger: 要使用的日志记录器，若为None则使用函数模块的记录器
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        # 如果没有提供logger，则使用函数所在模块的logger
        nonlocal logger
        if logger is None:
            logger_name = func.__module__
            logger = logging.getLogger(logger_name)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            request_id = kwargs.get('request_id', str(uuid.uuid4()))
            user_id = kwargs.get('user_id', 'anonymous')
            
            # 如果第一个参数是self，尝试从self中获取请求ID和用户ID
            if args and hasattr(args[0], 'request_id'):
                request_id = getattr(args[0], 'request_id', request_id)
            if args and hasattr(args[0], 'user_id'):
                user_id = getattr(args[0], 'user_id', user_id)
            
            # 创建日志上下文
            extra = {
                'request_id': request_id,
                'user_id': user_id
            }
            
            # 过滤敏感参数，避免记录密码等信息
            safe_kwargs = {k: v for k, v in kwargs.items() if k not in ['password', 'token']}
            
            # 记录函数开始执行
            params = {
                'args': str(args),
                'kwargs': safe_kwargs
            }
            logger.info(f"开始执行 {func.__name__} 函数，参数: {json.dumps(params, ensure_ascii=False)}", extra=extra)
            
            start_time = time.time()
            try:
                # 执行原函数
                result = func(*args, **kwargs)
                
                # 记录函数执行成功
                duration = time.time() - start_time
                logger.info(f"函数 {func.__name__} 执行成功，耗时: {duration:.3f}秒", extra=extra)
                return result
            except Exception as e:
                # 记录函数执行异常
                duration = time.time() - start_time
                logger.error(
                    f"函数 {func.__name__} 执行失败，耗时: {duration:.3f}秒，错误: {str(e)}\n"
                    f"异常堆栈: {traceback.format_exc()}",
                    extra=extra
                )
                raise
        return wrapper
    return decorator

# 初始化学习推荐模块的主日志记录器
logger = setup_logger("app.services.learning_recommendation") 