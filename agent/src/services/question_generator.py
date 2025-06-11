"""
面试问题生成服务

负责根据不同模式（快速模式和完整模式）生成面试问题
"""

import json
import logging
import random
import re
from typing import Dict, Any, List, Optional, Union

from ..core.system.config import AgentConfig
from ..services.openai_service import OpenAIService
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

# 日志配置
logger = logging.getLogger(__name__)

class QuestionGeneratorConfig:
    """问题生成器配置类"""
    
    def __init__(self, 
                 api_model: str = "gpt-4-turbo", 
                 temperature: float = 0.7,
                 max_tokens: int = 2000, 
                 use_cache: bool = True):
        """初始化配置
        
        Args:
            api_model: 使用的LLM模型名称
            temperature: 采样温度
            max_tokens: 最大生成的token数量
            use_cache: 是否使用结果缓存
        """
        self.api_model = api_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.use_cache = use_cache


class QuestionGenerator:
    """面试问题生成器，支持快速模式和完整模式
    
    该类负责根据不同面试模式和职位要求生成面试问题。
    支持个性化定制、多种难度级别和不同技术领域。
    
    设计原则:
    1. 依赖注入 - 所有外部依赖通过构造函数参数提供
    2. 单一职责 - 每个方法只负责一项具体功能
    3. 封装 - 内部状态和实现细节对外隐藏
    4. 异常处理 - 合理处理外部API调用异常
    """
    
    def __init__(self, 
                 openai_service: Optional[OpenAIService] = None,
                 config: Optional[QuestionGeneratorConfig] = None):
        """初始化问题生成器
        
        Args:
            openai_service: OpenAI服务实例，如果不提供则创建新实例
            config: 问题生成器配置，如果不提供则使用默认配置
        """
        # 初始化OpenAI服务
        if openai_service is None:
            agent_config = AgentConfig()
            openai_service = OpenAIService(agent_config)
        self.openai_service = openai_service
        
        # 初始化配置
        self.config = config or QuestionGeneratorConfig()
        
        # 缓存
        self.question_cache = {}  
        
        logger.info("问题生成器初始化完成")
    
    async def generate_questions(
        self, 
        job_position: Dict[str, Any],
        question_count: int = 5,
        difficulty_level: str = "medium",
        candidate_background: Optional[str] = None,
        mode: str = "full"
    ) -> List[Dict[str, Any]]:
        """根据面试模式生成面试问题
        
        Args:
            job_position: 职位信息，包含title, description, tech_field, position_type等
            question_count: 问题数量
            difficulty_level: 难度级别，可选值为"easy", "medium", "hard"
            candidate_background: 候选人背景信息（可选）
            mode: 面试模式，"quick"或"full"
            
        Returns:
            问题列表，每个问题包含text, type, duration, difficulty等字段
            
        Raises:
            ValueError: 参数无效时引发
        """
        # 参数验证
        self._validate_params(job_position, question_count, difficulty_level, mode)
        
        # 创建缓存键并检查缓存
        if self.config.use_cache:
            cache_key = self._create_cache_key(job_position, question_count, difficulty_level, mode)
            cached_questions = self._get_cached_questions(cache_key)
            if cached_questions:
                return cached_questions
        
        # 根据模式选择不同的生成策略
        try:
            if mode == "quick":
                questions = await self._generate_quick_questions(job_position, question_count, difficulty_level, candidate_background)
            else:  # 默认为完整模式
                questions = await self._generate_full_questions(job_position, question_count, difficulty_level, candidate_background)
            
            # 缓存结果
            if self.config.use_cache:
                self.question_cache[cache_key] = questions
                
            return questions
        except Exception as e:
            logger.error(f"生成问题失败: {str(e)}")
            # 使用备用方案
            return self._get_fallback_questions(job_position, question_count, difficulty_level, mode)
    
    def _validate_params(self, 
                        job_position: Dict[str, Any], 
                        question_count: int, 
                        difficulty_level: str,
                        mode: str) -> None:
        """验证输入参数
        
        Args:
            job_position: 职位信息
            question_count: 问题数量
            difficulty_level: 难度级别
            mode: 面试模式
            
        Raises:
            ValueError: 参数无效时引发
        """
        if not isinstance(job_position, dict):
            raise ValueError("职位信息必须是字典类型")
        
        if question_count <= 0:
            raise ValueError("问题数量必须为正整数")
        
        if difficulty_level not in ["easy", "medium", "hard"]:
            raise ValueError("难度级别必须为easy, medium或hard")
        
        if mode not in ["quick", "full"]:
            raise ValueError("面试模式必须为quick或full")
    
    def _create_cache_key(self, 
                         job_position: Dict[str, Any],
                         question_count: int,
                         difficulty_level: str,
                         mode: str) -> str:
        """创建缓存键
        
        Args:
            job_position: 职位信息
            question_count: 问题数量
            difficulty_level: 难度级别
            mode: 面试模式
            
        Returns:
            缓存键字符串
        """
        position_id = job_position.get("id", "")
        position_title = job_position.get("title", "")
        position_field = job_position.get("tech_field", "")
        return f"{position_id}_{position_title}_{position_field}_{question_count}_{difficulty_level}_{mode}"
    
    def _get_cached_questions(self, cache_key: str) -> List[Dict[str, Any]]:
        """从缓存获取问题
        
        Args:
            cache_key: 缓存键
            
        Returns:
            问题列表，如果缓存不存在则返回空列表
        """
        if cache_key in self.question_cache:
            logger.info(f"使用缓存的问题集: {cache_key}")
            return self.question_cache[cache_key]
        return []
    
    async def _generate_quick_questions(
        self,
        job_position: Dict[str, Any],
        question_count: int,
        difficulty_level: str,
        candidate_background: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """生成快速面试问题
        
        Args:
            job_position: 职位信息
            question_count: 问题数量
            difficulty_level: 难度级别
            candidate_background: 候选人背景信息（可选）
            
        Returns:
            问题列表
        """
        # 准备提示参数
        prompt_params = {
            "position_title": job_position.get("title", ""),
            "position_description": job_position.get("description", ""),
            "tech_field": job_position.get("tech_field", ""),
            "position_type": job_position.get("position_type", ""),
            "key_skills": ", ".join(job_position.get("required_skills", [])),
            "difficulty_level": difficulty_level,
            "question_count": question_count
        }
        
        # 如果有候选人背景，使用个性化提示
        if candidate_background:
            prompt = QUICK_PERSONALIZED_QUESTIONS_PROMPT.format(
                **prompt_params,
                candidate_background=candidate_background,
                background_keywords=self._extract_background_keywords(candidate_background)
            )
        else:
            # 使用基础快速提示模板
            prompt = QUICK_BASIC_QUESTIONS_PROMPT.format(**prompt_params)
        
        # 调用OpenAI生成问题
        response = await self.openai_service.chat_completion(
            messages=[
                {"role": "system", "content": "你是一位专业的面试问题设计专家"},
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
        logger.info(f"成功生成{len(questions)}个快速面试问题")
        
        return questions
    
    async def _generate_full_questions(
        self,
        job_position: Dict[str, Any],
        question_count: int,
        difficulty_level: str,
        candidate_background: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """生成完整面试问题
        
        Args:
            job_position: 职位信息
            question_count: 问题数量
            difficulty_level: 难度级别
            candidate_background: 候选人背景信息（可选）
            
        Returns:
            问题列表
        """
        # 准备提示参数
        prompt_params = {
            "position_title": job_position.get("title", ""),
            "position_description": job_position.get("description", ""),
            "tech_field": job_position.get("tech_field", ""),
            "position_type": job_position.get("position_type", ""),
            "key_skills": ", ".join(job_position.get("required_skills", [])),
            "difficulty_level": difficulty_level,
            "question_count": question_count,
            "advanced_requirements": "具有系统设计和算法能力",
            "system_complexity": "高",
            "scale_requirements": "大规模系统",
            "programming_languages": "Python, Java, Go等",
            "algorithm_requirements": "数据结构、算法设计与分析"
        }
        
        # 如果有候选人背景，使用个性化提示
        if candidate_background:
            prompt = FULL_PERSONALIZED_QUESTIONS_PROMPT.format(
                **prompt_params,
                work_experience=candidate_background,
                project_experience=candidate_background,
                technical_stack=", ".join(job_position.get("required_skills", [])),
                education_background="",
                career_goals="",
                job_responsibilities=job_position.get("description", ""),
                team_context="",
                technical_challenges=""
            )
        else:
            # 使用基础完整提示模板
            prompt = FULL_BASIC_QUESTIONS_PROMPT.format(**prompt_params)
        
        # 调用OpenAI生成问题
        response = await self.openai_service.chat_completion(
            messages=[
                {"role": "system", "content": "你是一位专业的深度技术面试问题设计专家"},
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
        logger.info(f"成功生成{len(questions)}个完整面试问题")
        
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
    
    def _extract_background_keywords(self, background: str) -> str:
        """从候选人背景中提取关键词
        
        Args:
            background: 候选人背景文本
            
        Returns:
            提取的关键词字符串
        """
        if not background:
            return ""
            
        # 简单实现，实际应用中可以使用更复杂的NLP技术
        words = background.lower().split()
        # 过滤短词和常见词
        common_words = {"and", "the", "to", "of", "a", "in", "for", "on", "is", "that", "it", "with"}
        keywords = [word for word in words if len(word) > 3 and word not in common_words]
        # 去重并限制数量
        unique_keywords = list(set(keywords))[:15]
        return ", ".join(unique_keywords)
    
    def _get_fallback_questions(
        self, 
        job_position: Dict[str, Any],
        question_count: int,
        difficulty_level: str,
        mode: str
    ) -> List[Dict[str, Any]]:
        """获取备用面试问题
        
        在API调用失败时使用的预定义问题
        
        Args:
            job_position: 职位信息
            question_count: 问题数量
            difficulty_level: 难度级别
            mode: 面试模式，"quick"或"full"
            
        Returns:
            问题列表
        """
        if mode == "quick":
            return self._get_fallback_quick_questions(job_position, question_count, difficulty_level)
        else:
            return self._get_fallback_full_questions(job_position, question_count, difficulty_level)
    
    def _get_fallback_quick_questions(
        self, 
        job_position: Dict[str, Any],
        question_count: int,
        difficulty_level: str
    ) -> List[Dict[str, Any]]:
        """获取备用快速面试问题
        
        在API调用失败时使用的预定义问题
        
        Args:
            job_position: 职位信息
            question_count: 问题数量
            difficulty_level: 难度级别
            
        Returns:
            问题列表
        """
        tech_field = job_position.get("tech_field", "").lower()
        position_type = job_position.get("position_type", "").lower()
        
        # 通用问题
        general_questions = [
            {
                "text": "请简单介绍一下自己的专业背景和核心技能。",
                "type": "SELF_INTRO",
                "duration": 60,
                "difficulty": "easy"
            },
            {
                "text": "简述一下你最近参与的一个项目，你在其中的角色是什么？",
                "type": "BEHAVIORAL",
                "duration": 120,
                "difficulty": difficulty_level
            }
        ]
        
        # 根据技术领域添加特定问题
        field_specific_questions = {
            "ai": [
                {
                    "text": "简述一下深度学习与传统机器学习的主要区别。",
                    "type": "TECHNICAL",
                    "duration": 120,
                    "difficulty": difficulty_level
                },
                {
                    "text": "你最熟悉的一种深度学习框架是什么？请简述其优缺点。",
                    "type": "TECHNICAL",
                    "duration": 120,
                    "difficulty": difficulty_level
                }
            ],
            "bigdata": [
                {
                    "text": "简述Hadoop的核心组件及其作用。",
                    "type": "TECHNICAL",
                    "duration": 120,
                    "difficulty": difficulty_level
                },
                {
                    "text": "你使用过哪些大数据处理框架？简述其中一个的优势。",
                    "type": "TECHNICAL",
                    "duration": 120,
                    "difficulty": difficulty_level
                }
            ],
            "backend": [
                {
                    "text": "简述RESTful API的主要设计原则。",
                    "type": "TECHNICAL",
                    "duration": 120,
                    "difficulty": difficulty_level
                },
                {
                    "text": "你如何处理高并发场景下的性能问题？",
                    "type": "TECHNICAL",
                    "duration": 120,
                    "difficulty": difficulty_level
                }
            ],
            "frontend": [
                {
                    "text": "简述React和Vue的主要区别。",
                    "type": "TECHNICAL",
                    "duration": 120,
                    "difficulty": difficulty_level
                },
                {
                    "text": "如何优化前端页面的加载性能？",
                    "type": "TECHNICAL",
                    "duration": 120,
                    "difficulty": difficulty_level
                }
            ],
            "product": [
                {
                    "text": "描述你如何确定产品需求的优先级。",
                    "type": "TECHNICAL",
                    "duration": 120,
                    "difficulty": difficulty_level
                },
                {
                    "text": "你如何平衡用户体验和技术实现的限制？",
                    "type": "TECHNICAL",
                    "duration": 120,
                    "difficulty": difficulty_level
                }
            ]
        }
        
        # 尝试获取特定领域问题，如果没有则使用通用技术问题
        specific_questions = field_specific_questions.get(
            tech_field, 
            [
                {
                    "text": "简述你最熟悉的编程语言的优缺点。",
                    "type": "TECHNICAL",
                    "duration": 120,
                    "difficulty": difficulty_level
                },
                {
                    "text": "你如何保证代码质量？有哪些实践经验？",
                    "type": "TECHNICAL",
                    "duration": 120,
                    "difficulty": difficulty_level
                }
            ]
        )
        
        # 合并问题并限制数量
        all_questions = general_questions + specific_questions
        return all_questions[:question_count]
    
    def _get_fallback_full_questions(
        self, 
        job_position: Dict[str, Any],
        question_count: int,
        difficulty_level: str
    ) -> List[Dict[str, Any]]:
        """获取备用完整面试问题
        
        在API调用失败时使用的预定义问题
        
        Args:
            job_position: 职位信息
            question_count: 问题数量
            difficulty_level: 难度级别
            
        Returns:
            问题列表
        """
        tech_field = job_position.get("tech_field", "").lower()
        position_type = job_position.get("position_type", "").lower()
        
        # 通用问题
        general_questions = [
            {
                "text": "请先做一个简单的自我介绍，包括您的教育背景、技能特长和职业目标。",
                "type": "SELF_INTRO",
                "duration": 120,
                "difficulty": "easy"
            },
            {
                "text": "描述一个你曾经面临的技术挑战，以及你是如何解决的？",
                "type": "BEHAVIORAL",
                "duration": 300,
                "difficulty": difficulty_level
            },
            {
                "text": "你如何保持对技术趋势的了解？请分享你的学习方法。",
                "type": "BEHAVIORAL",
                "duration": 240,
                "difficulty": difficulty_level
            }
        ]
        
        # 根据技术领域添加特定问题
        field_specific_questions = {
            "ai": [
                {
                    "text": "请解释深度学习中的反向传播算法原理，并说明梯度消失问题及其解决方案。",
                    "type": "TECHNICAL",
                    "duration": 300,
                    "difficulty": difficulty_level
                },
                {
                    "text": "假设你需要设计一个图像识别系统，请描述你的技术选型和架构设计思路。",
                    "type": "SYSTEM_DESIGN",
                    "duration": 400,
                    "difficulty": difficulty_level
                },
                {
                    "text": "请用Python实现一个简单的线性回归模型，并解释关键代码。",
                    "type": "CODING",
                    "duration": 600,
                    "difficulty": difficulty_level
                }
            ],
            "bigdata": [
                {
                    "text": "请解释Hadoop生态系统的核心组件及其作用。",
                    "type": "TECHNICAL",
                    "duration": 300,
                    "difficulty": difficulty_level
                },
                {
                    "text": "如何设计一个处理TB级数据的实时分析系统？",
                    "type": "SYSTEM_DESIGN",
                    "duration": 400,
                    "difficulty": difficulty_level
                },
                {
                    "text": "在处理大数据时，你是如何优化查询性能的？请给出具体案例。",
                    "type": "BEHAVIORAL",
                    "duration": 300,
                    "difficulty": difficulty_level
                }
            ],
            "backend": [
                {
                    "text": "详细讲解数据库索引的工作原理，以及如何优化索引设计。",
                    "type": "TECHNICAL",
                    "duration": 300,
                    "difficulty": difficulty_level
                },
                {
                    "text": "设计一个高并发的短链接服务，需要支持每秒万级的请求量。",
                    "type": "SYSTEM_DESIGN",
                    "duration": 600,
                    "difficulty": difficulty_level
                },
                {
                    "text": "请实现一个LRU缓存的数据结构，并分析时间复杂度。",
                    "type": "CODING",
                    "duration": 600,
                    "difficulty": difficulty_level
                }
            ],
            "frontend": [
                {
                    "text": "深入解释JavaScript的事件循环机制和异步编程模型。",
                    "type": "TECHNICAL",
                    "duration": 300,
                    "difficulty": difficulty_level
                },
                {
                    "text": "设计一个大型前端应用的状态管理方案，讨论不同方案的优缺点。",
                    "type": "SYSTEM_DESIGN",
                    "duration": 450,
                    "difficulty": difficulty_level
                },
                {
                    "text": "请实现一个自定义React Hook，用于处理分页加载数据。",
                    "type": "CODING",
                    "duration": 500,
                    "difficulty": difficulty_level
                }
            ],
            "product": [
                {
                    "text": "详细讲解如何从用户需求到产品设计的全流程。",
                    "type": "TECHNICAL",
                    "duration": 300,
                    "difficulty": difficulty_level
                },
                {
                    "text": "如果你的产品在上线后用户反馈不佳，你会采取什么措施？",
                    "type": "BEHAVIORAL",
                    "duration": 300,
                    "difficulty": difficulty_level
                },
                {
                    "text": "请设计一个新的社交媒体功能，并说明如何评估其成功与否。",
                    "type": "SYSTEM_DESIGN",
                    "duration": 450,
                    "difficulty": difficulty_level
                }
            ]
        }
        
        # 尝试获取特定领域问题，如果没有则使用通用技术问题
        specific_questions = field_specific_questions.get(
            tech_field, 
            [
                {
                    "text": "详细分析你最熟悉的编程语言的内存管理机制。",
                    "type": "TECHNICAL",
                    "duration": 300,
                    "difficulty": difficulty_level
                },
                {
                    "text": "设计一个分布式系统，确保数据一致性和高可用性。",
                    "type": "SYSTEM_DESIGN",
                    "duration": 600,
                    "difficulty": difficulty_level
                },
                {
                    "text": "实现一个二叉树的序列化和反序列化算法。",
                    "type": "CODING",
                    "duration": 500,
                    "difficulty": difficulty_level
                }
            ]
        )
        
        # 合并问题并限制数量
        all_questions = general_questions + specific_questions
        return all_questions[:question_count]


def create_question_generator(
    openai_service: Optional[OpenAIService] = None,
    config: Optional[QuestionGeneratorConfig] = None
) -> QuestionGenerator:
    """创建问题生成器实例的工厂函数
    
    Args:
        openai_service: OpenAI服务实例
        config: 配置对象
        
    Returns:
        QuestionGenerator实例
    """
    return QuestionGenerator(openai_service, config) 