# agent/nodes/executors/learning_path_generator.py

from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import asyncio
import time
import json
from pydantic import BaseModel, Field

from ...core.system.config import AgentConfig
from ...services.modelscope_service import ModelScopeService
from ...services.websearch_service import WebSearchService
from ...retrieval import HybridRetriever, Context7Retriever
from ...services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class LearningNeed(BaseModel):
    """学习需求"""
    area: str = Field(..., description="需要提升的领域")
    level: str = Field(..., description="当前水平")
    priority: int = Field(..., description="优先级(1-5)")
    description: str = Field(..., description="详细描述")

class LearningResource(BaseModel):
    """学习资源"""
    title: str = Field(..., description="资源标题")
    url: Optional[str] = Field(None, description="资源链接")
    source: str = Field(..., description="来源类型(article, course, video, ebook)")
    description: str = Field(..., description="资源描述")
    relevance: float = Field(..., description="相关度(0-1)")
    level: str = Field(..., description="适合水平(beginner, intermediate, advanced)")
    estimated_time: str = Field(..., description="预计学习时间")

class LearningPath(BaseModel):
    """学习路径"""
    need: LearningNeed = Field(..., description="学习需求")
    resources: List[LearningResource] = Field(default_factory=list, description="推荐资源列表")
    timeline: str = Field(..., description="学习时间线")
    milestones: List[str] = Field(default_factory=list, description="学习里程碑")

class LearningPathGeneratorInput(BaseModel):
    """学习路径生成器输入"""
    analysis_result: Dict[str, Any] = Field(..., description="面试分析结果")
    job_position: Optional[str] = Field(None, description="目标职位")
    tech_field: Optional[str] = Field(None, description="技术领域")
    time_constraint: Optional[str] = Field(None, description="时间约束")
    focus_areas: Optional[List[str]] = Field(None, description="重点提升领域")

class LearningPathGeneratorOutput(BaseModel):
    """学习路径生成器输出"""
    learning_report: Dict[str, Any] = Field(..., description="学习需求报告")
    learning_paths: List[LearningPath] = Field(default_factory=list, description="个性化学习路径")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

class LearningPathGenerator:
    """学习路径生成器
    
    基于面试分析结果生成个性化学习路径
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化学习路径生成器
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        self.config = config or AgentConfig()
        
        # 初始化服务
        self.modelscope_service = None
        self.websearch_service = None
        self.hybrid_retriever = None
        self.context7_retriever = None
        self.openai_service = None
        
        # 加载配置
        self.max_resources_per_need = self.config.get_learning_config("max_resources_per_need", 5)
        self.search_results_limit = self.config.get_learning_config("search_results_limit", 10)
        self.context_window = self.config.get_learning_config("context_window", 4000)
        self.default_tech_field_model = self.config.get_learning_config(
            "default_tech_field_model", 
            "damo/nlp_structbert_text-classification_chinese-base"
        )
        self.default_report_template = self.config.get_learning_config(
            "default_report_template",
            """
            基于以下面试分析结果，生成学习需求报告:
            
            分析结果：
            {analysis_result}
            
            目标职位：{job_position}
            技术领域：{tech_field}
            时间约束：{time_constraint}
            重点领域：{focus_areas}
            
            请生成详细的学习需求报告，包括：
            1. 需要提升的关键领域(至少3个)
            2. 每个领域的当前水平评估
            3. 提升的优先级(1-5，5为最高)
            4. 每个领域的具体提升目标
            
            输出格式应为JSON，每个领域作为一个对象，包含area、level、priority、description字段。
            """
        )
    
    def _ensure_services_initialized(self):
        """确保服务已初始化"""
        if self.modelscope_service is None:
            self.modelscope_service = ModelScopeService(self.config)
            logger.info("ModelScope服务初始化完成")
        
        if self.websearch_service is None:
            self.websearch_service = WebSearchService(self.config)
            logger.info("WebSearch服务初始化完成")
        
        if self.hybrid_retriever is None:
            # 导入放在这里避免循环导入
            from ...retrieval import HybridRetriever
            self.hybrid_retriever = HybridRetriever(self.config)
            logger.info("混合检索器初始化完成")
        
        if self.context7_retriever is None:
            # 导入放在这里避免循环导入
            from ...retrieval import Context7Retriever
            self.context7_retriever = Context7Retriever(self.config)
            logger.info("Context7检索器初始化完成")
        
        if self.openai_service is None:
            self.openai_service = OpenAIService(self.config)
            logger.info("OpenAI服务初始化完成")
    
    async def _generate_learning_report(self, input_data: LearningPathGeneratorInput) -> Dict[str, Any]:
        """生成学习需求报告
        
        使用ModelScope模型生成学习需求报告
        
        Args:
            input_data: 输入数据
            
        Returns:
            Dict[str, Any]: 学习需求报告
        """
        self._ensure_services_initialized()
        
        # 准备报告内容
        report_prompt = self.default_report_template.format(
            analysis_result=json.dumps(input_data.analysis_result, ensure_ascii=False),
            job_position=input_data.job_position or "未指定",
            tech_field=input_data.tech_field or "未指定",
            time_constraint=input_data.time_constraint or "未指定",
            focus_areas=", ".join(input_data.focus_areas) if input_data.focus_areas else "未指定"
        )
        
        try:
            # 方法1: 尝试使用ModelScope的文本生成模型
            try:
                # 使用ModelScope的文本生成模型
                result = await self.modelscope_service.run_pipeline(
                    task="text_generation", 
                    model_id="damo/nlp_bart_text-generation_chinese-base",
                    inputs=report_prompt
                )
                
                if result.get("status") == "success" and "text" in result:
                    # 解析生成的文本
                    generated_text = result["text"]
                    # 提取JSON部分
                    json_start = generated_text.find('{')
                    json_end = generated_text.rfind('}') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_str = generated_text[json_start:json_end]
                        try:
                            learning_needs = json.loads(json_str)
                            return learning_needs
                        except json.JSONDecodeError:
                            logger.warning("ModelScope生成的文本无法解析为JSON，尝试使用OpenAI")
                    else:
                        logger.warning("ModelScope生成的文本中未找到JSON，尝试使用OpenAI")
            except Exception as e:
                logger.warning(f"使用ModelScope生成报告失败: {e}，尝试使用OpenAI")
            
            # 方法2: 使用OpenAI生成报告
            messages = [
                {"role": "system", "content": "你是一个专业的学习需求分析师，擅长根据面试分析结果生成学习需求报告。请以JSON格式输出。"},
                {"role": "user", "content": report_prompt}
            ]
            
            result = await self.openai_service.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=1500
            )
            
            if result.get("status") == "success" and "content" in result:
                content = result["content"]
                # 提取JSON部分
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    learning_needs = json.loads(json_str)
                    return learning_needs
                else:
                    # 尝试直接解析整个内容
                    try:
                        learning_needs = json.loads(content)
                        return learning_needs
                    except json.JSONDecodeError:
                        logger.error("无法从生成的内容中提取JSON")
                        return {"error": "无法生成有效的学习需求报告"}
            else:
                logger.error(f"生成报告失败: {result.get('error', '未知错误')}")
                return {"error": "生成报告失败"}
                
        except Exception as e:
            logger.error(f"生成学习需求报告异常: {e}")
            return {"error": str(e)}
    
    async def _search_learning_resources(self, need: LearningNeed, tech_field: str) -> List[Dict[str, Any]]:
        """搜索学习资源
        
        结合RAG检索和Web搜索查找学习资源
        
        Args:
            need: 学习需求
            tech_field: 技术领域
            
        Returns:
            List[Dict[str, Any]]: 学习资源列表
        """
        self._ensure_services_initialized()
        
        # 构建搜索查询
        search_query = f"{tech_field} {need.area} {need.level} 学习资源 教程"
        
        try:
            # 并行执行RAG检索和Web搜索
            rag_task = self._rag_search(search_query)
            web_task = self._web_search(search_query)
            
            rag_results, web_results = await asyncio.gather(rag_task, web_task)
            
            # 合并结果
            all_results = []
            all_results.extend(rag_results)
            all_results.extend(web_results)
            
            # 去重并限制结果数量
            unique_results = self._remove_duplicates(all_results)
            limited_results = unique_results[:self.max_resources_per_need]
            
            # 转换为学习资源格式
            resources = await self._format_resources(limited_results, need)
            
            logger.info(f"为学习需求 '{need.area}' 找到 {len(resources)} 个资源")
            return resources
            
        except Exception as e:
            logger.error(f"搜索学习资源异常: {e}")
            return []
    
    async def _rag_search(self, query: str) -> List[Dict[str, Any]]:
        """RAG检索
        
        使用混合检索器和Context7检索器查找相关内容
        
        Args:
            query: 查询文本
            
        Returns:
            List[Dict[str, Any]]: 检索结果
        """
        try:
            # 使用混合检索器
            hybrid_results = await self.hybrid_retriever.retrieve(query, max_results=self.search_results_limit // 2)
            
            # 使用Context7检索器 - 尝试常见的学习资源库
            learning_libraries = ["learning-resources", "programming-courses", "tech-tutorials"]
            
            context7_results = []
            for lib in learning_libraries:
                try:
                    results = await self.context7_retriever.retrieve(
                        query, 
                        library_name=lib, 
                        tokens=3000
                    )
                    context7_results.extend(results)
                except Exception as e:
                    logger.warning(f"Context7检索库 {lib} 失败: {e}")
            
            # 合并结果
            all_results = hybrid_results + context7_results
            
            # 添加来源标记
            for result in all_results:
                result["resource_type"] = "internal"
            
            return all_results
            
        except Exception as e:
            logger.error(f"RAG检索异常: {e}")
            return []
    
    async def _web_search(self, query: str) -> List[Dict[str, Any]]:
        """Web搜索
        
        使用WebSearch服务查找在线资源
        
        Args:
            query: 查询文本
            
        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        try:
            # 使用WebSearch服务
            search_result = await self.websearch_service.search(
                query=query,
                num_results=self.search_results_limit // 2
            )
            
            if search_result.get("status") == "success" and "results" in search_result:
                # 转换为统一格式
                results = []
                for item in search_result["results"]:
                    result = {
                        "text": item.get("snippet", "") or item.get("description", ""),
                        "metadata": {
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "source": "web_search"
                        },
                        "score": 0.8,  # 默认分数
                        "resource_type": "external"
                    }
                    results.append(result)
                
                return results
            else:
                logger.warning(f"Web搜索失败: {search_result.get('error', '未知错误')}")
                return []
                
        except Exception as e:
            logger.error(f"Web搜索异常: {e}")
            return []
    
    def _remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去除重复结果
        
        Args:
            results: 搜索结果列表
            
        Returns:
            List[Dict[str, Any]]: 去重后的结果列表
        """
        unique_results = []
        urls = set()
        titles = set()
        
        for result in results:
            url = result.get("metadata", {}).get("url", "")
            title = result.get("metadata", {}).get("title", "")
            
            # 如果URL和标题都没有出现过，添加到结果中
            if (not url or url not in urls) and (not title or title not in titles):
                if url:
                    urls.add(url)
                if title:
                    titles.add(title)
                unique_results.append(result)
        
        return unique_results
    
    async def _format_resources(self, results: List[Dict[str, Any]], need: LearningNeed) -> List[LearningResource]:
        """格式化学习资源
        
        将搜索结果转换为结构化的学习资源
        
        Args:
            results: 搜索结果
            need: 学习需求
            
        Returns:
            List[LearningResource]: 学习资源列表
        """
        self._ensure_services_initialized()
        
        resources = []
        
        for result in results:
            # 提取基本信息
            text = result.get("text", "")
            metadata = result.get("metadata", {})
            title = metadata.get("title", "未知资源")
            url = metadata.get("url", None)
            
            # 使用LLM分析资源类型和预计学习时间
            try:
                resource_info = await self._analyze_resource(text, title, need)
                
                # 创建学习资源
                resource = LearningResource(
                    title=title,
                    url=url,
                    source=resource_info.get("source", "article"),
                    description=resource_info.get("description", text[:200] + "..."),
                    relevance=float(result.get("score", 0.7)),
                    level=resource_info.get("level", "beginner"),
                    estimated_time=resource_info.get("estimated_time", "1-2小时")
                )
                
                resources.append(resource)
                
            except Exception as e:
                logger.error(f"格式化资源异常: {e}")
                # 创建简单的默认资源
                resource = LearningResource(
                    title=title,
                    url=url,
                    source="unknown",
                    description=text[:200] + "..." if len(text) > 200 else text,
                    relevance=float(result.get("score", 0.5)),
                    level="intermediate",
                    estimated_time="未知"
                )
                resources.append(resource)
        
        return resources
    
    async def _analyze_resource(self, text: str, title: str, need: LearningNeed) -> Dict[str, str]:
        """分析资源信息
        
        使用LLM分析资源的类型、难度和预计学习时间
        
        Args:
            text: 资源文本
            title: 资源标题
            need: 学习需求
            
        Returns:
            Dict[str, str]: 资源信息
        """
        prompt = f"""
        分析以下学习资源，并提供资源类型、适合难度和预计学习时间：
        
        资源标题: {title}
        资源内容: {text[:500]}...
        
        该资源将用于提升以下能力:
        - 领域: {need.area}
        - 当前水平: {need.level}
        - 提升目标: {need.description}
        
        请输出以下信息(JSON格式):
        1. source: 资源类型(article, course, video, ebook, tool)
        2. level: 适合水平(beginner, intermediate, advanced)
        3. estimated_time: 预计学习时间
        4. description: 简短描述该资源(100字以内)
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的学习资源分析师，擅长分析学习资源的类型、难度和学习时间。"},
            {"role": "user", "content": prompt}
        ]
        
        result = await self.openai_service.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )
        
        if result.get("status") == "success" and "content" in result:
            content = result["content"]
            # 提取JSON部分
            try:
                # 尝试直接解析
                resource_info = json.loads(content)
                return resource_info
            except json.JSONDecodeError:
                # 尝试提取JSON部分
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    try:
                        resource_info = json.loads(json_str)
                        return resource_info
                    except json.JSONDecodeError:
                        pass
        
        # 返回默认值
        return {
            "source": "article",
            "level": "intermediate",
            "estimated_time": "1-2小时",
            "description": text[:100] + "..." if len(text) > 100 else text
        }
    
    async def _generate_learning_path(self, need: LearningNeed, resources: List[LearningResource], time_constraint: Optional[str] = None) -> LearningPath:
        """生成学习路径
        
        根据学习需求和资源生成学习路径
        
        Args:
            need: 学习需求
            resources: 学习资源列表
            time_constraint: 时间约束
            
        Returns:
            LearningPath: 学习路径
        """
        self._ensure_services_initialized()
        
        # 准备提示内容
        resources_text = ""
        for i, resource in enumerate(resources):
            resources_text += f"{i+1}. {resource.title} ({resource.source}, {resource.level}): {resource.description}\n"
        
        prompt = f"""
        根据以下学习需求和资源，生成一个学习路径:
        
        学习需求:
        - 领域: {need.area}
        - 当前水平: {need.level}
        - 优先级: {need.priority}
        - 目标: {need.description}
        
        可用资源:
        {resources_text}
        
        时间约束: {time_constraint or '无特定时间约束'}
        
        请提供:
        1. 学习时间线(timeline): 提供一个合理的学习时间线，考虑时间约束
        2. 学习里程碑(milestones): 至少3个关键里程碑，每个里程碑应该包含具体的学习目标
        
        以JSON格式输出，包含timeline和milestones字段。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的学习路径规划师，擅长设计高效的学习路径和时间规划。"},
            {"role": "user", "content": prompt}
        ]
        
        result = await self.openai_service.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        if result.get("status") == "success" and "content" in result:
            content = result["content"]
            
            # 提取JSON部分
            try:
                # 尝试直接解析
                path_info = json.loads(content)
                
                # 创建学习路径
                learning_path = LearningPath(
                    need=need,
                    resources=resources,
                    timeline=path_info.get("timeline", "未指定时间线"),
                    milestones=path_info.get("milestones", [])
                )
                
                return learning_path
                
            except json.JSONDecodeError:
                # 尝试提取JSON部分
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    try:
                        path_info = json.loads(json_str)
                        
                        # 创建学习路径
                        learning_path = LearningPath(
                            need=need,
                            resources=resources,
                            timeline=path_info.get("timeline", "未指定时间线"),
                            milestones=path_info.get("milestones", [])
                        )
                        
                        return learning_path
                    except json.JSONDecodeError:
                        pass
        
        # 返回默认学习路径
        return LearningPath(
            need=need,
            resources=resources,
            timeline=f"建议在 {len(resources)*2} 天内完成学习",
            milestones=["理解基本概念", "掌握核心技能", "实践应用"]
        )
    
    async def generate(self, input_data: Union[Dict[str, Any], LearningPathGeneratorInput]) -> LearningPathGeneratorOutput:
        """生成个性化学习路径
        
        Args:
            input_data: 输入数据
            
        Returns:
            LearningPathGeneratorOutput: 输出数据
        """
        # 确保输入是LearningPathGeneratorInput类型
        if isinstance(input_data, dict):
            input_data = LearningPathGeneratorInput(**input_data)
        
        start_time = time.time()
        logger.info(f"开始生成学习路径: {input_data.tech_field or '未指定技术领域'}")
        
        try:
            # 生成学习需求报告
            learning_report = await self._generate_learning_report(input_data)
            
            # 提取学习需求
            learning_needs = []
            if "error" not in learning_report:
                # 遍历报告中的每个学习需求
                for key, value in learning_report.items():
                    if isinstance(value, dict) and "area" in value:
                        # 直接使用报告中的需求项
                        need = LearningNeed(
                            area=value["area"],
                            level=value["level"],
                            priority=value["priority"],
                            description=value["description"]
                        )
                        learning_needs.append(need)
                    elif isinstance(value, dict):
                        # 尝试使用键作为领域
                        need = LearningNeed(
                            area=key,
                            level=value.get("level", "beginner"),
                            priority=value.get("priority", 3),
                            description=value.get("description", "提升该领域的综合能力")
                        )
                        learning_needs.append(need)
            
            # 按优先级排序
            learning_needs.sort(key=lambda x: x.priority, reverse=True)
            
            # 为每个学习需求生成学习路径
            learning_paths = []
            for need in learning_needs:
                # 搜索学习资源
                resources = await self._search_learning_resources(
                    need, 
                    input_data.tech_field or ""
                )
                
                # 生成学习路径
                if resources:
                    learning_path = await self._generate_learning_path(
                        need, 
                        resources, 
                        input_data.time_constraint
                    )
                    learning_paths.append(learning_path)
            
            # 准备元数据
            metadata = {
                "execution_time": time.time() - start_time,
                "needs_count": len(learning_needs),
                "paths_count": len(learning_paths),
                "tech_field": input_data.tech_field
            }
            
            # 创建输出
            output = LearningPathGeneratorOutput(
                learning_report=learning_report,
                learning_paths=learning_paths,
                metadata=metadata
            )
            
            logger.info(f"学习路径生成完成，路径数量: {len(learning_paths)}，用时: {metadata['execution_time']:.2f}s")
            return output
            
        except Exception as e:
            logger.error(f"生成学习路径异常: {e}")
            
            # 创建错误输出
            output = LearningPathGeneratorOutput(
                learning_report={"error": str(e)},
                learning_paths=[],
                metadata={"error": str(e), "execution_time": time.time() - start_time}
            )
            
            return output 