# ai_agent/scenarios/tech_interview.py

from typing import Dict, Any, List
import re

class TechInterviewScenario:
    """技术面试场景
    
    专门用于技术岗位面试的场景定义和分析
    """
    
    def __init__(self):
        """初始化技术面试场景"""
        self.name = "tech_interview"
        self.description = "技术岗位面试场景"
        
        # 技术关键词列表
        self.tech_keywords = [
            # 编程语言
            "Java", "Python", "C++", "JavaScript", "Go", "Rust", "PHP", "C#",
            # 算法与数据结构
            "算法", "数据结构", "复杂度", "排序", "搜索", "树", "图", "哈希", "动态规划",
            # 系统设计
            "架构", "设计模式", "微服务", "分布式", "高并发", "高可用", "负载均衡", "缓存",
            # 数据库
            "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "索引", "事务", "存储过程",
            # 前端技术
            "HTML", "CSS", "React", "Vue", "Angular", "DOM", "响应式", "前端框架",
            # 后端技术
            "API", "RESTful", "后端框架", "中间件", "消息队列", "RPC",
            # 运维与DevOps
            "Linux", "Docker", "Kubernetes", "CI/CD", "自动化测试", "监控", "日志",
            # 人工智能
            "机器学习", "深度学习", "神经网络", "自然语言处理", "计算机视觉", "推荐系统"
        ]
        
        # 技术问题模式
        self.question_patterns = [
            r"如何实现.+",
            r"请描述.+的原理",
            r"你如何解决.+问题",
            r"谈谈你对.+的理解",
            r"比较.+和.+的区别",
            r"设计一个.+系统"
        ]
    
    def recognize(self, text: str) -> float:
        """识别是否为技术面试场景
        
        根据文本内容判断是否为技术面试场景，并返回匹配度
        
        Args:
            text: 文本内容
            
        Returns:
            float: 匹配度（0-1）
        """
        if not text:
            return 0.3  # 默认匹配度
        
        # 计算技术关键词匹配数量
        keyword_matches = sum(1 for keyword in self.tech_keywords if keyword.lower() in text.lower())
        keyword_match_ratio = min(1.0, keyword_matches / 10)  # 最多10个关键词就算完全匹配
        
        # 检查是否包含技术问题模式
        question_matches = sum(1 for pattern in self.question_patterns if re.search(pattern, text))
        question_match_ratio = min(1.0, question_matches / 2)  # 最多2个问题模式就算完全匹配
        
        # 综合评分，关键词占70%，问题模式占30%
        match_score = 0.7 * keyword_match_ratio + 0.3 * question_match_ratio
        
        return match_score
    
    def get_analysis_params(self) -> Dict[str, Any]:
        """获取分析参数
        
        返回适用于技术面试场景的分析参数
        
        Returns:
            Dict[str, Any]: 分析参数
        """
        return {
            # 权重配置
            "speech_weight": 0.2,        # 语音在技术面试中权重较低
            "visual_weight": 0.2,        # 视觉在技术面试中权重较低
            "content_weight": 0.6,       # 内容在技术面试中权重较高
            
            # 内容分析参数
            "expected_keywords": self.tech_keywords,  # 期望出现的技术关键词
            "focus_areas": ["coding_skills", "system_design", "problem_solving"],
            
            # 输出配置
            "strengths_count": 3,
            "weaknesses_count": 3,
            "suggestions_count": 5
        }
    
    def get_custom_suggestions(self, analysis_result: Dict[str, Any]) -> List[str]:
        """获取自定义建议
        
        根据分析结果生成针对技术面试的自定义建议
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            List[str]: 自定义建议列表
        """
        # 导入建议库
        from .tech_interview_suggestions import get_suggestions_by_category, get_random_suggestions
        
        suggestions = []
        
        # 内容相关建议
        content = analysis_result.get("content", {})
        if content.get("relevance", 0) < 6.0:
            # 从建议库中获取相关性建议
            relevance_suggestions = get_suggestions_by_category("relevance", 2)
            suggestions.extend(relevance_suggestions)
        
        if content.get("structure", 0) < 6.0:
            # 从建议库中获取结构建议
            structure_suggestions = get_suggestions_by_category("structure", 2)
            suggestions.extend(structure_suggestions)
        
        # 关键词相关建议
        keywords = content.get("keywords", [])
        if len(keywords) < 5:
            # 从建议库中获取术语使用建议
            terminology_suggestions = get_suggestions_by_category("terminology", 2)
            suggestions.extend(terminology_suggestions)
        
        # 根据分析结果中的重点领域添加针对性建议
        focus_areas = analysis_result.get("content", {}).get("focus_areas", [])
        for area in focus_areas:
            if area == "coding_skills" and len(suggestions) < 8:
                coding_suggestions = get_suggestions_by_category("coding", 2)
                suggestions.extend(coding_suggestions)
            
            if area == "system_design" and len(suggestions) < 8:
                design_suggestions = get_suggestions_by_category("system_design", 2)
                suggestions.extend(design_suggestions)
            
            if area == "problem_solving" and len(suggestions) < 8:
                problem_solving_suggestions = get_suggestions_by_category("problem_solving", 2)
                suggestions.extend(problem_solving_suggestions)
        
        # 如果建议不足，添加项目经验相关建议
        if len(suggestions) < 5:
            project_suggestions = get_suggestions_by_category("project_experience", 2)
            suggestions.extend(project_suggestions)
        
        # 如果建议仍不足，添加通用技术面试建议
        if len(suggestions) < 5:
            general_suggestions = get_suggestions_by_category("general", 5 - len(suggestions))
            suggestions.extend(general_suggestions)
        
        # 如果没有任何建议（极少情况），获取随机建议
        if not suggestions:
            suggestions = get_random_suggestions(5)
        
        # 确保建议不重复
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in unique_suggestions:
                unique_suggestions.append(suggestion)
        
        # 返回建议（最多5条）
        return unique_suggestions[:5]