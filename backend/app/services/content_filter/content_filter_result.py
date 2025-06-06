"""
敏感内容过滤结果

表示敏感内容过滤操作的结果
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field


@dataclass
class SensitiveWordMatch:
    """敏感词匹配记录"""
    word: str              # 敏感词
    start_pos: int         # 在原文中的起始位置
    end_pos: int           # 在原文中的结束位置
    category: str          # 敏感词类别 (privacy, inappropriate, discrimination)
    severity: int          # 严重程度 (1-低, 2-中, 3-高)


@dataclass
class ContentFilterResult:
    """敏感内容过滤结果"""
    original_text: str                         # 原始文本
    filtered_text: str                         # 过滤后的文本
    has_sensitive_content: bool = False        # 是否包含敏感内容
    matches: List[SensitiveWordMatch] = field(default_factory=list)  # 敏感词匹配列表
    
    @property
    def sensitive_word_count(self) -> int:
        """敏感词匹配数量"""
        return len(self.matches)
    
    @property
    def sensitive_categories(self) -> List[str]:
        """包含的敏感词类别"""
        return list(set(match.category for match in self.matches))
    
    @property
    def highest_severity(self) -> int:
        """最高敏感级别"""
        if not self.matches:
            return 0
        return max(match.severity for match in self.matches)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将结果转换为字典
        
        Returns:
            结果字典
        """
        return {
            "has_sensitive_content": self.has_sensitive_content,
            "sensitive_word_count": self.sensitive_word_count,
            "sensitive_categories": self.sensitive_categories,
            "highest_severity": self.highest_severity,
            "filtered_text": self.filtered_text,
            "matches": [
                {
                    "word": match.word,
                    "category": match.category,
                    "severity": match.severity,
                    "position": (match.start_pos, match.end_pos)
                }
                for match in self.matches
            ]
        }
    
    def get_summary(self) -> str:
        """
        获取过滤结果摘要
        
        Returns:
            过滤结果摘要
        """
        if not self.has_sensitive_content:
            return "未检测到敏感内容"
        
        category_counts = {}
        for category in self.sensitive_categories:
            category_counts[category] = sum(1 for m in self.matches if m.category == category)
        
        summary_parts = [
            f"检测到 {self.sensitive_word_count} 处敏感内容",
            ", ".join(f"{count}处{category_name}" 
                      for category_name, count in category_counts.items())
        ]
        return "，".join(summary_parts) 