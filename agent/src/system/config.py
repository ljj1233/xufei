# -*- coding: utf-8 -*-
"""
配置模块

提供系统配置管理
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AgentConfig:
    """代理配置类
    
    管理系统配置
    """
    
    def __init__(self):
        """初始化代理配置"""
        self._config = {}
        
    def set_config(self, key: str, value: Any) -> None:
        """设置配置项
        
        Args:
            key: 配置项键名
            value: 配置项值
        """
        self._config[key] = value
        logger.debug(f"设置配置: {key} = {value}")
        
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key: 配置项键名
            default: 默认值
            
        Returns:
            Any: 配置项值
        """
        return self._config.get(key, default)
        
    def load_from_file(self, file_path: str) -> bool:
        """从文件加载配置
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            bool: 是否加载成功
        """
        try:
            import json
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self._config.update(config)
            return True
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return False
        
    def save_to_file(self, file_path: str) -> bool:
        """保存配置到文件
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            bool: 是否保存成功
        """
        try:
            import json
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")
            return False
            
    def __getitem__(self, key: str) -> Any:
        """获取配置项
        
        Args:
            key: 配置项键名
            
        Returns:
            Any: 配置项值
        """
        return self.get_config(key)
        
    def __setitem__(self, key: str, value: Any) -> None:
        """设置配置项
        
        Args:
            key: 配置项键名
            value: 配置项值
        """
        self.set_config(key, value) 