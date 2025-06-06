"""
职位-技能映射服务

负责维护职位与所需技能的映射关系
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

from app.services.learning_recommendation.logging_config import setup_logger, log_function

# 设置日志
logger = setup_logger("app.services.learning_recommendation.job_skill_mapping")

class JobSkillMappingService:
    """职位-技能映射服务，负责维护职位与所需技能的映射关系"""
    
    def __init__(self, mapping_file: str = "data/job_skill_mapping.json"):
        """
        初始化职位-技能映射服务
        
        Args:
            mapping_file: 映射文件路径
        """
        self.mapping_file = mapping_file
        self.mapping_data = {}
        self._load_mapping()
        logger.info("职位-技能映射服务初始化完成", extra={'request_id': 'system', 'user_id': 'system'})
    
    @log_function(logger)    
    def _load_mapping(self) -> None:
        """从文件加载映射数据"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.mapping_file), exist_ok=True)
            
            # 如果文件存在则加载，否则创建默认映射
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    self.mapping_data = json.load(f)
                logger.info(f"成功从 {self.mapping_file} 加载职位-技能映射数据", 
                           extra={'request_id': 'system', 'user_id': 'system'})
            else:
                # 初始化默认映射并保存
                self.mapping_data = self._get_default_mapping()
                self._save_mapping()
                logger.info("创建了默认的职位-技能映射数据", 
                           extra={'request_id': 'system', 'user_id': 'system'})
        except Exception as e:
            logger.error(f"加载职位-技能映射数据失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'system', 'user_id': 'system'})
            # 初始化默认映射
            self.mapping_data = self._get_default_mapping()
    
    @log_function(logger)
    def _save_mapping(self) -> None:
        """保存映射数据到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.mapping_file), exist_ok=True)
            
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self.mapping_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"职位-技能映射数据已保存到 {self.mapping_file}",
                       extra={'request_id': 'system', 'user_id': 'system'})
        except Exception as e:
            logger.error(f"保存职位-技能映射数据失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'system', 'user_id': 'system'})
    
    def _get_default_mapping(self) -> Dict[str, Any]:
        """获取默认的职位-技能映射"""
        return {
            "software_developer": {
                "title": "软件开发工程师",
                "description": "负责设计、开发和维护软件系统，解决技术问题，并参与整个软件开发生命周期。",
                "skills": {
                    "programming": {"weight": 0.8, "name": "编程技能", "description": "掌握一种或多种编程语言，如Python, JavaScript, Java等"},
                    "algorithms": {"weight": 0.7, "name": "算法与数据结构", "description": "理解和应用常见的算法和数据结构"},
                    "design_patterns": {"weight": 0.6, "name": "软件设计模式", "description": "掌握常见的设计模式和软件架构原则"},
                    "devops": {"weight": 0.5, "name": "DevOps知识", "description": "了解持续集成/持续部署和自动化测试"},
                    "version_control": {"weight": 0.7, "name": "版本控制", "description": "熟练使用Git等版本控制系统"},
                    "testing": {"weight": 0.6, "name": "软件测试", "description": "编写单元测试和集成测试"},
                    "debugging": {"weight": 0.7, "name": "调试能力", "description": "能够有效定位和解决问题"},
                    "communication": {"weight": 0.5, "name": "沟通能力", "description": "与团队成员和利益相关者有效沟通"}
                }
            },
            "data_scientist": {
                "title": "数据科学家",
                "description": "利用数据分析和机器学习技术解决业务问题，提取数据洞察，并开发预测模型。",
                "skills": {
                    "statistics": {"weight": 0.8, "name": "统计分析", "description": "熟悉统计理论和方法"},
                    "programming": {"weight": 0.7, "name": "编程技能", "description": "精通Python或R语言"},
                    "machine_learning": {"weight": 0.8, "name": "机器学习", "description": "理解和应用各种机器学习算法"},
                    "data_visualization": {"weight": 0.6, "name": "数据可视化", "description": "能够创建清晰有效的数据可视化"},
                    "sql": {"weight": 0.7, "name": "SQL和数据库", "description": "编写高效的数据库查询"},
                    "big_data": {"weight": 0.5, "name": "大数据技术", "description": "熟悉大数据处理框架如Spark"},
                    "deep_learning": {"weight": 0.6, "name": "深度学习", "description": "了解神经网络和深度学习框架"},
                    "business_acumen": {"weight": 0.5, "name": "业务理解", "description": "将数据科学技术应用于业务问题"}
                }
            },
            "data_analyst": {
                "title": "数据分析师",
                "description": "分析数据以提取业务洞察，创建报告和可视化，并支持数据驱动的决策制定。",
                "skills": {
                    "data_processing": {"weight": 0.8, "name": "数据处理", "description": "清理、转换和组织数据"},
                    "sql": {"weight": 0.7, "name": "SQL和数据库", "description": "编写高效的数据库查询"},
                    "bi_tools": {"weight": 0.7, "name": "商业智能工具", "description": "使用Tableau, Power BI等工具"},
                    "statistics": {"weight": 0.6, "name": "统计分析基础", "description": "应用基本的统计方法"},
                    "data_visualization": {"weight": 0.8, "name": "数据可视化", "description": "创建清晰有效的图表和仪表板"},
                    "excel": {"weight": 0.7, "name": "Excel高级技能", "description": "使用高级函数、数据透视表等"},
                    "reporting": {"weight": 0.6, "name": "报告撰写", "description": "创建清晰的数据报告"},
                    "critical_thinking": {"weight": 0.6, "name": "批判性思维", "description": "质疑数据和识别模式"}
                }
            },
            "ui_ux_designer": {
                "title": "UI/UX设计师",
                "description": "设计用户界面和体验，创建原型和线框图，并确保产品具有良好的可用性和吸引力。",
                "skills": {
                    "design_theory": {"weight": 0.8, "name": "设计基础理论", "description": "色彩、排版、布局等设计原理"},
                    "user_research": {"weight": 0.7, "name": "用户研究", "description": "进行用户访谈和可用性测试"},
                    "prototyping": {"weight": 0.8, "name": "原型设计", "description": "创建低保真和高保真原型"},
                    "design_tools": {"weight": 0.7, "name": "设计工具", "description": "熟练使用Figma, Sketch等工具"},
                    "user_testing": {"weight": 0.6, "name": "用户测试", "description": "规划和执行用户测试"},
                    "wireframing": {"weight": 0.7, "name": "线框图设计", "description": "创建清晰的界面线框图"},
                    "interaction_design": {"weight": 0.7, "name": "交互设计", "description": "设计用户流和交互模式"},
                    "visual_design": {"weight": 0.6, "name": "视觉设计", "description": "创建视觉风格和元素"}
                }
            }
        }
    
    @log_function(logger)
    def get_skills_for_job(self, job_id: str) -> Dict[str, Any]:
        """
        获取指定职位所需的技能列表
        
        Args:
            job_id: 职位ID
            
        Returns:
            包含技能信息的字典
        """
        if job_id in self.mapping_data:
            return self.mapping_data[job_id]
        else:
            logger.warning(f"未找到职位 {job_id} 的技能映射，使用通用技能", 
                          extra={'request_id': 'auto', 'user_id': 'system'})
            return {
                "title": "通用职位",
                "description": "跨领域的通用职位",
                "skills": {
                    "communication": {"weight": 0.7, "name": "沟通能力", "description": "清晰有效地传达信息"},
                    "problem_solving": {"weight": 0.7, "name": "问题解决能力", "description": "分析和解决复杂问题"},
                    "teamwork": {"weight": 0.6, "name": "团队协作", "description": "在团队中有效工作"},
                    "time_management": {"weight": 0.6, "name": "时间管理", "description": "有效规划和执行任务"},
                    "adaptability": {"weight": 0.5, "name": "适应能力", "description": "应对变化和学习新技能"}
                }
            }
    
    @log_function(logger)
    def get_all_job_titles(self) -> List[Dict[str, str]]:
        """
        获取所有支持的职位列表
        
        Returns:
            职位列表，每个职位包含id和title
        """
        return [{"id": job_id, "title": job_info["title"]} 
                for job_id, job_info in self.mapping_data.items()]
    
    @log_function(logger)
    def update_job_skill_mapping(self, job_id: str, job_info: Dict[str, Any]) -> bool:
        """
        更新职位的技能映射
        
        Args:
            job_id: 职位ID
            job_info: 职位信息，包括title, description和skills
            
        Returns:
            是否更新成功
        """
        try:
            self.mapping_data[job_id] = job_info
            
            # 保存到文件
            self._save_mapping()
            
            logger.info(f"职位 {job_id} 的技能映射更新成功", 
                       extra={'request_id': 'auto', 'user_id': 'system'})
            return True
        except Exception as e:
            logger.error(f"更新职位 {job_id} 的技能映射失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'auto', 'user_id': 'system'})
            return False
    
    @log_function(logger)
    def delete_job(self, job_id: str) -> bool:
        """
        删除职位及其技能映射
        
        Args:
            job_id: 职位ID
            
        Returns:
            是否删除成功
        """
        try:
            if job_id in self.mapping_data:
                del self.mapping_data[job_id]
                self._save_mapping()
                logger.info(f"职位 {job_id} 已被删除", 
                           extra={'request_id': 'auto', 'user_id': 'system'})
                return True
            else:
                logger.warning(f"尝试删除不存在的职位 {job_id}", 
                              extra={'request_id': 'auto', 'user_id': 'system'})
                return False
        except Exception as e:
            logger.error(f"删除职位 {job_id} 失败: {str(e)}", exc_info=True,
                        extra={'request_id': 'auto', 'user_id': 'system'})
            return False 