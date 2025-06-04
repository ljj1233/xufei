# 面试智能体项目

基于LangGraph的面试辅导智能体系统，提供多模态分析和个性化辅导。

## 功能特点

- **多模态分析**：分析面试者的语音、视觉和内容表现
- **智能反馈**：提供针对性的面试改进建议
- **个性化辅导**：根据分析结果生成定制化学习路径
- **RAG知识增强**：利用混合检索技术提供准确的知识支持
- **异步API支持**：高效处理并发请求，提高响应速度
- **个性化学习路径**：基于ModelScope和网络搜索生成定制化学习计划

## 技术架构

- **LangGraph工作流**：基于有向图的任务编排和执行
- **混合检索系统**：结合向量检索和关键词检索的RAG系统
- **多模态分析**：语音、视觉和内容的综合分析
- **异步处理**：基于asyncio的异步API调用
- **外部知识集成**：支持Context7和WebSearch的知识检索
- **学习路径生成**：结合ModelScope和RAG的个性化学习规划

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

创建`.env`文件，配置必要的API密钥：

```
OPENAI_API_KEY=your_openai_api_key
XUNFEI_APP_ID=your_xunfei_app_id
XUNFEI_API_KEY=your_xunfei_api_key
XUNFEI_API_SECRET=your_xunfei_api_secret
```

### 运行示例

```bash
# 面试分析示例
python examples/interview_analysis.py

# 学习路径生成示例
python examples/learning_path_example.py
```

## 主要模块

### 核心模块

- **工作流引擎**：基于LangGraph的任务编排和执行
- **系统配置**：灵活的配置管理
- **状态管理**：工作流状态的追踪和更新

### 分析模块

- **语音分析**：评估语音清晰度、语速和情感
- **视觉分析**：分析面部表情、眼神接触等
- **内容分析**：评估回答的相关性、结构和深度

### 检索模块

- **混合检索器**：结合向量和关键词的混合检索
- **向量数据库**：支持FAISS和内存索引
- **文档处理器**：文本分块和元数据管理
- **Context7集成**：外部库文档检索

### 服务模块

- **OpenAI服务**：与OpenAI API的异步交互
- **讯飞服务**：与讯飞开放平台的异步交互
- **ModelScope服务**：与ModelScope的模型交互
- **WebSearch服务**：网络搜索功能

### 学习路径模块

- **学习需求分析**：基于面试结果分析学习需求
- **资源检索**：结合RAG和网络搜索查找学习资源
- **路径生成**：生成定制化学习时间线和里程碑
- **ModelScope集成**：使用ModelScope模型生成学习报告

## 学习路径生成器

学习路径生成器基于面试分析结果，生成个性化的学习计划和资源推荐。整个流程包括：

1. **需求分析**：使用ModelScope模型分析面试结果，生成学习需求报告
2. **资源检索**：结合RAG系统和网络搜索查找相关学习资源
3. **学习规划**：为每个需求领域创建学习路径，包括时间线和里程碑
4. **资源推荐**：推荐针对性的学习资源，包括文章、课程、视频等

### 示例用法

```python
from xufei.agent.src.nodes.executors.learning_path_generator import (
    LearningPathGenerator, 
    LearningPathGeneratorInput
)

# 创建学习路径生成器
generator = LearningPathGenerator()

# 准备输入数据
input_data = LearningPathGeneratorInput(
    analysis_result=analysis_result,
    job_position="后端工程师",
    tech_field="后端开发",
    time_constraint="三个月",
    focus_areas=["系统设计", "算法", "数据库"]
)

# 生成学习路径
output = await generator.generate(input_data)

# 获取学习需求报告
learning_report = output.learning_report

# 获取学习路径
learning_paths = output.learning_paths
```

## 项目结构

```
agent/
├── src/
│   ├── analyzers/         # 分析器模块
│   │   ├── content/       # 内容分析
│   │   ├── speech/        # 语音分析
│   │   └── visual/        # 视觉分析
│   ├── core/              # 核心模块
│   │   ├── agent/         # 智能体定义
│   │   ├── system/        # 系统功能
│   │   └── workflow/      # 工作流定义
│   ├── nodes/             # 工作流节点
│   │   └── executors/     # 执行器
│   │       └── learning_path_generator.py  # 学习路径生成器
│   ├── retrieval/         # 检索模块
│   │   ├── vector_db.py   # 向量数据库
│   │   └── retriever.py   # 检索器
│   ├── services/          # 服务模块
│   │   ├── openai_service.py     # OpenAI服务
│   │   ├── xunfei_service.py     # 讯飞服务
│   │   ├── websearch_service.py  # 网络搜索服务
│   │   └── modelscope_service.py # ModelScope服务
│   └── utils/             # 工具模块
├── examples/              # 示例代码
│   ├── interview_analysis.py     # 面试分析示例
│   └── learning_path_example.py  # 学习路径生成示例
├── tests/                 # 测试代码
├── requirements.txt       # 依赖列表
└── README.md              # 项目说明
```

## 贡献指南

欢迎贡献代码、报告问题或提出建议。请遵循以下步骤：

1. Fork本仓库
2. 创建特性分支：`git checkout -b feature/your-feature-name`
3. 提交更改：`git commit -m 'Add some feature'`
4. 推送到分支：`git push origin feature/your-feature-name`
5. 提交Pull Request

## 许可证

本项目采用MIT许可证。详见[LICENSE](LICENSE)文件。


