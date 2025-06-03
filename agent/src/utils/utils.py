# agent/core/utils.py

from typing import Dict, Any, List, Optional
import os
import numpy as np
import json
import logging

# 配置日志
logger = logging.getLogger("agent")

def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """设置日志
    
    Args:
        level: 日志级别
        log_file: 日志文件路径，如果为None则只输出到控制台
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # 配置根日志记录器
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 如果提供了日志文件路径，添加文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(file_handler)

def ensure_dir(directory: str):
    """确保目录存在
    
    Args:
        directory: 目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def save_json(data: Dict[str, Any], file_path: str):
    """保存JSON数据到文件
    
    Args:
        data: 要保存的数据
        file_path: 文件路径
    """
    try:
        # 确保目录存在
        ensure_dir(os.path.dirname(file_path))
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"保存JSON文件失败: {e}")

def load_json(file_path: str) -> Dict[str, Any]:
    """从文件加载JSON数据
    
    Args:
        file_path: 文件路径
        
    Returns:
        Dict[str, Any]: 加载的数据
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载JSON文件失败: {e}")
        return {}

def normalize_score(score: float, min_val: float = 0.0, max_val: float = 10.0) -> float:
    """归一化评分
    
    将评分归一化到指定范围
    
    Args:
        score: 原始评分
        min_val: 最小值
        max_val: 最大值
        
    Returns:
        float: 归一化后的评分
    """
    return min(max_val, max(min_val, score))

def weighted_average(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """计算加权平均分
    
    Args:
        scores: 各项评分
        weights: 各项权重
        
    Returns:
        float: 加权平均分
    """
    total_score = 0.0
    total_weight = 0.0
    
    for key, score in scores.items():
        if key in weights:
            weight = weights[key]
            total_score += score * weight
            total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return total_score / total_weight

def detect_file_type(file_path: str) -> str:
    """检测文件类型
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 文件类型（'video'或'audio'）
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in [".mp4", ".avi", ".mov", ".wmv"]:
        return "video"
    elif ext in [".mp3", ".wav", ".ogg", ".flac"]:
        return "audio"
    else:
        raise ValueError(f"无法识别的文件类型: {ext}")