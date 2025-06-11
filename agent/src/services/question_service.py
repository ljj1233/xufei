"""
面试问题生成服务

该服务负责根据职位信息动态生成面试问题，包括问题内容、考察技能、建议回答时间和参考答案。
支持两种面试模式：快速模式和完整模式。
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Union

from ..core.system.config import AgentConfig
from ..services.openai_service import OpenAIService
from ..services.content_filter_service import ContentFilterService, FilterResult
from ..prompts.quick_interview_questions import (
    QUICK_BASIC_QUESTIONS_PROMPT,
    QUICK_TECHNICAL_QUESTIONS_PROMPT,
    QUICK_BEHAVIORAL_QUESTIONS_PROMPT,
    QUICK_PERSONALIZED_QUESTIONS_PROMPT
)
from ..prompts.full_interview_questions import (
    FULL_BASIC_QUESTIONS_PROMPT,
    FULL_TECHNICAL_QUESTIONS_PROMPT,
    FULL_SYSTEM_DESIGN_QUESTIONS_PROMPT,
    FULL_BEHAVIORAL_QUESTIONS_PROMPT,
    FULL_PERSONALIZED_QUESTIONS_PROMPT,
    FULL_CODING_QUESTIONS_PROMPT
)

# 配置日志
logger = logging.getLogger(__name__)

class QuestionServiceConfig:
    """问题服务配置类"""
    
    def __init__(self, 
                 api_model: str = "gpt-4-turbo", 
                 temperature: float = 0.7,
                 max_tokens: int = 2000,
                 enable_content_filter: bool = True):
        """初始化配置
        
        Args:
            api_model: 使用的LLM模型名称
            temperature: 采样温度
            max_tokens: 最大生成的token数量
            enable_content_filter: 是否启用内容过滤
        """
        self.api_model = api_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_content_filter = enable_content_filter


class QuestionService:
    """
    面试问题生成服务
    
    通过调用OpenAI API，基于职位和技能信息生成高质量的面试问题。
    支持两种模式：快速模式和完整模式。
    问题包含问题内容、考察的技能点、建议回答时间和参考答案。
    """
    
    def __init__(self, 
                 openai_service: Optional[OpenAIService] = None,
                 config: Optional[QuestionServiceConfig] = None):
        """
        初始化问题生成服务
        
        Args:
            openai_service: OpenAI服务实例，如果为None则创建新实例
            config: 服务配置，如果为None则使用默认配置
        """
        logger.info("初始化问题生成服务")
        
        # 初始化OpenAI服务
        if openai_service is None:
            agent_config = AgentConfig()
            self.openai_service = OpenAIService(agent_config)
        else:
            self.openai_service = openai_service
            
        # 初始化配置
        self.config = config or QuestionServiceConfig()
        
        # 初始化内容过滤服务
        self.content_filter = ContentFilterService.get_instance()
    
    async def generate_interview_questions(
        self, 
        position_info: Dict[str, Any],
        question_count: int = 5,
        difficulty_level: str = "medium",
        candidate_background: Optional[str] = None,
        mode: str = "full",
        question_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        生成面试问题
        
        Args:
            position_info: 职位信息，包含title, description, tech_field, skills等
            question_count: 需要生成的问题数量，默认为5道
            difficulty_level: 难度级别，可选值为"easy", "medium", "hard"
            candidate_background: 候选人背景信息（可选）
            mode: 面试模式，"quick"或"full"
            question_type: 问题类型（可选），如"technical", "behavioral"等
            
        Returns:
            问题列表，每个问题包含问题内容、类型、建议回答时长和难度级别等
            
        Raises:
            ValueError: 参数无效或API调用失败时引发
        """
        # 参数验证
        self._validate_params(position_info, question_count, difficulty_level, mode)
        
        # 根据模式选择不同的生成策略
        try:
            if mode == "quick":
                questions = await self._generate_quick_questions(
                    position_info, 
                    question_count, 
                    difficulty_level, 
                    candidate_background,
                    question_type
                )
            else:  # 默认为完整模式
                questions = await self._generate_full_questions(
                    position_info, 
                    question_count, 
                    difficulty_level, 
                    candidate_background,
                    question_type
                )
                
            # 对生成的问题进行内容过滤
            if self.config.enable_content_filter:
                questions = self._filter_questions(questions)
                
            return questions
        except Exception as e:
            logger.error(f"生成问题失败: {str(e)}")
            # 使用备用方案
            return self._get_fallback_questions(position_info, question_count, difficulty_level, mode)
    
    def _validate_params(self, 
                        position_info: Dict[str, Any], 
                        question_count: int, 
                        difficulty_level: str,
                        mode: str) -> None:
        """验证输入参数
        
        Args:
            position_info: 职位信息
            question_count: 问题数量
            difficulty_level: 难度级别
            mode: 面试模式
            
        Raises:
            ValueError: 参数无效时引发
        """
        if not isinstance(position_info, dict):
            raise ValueError("职位信息必须是字典类型")
        
        if question_count <= 0:
            raise ValueError("问题数量必须为正整数")
        
        if difficulty_level not in ["easy", "medium", "hard"]:
            raise ValueError("难度级别必须为easy, medium或hard")
        
        if mode not in ["quick", "full"]:
            raise ValueError("面试模式必须为quick或full")
    
    async def _generate_quick_questions(
        self,
        position_info: Dict[str, Any],
        question_count: int,
        difficulty_level: str,
        candidate_background: Optional[str] = None,
        question_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """生成快速面试问题
        
        Args:
            position_info: 职位信息
            question_count: 问题数量
            difficulty_level: 难度级别
            candidate_background: 候选人背景信息（可选）
            question_type: 问题类型（可选）
            
        Returns:
            问题列表
        """
        # 准备提示参数
        prompt_params = {
            "position_title": position_info.get("title", position_info.get("position_name", "")),
            "position_description": position_info.get("description", ""),
            "tech_field": position_info.get("tech_field", ""),
            "position_type": position_info.get("position_type", "技术岗位"),
            "key_skills": ", ".join(position_info.get("skills", [])),
            "difficulty_level": difficulty_level,
            "question_count": question_count
        }
        
        # 根据问题类型选择提示模板
        prompt = self._select_quick_prompt_template(question_type, candidate_background, prompt_params)
        
        # 调用OpenAI生成问题
        return await self._generate_questions_with_openai(prompt, "快速面试问题设计专家")
    
    def _select_quick_prompt_template(
        self, 
        question_type: Optional[str], 
        candidate_background: Optional[str],
        prompt_params: Dict[str, Any]
    ) -> str:
        """选择快速模式的提示模板
        
        Args:
            question_type: 问题类型
            candidate_background: 候选人背景
            prompt_params: 提示参数
            
        Returns:
            格式化后的提示模板
        """
        # 如果有候选人背景，优先使用个性化提示
        if candidate_background:
            return QUICK_PERSONALIZED_QUESTIONS_PROMPT.format(
                **prompt_params,
                candidate_background=candidate_background,
                background_keywords=self._extract_keywords(candidate_background)
            )
        
        # 根据问题类型选择提示模板
        if question_type == "technical":
            return QUICK_TECHNICAL_QUESTIONS_PROMPT.format(**prompt_params)
        elif question_type == "behavioral":
            return QUICK_BEHAVIORAL_QUESTIONS_PROMPT.format(
                **prompt_params,
                teamwork_requirements="高效协作",
                job_nature="技术研发"
            )
        
        # 默认使用基础提示模板
        return QUICK_BASIC_QUESTIONS_PROMPT.format(**prompt_params)
    
    async def _generate_full_questions(
        self,
        position_info: Dict[str, Any],
        question_count: int,
        difficulty_level: str,
        candidate_background: Optional[str] = None,
        question_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """生成完整面试问题
        
        Args:
            position_info: 职位信息
            question_count: 问题数量
            difficulty_level: 难度级别
            candidate_background: 候选人背景信息（可选）
            question_type: 问题类型（可选）
            
        Returns:
            问题列表
        """
        # 准备提示参数
        prompt_params = {
            "position_title": position_info.get("title", position_info.get("position_name", "")),
            "position_description": position_info.get("description", ""),
            "tech_field": position_info.get("tech_field", ""),
            "position_type": position_info.get("position_type", "技术岗位"),
            "key_skills": ", ".join(position_info.get("skills", [])),
            "difficulty_level": difficulty_level,
            "question_count": question_count,
            "advanced_requirements": "具有系统设计和算法能力",
            "system_complexity": "高",
            "scale_requirements": "大规模系统",
            "programming_languages": "Python, Java, Go等",
            "algorithm_requirements": "数据结构、算法设计与分析"
        }
        
        # 根据问题类型选择提示模板
        prompt = self._select_full_prompt_template(question_type, candidate_background, prompt_params)
        
        # 调用OpenAI生成问题
        return await self._generate_questions_with_openai(prompt, "深度技术面试问题设计专家")
    
    def _select_full_prompt_template(
        self, 
        question_type: Optional[str], 
        candidate_background: Optional[str],
        prompt_params: Dict[str, Any]
    ) -> str:
        """选择完整模式的提示模板
        
        Args:
            question_type: 问题类型
            candidate_background: 候选人背景
            prompt_params: 提示参数
            
        Returns:
            格式化后的提示模板
        """
        # 如果有候选人背景，优先使用个性化提示
        if candidate_background:
            return FULL_PERSONALIZED_QUESTIONS_PROMPT.format(
                **prompt_params,
                work_experience=candidate_background,
                project_experience=candidate_background,
                technical_stack=prompt_params["key_skills"],
                education_background="",
                career_goals="",
                job_responsibilities=prompt_params["position_description"],
                team_context="",
                technical_challenges=""
            )
        
        # 根据问题类型选择提示模板
        if question_type == "technical":
            return FULL_TECHNICAL_QUESTIONS_PROMPT.format(**prompt_params)
        elif question_type == "system_design":
            return FULL_SYSTEM_DESIGN_QUESTIONS_PROMPT.format(**prompt_params)
        elif question_type == "behavioral":
            return FULL_BEHAVIORAL_QUESTIONS_PROMPT.format(
                **prompt_params,
                team_size="中型团队",
                job_challenges="技术挑战和团队协作",
                leadership_requirements="技术领导力"
            )
        elif question_type == "coding":
            return FULL_CODING_QUESTIONS_PROMPT.format(**prompt_params)
        
        # 默认使用基础提示模板
        return FULL_BASIC_QUESTIONS_PROMPT.format(**prompt_params)
    
    async def _generate_questions_with_openai(self, prompt: str, system_role: str) -> List[Dict[str, Any]]:
        """使用OpenAI API生成问题
        
        Args:
            prompt: 提示词
            system_role: 系统角色描述
            
        Returns:
            生成的问题列表
            
        Raises:
            ValueError: 如果API调用失败
        """
        # 调用OpenAI生成问题
        response = await self.openai_service.chat_completion(
            messages=[
                {"role": "system", "content": f"你是一位专业的{system_role}"},
                {"role": "user", "content": prompt}
            ],
            model=self.config.api_model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        # 检查响应状态
        if response.get("status") != "success":
            error_msg = response.get("error", "未知错误")
            logger.error(f"OpenAI API调用失败: {error_msg}")
            raise ValueError(f"生成问题失败: {error_msg}")
        
        # 解析响应生成问题
        questions = self._parse_questions_from_response(response)
        logger.info(f"成功生成{len(questions)}个面试问题")
        
        return questions
    
    def _parse_questions_from_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从API响应中解析问题列表
        
        Args:
            response: API响应
            
        Returns:
            问题列表
        """
        try:
            content = response.get("content", "")
            if not content:
                logger.warning("API响应内容为空")
                return []
            
            # 尝试从内容中提取JSON部分
            # 方法1: 提取方括号中的内容
            json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    questions = json.loads(json_str)
                    return questions
                except json.JSONDecodeError:
                    logger.warning("方法1提取的JSON无效，尝试方法2")
            
            # 方法2: 提取```json包装的内容
            json_match = re.search(r'```(?:json)?\s*(\[\s*\{.*?\}\s*\])\s*```', content, re.DOTALL)
            if json_match:
                try:
                    questions = json.loads(json_match.group(1))
                    return questions
                except json.JSONDecodeError:
                    logger.warning("方法2提取的JSON无效，尝试方法3")
            
            # 方法3: 尝试将整个内容作为JSON解析
            try:
                content_json = json.loads(content)
                if isinstance(content_json, list) and all(isinstance(item, dict) for item in content_json):
                    return content_json
                
                # 如果响应是包装的JSON对象，提取questions字段
                if isinstance(content_json, dict) and "questions" in content_json:
                    return content_json["questions"]
            except json.JSONDecodeError:
                logger.warning("方法3尝试解析整个内容为JSON失败")
            
            # 如果仍然无法解析，记录错误并返回空列表
            logger.error(f"无法从响应中解析JSON: {content[:200]}...")
            return []
        
        except Exception as e:
            logger.error(f"解析问题时出错: {str(e)}")
            return []
    
    def _filter_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """对问题内容进行敏感内容过滤
        
        Args:
            questions: 需要过滤的问题列表
            
        Returns:
            过滤后的问题列表
        """
        filtered_questions = []
        
        for question in questions:
            # 过滤问题文本
            question_text = question.get("text", question.get("question", ""))
            if question_text:
                filter_result = self.content_filter.filter_text(question_text)
                
                # 如果检测到敏感内容，记录日志
                if filter_result.has_sensitive_content:
                    logger.warning(
                        f"问题包含敏感内容，类别: {filter_result.sensitive_categories}, "
                        f"级别: {filter_result.highest_severity}, "
                        f"敏感词数量: {filter_result.sensitive_word_count}"
                    )
                    
                    # 使用过滤后的文本替换原文本
                    if "text" in question:
                        question["text"] = filter_result.filtered_text
                    else:
                        question["question"] = filter_result.filtered_text
                    
                    # 添加过滤标记
                    question["filtered"] = True
                    question["sensitive_categories"] = filter_result.sensitive_categories
                
            # 过滤参考答案（如果有）
            if "reference_answer" in question and question["reference_answer"]:
                answer_filter_result = self.content_filter.filter_text(question["reference_answer"])
                
                if answer_filter_result.has_sensitive_content:
                    logger.warning(
                        f"参考答案包含敏感内容，类别: {answer_filter_result.sensitive_categories}, "
                        f"级别: {answer_filter_result.highest_severity}, "
                        f"敏感词数量: {answer_filter_result.sensitive_word_count}"
                    )
                    
                    # 使用过滤后的文本替换原文本
                    question["reference_answer"] = answer_filter_result.filtered_text
                    
                    # 添加过滤标记（如果尚未添加）
                    if "filtered" not in question:
                        question["filtered"] = True
                        question["sensitive_categories"] = answer_filter_result.sensitive_categories
            
            filtered_questions.append(question)
        
        return filtered_questions
    
    def _extract_keywords(self, text: str) -> str:
        """从文本中提取关键词
        
        Args:
            text: 输入文本
            
        Returns:
            提取的关键词字符串
        """
        if not text:
            return ""
            
        # 简单实现，实际应用中可以使用更复杂的NLP技术
        words = text.lower().split()
        # 过滤短词和常见词
        common_words = {"and", "the", "to", "of", "a", "in", "for", "on", "is", "that", "it", "with"}
        keywords = [word for word in words if len(word) > 3 and word not in common_words]
        # 去重并限制数量
        unique_keywords = list(set(keywords))[:15]
        return ", ".join(unique_keywords)
    
    def _get_fallback_questions(
        self, 
        position_info: Dict[str, Any],
        question_count: int,
        difficulty_level: str,
        mode: str
    ) -> List[Dict[str, Any]]:
        """获取备用面试问题
        
        在API调用失败时使用的预定义问题
        
        Args:
            position_info: 职位信息
            question_count: 问题数量
            difficulty_level: 难度级别
            mode: 面试模式，"quick"或"full"
            
        Returns:
            问题列表
        """
        tech_field = position_info.get("tech_field", "").lower()
        
        # 通用问题
        general_questions = [
            {
                "text": "请简单介绍一下自己的专业背景和核心技能。",
                "type": "自我介绍",
                "duration": 60 if mode == "quick" else 180,
                "difficulty": "easy"
            },
            {
                "text": "描述一下你最近参与的一个项目，你在其中的角色是什么？",
                "type": "项目经验",
                "duration": 120 if mode == "quick" else 300,
                "difficulty": difficulty_level
            }
        ]
        
        # 技术领域相关问题
        tech_questions = {
            "ai": [
                {
                    "text": "简述一下深度学习与传统机器学习的主要区别。",
                    "type": "技术问题",
                    "duration": 120 if mode == "quick" else 240,
                    "difficulty": difficulty_level
                }
            ],
            "web": [
                {
                    "text": "描述一下前端性能优化的常用方法。",
                    "type": "技术问题", 
                    "duration": 120 if mode == "quick" else 240,
                    "difficulty": difficulty_level
                }
            ],
            "backend": [
                {
                    "text": "如何设计一个高并发的Web服务？",
                    "type": "系统设计",
                    "duration": 120 if mode == "quick" else 300,
                    "difficulty": difficulty_level
                }
            ]
        }
        
        # 根据技术领域选择问题
        field_questions = []
        for field, questions in tech_questions.items():
            if field in tech_field:
                field_questions.extend(questions)
                break
        
        # 如果没有匹配的技术领域问题，使用默认技术问题
        if not field_questions:
            field_questions = [
                {
                    "text": "描述你最熟悉的编程语言的优缺点。",
                    "type": "技术问题",
                    "duration": 120 if mode == "quick" else 240,
                    "difficulty": difficulty_level
                }
            ]
        
        # 组合问题并限制数量
        all_questions = general_questions + field_questions
        if len(all_questions) > question_count:
            all_questions = all_questions[:question_count]
        
        # 对备用问题也进行内容过滤
        if self.config.enable_content_filter:
            all_questions = self._filter_questions(all_questions)
        
        return all_questions


def create_question_service(
    openai_service: Optional[OpenAIService] = None,
    config: Optional[QuestionServiceConfig] = None
) -> QuestionService:
    """创建问题服务实例
    
    工厂函数，用于创建QuestionService实例
    
    Args:
        openai_service: OpenAI服务实例，如果为None则创建新实例
        config: 服务配置，如果为None则使用默认配置
        
    Returns:
        QuestionService实例
    """
    return QuestionService(openai_service, config) 