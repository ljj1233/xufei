# -*- coding: utf-8 -*-
"""
内容过滤服务模块

提供文本和音频内容的过滤功能，支持多种敏感内容类别检测和过滤
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class FilterResult:
    """过滤结果数据类"""
    filtered_text: str
    has_sensitive_content: bool
    sensitive_word_count: int
    sensitive_categories: List[str]
    highest_severity: str
    detected_words: Dict[str, List[str]] = None  # 按类别存储检测到的敏感词

    def __post_init__(self):
        if self.detected_words is None:
            self.detected_words = {}

class ContentFilterService:
    """内容过滤服务
    
    用于过滤文本和音频内容中的敏感内容，支持多种敏感内容类别
    """
    
    _instance = None
    
    # 敏感内容类别定义
    CATEGORY_POLITICAL = "政治敏感"
    CATEGORY_INAPPROPRIATE = "不当言论"
    CATEGORY_DISCRIMINATION = "歧视性语言"
    CATEGORY_VIOLENCE = "暴力内容"
    CATEGORY_ADULT = "成人内容"
    CATEGORY_FRAUD = "欺诈内容"
    
    # 敏感级别定义
    SEVERITY_LOW = "low"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_HIGH = "high"
    
    @classmethod
    def get_instance(cls):
        """获取单例实例
        
        Returns:
            ContentFilterService: 服务实例
        """
        if cls._instance is None:
            cls._instance = ContentFilterService()
        return cls._instance
    
    def __init__(self):
        """初始化内容过滤服务"""
        logger.info("开始初始化内容过滤服务...")
        
        # 按类别定义敏感词词典
        self.sensitive_words_dict = {
            self.CATEGORY_POLITICAL: {
                # 政治敏感词汇
                "敏感政治人物": self.SEVERITY_HIGH,
                "政治事件": self.SEVERITY_HIGH,
                "政治立场": self.SEVERITY_MEDIUM,
                "政治倾向": self.SEVERITY_MEDIUM,
                "政治争议": self.SEVERITY_MEDIUM
            },
            self.CATEGORY_INAPPROPRIATE: {
                # 不当言论
                "脏话1": self.SEVERITY_MEDIUM,
                "脏话2": self.SEVERITY_MEDIUM,
                "侮辱性词汇": self.SEVERITY_HIGH,
                "不文明用语": self.SEVERITY_LOW
            },
            self.CATEGORY_DISCRIMINATION: {
                # 歧视性语言
                "种族歧视词汇": self.SEVERITY_HIGH,
                "性别歧视词汇": self.SEVERITY_HIGH,
                "地域歧视词汇": self.SEVERITY_MEDIUM,
                "职业歧视词汇": self.SEVERITY_MEDIUM
            },
            self.CATEGORY_VIOLENCE: {
                # 暴力内容
                "暴力词汇1": self.SEVERITY_HIGH,
                "暴力词汇2": self.SEVERITY_HIGH,
                "威胁性语言": self.SEVERITY_HIGH
            },
            self.CATEGORY_ADULT: {
                # 成人内容
                "成人词汇1": self.SEVERITY_HIGH,
                "成人词汇2": self.SEVERITY_HIGH,
                "不适内容": self.SEVERITY_MEDIUM
            },
            self.CATEGORY_FRAUD: {
                # 欺诈内容
                "诈骗关键词": self.SEVERITY_HIGH,
                "虚假宣传词": self.SEVERITY_MEDIUM,
                "误导性表述": self.SEVERITY_LOW
            }
        }
        
        # 将字典扁平化为列表，便于快速检查
        self._build_sensitive_word_list()
        
        # 编译正则表达式以提高性能
        self._compile_regex_patterns()
        
        logger.info(f"内容过滤服务初始化完成，共加载 {len(self.sensitive_words)} 个敏感词，涵盖 {len(self.sensitive_words_dict)} 个类别")
    
    def _build_sensitive_word_list(self):
        """构建敏感词列表和映射"""
        self.sensitive_words = []
        self.word_to_category = {}
        self.word_to_severity = {}
        
        for category, words in self.sensitive_words_dict.items():
            for word, severity in words.items():
                self.sensitive_words.append(word)
                self.word_to_category[word] = category
                self.word_to_severity[word] = severity
    
    def _compile_regex_patterns(self):
        """编译正则表达式模式以提高性能"""
        self.regex_patterns = {}
        
        for category, words in self.sensitive_words_dict.items():
            # 对每个类别创建一个正则表达式
            if words:
                pattern = '|'.join(re.escape(word) for word in words.keys())
                self.regex_patterns[category] = re.compile(pattern)
    
    def filter_text(self, text: str) -> FilterResult:
        """过滤文本内容
        
        对文本进行敏感内容检测和过滤
        
        Args:
            text: 需要过滤的文本
            
        Returns:
            FilterResult: 过滤结果
        """
        logger.debug(f"开始过滤文本，长度: {len(text) if text else 0}")
        
        if not text:
            logger.debug("文本为空，跳过过滤")
            return FilterResult(
                filtered_text="",
                has_sensitive_content=False,
                sensitive_word_count=0,
                sensitive_categories=[],
                highest_severity=self.SEVERITY_LOW,
                detected_words={}
            )
        
        # 初始化检测结果
        filtered_text = text
        detected_words = defaultdict(list)
        highest_severity = self.SEVERITY_LOW
        
        # 使用正则表达式进行高效检测
        for category, pattern in self.regex_patterns.items():
            matches = pattern.findall(text)
            
            if matches:
                logger.debug(f"在类别 '{category}' 中检测到 {len(matches)} 个敏感词")
                
                # 记录检测到的敏感词
                for word in matches:
                    detected_words[category].append(word)
                    
                    # 更新最高敏感级别
                    word_severity = self.word_to_severity.get(word, self.SEVERITY_LOW)
                    if self._severity_level(word_severity) > self._severity_level(highest_severity):
                        highest_severity = word_severity
                
                # 替换敏感词
                filtered_text = pattern.sub(lambda m: '*' * len(m.group(0)), filtered_text)
        
        # 统计结果
        sensitive_word_count = sum(len(words) for words in detected_words.values())
        sensitive_categories = list(detected_words.keys())
        
        # 记录日志
        if sensitive_word_count > 0:
            logger.warning(f"检测到 {sensitive_word_count} 个敏感词，涉及 {len(sensitive_categories)} 个类别，最高敏感级别: {highest_severity}")
            logger.debug(f"敏感词详情: {json.dumps(dict(detected_words), ensure_ascii=False)}")
        else:
            logger.debug("未检测到敏感内容")
        
        # 构建结果
        return FilterResult(
            filtered_text=filtered_text,
            has_sensitive_content=sensitive_word_count > 0,
            sensitive_word_count=sensitive_word_count,
            sensitive_categories=sensitive_categories,
            highest_severity=highest_severity,
            detected_words=dict(detected_words)
        )
    
    def filter_audio(self, audio_data: bytes) -> FilterResult:
        """过滤音频内容
        
        将音频转换为文本并进行敏感内容过滤
        
        Args:
            audio_data: 音频数据
            
        Returns:
            FilterResult: 过滤结果
        """
        logger.info(f"开始过滤音频内容，数据大小: {len(audio_data)} 字节")
        
        try:
            # 实际应用中，这里应该调用语音识别API将音频转换为文本
            # 这里简化处理，假设已经转换为文本
            transcribed_text = "这是从音频转写的文本"
            logger.debug(f"音频转写完成，文本长度: {len(transcribed_text)}")
            
            # 使用文本过滤方法处理转写文本
            return self.filter_text(transcribed_text)
            
        except Exception as e:
            logger.exception(f"音频过滤失败: {e}")
            return FilterResult(
                filtered_text="",
                has_sensitive_content=False,
                sensitive_word_count=0,
                sensitive_categories=[],
                highest_severity=self.SEVERITY_LOW,
                detected_words={}
            )
    
    def _severity_level(self, severity: str) -> int:
        """将敏感级别转换为数值
        
        Args:
            severity: 敏感级别字符串
            
        Returns:
            int: 对应的数值级别
        """
        severity_map = {
            self.SEVERITY_LOW: 1,
            self.SEVERITY_MEDIUM: 2,
            self.SEVERITY_HIGH: 3
        }
        return severity_map.get(severity, 0)
    
    def add_custom_sensitive_words(self, category: str, words_dict: Dict[str, str]):
        """添加自定义敏感词
        
        Args:
            category: 敏感词类别
            words_dict: 敏感词字典，格式为 {敏感词: 敏感级别}
        """
        logger.info(f"添加自定义敏感词，类别: {category}，数量: {len(words_dict)}")
        
        # 更新敏感词字典
        if category not in self.sensitive_words_dict:
            self.sensitive_words_dict[category] = {}
        
        self.sensitive_words_dict[category].update(words_dict)
        
        # 重建敏感词列表和映射
        self._build_sensitive_word_list()
        
        # 重新编译正则表达式
        self._compile_regex_patterns()
        
        logger.info(f"自定义敏感词添加完成，当前共有 {len(self.sensitive_words)} 个敏感词") 