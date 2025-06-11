"""
面试问题生成服务

该服务负责根据职位信息动态生成面试问题，包括问题内容、考察技能、建议回答时间和参考答案。
"""

import json
import logging
import random
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.job import JobPosition, JobSkill
from backend.app.models.interview import InterviewQuestion
from backend.app.services.llm_service import LLMService

# 配置日志
logger = logging.getLogger(__name__)

class QuestionGenerationService:
    """
    面试问题生成服务
    
    通过调用大模型API，基于职位和技能信息生成高质量的面试问题。
    问题包含问题内容、考察的技能点、建议回答时间和参考答案。
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None, db: Optional[Session] = None):
        """
        初始化问题生成服务
        
        Args:
            llm_service: 大模型服务实例，如果为None则创建新实例
            db: 数据库会话，如果为None则使用默认会话
        """
        logger.info("初始化问题生成服务")
        self.llm_service = llm_service or LLMService()
        self._db = db
    
    @property
    def db(self) -> Session:
        """获取数据库会话"""
        if self._db is None:
            self._db = next(get_db())
        return self._db
    
    async def generate_questions_for_position(self, position_id: int, count: int = 6) -> List[Dict[str, Any]]:
        """
        为指定职位生成面试问题
        
        Args:
            position_id: 职位ID
            count: 需要生成的问题数量，默认为6道
            
        Returns:
            问题列表，每个问题包含问题内容、技能标签、建议回答时长和参考答案
        """
        logger.info(f"开始为职位ID={position_id}生成{count}道面试问题")
        
        # 1. 查询职位信息和关联技能
        position_info = self._get_position_info(position_id)
        if not position_info:
            logger.error(f"无法找到职位ID={position_id}的信息")
            return []
        
        # 2. 检查缓存的问题
        cached_questions = self._get_cached_questions(position_id, count)
        if len(cached_questions) >= count:
            logger.info(f"从缓存中获取到{len(cached_questions)}道问题，无需生成新问题")
            return cached_questions[:count]
        
        # 3. 计算需要生成的新问题数量
        new_questions_count = count - len(cached_questions)
        logger.info(f"缓存中有{len(cached_questions)}道问题，需要生成{new_questions_count}道新问题")
        
        # 4. 生成新问题
        new_questions = await self._generate_new_questions(position_info, new_questions_count)
        
        # 5. 缓存新生成的问题
        if new_questions:
            self._cache_questions(position_id, new_questions)
        
        # 6. 合并缓存问题和新问题
        all_questions = cached_questions + new_questions
        logger.info(f"成功为职位ID={position_id}生成{len(all_questions)}道面试问题")
        
        return all_questions
    
    def _get_position_info(self, position_id: int) -> Dict[str, Any]:
        """
        获取职位信息和相关技能
        
        Args:
            position_id: 职位ID
            
        Returns:
            包含职位名称、技术领域和技能列表的字典
        """
        try:
            # 查询职位信息
            position = self.db.query(JobPosition).filter(JobPosition.id == position_id).first()
            if not position:
                logger.error(f"未找到职位ID={position_id}的记录")
                return {}
            
            # 查询相关技能
            skills = self.db.query(JobSkill).filter(JobSkill.position_id == position_id).all()
            skill_names = [skill.name for skill in skills]
            
            position_info = {
                "position_id": position.id,
                "position_name": position.name,
                "tech_field": position.tech_field,
                "skills": skill_names
            }
            
            logger.info(f"获取到职位信息: {position.name}, 技术领域: {position.tech_field}, "
                       f"技能数量: {len(skill_names)}")
            return position_info
            
        except Exception as e:
            logger.error(f"获取职位信息时出错: {str(e)}", exc_info=True)
            return {}
    
    def _get_cached_questions(self, position_id: int, count: int) -> List[Dict[str, Any]]:
        """
        从数据库获取已缓存的问题
        
        Args:
            position_id: 职位ID
            count: 需要的问题数量
            
        Returns:
            缓存的问题列表
        """
        try:
            # 查询与职位关联的问题
            questions = (self.db.query(InterviewQuestion)
                        .filter(InterviewQuestion.position_id == position_id)
                        .limit(count * 2)  # 多查一些以增加多样性
                        .all())
            
            if not questions:
                logger.info(f"数据库中没有职位ID={position_id}的缓存问题")
                return []
            
            # 随机选择问题以增加多样性
            if len(questions) > count:
                questions = random.sample(questions, count)
            
            # 转换为字典格式
            result = []
            for q in questions:
                question_dict = {
                    "id": q.id,
                    "question": q.content,
                    "skill_tags": q.skill_tags.split(",") if q.skill_tags else [],
                    "suggested_duration_seconds": q.suggested_duration_seconds or 120,
                    "reference_answer": q.reference_answer
                }
                result.append(question_dict)
            
            logger.info(f"从缓存中获取到{len(result)}道问题")
            return result
            
        except Exception as e:
            logger.error(f"获取缓存问题时出错: {str(e)}", exc_info=True)
            return []
    
    async def _generate_new_questions(self, position_info: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """
        调用大模型生成新问题
        
        Args:
            position_info: 职位信息字典
            count: 需要生成的问题数量
            
        Returns:
            新生成的问题列表
        """
        if not position_info:
            logger.error("职位信息为空，无法生成问题")
            return []
        
        try:
            # 构建提示词
            prompt = self._build_question_prompt(position_info, count)
            
            logger.info(f"开始调用大模型生成{count}道面试问题")
            # 调用大模型
            response = await self.llm_service.generate_completion(
                prompt=prompt,
                temperature=0.7,  # 适当的随机性
                max_tokens=3000,  # 确保足够长度
                response_format={"type": "json_object"}  # 确保返回JSON格式
            )
            
            # 解析响应
            questions = self._parse_llm_response(response, position_info["position_id"])
            
            if not questions:
                logger.error("大模型生成问题失败或解析响应失败")
                return []
            
            logger.info(f"成功生成{len(questions)}道新问题")
            return questions
            
        except Exception as e:
            logger.error(f"生成面试问题时出错: {str(e)}", exc_info=True)
            return []
    
    def _build_question_prompt(self, position_info: Dict[str, Any], count: int) -> str:
        """
        构建问题生成提示词
        
        Args:
            position_info: 职位信息
            count: 问题数量
            
        Returns:
            构建好的提示词
        """
        position_name = position_info.get("position_name", "软件工程师")
        skills = position_info.get("skills", ["编程", "算法", "系统设计"])
        tech_field = position_info.get("tech_field", "软件开发")
        
        prompt = f"""
        你是一位专业的技术面试官，精通{tech_field}领域，现在需要为{position_name}职位生成{count}道高质量的面试问题。

        职位名称: {position_name}
        技术领域: {tech_field}
        技能要求: {', '.join(skills)}

        请生成{count}道面试问题，每道问题需要包含以下信息：
        1. 问题内容：清晰、具体、难度适中的技术问题
        2. 技能标签：问题考察的主要技能点（从上述技能列表中选择）
        3. 建议回答时间：以秒为单位，通常在60-240秒之间
        4. 参考答案：一个专业、全面但简洁的回答示例

        请以JSON格式返回，格式如下：
        {{
            "questions": [
                {{
                    "question": "问题内容",
                    "skill_tags": ["技能1", "技能2"],
                    "suggested_duration_seconds": 120,
                    "reference_answer": "参考答案"
                }},
                ...共{count}道问题
            ]
        }}
        """
        
        return prompt
    
    def _parse_llm_response(self, response: str, position_id: int) -> List[Dict[str, Any]]:
        """
        解析大模型返回的响应
        
        Args:
            response: 大模型响应文本
            position_id: 职位ID
            
        Returns:
            解析后的问题列表
        """
        try:
            # 尝试解析JSON
            data = json.loads(response)
            
            # 获取问题列表
            questions = data.get("questions", [])
            
            # 验证数据格式并添加position_id
            result = []
            for q in questions:
                if not isinstance(q, dict) or "question" not in q:
                    continue
                
                question_dict = {
                    "question": q.get("question", ""),
                    "skill_tags": q.get("skill_tags", []),
                    "suggested_duration_seconds": q.get("suggested_duration_seconds", 120),
                    "reference_answer": q.get("reference_answer", ""),
                    "position_id": position_id
                }
                result.append(question_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"解析大模型响应时出错: {str(e)}", exc_info=True)
            return []
    
    def _cache_questions(self, position_id: int, questions: List[Dict[str, Any]]) -> None:
        """
        将生成的问题缓存到数据库
        
        Args:
            position_id: 职位ID
            questions: 问题列表
        """
        try:
            # 创建InterviewQuestion对象并添加到数据库
            for q in questions:
                question = InterviewQuestion(
                    content=q["question"],
                    skill_tags=",".join(q["skill_tags"]) if q["skill_tags"] else "",
                    suggested_duration_seconds=q["suggested_duration_seconds"],
                    reference_answer=q["reference_answer"],
                    position_id=position_id
                )
                self.db.add(question)
            
            # 提交事务
            self.db.commit()
            logger.info(f"成功将{len(questions)}道问题缓存到数据库")
            
        except Exception as e:
            # 回滚事务
            self.db.rollback()
            logger.error(f"缓存问题到数据库时出错: {str(e)}", exc_info=True) 