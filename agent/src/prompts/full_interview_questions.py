"""
完整面试模式的问题生成提示模板
"""

# 基础完整面试问题提示
FULL_BASIC_QUESTIONS_PROMPT = """
请根据以下岗位信息生成{question_count}个全面深入的面试问题:

岗位：{position_title}
岗位描述：{position_description}
技术领域：{tech_field}
岗位类型：{position_type}
难度级别：{difficulty_level}

要求：
1. 问题应全面深入，适合完整面试环节（每题3-10分钟回答）
2. 问题应覆盖技术深度、系统设计、工程实践和团队协作等多个方面
3. 问题数量应为{question_count}个，包括1个全面的自我介绍问题
4. 问题类型应多样化，包含：技术问题、系统设计问题、编码问题、行为问题等
5. 问题应能评估候选人的深度思考能力和实际解决问题的能力

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
- 确保问题能够深入测试候选人的专业能力和思维深度
- 设计一些开放性问题，评估候选人的思考过程
- 系统设计和编码问题应预留足够的回答时间（5-10分钟）
"""

# 深度技术面试问题提示
FULL_TECHNICAL_QUESTIONS_PROMPT = """
为完整技术面试环节生成{question_count}个深度技术问题:

技术领域：{tech_field}
核心技能要求：{key_skills}
岗位类型：{position_type}
难度级别：{difficulty_level}
高级技术要求：{advanced_requirements}

要求：
1. 问题应全面评估候选人的技术深度和广度
2. 包含基础概念、应用实践和高级技术挑战
3. 问题应包括至少一个系统设计问题和一个算法/编程问题
4. 每个问题应能引导候选人深入讨论其专业能力
5. 问题应验证候选人解决复杂技术问题的思路和方法

以JSON格式返回问题列表：
[
  {{
    "text": "问题内容",
    "type": "问题类型",
    "duration": 预期回答时长（秒）,
    "difficulty": "难度级别",
    "assessment_focus": "评估重点"
  }}
]

注意：问题应具有足够的深度和挑战性，适合评估高级技术人才
"""

# 系统设计问题提示
FULL_SYSTEM_DESIGN_QUESTIONS_PROMPT = """
为完整面试环节生成{question_count}个系统设计问题:

岗位：{position_title}
技术领域：{tech_field}
系统复杂度要求：{system_complexity}
规模要求：{scale_requirements}
难度级别：{difficulty_level}

要求：
1. 问题应考察候选人的系统设计思维和架构能力
2. 问题应包含明确的场景、约束和要求
3. 问题应涵盖可扩展性、可靠性、一致性等关键设计考量
4. 问题难度应符合岗位级别和要求
5. 每个问题应预留5-10分钟回答时间

以JSON格式返回问题列表：
[
  {{
    "text": "问题内容",
    "type": "系统设计",
    "duration": 预期回答时长（秒）,
    "difficulty": "难度级别",
    "design_aspects": ["需要考虑的设计方面1", "设计方面2", ...]
  }}
]

注意：系统设计问题应具有足够的开放性，同时有明确的评判标准
"""

# 全面行为问题提示
FULL_BEHAVIORAL_QUESTIONS_PROMPT = """
为完整面试环节生成{question_count}个深入的行为面试问题:

岗位：{position_title}
团队规模：{team_size}
工作挑战：{job_challenges}
领导力要求：{leadership_requirements}
难度级别：{difficulty_level}

要求：
1. 问题应评估候选人的软技能、团队协作和领导力
2. 问题应引导候选人提供具体的过往经历和案例
3. 问题应基于STAR法则（情境-任务-行动-结果）设计
4. 问题应涵盖：团队协作、冲突处理、项目管理、压力处理等方面
5. 每个问题应预留3-5分钟的回答时间

以JSON格式返回问题列表：
[
  {{
    "text": "问题内容",
    "type": "行为问题",
    "duration": 预期回答时长（秒）,
    "difficulty": "难度级别",
    "assessment_area": "评估领域"
  }}
]

注意：问题设计应引导候选人提供具体例子而非泛泛而谈
"""

# 全面个性化问题提示
FULL_PERSONALIZED_QUESTIONS_PROMPT = """
基于候选人背景全面生成{question_count}个个性化深度面试问题:

## 候选人详细背景
工作经历：{work_experience}
项目经验：{project_experience}
技术栈：{technical_stack}
教育背景：{education_background}
职业目标：{career_goals}

## 岗位信息
岗位：{position_title}
岗位职责：{job_responsibilities}
团队情况：{team_context}
技术挑战：{technical_challenges}

要求：
1. 问题应深入探讨候选人背景与岗位需求的契合度
2. 问题应验证候选人过往经历中的关键成就和贡献
3. 问题应探索候选人如何应对岗位中的实际挑战
4. 问题应评估候选人的成长潜力和职业规划与岗位的匹配度
5. 每个问题应能获取有价值的深入信息，而非表面回答

以JSON格式返回问题列表：
[
  {{
    "text": "问题内容",
    "type": "问题类型",
    "duration": 预期回答时长（秒）,
    "difficulty": "难度级别",
    "insight_goal": "希望获得的洞见"
  }}
]

注意：问题应基于候选人的独特背景定制，避免通用模板问题
"""

# 完整编码问题提示
FULL_CODING_QUESTIONS_PROMPT = """
为完整面试环节生成{question_count}个编码/算法面试问题:

技术领域：{tech_field}
编程语言要求：{programming_languages}
算法能力要求：{algorithm_requirements}
难度级别：{difficulty_level}

要求：
1. 问题应测试候选人的编程能力和算法思维
2. 问题应包含明确的输入、输出和约束条件
3. 问题应涵盖：数据结构、算法复杂度、边界情况处理等方面
4. 难度应符合岗位级别要求
5. 每个问题应预留10-15分钟的回答时间

以JSON格式返回问题列表：
[
  {{
    "text": "问题内容",
    "type": "编码问题",
    "duration": 预期回答时长（秒）,
    "difficulty": "难度级别",
    "key_concepts": ["涉及的核心概念1", "核心概念2", ...],
    "follow_up": "可能的延伸问题"
  }}
]

注意：问题应考察实际编码能力和思维过程，而非纯粹的算法难题
""" 