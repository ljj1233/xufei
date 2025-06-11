"""
快速面试模式的问题生成提示模板
"""

# 基础快速面试问题提示（简短、直接）
QUICK_BASIC_QUESTIONS_PROMPT = """
请根据以下岗位信息生成{question_count}个快速面试问题:

岗位：{position_title}
岗位描述：{position_description}
技术领域：{tech_field}
岗位类型：{position_type}
难度级别：{difficulty_level}

要求：
1. 问题应简短直接，适合快速面试环节（每题1-2分钟回答）
2. 优先生成能快速评估核心能力的问题
3. 问题应涵盖基础技术知识和简要经验验证
4. 总问题数量应为{question_count}个，包括1个自我介绍问题
5. 自我介绍问题应限定在1分钟内完成

以JSON格式返回问题列表：
[
  {{
    "text": "问题内容",
    "type": "问题类型",
    "duration": 预期回答时长（秒）,
    "difficulty": "难度级别"
  }}
]

注意：
- 确保问题简洁明了，直指核心能力
- 不要包含复杂的系统设计或编码问题
- 每个问题预期回答时间不应超过2分钟（120秒）
"""

# 快速技术面试问题提示
QUICK_TECHNICAL_QUESTIONS_PROMPT = """
为快速技术面试环节生成{question_count}个高效的技术问题:

技术领域：{tech_field}
核心技能要求：{key_skills}
岗位类型：{position_type}
难度级别：{difficulty_level}

要求：
1. 问题必须简短直接，且答案应简洁明确
2. 问题应针对候选人核心技术能力进行评估
3. 每个问题可在60-90秒内回答完毕
4. 避免复杂的概念性问题，专注于实用技能验证
5. 问题类型可包括：概念理解、技术应用、常见问题解决等

以JSON格式返回问题列表：
[
  {{
    "text": "问题内容",
    "type": "技术问题",
    "duration": 预期回答时长（秒）,
    "difficulty": "难度级别",
    "skill_focus": "针对的核心技能"
  }}
]

注意：所有问题应适合快速面试环节，能在短时间内完成
"""

# 快速行为问题提示
QUICK_BEHAVIORAL_QUESTIONS_PROMPT = """
为快速面试环节生成{question_count}个简短的行为面试问题:

岗位：{position_title}
团队协作要求：{teamwork_requirements}
工作性质：{job_nature}
难度级别：{difficulty_level}

要求：
1. 问题应简短明确，可在60-90秒内回答
2. 问题应聚焦于关键行为特质的快速评估
3. 问题应包括但不限于：快速决策能力、团队协作、压力应对等
4. 避免需要长篇故事的问题，转向具体情境的简短回答

以JSON格式返回问题列表：
[
  {{
    "text": "问题内容", 
    "type": "行为问题",
    "duration": 预期回答时长（秒）,
    "difficulty": "难度级别",
    "trait_focus": "评估的关键特质"
  }}
]

注意：设计问题时考虑快速面试的时间限制，确保简短有效
"""

# 快速个性化面试问题提示
QUICK_PERSONALIZED_QUESTIONS_PROMPT = """
基于候选人背景快速生成{question_count}个针对性面试问题:

## 候选人简介
背景摘要：{candidate_background}
核心关键词：{background_keywords}

## 岗位信息
岗位：{position_title}
技术领域：{tech_field}
核心技能要求：{key_skills}

要求：
1. 问题应直接基于候选人背景与岗位需求的交叉点
2. 每个问题应在90秒内可以完成回答
3. 问题应验证候选人简历中声称的技能与经验
4. 问题应简洁明确，避免开放式讨论

以JSON格式返回问题列表：
[
  {{
    "text": "问题内容",
    "type": "问题类型",
    "duration": 预期回答时长（秒）,
    "difficulty": "难度级别",
    "verification_focus": "验证的关键点"
  }}
]

注意：问题设计应考虑快速面试的时间限制，同时保持针对性
""" 