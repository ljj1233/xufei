"""
个性化学习推荐服务

根据面试评测结果和职位要求生成个性化学习推荐
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid

from app.services.learning_recommendation.logging_config import setup_logger, log_function
from app.services.learning_recommendation.job_skill_mapping import JobSkillMappingService
from app.services.learning_recommendation.assessment_analysis import AssessmentAnalysisService
from app.services.learning_recommendation.resource_management import ResourceManagementService
from app.services.learning_recommendation.rag_engine import RAGEngine
from app.services.learning_recommendation.models import LearningGoal, LearningPath

# 设置日志
logger = setup_logger("app.services.learning_recommendation.recommendation")

class RecommendationService:
    """个性化学习推荐服务，负责生成学习路径和推荐"""
    
    def __init__(self,
                job_skill_service: Optional[JobSkillMappingService] = None,
                assessment_service: Optional[AssessmentAnalysisService] = None,
                resource_service: Optional[ResourceManagementService] = None,
                rag_engine: Optional[RAGEngine] = None,
                api_key: Optional[str] = None):
        """
        初始化推荐服务
        
        Args:
            job_skill_service: 职位-技能映射服务
            assessment_service: 评测分析服务
            resource_service: 资源管理服务
            rag_engine: RAG检索引擎
            api_key: OpenAI API密钥
        """
        # 初始化或创建依赖的服务
        self.job_skill_service = job_skill_service or JobSkillMappingService()
        
        if assessment_service:
            self.assessment_service = assessment_service
        else:
            self.assessment_service = AssessmentAnalysisService(self.job_skill_service)
            
        self.resource_service = resource_service or ResourceManagementService()
        
        if rag_engine:
            self.rag_engine = rag_engine
        else:
            self.rag_engine = RAGEngine(
                resource_service=self.resource_service,
                api_key=api_key
            )
            
        logger.info("个性化学习推荐服务初始化完成", extra={'request_id': 'system', 'user_id': 'system'})
    
    @log_function(logger)
    def generate_learning_path(self, 
                             user_id: str,
                             job_position_id: str,
                             assessment_results: Dict[str, Any],
                             user_preferences: Optional[Dict[str, Any]] = None) -> LearningPath:
        """
        生成个性化学习路径
        
        Args:
            user_id: 用户ID
            job_position_id: 职位ID
            assessment_results: 面试评测结果
            user_preferences: 用户偏好
            
        Returns:
            学习路径
        """
        request_id = str(uuid.uuid4())
        logger.info(f"开始生成学习路径，用户ID: {user_id}, 职位ID: {job_position_id}", 
                   extra={'request_id': request_id, 'user_id': user_id})
        
        try:
            # 获取职位信息
            job_info = self.job_skill_service.get_skills_for_job(job_position_id)
            job_position = {
                "id": job_position_id,
                "title": job_info.get("title", ""),
                "description": job_info.get("description", ""),
                "required_skills": {skill_id: data.get("weight", 0.5) for skill_id, data in job_info.get("skills", {}).items()}
            }
            
            # 分析评测结果，识别需要提升的能力
            improvement_areas = self.assessment_service.identify_improvement_areas(
                assessment_results, job_position
            )
            
            # 获取评测总结
            assessment_summary = self.assessment_service.get_assessment_summary(assessment_results)
            
            # 为每个改进领域推荐学习资源
            learning_goals = self._generate_learning_goals(
                improvement_areas, job_position, user_preferences, request_id, user_id
            )
            
            # 将学习目标按期限分组
            grouped_goals = self._group_learning_goals_by_term(learning_goals)
            
            # 创建学习路径
            path_id = f"path_{str(uuid.uuid4())[:8]}"
            learning_path = LearningPath(
                id=path_id,
                user_id=user_id,
                job_position=job_position,
                created_at=datetime.now(),
                goals=grouped_goals,
                summary=self._generate_path_summary(grouped_goals, assessment_summary)
            )
            
            logger.info(f"学习路径生成完成，路径ID: {path_id}", 
                       extra={'request_id': request_id, 'user_id': user_id})
            
            return learning_path
            
        except Exception as e:
            logger.error(f"生成学习路径失败: {str(e)}", exc_info=True,
                        extra={'request_id': request_id, 'user_id': user_id})
            raise
    
    @log_function(logger)
    def _generate_learning_goals(self, 
                               improvement_areas: List[Dict[str, Any]],
                               job_position: Dict[str, Any],
                               user_preferences: Optional[Dict[str, Any]],
                               request_id: str,
                               user_id: str) -> List[LearningGoal]:
        """生成学习目标"""
        learning_goals = []
        
        # 为每个改进领域生成学习目标
        for area in improvement_areas:
            # 分配学习期限：优先级高的是短期，中等的是中期，低的是长期
            priority = area.get("priority_score", 0)
            if priority >= 0.8:
                term_type = "short"
            elif priority >= 0.5:
                term_type = "mid"
            else:
                term_type = "long"
                
            # 获取推荐资源
            resources = self._get_recommended_resources(
                area, job_position, user_preferences, term_type, request_id, user_id
            )
            
            # 创建学习目标
            goal = LearningGoal(
                skill=area.get("skill", ""),
                name=area.get("name", ""),
                priority_score=priority,
                term_type=term_type,
                resources=resources
            )
            
            learning_goals.append(goal)
            
        # 按优先级排序
        learning_goals.sort(key=lambda x: x.priority_score, reverse=True)
        
        logger.info(f"生成了 {len(learning_goals)} 个学习目标", 
                   extra={'request_id': request_id, 'user_id': user_id})
        
        return learning_goals
    
    @log_function(logger)
    def _get_recommended_resources(self, 
                                 area: Dict[str, Any],
                                 job_position: Dict[str, Any],
                                 user_preferences: Optional[Dict[str, Any]],
                                 term_type: str,
                                 request_id: str,
                                 user_id: str) -> List[Dict[str, Any]]:
        """获取推荐资源"""
        # 准备查询
        skill_name = area.get("name", "")
        skill_id = area.get("skill", "")
        
        query = {
            "text": f"学习 {skill_name} 的资源",
            "term_type": term_type,
            "request_id": request_id,
            "user_id": user_id
        }
        
        # 添加资源类型过滤
        if user_preferences and "preferred_resource_types" in user_preferences:
            query["resource_types"] = user_preferences.get("preferred_resource_types", [])
            
        # 添加难度过滤
        if user_preferences and "preferred_difficulty" in user_preferences:
            query["difficulty"] = user_preferences.get("preferred_difficulty")
            
        # 构建评估结果数据
        assessment_data = {
            "improvement_areas": [area]
        }
        
        # 使用RAG引擎检索资源
        results = self.rag_engine.search(
            query=query,
            job_position=job_position,
            assessment_results=assessment_data,
            top_k=5  # 每个技能最多5个资源
        )
        
        # 如果没有找到资源，记录警告
        if not results:
            logger.warning(f"为技能 {skill_name} ({skill_id}) 未找到推荐资源", 
                          extra={'request_id': request_id, 'user_id': user_id})
        
        return results
    
    @log_function(logger)
    def _group_learning_goals_by_term(self, goals: List[LearningGoal]) -> Dict[str, List[LearningGoal]]:
        """将学习目标按期限分组"""
        grouped = {
            "short": [],  # 短期目标
            "mid": [],    # 中期目标
            "long": []    # 长期目标
        }
        
        for goal in goals:
            term = goal.term_type or "mid"  # 默认为中期
            if term in grouped:
                grouped[term].append(goal)
                
        return grouped
    
    def _generate_path_summary(self, 
                              grouped_goals: Dict[str, List[LearningGoal]], 
                              assessment_summary: Dict[str, Any]) -> str:
        """生成学习路径总结"""
        # 获取评测总结
        overall_evaluation = assessment_summary.get("overall_evaluation", "")
        total_score = assessment_summary.get("total_score", 0)
        
        # 计算各期限的目标数量
        short_count = len(grouped_goals.get("short", []))
        mid_count = len(grouped_goals.get("mid", []))
        long_count = len(grouped_goals.get("long", []))
        
        # 生成学习路径描述
        if total_score >= 80:
            prefix = "您的面试表现良好，为进一步提升，"
        elif total_score >= 60:
            prefix = "您的面试表现中等，为了提高竞争力，"
        else:
            prefix = "您的面试表现需要改进，为了达到职位要求，"
            
        summary = f"{prefix}我们为您制定了个性化学习路径。"
        
        # 添加目标数量描述
        if short_count > 0:
            summary += f" 包含{short_count}个短期学习目标"
            if mid_count > 0 or long_count > 0:
                summary += "，"
        if mid_count > 0:
            summary += f"{mid_count}个中期学习目标"
            if long_count > 0:
                summary += "，"
        if long_count > 0:
            summary += f"{long_count}个长期学习目标"
        summary += "。"
        
        # 添加评估摘要
        if overall_evaluation:
            summary += f" {overall_evaluation}"
        
        return summary
    
    @log_function(logger)
    def get_resource_recommendations(self, 
                                  user_id: str,
                                  query: str,
                                  job_position_id: str,
                                  filters: Optional[Dict[str, Any]] = None,
                                  limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取资源推荐
        
        Args:
            user_id: 用户ID
            query: 查询文本
            job_position_id: 职位ID
            filters: 过滤条件
            limit: 结果数量限制
            
        Returns:
            推荐资源列表
        """
        request_id = str(uuid.uuid4())
        logger.info(f"开始获取资源推荐，用户ID: {user_id}, 查询: {query}", 
                   extra={'request_id': request_id, 'user_id': user_id})
        
        try:
            # 获取职位信息
            job_info = self.job_skill_service.get_skills_for_job(job_position_id)
            job_position = {
                "id": job_position_id,
                "title": job_info.get("title", ""),
                "description": job_info.get("description", ""),
                "required_skills": {skill_id: data.get("weight", 0.5) for skill_id, data in job_info.get("skills", {}).items()}
            }
            
            # 准备查询
            search_query = {
                "text": query,
                "request_id": request_id,
                "user_id": user_id
            }
            
            # 应用过滤器
            if filters:
                search_query.update(filters)
                
            # 使用简化的评估结果
            simple_assessment = {"improvement_areas": []}
            
            # 使用RAG引擎检索资源
            results = self.rag_engine.search(
                query=search_query,
                job_position=job_position,
                assessment_results=simple_assessment,
                top_k=limit
            )
            
            logger.info(f"资源推荐完成，找到 {len(results)} 条结果", 
                       extra={'request_id': request_id, 'user_id': user_id})
            
            return results
        except Exception as e:
            logger.error(f"获取资源推荐失败: {str(e)}", exc_info=True,
                        extra={'request_id': request_id, 'user_id': user_id})
            return [] 