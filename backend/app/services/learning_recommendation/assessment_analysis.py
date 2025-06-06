"""
评测结果分析服务

分析面试评测结果，识别需要改进的能力
"""

import logging
from typing import Dict, List, Any, Optional

from app.services.learning_recommendation.logging_config import setup_logger, log_function
from app.services.learning_recommendation.job_skill_mapping import JobSkillMappingService

# 设置日志
logger = setup_logger("app.services.learning_recommendation.assessment_analysis")

class AssessmentAnalysisService:
    """评测结果分析服务，负责分析面试评测结果并识别需要改进的能力"""
    
    def __init__(self, job_skill_service: JobSkillMappingService):
        """
        初始化评测结果分析服务
        
        Args:
            job_skill_service: 职位-技能映射服务
        """
        self.job_skill_service = job_skill_service
        logger.info("评测结果分析服务初始化完成", extra={'request_id': 'system', 'user_id': 'system'})
    
    @log_function(logger)
    def identify_improvement_areas(self, assessment_results: Dict[str, Any], job_position: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        识别需要改进的能力领域
        
        Args:
            assessment_results: 面试评测结果
            job_position: 职位信息
            
        Returns:
            需要改进的能力列表，按优先级排序
        """
        # 获取该职位所需的技能
        job_id = job_position.get("id", "")
        job_skills = {}
        
        if job_id:
            job_info = self.job_skill_service.get_skills_for_job(job_id)
            job_skills = job_info.get("skills", {})
            
        improvement_areas = []
        
        # 分析评测结果中的各个部分
        self._analyze_content_scores(assessment_results, job_skills, improvement_areas)
        self._analyze_delivery_scores(assessment_results, improvement_areas)
        self._analyze_behavior_scores(assessment_results, improvement_areas)
        
        # 计算每个改进领域的优先级分数
        self._calculate_priority_scores(improvement_areas, job_skills)
        
        # 按优先级排序
        improvement_areas.sort(key=lambda x: x["priority_score"], reverse=True)
        
        logger.info(f"已识别出 {len(improvement_areas)} 个需要改进的能力领域", 
                   extra={'request_id': 'auto', 'user_id': 'system'})
        return improvement_areas
    
    @log_function(logger)
    def _analyze_content_scores(self, assessment_results: Dict[str, Any], job_skills: Dict[str, Any], improvement_areas: List[Dict[str, Any]]) -> None:
        """分析内容得分，找出内容方面的改进领域"""
        content_results = assessment_results.get("content", {})
        
        # 针对不同职位的专业知识分析
        professional_knowledge = content_results.get("professional_knowledge", {})
        for skill, data in professional_knowledge.items():
            score = data.get("score", 0)
            if score < 80:  # 低于80分的技能被认为需要改进
                # 检查此技能是否是该职位的关键技能
                skill_info = job_skills.get(skill, {})
                weight = skill_info.get("weight", 0.5)
                name = skill_info.get("name", skill)
                
                improvement_areas.append({
                    "skill": skill,
                    "name": name,
                    "category": "专业知识",
                    "current_score": score,
                    "weight": weight,
                    "urgency": self._calculate_urgency(score),
                    "feedback": data.get("feedback", "需要提升专业知识水平")
                })
        
        # 分析回答结构性
        structure = content_results.get("structure", {})
        structure_score = structure.get("score", 0)
        if structure_score < 75:
            improvement_areas.append({
                "skill": "answer_structure",
                "name": "回答结构性",
                "category": "表达能力",
                "current_score": structure_score,
                "weight": 0.6,
                "urgency": self._calculate_urgency(structure_score),
                "feedback": structure.get("feedback", "回答结构需要更加清晰")
            })
            
        # 分析回答相关性
        relevance = content_results.get("relevance", {})
        relevance_score = relevance.get("score", 0)
        if relevance_score < 75:
            improvement_areas.append({
                "skill": "answer_relevance",
                "name": "回答相关性",
                "category": "表达能力",
                "current_score": relevance_score,
                "weight": 0.7,
                "urgency": self._calculate_urgency(relevance_score),
                "feedback": relevance.get("feedback", "回答需要更加贴切问题")
            })
            
        # 分析逻辑思维能力
        logic = content_results.get("logic", {})
        logic_score = logic.get("score", 0)
        if logic_score < 75:
            improvement_areas.append({
                "skill": "logical_thinking",
                "name": "逻辑思维能力",
                "category": "思维能力",
                "current_score": logic_score,
                "weight": 0.8,
                "urgency": self._calculate_urgency(logic_score),
                "feedback": logic.get("feedback", "逻辑思维能力需要提升")
            })
    
    @log_function(logger)
    def _analyze_delivery_scores(self, assessment_results: Dict[str, Any], improvement_areas: List[Dict[str, Any]]) -> None:
        """分析表达方式得分，找出表达方面的改进领域"""
        delivery_results = assessment_results.get("delivery", {})
        
        # 分析语速
        speech_rate = delivery_results.get("speech_rate", {})
        speech_rate_score = speech_rate.get("score", 0)
        if speech_rate_score < 70:
            improvement_areas.append({
                "skill": "speech_rate",
                "name": "语速控制",
                "category": "表达方式",
                "current_score": speech_rate_score,
                "weight": 0.5,
                "urgency": self._calculate_urgency(speech_rate_score),
                "feedback": speech_rate.get("feedback", "语速需要更好地控制")
            })
            
        # 分析清晰度
        clarity = delivery_results.get("clarity", {})
        clarity_score = clarity.get("score", 0)
        if clarity_score < 75:
            improvement_areas.append({
                "skill": "speech_clarity",
                "name": "表达清晰度",
                "category": "表达方式",
                "current_score": clarity_score,
                "weight": 0.6,
                "urgency": self._calculate_urgency(clarity_score),
                "feedback": clarity.get("feedback", "表达需要更加清晰")
            })
            
        # 分析语音变化
        vocal_variety = delivery_results.get("vocal_variety", {})
        vocal_variety_score = vocal_variety.get("score", 0)
        if vocal_variety_score < 70:
            improvement_areas.append({
                "skill": "vocal_variety",
                "name": "语音表现力",
                "category": "表达方式",
                "current_score": vocal_variety_score,
                "weight": 0.4,
                "urgency": self._calculate_urgency(vocal_variety_score),
                "feedback": vocal_variety.get("feedback", "语音表现力需要提升")
            })
            
        # 分析流利度
        fluency = delivery_results.get("fluency", {})
        fluency_score = fluency.get("score", 0)
        if fluency_score < 75:
            improvement_areas.append({
                "skill": "speech_fluency",
                "name": "表达流利度",
                "category": "表达方式",
                "current_score": fluency_score,
                "weight": 0.6,
                "urgency": self._calculate_urgency(fluency_score),
                "feedback": fluency.get("feedback", "表达需要更加流利")
            })
    
    @log_function(logger)
    def _analyze_behavior_scores(self, assessment_results: Dict[str, Any], improvement_areas: List[Dict[str, Any]]) -> None:
        """分析行为表现得分，找出行为方面的改进领域"""
        behavior_results = assessment_results.get("behavior", {})
        
        # 分析肢体语言
        body_language = behavior_results.get("body_language", {})
        body_language_score = body_language.get("score", 0)
        if body_language_score < 70:
            improvement_areas.append({
                "skill": "body_language",
                "name": "肢体语言",
                "category": "非语言表达",
                "current_score": body_language_score,
                "weight": 0.5,
                "urgency": self._calculate_urgency(body_language_score),
                "feedback": body_language.get("feedback", "肢体语言需要更加自然得体")
            })
            
        # 分析面部表情
        facial_expression = behavior_results.get("facial_expression", {})
        facial_expression_score = facial_expression.get("score", 0)
        if facial_expression_score < 70:
            improvement_areas.append({
                "skill": "facial_expression",
                "name": "面部表情",
                "category": "非语言表达",
                "current_score": facial_expression_score,
                "weight": 0.5,
                "urgency": self._calculate_urgency(facial_expression_score),
                "feedback": facial_expression.get("feedback", "面部表情需要更加自然")
            })
            
        # 分析眼神接触
        eye_contact = behavior_results.get("eye_contact", {})
        eye_contact_score = eye_contact.get("score", 0)
        if eye_contact_score < 70:
            improvement_areas.append({
                "skill": "eye_contact",
                "name": "眼神接触",
                "category": "非语言表达",
                "current_score": eye_contact_score,
                "weight": 0.6,
                "urgency": self._calculate_urgency(eye_contact_score),
                "feedback": eye_contact.get("feedback", "眼神接触需要更加自然")
            })
            
        # 分析自信表现
        confidence = behavior_results.get("confidence", {})
        confidence_score = confidence.get("score", 0)
        if confidence_score < 75:
            improvement_areas.append({
                "skill": "confidence",
                "name": "自信表现",
                "category": "心理素质",
                "current_score": confidence_score,
                "weight": 0.7,
                "urgency": self._calculate_urgency(confidence_score),
                "feedback": confidence.get("feedback", "自信表现需要提升")
            })
    
    def _calculate_urgency(self, score: float) -> float:
        """
        基于分数计算紧急度
        
        Args:
            score: 能力得分
            
        Returns:
            紧急度得分 (0-1)
        """
        if score < 50:
            return 1.0  # 极度紧急
        elif score < 60:
            return 0.9  # 非常紧急
        elif score < 70:
            return 0.7  # 很紧急
        elif score < 80:
            return 0.5  # 中等紧急
        else:
            return 0.3  # 低紧急
    
    @log_function(logger)
    def _calculate_priority_scores(self, improvement_areas: List[Dict[str, Any]], job_skills: Dict[str, Any]) -> None:
        """
        计算每个改进领域的优先级分数
        
        Args:
            improvement_areas: 需要改进的能力列表
            job_skills: 职位所需技能
        """
        for area in improvement_areas:
            skill_id = area["skill"]
            
            # 基础优先级由紧急度和权重决定
            base_priority = area["urgency"] * area["weight"]
            
            # 如果是职位关键技能，增加优先级
            if skill_id in job_skills:
                job_skill_weight = job_skills[skill_id].get("weight", 0.5)
                # 职位技能权重提升优先级
                job_priority_boost = job_skill_weight * 0.3
                final_priority = base_priority + job_priority_boost
            else:
                final_priority = base_priority
                
            # 将最终优先级限制在0-1范围内
            area["priority_score"] = min(1.0, max(0.0, final_priority))
    
    @log_function(logger)
    def get_assessment_summary(self, assessment_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成评测结果摘要
        
        Args:
            assessment_results: 面试评测结果
            
        Returns:
            评测结果摘要，包括总体得分、强项和弱项
        """
        # 计算总体得分
        total_score = self._calculate_total_score(assessment_results)
        
        # 识别强项和弱项
        strengths, weaknesses = self._identify_strengths_and_weaknesses(assessment_results)
        
        # 生成整体评价
        overall_evaluation = self._generate_overall_evaluation(total_score, strengths, weaknesses)
        
        return {
            "total_score": total_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "overall_evaluation": overall_evaluation
        }
    
    def _calculate_total_score(self, assessment_results: Dict[str, Any]) -> float:
        """计算评测结果的总体得分"""
        # 这里应实现权重计算总分的逻辑
        # 简化示例
        total = 0
        count = 0
        
        # 内容得分 (权重0.5)
        content_results = assessment_results.get("content", {})
        content_score = 0
        content_count = 0
        
        # 专业知识
        professional_knowledge = content_results.get("professional_knowledge", {})
        for _, data in professional_knowledge.items():
            content_score += data.get("score", 0)
            content_count += 1
            
        # 其他内容指标
        for key in ["structure", "relevance", "logic"]:
            if key in content_results:
                content_score += content_results[key].get("score", 0)
                content_count += 1
                
        if content_count > 0:
            content_avg = content_score / content_count
            total += content_avg * 0.5
            count += 0.5
            
        # 表达方式得分 (权重0.3)
        delivery_results = assessment_results.get("delivery", {})
        delivery_score = 0
        delivery_count = 0
        
        for key in ["speech_rate", "clarity", "vocal_variety", "fluency"]:
            if key in delivery_results:
                delivery_score += delivery_results[key].get("score", 0)
                delivery_count += 1
                
        if delivery_count > 0:
            delivery_avg = delivery_score / delivery_count
            total += delivery_avg * 0.3
            count += 0.3
            
        # 行为表现得分 (权重0.2)
        behavior_results = assessment_results.get("behavior", {})
        behavior_score = 0
        behavior_count = 0
        
        for key in ["body_language", "facial_expression", "eye_contact", "confidence"]:
            if key in behavior_results:
                behavior_score += behavior_results[key].get("score", 0)
                behavior_count += 1
                
        if behavior_count > 0:
            behavior_avg = behavior_score / behavior_count
            total += behavior_avg * 0.2
            count += 0.2
            
        # 计算最终得分
        if count > 0:
            return round(total / count, 1)
        else:
            return 0.0
    
    def _identify_strengths_and_weaknesses(self, assessment_results: Dict[str, Any]) -> tuple:
        """识别评测结果中的强项和弱项"""
        all_scores = []
        
        # 收集所有得分项
        # 内容得分
        content_results = assessment_results.get("content", {})
        professional_knowledge = content_results.get("professional_knowledge", {})
        for skill, data in professional_knowledge.items():
            all_scores.append({
                "skill": skill,
                "name": data.get("name", skill),
                "category": "专业知识",
                "score": data.get("score", 0),
                "feedback": data.get("feedback", "")
            })
            
        # 添加其他内容指标
        for key, name in [
            ("structure", "回答结构性"),
            ("relevance", "回答相关性"),
            ("logic", "逻辑思维能力")
        ]:
            if key in content_results:
                item = content_results[key]
                all_scores.append({
                    "skill": key,
                    "name": name,
                    "category": "表达能力",
                    "score": item.get("score", 0),
                    "feedback": item.get("feedback", "")
                })
                
        # 表达方式得分
        delivery_results = assessment_results.get("delivery", {})
        for key, name in [
            ("speech_rate", "语速控制"),
            ("clarity", "表达清晰度"),
            ("vocal_variety", "语音表现力"),
            ("fluency", "表达流利度")
        ]:
            if key in delivery_results:
                item = delivery_results[key]
                all_scores.append({
                    "skill": key,
                    "name": name,
                    "category": "表达方式",
                    "score": item.get("score", 0),
                    "feedback": item.get("feedback", "")
                })
                
        # 行为表现得分
        behavior_results = assessment_results.get("behavior", {})
        for key, name, category in [
            ("body_language", "肢体语言", "非语言表达"),
            ("facial_expression", "面部表情", "非语言表达"),
            ("eye_contact", "眼神接触", "非语言表达"),
            ("confidence", "自信表现", "心理素质")
        ]:
            if key in behavior_results:
                item = behavior_results[key]
                all_scores.append({
                    "skill": key,
                    "name": name,
                    "category": category,
                    "score": item.get("score", 0),
                    "feedback": item.get("feedback", "")
                })
                
        # 排序并提取强项和弱项
        all_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # 取得分最高的3项为强项
        strengths = all_scores[:3] if len(all_scores) >= 3 else all_scores
        
        # 取得分最低的3项为弱项
        weaknesses = all_scores[-3:] if len(all_scores) >= 3 else all_scores
        weaknesses.reverse()  # 从低到高排序
        
        return strengths, weaknesses
    
    def _generate_overall_evaluation(self, total_score: float, strengths: List[Dict[str, Any]], weaknesses: List[Dict[str, Any]]) -> str:
        """根据总分、强项和弱项生成整体评价"""
        if total_score >= 90:
            evaluation = "优秀的面试表现。"
        elif total_score >= 80:
            evaluation = "良好的面试表现。"
        elif total_score >= 70:
            evaluation = "中等的面试表现，有一些明显可以提升的地方。"
        elif total_score >= 60:
            evaluation = "基础的面试表现，需要在多个方面提升。"
        else:
            evaluation = "面试表现较弱，需要全面提升。"
            
        # 添加强项描述
        if strengths:
            evaluation += " 强项包括"
            for i, strength in enumerate(strengths):
                if i == len(strengths) - 1 and i > 0:
                    evaluation += "和"
                evaluation += f"{strength['name']}"
                if i < len(strengths) - 2:
                    evaluation += "、"
            evaluation += "。"
            
        # 添加弱项和改进建议
        if weaknesses:
            evaluation += " 建议重点提升"
            for i, weakness in enumerate(weaknesses):
                if i == len(weaknesses) - 1 and i > 0:
                    evaluation += "和"
                evaluation += f"{weakness['name']}"
                if i < len(weaknesses) - 2:
                    evaluation += "、"
            evaluation += "。"
            
        return evaluation 