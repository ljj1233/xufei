"""
检索增强生成引擎

基于向量检索和大语言模型的学习资源检索增强生成引擎
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
import requests

from app.services.learning_recommendation.logging_config import setup_logger, log_function
from app.services.learning_recommendation.vector_utils import compute_embedding, compute_similarity
from app.services.learning_recommendation.resource_management import ResourceManagementService

# 设置日志
logger = setup_logger("app.services.learning_recommendation.rag_engine")

class RAGEngine:
    """检索增强生成引擎，用于个性化推荐系统的检索增强生成"""
    
    def __init__(self, 
                resource_service: ResourceManagementService,
                api_key: Optional[str] = None,
                llm_model: str = "Qwen/Qwen2.5-7B-Instruct",
                embedding_model: str = "text-embedding-ada-002"):
        """
        初始化RAG检索引擎
        
        Args:
            resource_service: 资源管理服务
            api_key: OpenAI API密钥，如不提供，将尝试从环境变量OPENAI_API_KEY获取
            llm_model: 大语言模型名称
            embedding_model: 向量嵌入模型名称
        """
        self.resource_service = resource_service
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        
        logger.info("RAG检索引擎初始化完成", extra={'request_id': 'system', 'user_id': 'system'})
    
    @log_function(logger)
    def search(self, 
               query: Dict[str, Any], 
               job_position: Dict[str, Any],
               assessment_results: Dict[str, Any],
               top_k: int = 10) -> List[Dict[str, Any]]:
        """
        根据查询、职位和评估结果搜索学习资源
        
        Args:
            query: 查询参数
            job_position: 职位信息
            assessment_results: 评估结果
            top_k: 返回结果数量
            
        Returns:
            检索到的学习资源列表
        """
        start_time = time.time()
        request_id = query.get("request_id", "unknown")
        logger.info(f"开始执行检索，请求ID: {request_id}, 职位: {job_position.get('title', 'unknown')}", 
                  extra={'request_id': request_id, 'user_id': query.get('user_id', 'anonymous')})
        
        try:
            # 1. 构建查询向量
            query_text = self._build_query_text(query, job_position, assessment_results)
            logger.info(f"构建的查询文本: {query_text}", 
                      extra={'request_id': request_id, 'user_id': query.get('user_id', 'anonymous')})
            
            # 2. 执行语义搜索
            raw_results = self._semantic_search(query_text, top_k * 2)  # 获取更多结果供后处理
            
            # 3. 过滤结果
            filtered_results = self._filter_results(raw_results, query, job_position)
            
            # 4. 结果排序和优化
            ranked_results = self._rank_results(filtered_results, job_position, assessment_results)
            
            # 5. 多样性优化
            diverse_results = self._diversify_results(ranked_results)[:top_k]
            
            # 6. 增强结果
            enhanced_results = self._enhance_results(diverse_results, job_position, assessment_results)
            
            duration = time.time() - start_time
            logger.info(f"检索完成，请求ID: {request_id}, 耗时: {duration:.2f}秒, 找到 {len(enhanced_results)} 条结果", 
                      extra={'request_id': request_id, 'user_id': query.get('user_id', 'anonymous')})
            return enhanced_results
            
        except Exception as e:
            logger.error(f"检索失败，请求ID: {request_id}, 错误: {str(e)}", exc_info=True,
                        extra={'request_id': request_id, 'user_id': query.get('user_id', 'anonymous')})
            return []
    
    @log_function(logger)
    def _build_query_text(self, query: Dict[str, Any], job_position: Dict[str, Any], 
                        assessment_results: Dict[str, Any]) -> str:
        """构建查询文本"""
        # 获取职位信息
        job_title = job_position.get("title", "")
        job_id = job_position.get("id", "")
        
        # 从评估结果中提取需要提升的能力
        weak_areas = []
        if "improvement_areas" in assessment_results:
            # 已经预处理好的改进领域
            for area in assessment_results["improvement_areas"]:
                score = area.get("current_score", 0)
                if score < 70:  # 低于70分的技能被视为弱项
                    weak_areas.append(f"{area.get('name', '')} ({score}分)")
        else:
            # 直接从评估结果中提取
            for category, results in assessment_results.items():
                if isinstance(results, dict):
                    for skill, data in results.items():
                        if isinstance(data, dict):
                            score = data.get("score", 0)
                            if score < 70:
                                skill_name = data.get("name", skill)
                                weak_areas.append(f"{skill_name} ({score}分)")
        
        # 处理查询参数
        original_query = query.get("text", "")
        term_type = query.get("term_type", "")  # short/mid/long
        resource_types = query.get("resource_types", [])
        
        # 构建强化的查询文本
        components = []
        
        # 添加职位信息
        if job_title:
            components.append(f"职位: {job_title}")
        
        # 添加弱项信息
        if weak_areas:
            weak_areas_text = ", ".join(weak_areas)
            components.append(f"需要提升的能力: {weak_areas_text}")
        
        # 添加原始查询
        if original_query:
            components.append(f"查询: {original_query}")
            
        # 添加学习期限偏好
        if term_type == "short":
            components.append("短期学习资源（可以快速学习的内容）")
        elif term_type == "mid":
            components.append("中期学习资源（需要一定时间投入的系统性内容）")
        elif term_type == "long":
            components.append("长期学习资源（深入系统的学习内容）")
            
        # 添加资源类型偏好
        if resource_types:
            types_text = ", ".join(resource_types)
            components.append(f"资源类型: {types_text}")
        
        # 组合查询文本
        query_text = ". ".join(components)
        
        return query_text
    
    @log_function(logger)
    def _semantic_search(self, query_text: str, top_k: int) -> List[Dict[str, Any]]:
        """执行语义搜索"""
        try:
            # 使用资源管理服务进行搜索
            search_results = self.resource_service.search_resources(
                query=query_text,
                top_k=top_k
            )
            
            logger.info(f"语义搜索返回 {len(search_results)} 条结果", 
                      extra={'request_id': 'auto', 'user_id': 'system'})
                      
            return search_results
        except Exception as e:
            logger.error(f"执行语义搜索失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'auto', 'user_id': 'system'})
            return []
    
    @log_function(logger)
    def _filter_results(self, results: List[Dict[str, Any]], 
                      query: Dict[str, Any], 
                      job_position: Dict[str, Any]) -> List[Dict[str, Any]]:
        """过滤搜索结果"""
        filtered_results = []
        
        # 获取过滤条件
        resource_types = query.get("resource_types", [])
        difficulty = query.get("difficulty")
        job_id = job_position.get("id")
        
        for result in results:
            # 检查资源类型
            if resource_types and result.get("resource_type") not in resource_types:
                continue
                
            # 检查难度级别
            if difficulty and result.get("difficulty") != difficulty:
                continue
                
            # 检查职位相关性
            if job_id and job_id not in result.get("job_relevance", []) and len(result.get("job_relevance", [])) > 0:
                # 如果资源指定了职位相关性，但不包含当前职位，则过滤掉
                # 如果资源没有指定职位相关性，则保留
                continue
                
            # 通过所有过滤条件
            filtered_results.append(result)
        
        logger.info(f"过滤后剩余 {len(filtered_results)} 条结果", 
                   extra={'request_id': 'auto', 'user_id': 'system'})
                   
        return filtered_results
    
    @log_function(logger)
    def _rank_results(self, results: List[Dict[str, Any]], 
                    job_position: Dict[str, Any],
                    assessment_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """对结果进行排序"""
        # 提取职位所需技能
        job_skills = {}
        job_id = job_position.get("id", "")
        
        if "required_skills" in job_position:
            job_skills = job_position.get("required_skills", {})
        
        # 提取弱项技能
        weak_skills = {}
        if "improvement_areas" in assessment_results:
            for area in assessment_results["improvement_areas"]:
                skill = area.get("skill", "")
                if skill:
                    score = area.get("current_score", 0)
                    priority = area.get("priority_score", 0)
                    weak_skills[skill] = {
                        "score": score,
                        "priority": priority
                    }
        
        # 为每个结果计算相关性分数
        scored_results = []
        for result in results:
            # 初始分数为搜索相似度或默认值
            base_score = result.get("similarity", 0.5)
            
            # 资源技能与职位所需技能的匹配度
            skill_match_score = 0
            resource_skills = result.get("skills", [])
            
            for skill in resource_skills:
                if skill in job_skills:
                    # 该技能是职位所需技能
                    importance = job_skills.get(skill, 0.5)
                    skill_match_score += importance * 0.2
                    
                if skill in weak_skills:
                    # 该技能是用户的弱项
                    priority = weak_skills[skill].get("priority", 0.5)
                    skill_match_score += priority * 0.3
            
            # 资源质量分数
            quality_score = min(1.0, (result.get("rating", 0) / 5.0) * 0.5 + 0.5)  # 使评分影响不要太大
            
            # 计算最终分数
            final_score = base_score * 0.4 + skill_match_score * 0.4 + quality_score * 0.2
            
            # 记录原始分数，用于调试
            result["ranking_debug"] = {
                "base_score": base_score,
                "skill_match_score": skill_match_score,
                "quality_score": quality_score,
                "final_score": final_score
            }
            
            # 添加最终分数
            result["ranking_score"] = final_score
            scored_results.append(result)
        
        # 根据最终分数排序
        scored_results.sort(key=lambda x: x["ranking_score"], reverse=True)
        
        logger.info(f"结果排序完成", extra={'request_id': 'auto', 'user_id': 'system'})
        
        return scored_results
    
    @log_function(logger)
    def _diversify_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """确保结果多样性"""
        if len(results) <= 3:
            return results
            
        diversified = []
        resource_types_count = {}
        skill_count = {}
        
        for result in results:
            resource_type = result.get("resource_type")
            skills = result.get("skills", [])
            
            # 检查是否已经有太多同类型资源
            if resource_types_count.get(resource_type, 0) >= 3:  # 每种类型最多3个
                continue
                
            # 检查是否已经有太多针对同一技能的资源
            skill_overlap = False
            for skill in skills:
                if skill_count.get(skill, 0) >= 2:  # 每个技能最多2个资源
                    skill_overlap = True
                    break
                    
            if skill_overlap:
                continue
                
            # 添加到多样化结果
            diversified.append(result)
            
            # 更新计数
            resource_types_count[resource_type] = resource_types_count.get(resource_type, 0) + 1
            for skill in skills:
                skill_count[skill] = skill_count.get(skill, 0) + 1
                
        # 如果多样化后结果太少，添加一些原始结果
        if len(diversified) < 3 and len(results) > len(diversified):
            for result in results:
                if result not in diversified:
                    diversified.append(result)
                    if len(diversified) >= len(results) / 2:  # 至少保留一半的结果
                        break
        
        logger.info(f"多样化后的结果数量: {len(diversified)}", 
                   extra={'request_id': 'auto', 'user_id': 'system'})
                   
        return diversified
    
    @log_function(logger)
    def _enhance_results(self, results: List[Dict[str, Any]],
                       job_position: Dict[str, Any],
                       assessment_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """使用大语言模型增强结果"""
        if not results or not self.api_key:
            return results
            
        enhanced_results = []
        
        for result in results:
            try:
                # 生成推荐理由和预期收益
                enhancement = self._generate_enhancement(result, job_position, assessment_results)
                
                # 添加增强信息
                result_copy = result.copy()
                result_copy["enhancement"] = enhancement
                
                # 移除调试信息
                if "ranking_debug" in result_copy:
                    del result_copy["ranking_debug"]
                
                enhanced_results.append(result_copy)
            except Exception as e:
                logger.error(f"增强结果失败: {str(e)}", exc_info=True,
                           extra={'request_id': 'auto', 'user_id': 'system'})
                # 如果增强失败，保留原始结果
                enhanced_results.append(result)
        
        logger.info(f"已增强 {len(enhanced_results)} 条结果", 
                   extra={'request_id': 'auto', 'user_id': 'system'})
                   
        return enhanced_results
    
    @log_function(logger)
    def _generate_enhancement(self, result: Dict[str, Any],
                            job_position: Dict[str, Any],
                            assessment_results: Dict[str, Any]) -> Dict[str, str]:
        """生成个性化推荐理由和预期收益"""
        # 准备相关信息
        job_title = job_position.get("title", "专业人士")
        result_title = result.get("title", "")
        result_description = result.get("description", "")
        result_type = result.get("resource_type", "")
        result_skills = result.get("skills", [])
        
        # 提取弱项
        weak_areas = []
        if "improvement_areas" in assessment_results:
            for area in assessment_results["improvement_areas"][:3]:  # 只使用前3个弱项
                weak_areas.append({
                    "name": area.get("name", ""),
                    "score": area.get("current_score", 0),
                    "feedback": area.get("feedback", "")
                })
        
        # 构建提示
        prompt = f"""
        作为学习推荐系统，你需要为一位{job_title}提供个性化的学习资源推荐理由。
        
        资源信息:
        - 标题: {result_title}
        - 描述: {result_description}
        - 类型: {result_type}
        - 相关技能: {', '.join(result_skills)}
        
        用户需要提升的能力:
        {json.dumps(weak_areas, ensure_ascii=False)}
        
        请提供:
        1. 一段个性化的推荐理由，解释为什么这个资源适合这位用户(50-100字)
        2. 完成学习后预期的收获和提升(30-50字)
        3. 大致的完成时间估计(10-20字)
        
        以JSON格式返回:
        {{
            "reason": "个性化推荐理由",
            "outcome": "预期收获",
            "time_estimate": "时间估计"
        }}
        """
        
        try:
            # 调用OpenAI API
            response = self._call_openai_chat_api(prompt)
            
            # 解析JSON响应
            enhancement = json.loads(response)
            
            # 验证返回的字段
            if "reason" not in enhancement or "outcome" not in enhancement:
                raise ValueError("API响应格式不正确")
                
            return enhancement
        except Exception as e:
            logger.error(f"生成增强信息失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'auto', 'user_id': 'system'})
            
            # 返回默认增强信息
            return {
                "reason": f"此{result_type}资源涵盖了与您职位相关的知识，可以帮助您提升技能。",
                "outcome": "提高相关知识和实践能力",
                "time_estimate": "视学习进度而定"
            }
    
    def _call_openai_chat_api(self, prompt: str) -> str:
        """调用OpenAI Chat API"""
        if not self.api_key:
            raise ValueError("未提供OpenAI API密钥")
            
        # 从环境变量获取API基础URL，如果不存在则使用默认值
        api_base = os.environ.get("OPENAI_API_BASE", "https://api-inference.modelscope.cn/v1/")
        
        # 准备API请求
        url = f"{api_base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": self.llm_model,
            "messages": [
                {"role": "system", "content": "你是一个学习资源推荐助手，根据用户信息提供个性化的学习资源推荐理由。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
        
        # 发送请求
        response = requests.post(url, headers=headers, json=data)
        
        # 检查响应状态
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code} - {response.text}")
            
        # 解析响应
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        return content 