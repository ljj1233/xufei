# agent/core/analyzer.py

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from .config import AgentConfig


class Analyzer(ABC):
    """分析器基类
    
    所有具体分析器的抽象基类，定义了分析器的通用接口
    """
    
    def __init__(self, name: str, analyzer_type: str, config: Optional[AgentConfig] = None):
        """初始化分析器
        
        Args:
            name: 分析器名称
            analyzer_type: 分析器类型（speech, visual, content, overall）
            config: 配置对象，如果为None则创建默认配置
        """
        self.name = name
        self.type = analyzer_type
        self.config = config or AgentConfig()
    
    @abstractmethod
    def extract_features(self, data: Any) -> Dict[str, Any]:
        """提取特征
        
        从输入数据中提取特征
        
        Args:
            data: 输入数据（可以是文件路径、音频数据、视频数据等）
            
        Returns:
            Dict[str, Any]: 提取的特征
        """
        pass
    
    @abstractmethod
    def analyze(self, features: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """分析特征
        
        根据提取的特征进行分析
        
        Args:
            features: 提取的特征
            params: 分析参数，如果为None则使用默认参数
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        从配置中获取特定于该分析器类型的配置值
        
        Args:
            key: 配置键名
            default: 默认值（如果配置不存在）
            
        Returns:
            Any: 配置值
        """
        return self.config.get(self.type, key, default)
    
    def get_service_config(self, service: str, key: str, default: Any = None) -> Any:
        """获取服务配置值
        
        从配置中获取特定服务的配置值
        
        Args:
            service: 服务名称
            key: 配置键名
            default: 默认值（如果配置不存在）
            
        Returns:
            Any: 配置值
        """
        services_config = self.config.get_section("services")
        service_config = services_config.get(service, {})
        return service_config.get(key, default)