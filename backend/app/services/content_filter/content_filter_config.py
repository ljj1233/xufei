"""
敏感内容过滤配置

定义过滤级别和配置选项
"""

from enum import Enum
from typing import Dict, Any, Optional, List


class FilterLevel(Enum):
    """敏感内容过滤级别"""
    LOW = 1      # 仅过滤最严重的敏感词
    MEDIUM = 2   # 过滤中等及以上级别的敏感词
    HIGH = 3     # 过滤所有级别的敏感词


class ContentFilterConfig:
    """敏感内容过滤配置类"""
    
    def __init__(
        self,
        filter_level: FilterLevel = FilterLevel.MEDIUM,
        replacement_char: str = "*",
        enable_privacy_filter: bool = True,
        enable_inappropriate_filter: bool = True,
        enable_discrimination_filter: bool = True,
        custom_sensitive_words: Optional[List[str]] = None,
        custom_regex_patterns: Optional[Dict[str, str]] = None
    ):
        """
        初始化过滤配置
        
        Args:
            filter_level: 过滤级别
            replacement_char: 替换敏感词的字符
            enable_privacy_filter: 是否启用隐私信息过滤
            enable_inappropriate_filter: 是否启用不当言论过滤
            enable_discrimination_filter: 是否启用歧视性语言过滤
            custom_sensitive_words: 自定义敏感词列表
            custom_regex_patterns: 自定义正则表达式模式，用于匹配特定格式的敏感信息
        """
        self.filter_level = filter_level
        self.replacement_char = replacement_char
        self.enable_privacy_filter = enable_privacy_filter
        self.enable_inappropriate_filter = enable_inappropriate_filter
        self.enable_discrimination_filter = enable_discrimination_filter
        self.custom_sensitive_words = custom_sensitive_words or []
        self.custom_regex_patterns = custom_regex_patterns or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将配置转换为字典
        
        Returns:
            配置字典
        """
        return {
            "filter_level": self.filter_level.name,
            "replacement_char": self.replacement_char,
            "enable_privacy_filter": self.enable_privacy_filter,
            "enable_inappropriate_filter": self.enable_inappropriate_filter,
            "enable_discrimination_filter": self.enable_discrimination_filter,
            "custom_sensitive_words_count": len(self.custom_sensitive_words),
            "custom_regex_patterns_count": len(self.custom_regex_patterns)
        }
    
    @classmethod
    def default(cls) -> 'ContentFilterConfig':
        """
        创建默认配置
        
        Returns:
            默认配置实例
        """
        return ContentFilterConfig()
    
    @classmethod
    def strict(cls) -> 'ContentFilterConfig':
        """
        创建严格配置
        
        Returns:
            严格配置实例
        """
        return ContentFilterConfig(
            filter_level=FilterLevel.HIGH,
            replacement_char="*"
        )
    
    @classmethod
    def minimal(cls) -> 'ContentFilterConfig':
        """
        创建最小配置
        
        Returns:
            最小配置实例
        """
        return ContentFilterConfig(
            filter_level=FilterLevel.LOW,
            replacement_char="*"
        ) 