"""
敏感内容过滤器

实现基于DFA算法的高效敏感内容过滤
"""

import re
import logging
from typing import Dict, List, Set, Tuple, Any, Optional

from .sensitive_words_repository import SensitiveWordsRepository
from .content_filter_config import ContentFilterConfig, FilterLevel
from .content_filter_result import ContentFilterResult, SensitiveWordMatch

logger = logging.getLogger(__name__)


class TrieNode:
    """Trie树节点，用于DFA算法"""
    
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.word = None
        self.category = None
        self.severity = None


class SensitiveContentFilter:
    """敏感内容过滤器"""
    
    def __init__(self, repository: SensitiveWordsRepository, config: ContentFilterConfig):
        """
        初始化过滤器
        
        Args:
            repository: 敏感词库管理器
            config: 过滤配置
        """
        self.repository = repository
        self.config = config
        self.root = TrieNode()  # Trie树根节点
        
        # 构建Trie树
        self._build_trie()
    
    def _build_trie(self):
        """构建敏感词的Trie树"""
        sensitive_words = self.repository.get_all_sensitive_words()
        
        for word, info in sensitive_words.items():
            category = info["category"]
            severity = info["severity"]
            
            # 判断是否需要添加该词到Trie树
            if not self._should_filter_category(category) or not self._should_filter_severity(severity):
                continue
                
            node = self.root
            for char in word:
                if char not in node.children:
                    node.children[char] = TrieNode()
                node = node.children[char]
            
            node.is_end = True
            node.word = word
            node.category = category
            node.severity = severity
    
    def _should_filter_category(self, category: str) -> bool:
        """
        判断是否需要过滤该类别
        
        Args:
            category: 敏感词类别
            
        Returns:
            是否需要过滤
        """
        if category == "privacy":
            return self.config.enable_privacy_filter
        elif category == "inappropriate":
            return self.config.enable_inappropriate_filter
        elif category == "discrimination":
            return self.config.enable_discrimination_filter
        return True
    
    def _should_filter_severity(self, severity: int) -> bool:
        """
        判断是否需要过滤该严重程度
        
        Args:
            severity: 敏感词严重程度
            
        Returns:
            是否需要过滤
        """
        filter_level_value = self.config.filter_level.value
        return severity >= filter_level_value
    
    def filter_text(self, text: str) -> ContentFilterResult:
        """
        过滤文本中的敏感内容
        
        Args:
            text: 输入文本
            
        Returns:
            过滤结果
        """
        if not text:
            return ContentFilterResult(original_text=text, filtered_text=text)
        
        # 检测敏感词
        matches = self._detect_sensitive_words(text)
        
        # 检测正则表达式匹配
        regex_matches = self._detect_regex_patterns(text)
        matches.extend(regex_matches)
        
        if not matches:
            return ContentFilterResult(original_text=text, filtered_text=text)
        
        # 过滤文本
        filtered_text = self._replace_sensitive_content(text, matches)
        
        return ContentFilterResult(
            original_text=text,
            filtered_text=filtered_text,
            has_sensitive_content=bool(matches),
            matches=matches
        )
    
    def _detect_sensitive_words(self, text: str) -> List[SensitiveWordMatch]:
        """
        检测文本中的敏感词
        
        Args:
            text: 输入文本
            
        Returns:
            敏感词匹配列表
        """
        matches = []
        i = 0
        while i < len(text):
            node = self.root
            j = i
            last_match_pos = -1
            last_match_node = None
            
            while j < len(text) and text[j] in node.children:
                node = node.children[text[j]]
                j += 1
                
                if node.is_end:
                    last_match_pos = j
                    last_match_node = node
            
            if last_match_pos != -1:
                # 找到敏感词
                word_length = last_match_pos - i
                matches.append(SensitiveWordMatch(
                    word=last_match_node.word,
                    start_pos=i,
                    end_pos=last_match_pos - 1,
                    category=last_match_node.category,
                    severity=last_match_node.severity
                ))
                i = last_match_pos  # 跳过匹配的敏感词
            else:
                i += 1
        
        return matches
    
    def _detect_regex_patterns(self, text: str) -> List[SensitiveWordMatch]:
        """
        检测文本中的正则表达式匹配项
        
        Args:
            text: 输入文本
            
        Returns:
            匹配列表
        """
        matches = []
        regex_patterns = self.repository.get_all_regex_patterns()
        
        for name, pattern in regex_patterns.items():
            try:
                for match in re.finditer(pattern, text):
                    start_pos = match.start()
                    end_pos = match.end() - 1
                    matches.append(SensitiveWordMatch(
                        word=match.group(),
                        start_pos=start_pos,
                        end_pos=end_pos,
                        category="privacy",  # 所有正则匹配的都算作隐私信息
                        severity=3  # 正则匹配的敏感信息一般为高严重度
                    ))
            except re.error:
                logger.error(f"正则表达式 '{pattern}' 匹配失败")
        
        return matches
    
    def _replace_sensitive_content(self, text: str, matches: List[SensitiveWordMatch]) -> str:
        """
        替换文本中的敏感内容
        
        Args:
            text: 原始文本
            matches: 敏感词匹配列表
            
        Returns:
            替换后的文本
        """
        # 按匹配位置排序，确保从后向前替换不会影响位置
        matches = sorted(matches, key=lambda m: m.start_pos, reverse=True)
        
        result = text
        for match in matches:
            word_length = match.end_pos - match.start_pos + 1
            replacement = self.config.replacement_char * word_length
            result = result[:match.start_pos] + replacement + result[match.end_pos + 1:]
        
        return result
    
    def update_config(self, config: ContentFilterConfig):
        """
        更新过滤配置
        
        Args:
            config: 新的过滤配置
        """
        self.config = config
        # 重新构建Trie树
        self._build_trie() 