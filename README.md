# 多模态面试评测智能体

本项目是一个基于AI的多模态面试评测系统，支持音视频面试分析，提供专业的能力评估与改进建议。系统采用前后端分离架构，后端基于FastAPI，前端基于Vue 3 + Element Plus，数据库统一为MySQL。

## 1. 项目结构

```
多模态面试智能体/
├── backend/      # FastAPI后端服务
├── frontend/     # Vue 3前端应用
├── agent/        # AI分析与能力评测核心
├── uploads/      # 用户上传文件存储（可选）
├── .env          # 根环境变量（需自行创建）
├── README.md     # 总体说明文档
```

### 1.1 后端模块(backend/)

后端模块基于FastAPI框架，负责提供API接口、处理业务逻辑、管理数据库操作，以及与智能体模块的交互。

```
backend/
├── app/                 # 主应用目录
│   ├── api/             # API路由定义
│   │   ├── v1/          # API V1版本接口
│   │   └── api_v1/      # API V1路由注册
│   ├── apis/            # 扩展API接口
│   ├── core/            # 核心配置
│   ├── db/              # 数据库相关
│   ├── models/          # 数据库模型
│   ├── schemas/         # 请求/响应模型(Pydantic)
│   ├── services/        # 业务服务层
│   │   ├── ai_agent_service.py         # 智能体服务(与agent模块交互)
│   │   ├── interview_session_service.py # 面试会话服务
│   │   ├── analysis_service.py         # 分析服务
│   │   ├── content_analyzer.py         # 内容分析器
│   │   ├── speech_analyzer.py          # 语音分析器
│   │   ├── feedback_generator.py       # 反馈生成器
│   │   └── learning_recommendation/    # 学习推荐服务
│   └── utils/           # 工具函数
├── tests/               # 单元测试
├── uploads/             # 上传文件目录
├── requirements.txt     # 依赖包列表
├── run_tests.py         # 测试运行脚本
├── README.md            # 后端模块说明
└── QUICK_START.md       # 快速启动指南
```

### 1.2 智能体模块(agent/)

智能体模块是系统的分析核心，负责处理多模态数据(文本、音频、视频)，进行分析推理，并输出评估结果。

```
agent/
├── src/                 # 源代码目录
│   ├── analyzers/       # 分析器组件
│   │   ├── content_analyzer.py   # 内容分析器
│   │   ├── speech_analyzer.py    # 语音分析器
│   │   └── visual_analyzer.py    # 视觉分析器
│   ├── core/            # 核心功能
│   │   ├── agent/       # 智能体核心
│   │   └── workflow/    # 工作流引擎
│   ├── nodes/           # 处理节点
│   │   ├── strategy_decider.py   # 策略决策器
│   │   ├── content_node.py       # 内容处理节点
│   │   ├── speech_node.py        # 语音处理节点
│   │   └── visual_node.py        # 视觉处理节点
│   ├── services/        # 服务组件
│   ├── scenarios/       # 场景定义
│   ├── retrieval/       # 检索相关
│   ├── utils/           # 工具函数
│   ├── system/          # 系统配置
│   └── learning/        # 学习路径生成
├── tests/               # 测试目录
│   ├── unit/            # 单元测试
│   └── integration/     # 集成测试
├── data/                # 数据资源
├── docs/                # 文档
├── requirements.txt     # 依赖包列表
└── README.md            # 智能体模块说明
```

### 1.3 前端模块(frontend/)

前端模块基于Vue 3和Element Plus，提供用户界面，处理用户交互，并与后端通信。

```
frontend/
├── public/              # 静态资源
├── src/                 # 源代码
│   ├── assets/          # 资源文件
│   ├── components/      # 组件
│   ├── views/           # 页面视图
│   ├── router/          # 路由配置
│   ├── store/           # 状态管理
│   ├── api/             # API调用
│   └── utils/           # 工具函数
├── tests/               # 测试
├── package.json         # 依赖配置
└── README.md            # 前端说明
```

## 2. 接口设计与一致性

### 2.1 面试模式定义

系统支持两种面试模式：

1. **快速面试(quick)**: 仅使用内容分析和语音分析，适合快速评估和练习。
2. **完整面试(full)**: 使用内容分析、语音分析和视觉分析的完整评估，提供更全面的反馈。

### 2.2 智能体与后端接口

智能体模块提供策略决策功能，通过`StrategyDecider`类根据`mode`参数选择分析策略：
- `mode="quick"`: 使用content_analysis和speech_analysis
- `mode="full"`: 使用content_analysis、speech_analysis和visual_analysis

后端通过`ai_agent_service.py`与智能体交互，确保正确传递面试模式参数：
```python
async def analyze_question_answer(
    self,
    session_id: int,
    question_id: int,
    answer_text: str,
    audio_features: Optional[Dict[str, Any]] = None,
    visual_features: Optional[Dict[str, Any]] = None,
    mode: str = "full"  # 面试模式参数
) -> Optional[Dict[str, Any]]:
    # ...
```

### 2.3 数据模型

面试会话模型(`InterviewSession`)支持面试模式选择：
```python
class InterviewSession(Base):
    # ...
    mode = Column(Enum(InterviewMode), default=InterviewMode.FULL)  # 面试模式: quick, full
    # ...
```

请求模型(`InterviewSessionCreate`)包含模式选择参数：
```python
class InterviewSessionCreate(BaseModel):
    # ...
    mode: InterviewModeEnum = Field(InterviewModeEnum.FULL, 
                                  description="面试模式，'quick'为快速面试，'full'为完整面试")
```

## 3. 主要功能亮点

- 支持多领域典型岗位面试场景（技术、产品、运维等）
- 支持音频/视频文件上传与多模态分析（语音、视觉、内容）
- AI驱动的能力评估与改进建议
- 能力雷达图、评分、问题定位与个性化反馈
- 用户注册、登录、面试记录管理
- 支持快速面试和完整面试两种模式

## 4. 快速上手

### 4.1 环境准备
- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- 讯飞开放平台API密钥

### 4.2 后端启动
详见 [backend/README.md](backend/README.md)

### 4.3 前端启动
详见 [frontend/README.md](frontend/README.md)

### 4.4 数据库配置
- 已统一为MySQL，详见 `backend/.env.example` 和 `backend/MYSQL_MIGRATION_GUIDE.md`

### 4.5 AI服务配置
- 需注册讯飞开放平台，获取API密钥，填入`.env`文件

## 5. 贡献与开发

- 欢迎提交PR、Issue，详见各子模块README
- 代码风格与分支管理请参考 [CONTRIBUTING.md](CONTRIBUTING.md)（如有）

## 6. 联系与支持

如有问题请在Issue区留言，或联系项目维护者。

---

> **各子模块详细说明请见对应目录下的README.md。**

# 个性化学习推荐模块

这是多模态面试评测智能体的个性化学习推荐模块，基于面试评测结果和职位需求，为面试者提供个性化的学习资源推荐。

## 功能特点

- **职位-技能映射**：维护不同职位所需的核心技能及其重要性权重
- **评测分析**：分析面试评测结果，识别面试者的优势和需要提升的能力
- **个性化推荐**：根据面试者的职位、评测结果和个人偏好，生成个性化的学习推荐
- **多元化资源**：提供文章、视频、课程、项目等多种类型的学习资源
- **短中长期规划**：按优先级将学习目标分为短期、中期和长期，形成完整的学习路径

## 技术实现

- **RAG检索增强生成**：结合向量检索和大语言模型，提供高质量的学习资源推荐
- **混合检索策略**：综合语义相似度、职位要求匹配度和用户弱项进行资源排序
- **多样性优化**：确保推荐资源的类型和技能覆盖面多元化，避免信息冗余
- **结构化日志系统**：支持多级日志记录和请求跟踪，便于监控和问题排查

## 模块结构

```
backend/app/services/learning_recommendation/
├── __init__.py             # 模块初始化
├── logging_config.py       # 日志配置
├── models.py               # 数据模型
├── job_skill_mapping.py    # 职位-技能映射
├── assessment_analysis.py  # 评测结果分析
├── vector_utils.py         # 向量处理工具
├── resource_management.py  # 资源管理服务
├── rag_engine.py           # RAG检索引擎
└── recommendation.py       # 推荐生成服务
```

## API接口

- `POST /api/learning-recommendation/learning-path`：生成个性化学习路径
- `GET /api/learning-recommendation/resource-recommendations`：获取学习资源推荐
- `GET /api/learning-recommendation/job-positions`：获取支持的职位列表
- `GET /api/learning-recommendation/job-skills/{job_id}`：获取职位所需技能
- `POST /api/learning-recommendation/job-skill-mapping`：更新职位技能映射
- `DELETE /api/learning-recommendation/job-position/{job_id}`：删除职位

## 环境设置

1. 克隆项目并安装依赖：

```bash
git clone <仓库URL>
cd <项目目录>
pip install -r requirements.txt
```

2. 设置环境变量：

```bash
export OPENAI_API_KEY=<你的OpenAI API密钥>
```

3. 运行应用：

```bash
python -m app.main
```

服务将在 http://localhost:8000 启动，可以通过访问 http://localhost:8000/docs 查看API文档。

## 数据结构

### 职位-技能映射

```json
{
  "software_developer": {
    "title": "软件开发工程师",
    "description": "负责设计、开发和维护软件系统",
    "skills": {
      "programming": {
        "weight": 0.8,
        "name": "编程技能",
        "description": "掌握一种或多种编程语言"
      },
      "algorithms": {
        "weight": 0.7,
        "name": "算法与数据结构",
        "description": "理解和应用常见的算法和数据结构"
      }
    }
  }
}
```

### 学习路径

```json
{
  "id": "path_12345678",
  "user_id": "user123",
  "job_position": {
    "id": "software_developer",
    "title": "软件开发工程师"
  },
  "created_at": "2023-06-01T12:00:00",
  "goals": {
    "short": [
      {
        "skill": "programming",
        "name": "编程技能",
        "priority_score": 0.9,
        "resources": [...]
      }
    ],
    "mid": [...],
    "long": [...]
  },
  "summary": "为提升您的软件开发能力，我们为您制定了包含3个短期学习目标，2个中期学习目标的计划..."
}
```

## 贡献

欢迎提交问题报告或功能建议通过Issue，也欢迎提交Pull Request。

## 许可

[许可证名称] - 详情请参阅LICENSE文件。