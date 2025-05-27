# ai_agent/scenarios/tech_interview_suggestions.py

from typing import Dict, List

"""
技术面试建议库

包含针对技术面试的各类建议，按照不同维度和场景分类
"""

# 技术内容相关建议
CONTENT_SUGGESTIONS = {
    # 回答相关性建议
    "relevance": [
        "技术面试中，确保回答紧扣问题核心，展示你对相关技术的深入理解",
        "回答问题前，先确认你理解了面试官的问题，必要时可以请求澄清",
        "避免泛泛而谈，针对具体技术问题给出具体、精准的回答",
        "当不确定问题时，诚实表达并尝试引导到你熟悉的相关领域",
        "回答时注意控制信息量，突出最关键的技术要点"
    ],
    
    # 回答结构建议
    "structure": [
        "技术回答应当结构清晰，可以采用'定义-原理-应用-优缺点'的框架",
        "复杂技术问题可以先给出结论，再逐步展开论证过程",
        "使用'首先、其次、最后'等过渡词，使你的技术解释更有条理",
        "对于系统设计类问题，可以采用自顶向下或自底向上的结构化思路",
        "回答结束时做简短总结，强化你的核心观点"
    ],
    
    # 专业术语使用建议
    "terminology": [
        "在回答中适当使用专业技术术语，展示你的专业背景和知识深度",
        "使用专业术语时，确保你完全理解其含义，避免误用",
        "面对非技术背景的面试官时，注意解释专业术语，确保沟通有效",
        "平衡使用技术术语和通俗解释，展示你的沟通能力",
        "避免过度使用行业黑话(jargon)，保持表达的清晰性"
    ],
    
    # 技术深度建议
    "depth": [
        "准备好深入讨论你简历上提到的每一项技术和项目",
        "对于核心技术，不仅要知其然，还要知其所以然，理解底层原理",
        "准备一些你在技术上遇到的挑战和解决方案，展示问题解决能力",
        "对技术选型决策能够解释原因，展示你的技术判断力",
        "能够分析技术方案的优缺点，展示全面思考能力"
    ]
}

# 编程能力相关建议
CODING_SUGGESTIONS = [
    "编程面试中，先理解问题，再设计算法，最后才开始编码",
    "在白板编程或在线编程时，边写边解释你的思路，展示逻辑思维过程",
    "注意代码的可读性和命名规范，展示良好的编程习惯",
    "完成编码后主动分析时间和空间复杂度，展示算法分析能力",
    "主动测试你的代码，考虑边界情况和异常处理",
    "如果卡住，尝试从简单情况入手，逐步构建完整解决方案",
    "不要害怕在面试中修改代码，展示迭代优化的能力",
    "熟悉常见数据结构和算法，能够灵活应用于解决问题"
]

# 系统设计相关建议
SYSTEM_DESIGN_SUGGESTIONS = [
    "系统设计面试中，先澄清需求和约束，再进行高层设计",
    "讨论系统的可扩展性、可靠性和性能等关键非功能需求",
    "能够估算系统容量和资源需求，展示工程实践能力",
    "讨论系统的数据模型和存储选择，并解释原因",
    "考虑系统的安全性和隐私保护措施",
    "展示对分布式系统常见问题(如一致性、可用性)的理解",
    "能够权衡不同设计决策的利弊，展示决策能力",
    "使用图表辅助说明系统架构，提高沟通效率"
]

# 问题解决能力相关建议
PROBLEM_SOLVING_SUGGESTIONS = [
    "面对开放性问题，展示你的分析框架和思考过程",
    "遇到不熟悉的问题，尝试将其分解为你熟悉的子问题",
    "在解决问题时考虑多种方案，并比较它们的优缺点",
    "技术面试中遇到难题，保持冷静，与面试官互动寻求提示",
    "展示你如何在有限资源和约束下做出合理的技术决策",
    "分享你过去如何解决技术债务或优化系统性能的经验",
    "讨论你如何平衡技术完美和项目时间线的冲突"
]

# 项目经验相关建议
PROJECT_EXPERIENCE_SUGGESTIONS = [
    "准备一些你参与过的技术项目案例，使用STAR法则描述你的贡献和解决方案",
    "重点突出你在项目中解决的技术挑战和创新点",
    "准备讨论你在项目中的具体角色和责任，以及与团队的协作",
    "能够解释项目中的技术选型决策和架构设计考量",
    "准备讨论项目中的失败经验和学习收获",
    "展示你如何衡量项目成功，包括技术指标和业务价值",
    "分享你如何在项目中应用最佳实践和设计模式"
]

# 通用技术面试建议
GENERAL_TECH_SUGGESTIONS = [
    "技术面试中，遇到不会的问题可以展示你的思考过程，而不是简单回答'不知道'",
    "提前了解面试公司使用的技术栈，针对性地准备相关知识点",
    "准备一些你遇到的技术挑战和解决方案，展示你的问题解决能力",
    "技术面试结束前，可以主动询问面试官对你技术能力的评价，以及需要改进的地方",
    "展示你的学习能力和对新技术的热情，这在技术领域尤为重要",
    "准备一些你对行业技术趋势的见解，展示你的前瞻性思维",
    "诚实面对知识盲点，展示你的学习意愿而非掩饰无知",
    "技术面试中保持专业但友好的态度，展示你是一个好的团队协作者",
    "准备一些关于你技术学习方法和资源的讨论，展示持续学习能力",
    "面试前复习计算机科学基础知识，如数据结构、算法、网络和操作系统"
]


def get_suggestions_by_category(category: str, count: int = 3) -> List[str]:
    """根据类别获取建议
    
    Args:
        category: 建议类别
        count: 返回建议数量
        
    Returns:
        List[str]: 建议列表
    """
    if category == "coding":
        return CODING_SUGGESTIONS[:count]
    elif category == "system_design":
        return SYSTEM_DESIGN_SUGGESTIONS[:count]
    elif category == "problem_solving":
        return PROBLEM_SOLVING_SUGGESTIONS[:count]
    elif category == "project_experience":
        return PROJECT_EXPERIENCE_SUGGESTIONS[:count]
    elif category == "general":
        return GENERAL_TECH_SUGGESTIONS[:count]
    elif category in CONTENT_SUGGESTIONS:
        return CONTENT_SUGGESTIONS[category][:count]
    else:
        return GENERAL_TECH_SUGGESTIONS[:count]


def get_random_suggestions(count: int = 5) -> List[str]:
    """获取随机建议
    
    从所有建议中随机选择指定数量的建议
    
    Args:
        count: 返回建议数量
        
    Returns:
        List[str]: 建议列表
    """
    import random
    
    # 收集所有建议
    all_suggestions = []
    
    # 添加内容相关建议
    for suggestions in CONTENT_SUGGESTIONS.values():
        all_suggestions.extend(suggestions)
    
    # 添加其他类别建议
    all_suggestions.extend(CODING_SUGGESTIONS)
    all_suggestions.extend(SYSTEM_DESIGN_SUGGESTIONS)
    all_suggestions.extend(PROBLEM_SOLVING_SUGGESTIONS)
    all_suggestions.extend(PROJECT_EXPERIENCE_SUGGESTIONS)
    all_suggestions.extend(GENERAL_TECH_SUGGESTIONS)
    
    # 随机选择建议
    if count >= len(all_suggestions):
        return all_suggestions
    
    return random.sample(all_suggestions, count)