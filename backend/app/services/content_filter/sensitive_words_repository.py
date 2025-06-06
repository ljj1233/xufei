"""
敏感词库管理

负责加载、存储和管理敏感词库
"""

import os
import re
import json
import logging
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path


logger = logging.getLogger(__name__)


class SensitiveWordsRepository:
    """敏感词库管理类"""

    # 敏感词类别及默认严重程度
    CATEGORY_SEVERITY = {
        "privacy": 3,      # 隐私信息，最高严重度
        "inappropriate": 2, # 不当言论，中等严重度
        "discrimination": 2 # 歧视性语言，中等严重度
    }
    
    # 常用的正则表达式模式，用于匹配格式化的敏感信息
    DEFAULT_REGEX_PATTERNS = {
        "身份证号": r"\d{17}[\dXx]",
        "手机号": r"1[3-9]\d{9}",
        "邮箱": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "银行卡号": r"\d{16,19}"
    }
    
    def __init__(self, resource_dir: Optional[str] = None):
        """
        初始化敏感词库管理器
        
        Args:
            resource_dir: 敏感词库资源目录，如果为None则使用默认目录
        """
        if resource_dir is None:
            # 使用默认目录
            module_dir = Path(__file__).parent
            resource_dir = str(module_dir / "resources" / "sensitive_words")
            
        self.resource_dir = resource_dir
        self.sensitive_words: Dict[str, Dict[str, int]] = {}  # 词 -> (类别, 严重程度)
        self.regex_patterns: Dict[str, str] = {}  # 名称 -> 正则表达式
        
        # 初始化敏感词库和正则表达式
        self._load_default_regex_patterns()
        self._load_sensitive_words()
        
        logger.info(
            f"敏感词库初始化完成，共加载 {len(self.sensitive_words)} 个敏感词，"
            f"{len(self.regex_patterns)} 个正则表达式模式"
        )
    
    def _load_default_regex_patterns(self):
        """加载默认的正则表达式模式"""
        self.regex_patterns.update(self.DEFAULT_REGEX_PATTERNS)
    
    def _load_sensitive_words(self):
        """从文件加载敏感词"""
        for category, severity in self.CATEGORY_SEVERITY.items():
            file_path = os.path.join(self.resource_dir, f"{category}.txt")
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                # 分割行，获取敏感词和可能的自定义严重度
                                parts = line.split('|')
                                word = parts[0].strip()
                                word_severity = int(parts[1]) if len(parts) > 1 else severity
                                
                                self.sensitive_words[word] = {
                                    "category": category,
                                    "severity": word_severity
                                }
            except Exception as e:
                logger.error(f"加载敏感词文件 {file_path} 失败: {str(e)}")
    
    def add_sensitive_word(self, word: str, category: str, severity: int = None):
        """
        添加敏感词
        
        Args:
            word: 敏感词
            category: 类别
            severity: 严重程度，如果为None则使用类别默认严重度
        """
        if severity is None:
            severity = self.CATEGORY_SEVERITY.get(category, 1)
            
        self.sensitive_words[word] = {
            "category": category,
            "severity": severity
        }
    
    def add_regex_pattern(self, name: str, pattern: str):
        """
        添加正则表达式模式
        
        Args:
            name: 模式名称
            pattern: 正则表达式模式
        """
        try:
            # 验证正则表达式是否有效
            re.compile(pattern)
            self.regex_patterns[name] = pattern
        except re.error:
            logger.error(f"正则表达式模式 '{pattern}' 无效，忽略添加")
    
    def get_all_sensitive_words(self) -> Dict[str, Dict[str, int]]:
        """
        获取所有敏感词
        
        Returns:
            所有敏感词及其类别和严重程度
        """
        return self.sensitive_words
    
    def get_all_regex_patterns(self) -> Dict[str, str]:
        """
        获取所有正则表达式模式
        
        Returns:
            所有正则表达式模式
        """
        return self.regex_patterns
    
    def save_sensitive_words(self):
        """保存敏感词到文件"""
        # 按类别归类敏感词
        words_by_category = {}
        for word, info in self.sensitive_words.items():
            category = info["category"]
            severity = info["severity"]
            if category not in words_by_category:
                words_by_category[category] = []
            words_by_category[category].append((word, severity))
        
        # 保存到对应的文件
        for category, words in words_by_category.items():
            file_path = os.path.join(self.resource_dir, f"{category}.txt")
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for word, severity in words:
                        # 如果严重度与类别默认严重度相同，则只保存词
                        if severity == self.CATEGORY_SEVERITY.get(category, 1):
                            f.write(f"{word}\n")
                        else:
                            f.write(f"{word}|{severity}\n")
            except Exception as e:
                logger.error(f"保存敏感词文件 {file_path} 失败: {str(e)}")
    
    def create_default_sensitive_words(self):
        """创建默认的敏感词库文件（如果不存在）"""
        # 确保目录存在
        os.makedirs(self.resource_dir, exist_ok=True)
        
        default_words = {
            "privacy": [
                "身份证号码",
                "银行账号",
                "密码",
                "手机号",
                "家庭住址",
                "社保号",
                "信用卡号"
            ],
            "inappropriate": [
                "脏话",  # 实际应用中应该有完整的不当词汇列表
                "侮辱性词汇"
            ],
            "discrimination": [
                "性别歧视词汇",  # 实际应用中应该有完整的歧视性词汇列表
                "种族歧视词汇",
                "年龄歧视词汇"
            ]
        }
        
        # 创建每个类别的文件（如果不存在）
        for category, words in default_words.items():
            file_path = os.path.join(self.resource_dir, f"{category}.txt")
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        for word in words:
                            f.write(f"{word}\n")
                    logger.info(f"创建默认敏感词文件: {file_path}")
                except Exception as e:
                    logger.error(f"创建敏感词文件 {file_path} 失败: {str(e)}")
                    
        # 加载创建的敏感词
        self._load_sensitive_words() 