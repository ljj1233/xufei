# agent/core/workflow/graph.py

"""
工作流图定义模块

该模块定义了LangGraph工作流的节点和边，以及条件分支逻辑。
工作流图包含以下节点：
- 任务解析（task_parser）
- 策略决策（strategy_decider）
- 任务规划（task_planner）
- 分析执行（analyzer_executor）
- RAG执行（rag）
- 学习路径生成（learning_path）
- 结果整合（result_integrator）
- 反馈生成（feedback_generator）
"""

from typing import Dict, Any, List, Tuple, Annotated, TypedDict, Literal, Optional, Union, Callable, TypeVar, Type, cast
import logging
import asyncio
from enum import Enum
import time
import json

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, HumanMessage
from langchain_langgraph.graph import StateGraph, END

from agent.core.state import GraphState
from agent.core.nodes import (
    TaskParser,
    StrategyDecider,
    TaskPlanner,
    AnalyzerExecutor,
    ResultIntegrator,
    FeedbackGenerator,
)
from ..system.config import AgentConfig
from ...nodes.executors.rag_executor import RAGExecutor, RAGExecutorInput, RAGExecutorOutput
from ...nodes.executors.learning_path_generator import LearningPathGenerator, LearningPathGeneratorInput, LearningPathGeneratorOutput

# 配置日志
logger = logging.getLogger(__name__)

# 定义状态类型
T = TypeVar("T", bound=Dict[str, Any])

class NodeType(str, Enum):
    """节点类型"""
    TASK_PARSER = "task_parser"
    STRATEGY_SELECTOR = "strategy_selector"
    TASK_PLANNER = "task_planner"
    ANALYZER = "analyzer"
    RAG = "rag"
    LEARNING_PATH = "learning_path"
    GENERATOR = "generator"
    EVALUATOR = "evaluator"
    EXECUTOR = "executor"
    ROUTER = "router"

class WorkflowState(BaseModel):
    """工作流状态"""
    query: str = Field(default="", description="查询文本")
    task_type: str = Field(default="", description="任务类型")
    strategy: Dict[str, Any] = Field(default_factory=dict, description="策略")
    plan: List[Dict[str, Any]] = Field(default_factory=list, description="计划")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文")
    results: Dict[str, Any] = Field(default_factory=dict, description="结果")
    current_step: int = Field(default=0, description="当前步骤")
    history: List[Dict[str, Any]] = Field(default_factory=list, description="历史记录")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    error: Optional[str] = Field(default=None, description="错误信息")

class WorkflowBuilder:
    """工作流构建器"""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """初始化工作流构建器
        
        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        self.config = config or AgentConfig()
        self.graph = None
        
        # 初始化执行器
        self.analyzer_executor = AnalyzerExecutor(self.config)
        self.rag_executor = RAGExecutor(self.config)
        self.learning_path_generator = LearningPathGenerator(self.config)
        
        # 节点映射
        self.node_map = {}
    
    def build(self) -> StateGraph:
        """构建工作流图
        
        Returns:
            StateGraph: 工作流图
        """
        # 创建图
        self.graph = StateGraph(WorkflowState)
        
        # 添加节点
        self._add_nodes()
        
        # 添加边
        self._add_edges()
        
        # 编译图
        return self.graph.compile()
    
    def _add_nodes(self):
        """添加节点"""
        # 任务解析器
        self.graph.add_node(NodeType.TASK_PARSER, self._task_parser)
        self.node_map[NodeType.TASK_PARSER] = self._task_parser
        
        # 策略选择器
        self.graph.add_node(NodeType.STRATEGY_SELECTOR, self._strategy_selector)
        self.node_map[NodeType.STRATEGY_SELECTOR] = self._strategy_selector
        
        # 任务规划器
        self.graph.add_node(NodeType.TASK_PLANNER, self._task_planner)
        self.node_map[NodeType.TASK_PLANNER] = self._task_planner
        
        # 分析器
        self.graph.add_node(NodeType.ANALYZER, self._analyzer)
        self.node_map[NodeType.ANALYZER] = self._analyzer
        
        # RAG
        self.graph.add_node(NodeType.RAG, self._rag)
        self.node_map[NodeType.RAG] = self._rag
        
        # 学习路径生成器
        self.graph.add_node(NodeType.LEARNING_PATH, self._learning_path)
        self.node_map[NodeType.LEARNING_PATH] = self._learning_path
        
        # 生成器
        self.graph.add_node(NodeType.GENERATOR, self._generator)
        self.node_map[NodeType.GENERATOR] = self._generator
        
        # 评估器
        self.graph.add_node(NodeType.EVALUATOR, self._evaluator)
        self.node_map[NodeType.EVALUATOR] = self._evaluator
        
        # 路由器
        self.graph.add_node(NodeType.ROUTER, self._router)
        self.node_map[NodeType.ROUTER] = self._router
    
    def _add_edges(self):
        """添加边"""
        # 设置入口节点
        self.graph.set_entry_point(NodeType.TASK_PARSER)
        
        # 任务解析器 -> 策略选择器
        self.graph.add_edge(NodeType.TASK_PARSER, NodeType.STRATEGY_SELECTOR)
        
        # 策略选择器 -> 任务规划器
        self.graph.add_edge(NodeType.STRATEGY_SELECTOR, NodeType.TASK_PLANNER)
        
        # 任务规划器 -> 路由器
        self.graph.add_edge(NodeType.TASK_PLANNER, NodeType.ROUTER)
        
        # 路由器 -> 分析器/RAG/学习路径/生成器
        self.graph.add_conditional_edges(
            NodeType.ROUTER,
            self._route_next_step,
            {
                NodeType.ANALYZER: NodeType.ANALYZER,
                NodeType.RAG: NodeType.RAG,
                NodeType.LEARNING_PATH: NodeType.LEARNING_PATH,
                NodeType.GENERATOR: NodeType.GENERATOR,
                END: END
            }
        )
        
        # 分析器 -> 路由器
        self.graph.add_edge(NodeType.ANALYZER, NodeType.ROUTER)
        
        # RAG -> 路由器
        self.graph.add_edge(NodeType.RAG, NodeType.ROUTER)
        
        # 学习路径 -> 路由器
        self.graph.add_edge(NodeType.LEARNING_PATH, NodeType.ROUTER)
        
        # 生成器 -> 评估器
        self.graph.add_edge(NodeType.GENERATOR, NodeType.EVALUATOR)
        
        # 评估器 -> 路由器/结束
        self.graph.add_conditional_edges(
            NodeType.EVALUATOR,
            self._evaluate_result,
            {
                NodeType.ROUTER: NodeType.ROUTER,
                END: END
            }
        )
    
    async def _task_parser(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """任务解析器
        
        Args:
            state: 工作流状态
            config: 运行配置
            
        Returns:
            WorkflowState: 更新后的状态
        """
        logger.info(f"任务解析器: {state.query}")
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 简单实现，根据查询文本判断任务类型
            query = state.query.lower()
            
            if "面试" in query or "interview" in query:
                task_type = "interview"
            elif "简历" in query or "resume" in query:
                task_type = "resume"
            elif "学习" in query or "学习路径" in query or "学习计划" in query:
                task_type = "learning_path"
            elif "求职" in query or "job" in query:
                task_type = "job_search"
            else:
                task_type = "general"
            
            # 更新状态
            state.task_type = task_type
            state.metadata["task_parser_time"] = time.time() - start_time
            
            logger.info(f"任务类型: {task_type}")
            return state
            
        except Exception as e:
            logger.error(f"任务解析器异常: {e}")
            state.error = f"任务解析失败: {str(e)}"
            return state
    
    async def _strategy_selector(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """策略选择器
        
        Args:
            state: 工作流状态
            config: 运行配置
            
        Returns:
            WorkflowState: 更新后的状态
        """
        logger.info(f"策略选择器: {state.task_type}")
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 根据任务类型选择策略
            if state.task_type == "interview":
                strategy = {
                    "use_analyzer": True,
                    "use_rag": True,
                    "use_learning_path": True,
                    "use_context7": True,
                    "library_name": "interview_preparation",
                    "max_results": 5
                }
            elif state.task_type == "resume":
                strategy = {
                    "use_analyzer": False,
                    "use_rag": True,
                    "use_learning_path": True,
                    "use_context7": True,
                    "library_name": "resume_writing",
                    "max_results": 3
                }
            elif state.task_type == "learning_path":
                strategy = {
                    "use_analyzer": True,
                    "use_rag": True,
                    "use_learning_path": True,
                    "use_web_search": True,
                    "max_results": 5
                }
            elif state.task_type == "job_search":
                strategy = {
                    "use_analyzer": False,
                    "use_rag": True,
                    "use_learning_path": True,
                    "use_web_search": True,
                    "max_results": 5
                }
            else:
                strategy = {
                    "use_analyzer": False,
                    "use_rag": True,
                    "use_learning_path": False,
                    "max_results": 3
                }
            
            # 更新状态
            state.strategy = strategy
            state.metadata["strategy_selector_time"] = time.time() - start_time
            
            logger.info(f"策略: {json.dumps(strategy)}")
            return state
            
        except Exception as e:
            logger.error(f"策略选择器异常: {e}")
            state.error = f"策略选择失败: {str(e)}"
            return state
    
    async def _task_planner(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """任务规划器
        
        Args:
            state: 工作流状态
            config: 运行配置
            
        Returns:
            WorkflowState: 更新后的状态
        """
        logger.info(f"任务规划器: {state.task_type}")
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 根据策略创建计划
            plan = []
            
            # 如果使用分析器，添加分析步骤
            if state.strategy.get("use_analyzer", False):
                plan.append({
                    "type": NodeType.ANALYZER,
                    "name": "分析查询",
                    "config": {}
                })
            
            # 如果使用RAG，添加RAG步骤
            if state.strategy.get("use_rag", False):
                rag_config = {
                    "use_web_search": state.strategy.get("use_web_search", False),
                    "use_context7": state.strategy.get("use_context7", False),
                    "max_results": state.strategy.get("max_results", 5)
                }
                
                # 如果使用Context7，添加库名称
                if state.strategy.get("use_context7", False):
                    rag_config["library_name"] = state.strategy.get("library_name")
                
                plan.append({
                    "type": NodeType.RAG,
                    "name": "检索知识",
                    "config": rag_config
                })
            
            # 如果使用学习路径，添加学习路径步骤
            if state.strategy.get("use_learning_path", False):
                learning_path_config = {
                    "tech_field": self._extract_tech_field(state.query),
                    "time_constraint": self._extract_time_constraint(state.query),
                    "use_web_search": state.strategy.get("use_web_search", True)
                }
                
                plan.append({
                    "type": NodeType.LEARNING_PATH,
                    "name": "生成学习路径",
                    "config": learning_path_config
                })
            
            # 添加生成步骤
            plan.append({
                "type": NodeType.GENERATOR,
                "name": "生成回答",
                "config": {}
            })
            
            # 添加评估步骤
            plan.append({
                "type": NodeType.EVALUATOR,
                "name": "评估回答",
                "config": {}
            })
            
            # 更新状态
            state.plan = plan
            state.current_step = 0
            state.metadata["task_planner_time"] = time.time() - start_time
            
            logger.info(f"计划: {len(plan)} 步骤")
            return state
            
        except Exception as e:
            logger.error(f"任务规划器异常: {e}")
            state.error = f"任务规划失败: {str(e)}"
            return state
    
    def _extract_tech_field(self, query: str) -> str:
        """从查询中提取技术领域
        
        Args:
            query: 查询文本
            
        Returns:
            str: 技术领域
        """
        # 常见技术领域及关键词映射
        tech_fields = {
            "前端开发": ["前端", "前端开发", "web前端", "javascript", "react", "vue", "angular", "html", "css"],
            "后端开发": ["后端", "后端开发", "java", "python", "golang", "php", "nodejs", "服务端"],
            "移动开发": ["移动", "移动开发", "android", "ios", "flutter", "react native", "小程序"],
            "人工智能": ["人工智能", "机器学习", "深度学习", "神经网络", "ai", "ml", "nlp", "计算机视觉"],
            "大数据": ["大数据", "hadoop", "spark", "flink", "数据分析", "数据挖掘", "数据科学"],
            "云计算": ["云计算", "云原生", "devops", "kubernetes", "docker", "微服务"],
            "物联网": ["物联网", "iot", "嵌入式", "单片机", "传感器网络"],
            "区块链": ["区块链", "智能合约", "加密货币", "分布式账本"],
            "安全": ["网络安全", "信息安全", "安全", "渗透测试", "密码学"],
            "游戏开发": ["游戏", "游戏开发", "unity", "unreal", "游戏引擎"]
        }
        
        query_lower = query.lower()
        
        # 尝试根据关键词匹配
        for field, keywords in tech_fields.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    return field
        
        # 默认返回
        return "通用技术"
    
    def _extract_time_constraint(self, query: str) -> Optional[str]:
        """从查询中提取时间约束
        
        Args:
            query: 查询文本
            
        Returns:
            Optional[str]: 时间约束
        """
        query_lower = query.lower()
        
        # 尝试匹配常见时间约束模式
        time_patterns = [
            ("一周", "一周"),
            ("两周", "两周"),
            ("1周", "一周"),
            ("2周", "两周"),
            ("一个月", "一个月"),
            ("1个月", "一个月"),
            ("三个月", "三个月"),
            ("3个月", "三个月"),
            ("半年", "半年"),
            ("一年", "一年"),
            ("1年", "一年")
        ]
        
        for pattern, constraint in time_patterns:
            if pattern in query_lower:
                return constraint
        
        # 默认无时间约束
        return None
    
    async def _analyzer(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """分析器
        
        Args:
            state: 工作流状态
            config: 运行配置
            
        Returns:
            WorkflowState: 更新后的状态
        """
        logger.info("分析器")
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 执行分析
            analysis_result = await self.analyzer_executor.execute(state.query)
            
            # 更新状态
            if "analyzer_results" not in state.results:
                state.results["analyzer_results"] = []
            
            state.results["analyzer_results"].append(analysis_result)
            state.context["analysis"] = analysis_result
            state.current_step += 1
            state.metadata["analyzer_time"] = time.time() - start_time
            
            logger.info("分析完成")
            return state
            
        except Exception as e:
            logger.error(f"分析器异常: {e}")
            state.error = f"分析失败: {str(e)}"
            return state
    
    async def _rag(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """RAG
        
        Args:
            state: 工作流状态
            config: 运行配置
            
        Returns:
            WorkflowState: 更新后的状态
        """
        logger.info("RAG")
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 获取当前步骤的配置
            current_step = state.plan[state.current_step]
            step_config = current_step.get("config", {})
            
            # 准备RAG输入
            rag_input = RAGExecutorInput(
                query=state.query,
                context=state.context,
                library_name=step_config.get("library_name"),
                library_id=step_config.get("library_id"),
                max_results=step_config.get("max_results", 5),
                use_web_search=step_config.get("use_web_search", False),
                use_context7=step_config.get("use_context7", False)
            )
            
            # 执行RAG
            rag_output = await self.rag_executor.execute(rag_input)
            
            # 更新状态
            state.results["rag_result"] = rag_output.dict()
            state.context["rag_answer"] = rag_output.answer
            state.context["rag_sources"] = rag_output.sources
            state.current_step += 1
            state.metadata["rag_time"] = time.time() - start_time
            
            logger.info("RAG完成")
            return state
            
        except Exception as e:
            logger.error(f"RAG异常: {e}")
            state.error = f"RAG失败: {str(e)}"
            return state
    
    async def _learning_path(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """学习路径生成器
        
        Args:
            state: 工作流状态
            config: 运行配置
            
        Returns:
            WorkflowState: 更新后的状态
        """
        logger.info("学习路径生成器")
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 获取当前步骤的配置
            current_step = state.plan[state.current_step]
            step_config = current_step.get("config", {})
            
            # 获取分析结果
            analysis_result = {}
            if "analysis" in state.context:
                analysis_result = state.context["analysis"]
            
            # 获取RAG结果
            rag_result = {}
            if "rag_result" in state.results:
                rag_result = state.results["rag_result"]
            
            # 合并分析结果和RAG结果
            combined_analysis = {"analysis": analysis_result, "rag": rag_result}
            
            # 准备学习路径生成输入
            learning_path_input = LearningPathGeneratorInput(
                analysis_result=combined_analysis,
                job_position=self._extract_job_position(state.query),
                tech_field=step_config.get("tech_field"),
                time_constraint=step_config.get("time_constraint"),
                focus_areas=self._extract_focus_areas(state.query)
            )
            
            # 生成学习路径
            learning_path_output = await self.learning_path_generator.generate(learning_path_input)
            
            # 更新状态
            state.results["learning_path_result"] = learning_path_output.dict()
            state.context["learning_report"] = learning_path_output.learning_report
            state.context["learning_paths"] = [path.dict() for path in learning_path_output.learning_paths]
            state.current_step += 1
            state.metadata["learning_path_time"] = time.time() - start_time
            
            logger.info("学习路径生成完成")
            return state
            
        except Exception as e:
            logger.error(f"学习路径生成器异常: {e}")
            state.error = f"学习路径生成失败: {str(e)}"
            return state
    
    def _extract_job_position(self, query: str) -> Optional[str]:
        """从查询中提取职位
        
        Args:
            query: 查询文本
            
        Returns:
            Optional[str]: 职位
        """
        # 常见职位列表
        positions = [
            "前端工程师", "后端工程师", "全栈工程师", "iOS开发工程师", "Android开发工程师",
            "机器学习工程师", "数据科学家", "算法工程师", "DevOps工程师", "测试工程师",
            "产品经理", "UI设计师", "UX设计师", "系统架构师", "网络工程师",
            "安全工程师", "数据分析师", "数据库管理员", "游戏开发工程师"
        ]
        
        # 查找职位
        for position in positions:
            if position in query:
                return position
        
        # 默认返回空
        return None
    
    def _extract_focus_areas(self, query: str) -> Optional[List[str]]:
        """从查询中提取重点领域
        
        Args:
            query: 查询文本
            
        Returns:
            Optional[List[str]]: 重点领域列表
        """
        # 简单实现，从查询中提取特定关键词
        focus_areas = []
        
        keywords = [
            "算法", "编程", "数据结构", "系统设计", "网络", "数据库", "前端", "后端",
            "框架", "工具", "测试", "部署", "性能", "安全", "架构", "设计模式",
            "沟通能力", "团队协作", "项目管理", "问题解决", "技术面试", "简历",
            "英语", "演讲", "写作"
        ]
        
        for keyword in keywords:
            if keyword in query:
                focus_areas.append(keyword)
        
        # 如果没有找到重点领域，返回None
        return focus_areas if focus_areas else None
    
    async def _generator(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """生成器
        
        Args:
            state: 工作流状态
            config: 运行配置
            
        Returns:
            WorkflowState: 更新后的状态
        """
        logger.info("生成器")
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 检查是否有学习路径结果
            has_learning_path = "learning_path_result" in state.results
            
            if has_learning_path:
                # 使用学习路径结果生成最终回答
                learning_path_result = state.results["learning_path_result"]
                learning_paths = learning_path_result.get("learning_paths", [])
                
                # 格式化学习路径
                formatted_paths = []
                for path_data in learning_paths:
                    formatted_path = {
                        "area": path_data.get("need", {}).get("area", ""),
                        "level": path_data.get("need", {}).get("level", ""),
                        "timeline": path_data.get("timeline", ""),
                        "milestones": path_data.get("milestones", []),
                        "resources": []
                    }
                    
                    # 格式化资源
                    for res in path_data.get("resources", []):
                        formatted_resource = {
                            "title": res.get("title", ""),
                            "source": res.get("source", ""),
                            "level": res.get("level", ""),
                            "description": res.get("description", ""),
                            "url": res.get("url", "")
                        }
                        formatted_path["resources"].append(formatted_resource)
                    
                    formatted_paths.append(formatted_path)
                
                # 创建回答
                answer = {
                    "type": "learning_path",
                    "paths": formatted_paths,
                    "report": learning_path_result.get("learning_report", {})
                }
                
            elif "rag_result" in state.results:
                # 使用RAG结果创建回答
                rag_result = state.results["rag_result"]
                answer = {
                    "type": "rag",
                    "content": rag_result.get("answer", ""),
                    "sources": rag_result.get("sources", [])
                }
            else:
                # 默认回答
                answer = {
                    "type": "default",
                    "content": "抱歉，我无法找到相关信息。"
                }
            
            # 更新状态
            state.results["generator_result"] = answer
            state.current_step += 1
            state.metadata["generator_time"] = time.time() - start_time
            
            logger.info("生成完成")
            return state
            
        except Exception as e:
            logger.error(f"生成器异常: {e}")
            state.error = f"生成失败: {str(e)}"
            return state
    
    async def _evaluator(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """评估器
        
        Args:
            state: 工作流状态
            config: 运行配置
            
        Returns:
            WorkflowState: 更新后的状态
        """
        logger.info("评估器")
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 简单实现，始终通过评估
            evaluation = {
                "score": 0.8,
                "feedback": "回答质量良好",
                "passed": True
            }
            
            # 更新状态
            state.results["evaluation"] = evaluation
            state.current_step += 1
            state.metadata["evaluator_time"] = time.time() - start_time
            
            logger.info("评估完成")
            return state
            
        except Exception as e:
            logger.error(f"评估器异常: {e}")
            state.error = f"评估失败: {str(e)}"
            return state
    
    async def _router(self, state: WorkflowState, config: Optional[RunnableConfig] = None) -> WorkflowState:
        """路由器
        
        Args:
            state: 工作流状态
            config: 运行配置
            
        Returns:
            WorkflowState: 更新后的状态
        """
        logger.info(f"路由器: 当前步骤 {state.current_step}/{len(state.plan)}")
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 更新状态
            state.metadata["router_time"] = time.time() - start_time
            
            return state
            
        except Exception as e:
            logger.error(f"路由器异常: {e}")
            state.error = f"路由失败: {str(e)}"
            return state
    
    def _route_next_step(self, state: WorkflowState) -> str:
        """路由下一步
        
        Args:
            state: 工作流状态
            
        Returns:
            str: 下一步的节点类型
        """
        # 如果有错误，结束工作流
        if state.error:
            logger.warning(f"工作流出错，结束: {state.error}")
            return END
        
        # 如果已完成所有步骤，结束工作流
        if state.current_step >= len(state.plan):
            logger.info("工作流完成所有步骤，结束")
            return END
        
        # 获取下一步
        next_step = state.plan[state.current_step]
        next_type = next_step["type"]
        
        logger.info(f"路由到下一步: {next_step['name']} ({next_type})")
        return next_type
    
    def _evaluate_result(self, state: WorkflowState) -> str:
        """评估结果
        
        Args:
            state: 工作流状态
            
        Returns:
            str: 下一步的节点类型
        """
        # 如果有错误，结束工作流
        if state.error:
            logger.warning(f"工作流出错，结束: {state.error}")
            return END
        
        # 获取评估结果
        evaluation = state.results.get("evaluation", {})
        passed = evaluation.get("passed", False)
        
        if passed:
            logger.info("评估通过，结束工作流")
            return END
        else:
            logger.info("评估未通过，返回路由器")
            return NodeType.ROUTER

def create_interview_agent_graph() -> StateGraph:
    """创建面试智能体工作流图
    
    Returns:
        工作流图
    """
    # 创建工作流图
    workflow = StateGraph(GraphState)
    
    # 添加节点
    workflow.add_node("task_parser", TaskParser())
    workflow.add_node("strategy_decider", StrategyDecider())
    workflow.add_node("task_planner", TaskPlanner())
    workflow.add_node("analyzer_executor", AnalyzerExecutor())
    workflow.add_node("result_integrator", ResultIntegrator())
    workflow.add_node("feedback_generator", FeedbackGenerator())
    
    # 定义边
    # 从任务解析到策略决策
    workflow.add_edge("task_parser", "strategy_decider")
    
    # 从策略决策到任务规划
    workflow.add_edge("strategy_decider", "task_planner")
    
    # 从任务规划到分析执行
    workflow.add_edge("task_planner", "analyzer_executor")
    
    # 分析执行可能循环执行多次，直到所有任务完成
    workflow.add_conditional_edges(
        "analyzer_executor",
        lambda state: state.next_node,
        {
            "analyzer_executor": "analyzer_executor",
            "result_integrator": "result_integrator",
        }
    )
    
    # 从结果整合到反馈生成
    workflow.add_edge("result_integrator", "feedback_generator")
    
    # 反馈生成是最后一个节点，工作流结束
    workflow.add_edge("feedback_generator", END)
    
    # 设置入口节点
    workflow.set_entry_point("task_parser")
    
    return workflow


def get_or_create_interview_agent_graph() -> StateGraph:
    """获取或创建面试智能体工作流图
    
    如果工作流图已经创建，则返回已有的图；否则创建新的图。
    这个函数可以用于缓存工作流图，避免重复创建。
    
    Returns:
        工作流图
    """
    # 在实际实现中，这里可能会使用缓存机制
    # 目前简单返回新创建的图
    return create_interview_agent_graph()


class Graph:
    def __init__(self, compiled_graph: StateGraph):
        self.compiled_graph = compiled_graph

    def run(self, state: GraphState) -> GraphState:
        logger.info(f"工作流图开始执行，初始状态: {state}")
        try:
            # 这里假设有主流程调用
            result_state = self.compiled_graph.run(state)
            logger.info(f"工作流图执行完成，最终状态: {result_state}")
            return result_state
        except Exception as e:
            logger.error(f"工作流图执行异常: {e}")
            raise