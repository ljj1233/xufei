"""
面试问题生成提示模板
"""

# 基于岗位信息生成通用面试问题
GENERAL_QUESTIONS_PROMPT = """
请根据以下岗位信息生成{question_count}个面试问题:

岗位：{position_title}
岗位描述：{position_description}
技术领域：{tech_field}
岗位类型：{position_type}
难度级别：{difficulty_level}

要求：
1. 问题应涵盖技术知识、实际经验和场景应对能力
2. 问题难度应符合指定难度级别({difficulty_level})
3. 问题类型应包括：技术问题、行为问题、情景问题等
4. 每个问题附带合理的预期回答时长(秒)
5. 每个问题需标明类型

以JSON格式返回问题列表：
[
  {
    "text": "问题内容",
    "type": "问题类型",
    "duration": 预期回答时长,
    "difficulty": "难度级别"
  }
]

注意：确保生成的问题专业、简洁明了，且与岗位需求高度相关
"""

# 基于岗位信息和个人背景生成个性化问题
PERSONALIZED_QUESTIONS_PROMPT = """
请根据候选人背景和岗位信息生成{question_count}个定制化面试问题:

## 岗位信息
岗位：{position_title}
技术领域：{tech_field}
岗位类型：{position_type}
岗位描述：{position_description}

## 候选人背景
候选人描述：{candidate_background}
核心关键字：{background_keywords}

要求：
1. 问题应针对候选人背景与岗位要求的结合点
2. 问题难度应符合指定难度级别({difficulty_level})
3. 问题应包括技术验证、经验提取和能力评估
4. 每个问题附带预期回答时长(秒)
5. 每个问题需标明类型

以JSON格式返回问题列表：
[
  {
    "text": "问题内容",
    "type": "问题类型",
    "duration": 预期回答时长,
    "difficulty": "难度级别",
    "focus_area": "问题重点关注领域"
  }
]

注意：
- 避免过于宽泛的问题
- 确保问题能引导候选人具体展示其技能和经验
- 不要假设候选人的技能超出其描述范围
"""

# 快速面试问题提示（更简短、直接）
QUICK_INTERVIEW_PROMPT = """
请根据岗位需求生成{question_count}个简短有效的面试问题:

岗位：{position_title}
岗位类型：{position_type}
核心技能需求：{key_skills}
候选人背景关键词：{background_keywords}

要求：
1. 问题应直接、简短，能在短时间内评估候选人
2. 每个问题2-3分钟内可回答完毕
3. 问题应覆盖核心技能验证和经验证明
4. 特别关注候选人背景与岗位要求的匹配度

以JSON格式返回问题列表：
[
  {
    "text": "问题内容",
    "type": "问题类型",
    "duration": 预期回答时长,
    "difficulty": "难度级别"
  }
]

注意：问题应简洁明了，直指核心能力
"""

# 提取候选人背景关键词的提示
EXTRACT_BACKGROUND_KEYWORDS_PROMPT = """
请从以下候选人背景描述中提取关键技能、经验和特点的关键词:

{candidate_background}

要求:
1. 提取关键技术技能
2. 提取项目经验关键词
3. 提取软技能关键词
4. 提取教育背景关键词

以JSON格式返回:
{
  "technical_skills": ["技能1", "技能2", ...],
  "project_experience": ["经验1", "经验2", ...],
  "soft_skills": ["软技能1", "软技能2", ...],
  "education": ["教育背景1", "教育背景2", ...]
}

注意：仅提取文本中明确提及的内容，不要推测或添加未提及的内容。
"""