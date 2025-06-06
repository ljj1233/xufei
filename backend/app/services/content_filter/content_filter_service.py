"""
内容过滤服务

提供敏感内容过滤服务接口
"""

import logging
from typing import Dict, Any, List, Optional

from .sensitive_words_repository import SensitiveWordsRepository
from .sensitive_content_filter import SensitiveContentFilter
from .content_filter_config import ContentFilterConfig, FilterLevel
from .content_filter_result import ContentFilterResult

logger = logging.getLogger(__name__)


class ContentFilterService:
    """内容过滤服务类"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'ContentFilterService':
        """
        获取单例实例
        
        Returns:
            ContentFilterService 实例
        """
        if cls._instance is None:
            cls._instance = ContentFilterService()
        return cls._instance
    
    def __init__(self, config: Optional[ContentFilterConfig] = None):
        """
        初始化内容过滤服务
        
        Args:
            config: 过滤配置，如果为None则使用默认配置
        """
        self.config = config or ContentFilterConfig.default()
        
        # 初始化敏感词库管理器并创建默认敏感词库
        self.repository = SensitiveWordsRepository()
        self.repository.create_default_sensitive_words()
        
        # 初始化过滤器
        self.filter = SensitiveContentFilter(self.repository, self.config)
        
        logger.info("内容过滤服务初始化完成")
    
    def filter_text(self, text: str, config: Optional[ContentFilterConfig] = None) -> ContentFilterResult:
        """
        过滤文本中的敏感内容
        
        Args:
            text: 输入文本
            config: 过滤配置，如果为None则使用默认配置
            
        Returns:
            过滤结果
        """
        if config and config != self.config:
            # 临时使用不同的配置
            temp_filter = SensitiveContentFilter(self.repository, config)
            result = temp_filter.filter_text(text)
        else:
            # 使用默认配置
            result = self.filter.filter_text(text)
        
        # 记录过滤结果
        if result.has_sensitive_content:
            logger.info(
                f"检测到 {result.sensitive_word_count} 处敏感内容: "
                f"类别={result.sensitive_categories}, 最高级别={result.highest_severity}"
            )
        
        return result
    
    def update_config(self, config: ContentFilterConfig):
        """
        更新过滤配置
        
        Args:
            config: 新的过滤配置
        """
        self.config = config
        self.filter.update_config(config)
        logger.info(f"过滤配置已更新: {config.to_dict()}")
    
    def add_sensitive_word(self, word: str, category: str, severity: Optional[int] = None):
        """
        添加敏感词
        
        Args:
            word: 敏感词
            category: 类别
            severity: 严重程度，如果为None则使用类别默认严重度
        """
        self.repository.add_sensitive_word(word, category, severity)
        # 更新过滤器的Trie树
        self.filter._build_trie()
        logger.info(f"添加敏感词: {word} (类别={category}, 级别={severity})")
    
    def add_regex_pattern(self, name: str, pattern: str):
        """
        添加正则表达式模式
        
        Args:
            name: 模式名称
            pattern: 正则表达式模式
        """
        self.repository.add_regex_pattern(name, pattern)
        logger.info(f"添加正则表达式模式: {name} -> {pattern}")
    
    def save_sensitive_words(self):
        """保存敏感词库到文件"""
        self.repository.save_sensitive_words()
        logger.info("敏感词库已保存到文件")
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        获取服务信息
        
        Returns:
            服务信息
        """
        sensitive_words = self.repository.get_all_sensitive_words()
        regex_patterns = self.repository.get_all_regex_patterns()
        
        # 统计各类别敏感词数量
        category_counts = {}
        for info in sensitive_words.values():
            category = info["category"]
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1
        
        return {
            "config": self.config.to_dict(),
            "sensitive_words_count": len(sensitive_words),
            "regex_patterns_count": len(regex_patterns),
            "category_counts": category_counts
        } 