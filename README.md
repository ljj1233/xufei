# 多模态面试评测智能体

基于FastAPI、PostgreSQL和Streamlit构建的多模态面试评测系统，通过AI技术对面试视频/音频进行全方位分析，提供专业评估和改进建议。

## 1. 项目概述

多模态面试评测智能体是一个综合性面试辅助系统，能够对用户上传的面试视频或音频进行多维度分析，包括语音表现（如清晰度、流畅度、语速、情感）、视觉表现（如面部表情、眼神接触，若提供视频）以及内容质量评估。系统通过AI技术自动生成评分和改进建议，帮助用户提升面试表现。

### 主要功能

- **场景覆盖**：支持人工智能、大数据、物联网、智能系统等技术领域的典型岗位面试场景，包括技术岗、运维测试岗、产品岗等。
- **面试文件上传**：支持多种格式的面试视频和音频文件上传。
- **多模态分析**：
  - 语音分析：语言逻辑、情感语调、清晰度、语速等
  - 视觉分析：微表情识别、眼神接触、肢体语言等
  - 内容分析：专业知识水平、技能匹配度、STAR结构评估等
- **核心能力评估**：
  - 专业知识水平
  - 技能匹配度
  - 语言表达能力
  - 逻辑思维能力
  - 创新能力
  - 应变抗压能力
- **AI驱动的评估**：利用讯飞开放平台的语音识别、语音评测和情感分析能力。
- **智能反馈系统**：
  - 量化评分和具体改进建议
  - 能力雷达图可视化
  - 关键问题定位（如回答缺乏STAR结构、眼神交流不足等）
  - 针对性改进建议
- **用户账户管理**：支持注册、登录和个人面试记录管理。

## 2. 系统架构

### 整体架构

系统采用前后端分离架构：

- **前端**：基于Streamlit构建的交互式Web界面，负责用户交互和结果展示。
- **后端**：基于FastAPI的RESTful API服务，负责业务逻辑处理、数据存储和与AI服务交互。
- **数据库**：PostgreSQL关系型数据库，用于存储用户信息和面试分析数据。
- **AI服务**：集成讯飞开放平台的语音相关API。

### 目录结构

```
多模态面试智能体/
├── backend/                     # FastAPI后端应用
│   ├── app/                    # 应用核心代码
│   │   ├── api/                # API路由定义
│   │   │   └── api_v1/
│   │   │       ├── endpoints/  # 各模块API端点 (例如: interviews.py, users.py, analysis.py)
│   │   │       └── api.py      # API路由聚合
│   │   ├── core/               # 核心配置 (例如: config.py, xunfei_config.py)
│   │   ├── db/                 # 数据库相关
│   │   │   ├── database.py     # 数据库连接
│   │   │   ├── base.py         # 基础类
│   │   │   ├── models.py       # SQLAlchemy数据库模型
│   │   │   └── job_position.py # 职位相关模型
│   │   ├── models/             # Pydantic模型 (用于数据校验和序列化)
│   │   │   ├── __init__.py     # 模型导入管理
│   │   │   ├── schemas.py      # 数据验证和序列化模型
│   │   │   ├── user.py         # 用户模型
│   │   │   ├── interview.py    # 面试模型
│   │   │   ├── analysis.py     # 分析模型
│   │   │   └── job_position.py # 职位模型
│   │   ├── services/           # 业务逻辑服务 (例如: xunfei_service.py, analysis_service.py)
│   │   ├── utils/              # 工具函数
│   │   └── main.py             # FastAPI应用入口
│   ├── tests/                  # 测试代码
│   │   ├── test_api.py         # API测试
│   │   ├── test_services.py    # 服务测试
│   │   ├── test_db.py          # 数据库测试
│   │   └── test_data/          # 测试数据
│   ├── requirements.txt        # 后端Python依赖
│   ├── .env.example            # 后端环境变量示例 (指导用户创建.env)
│   └── README.md               # 后端说明文档
├── frontend/               # Vue 3前端应用
│   ├── src/                    # 源代码
│   │   ├── assets/             # 资源文件（CSS、图片等）
│   │   ├── components/         # 可复用组件
│   │   ├── router/             # 路由配置
│   │   ├── stores/             # Pinia状态管理
│   │   ├── views/              # 页面组件
│   │   ├── App.vue             # 根组件
│   │   └── main.js             # 入口文件
│   ├── tests/                  # 测试代码
│   │   ├── unit/               # 单元测试
│   │   └── e2e/                # 端到端测试
│   ├── index.html              # HTML模板
│   ├── package.json            # 项目依赖
│   ├── vite.config.js          # Vite配置
│   ├── .env                    # 前端环境变量
│   └── README.md               # 前端说明文档
├── uploads/                    # (可选) 用户上传文件存储目录 (如果本地存储)
├── .env                        # (用户需自行创建) 项目根目录下的总环境变量文件
├── .gitignore
└── README.md                   # 本文件
```

## 3. 代码结构说明

### 3.1 模型导入结构

为避免循环导入问题，项目采用了以下导入策略：

- **数据库模型**：在`app/db/`目录下定义SQLAlchemy数据库模型
- **Pydantic模型**：在`app/models/`目录下定义用于API请求和响应的Pydantic模型
- **导入顺序**：
  - 先导入基础枚举类型（如`TechField`、`PositionType`）
  - 然后导入数据模型（如`User`、`JobPosition`、`Interview`、`Analysis`）
  - 最后导入schemas模型
- **前向引用**：使用`ForwardRef`处理循环引用关系
- **命名区分**：在API端点中，使用`DBUser`、`DBInterview`等别名区分数据库模型和Pydantic模型

### 3.1.1 API响应模型说明

在FastAPI中，我们使用Pydantic模型作为API的响应模型（response_model），而不是直接使用SQLAlchemy数据库模型。这样做有以下几个重要原因：

1. **数据验证和序列化**
   - Pydantic模型可以自动验证响应数据的类型和格式
   - 确保返回给客户端的数据符合预定义的结构
   - 自动处理数据的序列化，包括日期时间、枚举等特殊类型

2. **安全性**
   - 可以控制哪些字段暴露给API
   - 避免意外暴露敏感数据（如密码哈希）
   - 可以添加额外的验证规则

3. **文档生成**
   - FastAPI可以根据Pydantic模型自动生成OpenAPI（Swagger）文档
   - 清晰展示API的请求和响应结构

4. **数据转换**
   - 可以在返回数据前进行必要的转换和格式化
   - 支持别名、计算字段等高级特性

示例：
```python
# 在app/models/schemas.py中定义Pydantic模型
class JobPosition(BaseModel):
    id: int
    title: str
    tech_field: TechField
    position_type: PositionType
    required_skills: List[str]
    job_description: str
    evaluation_criteria: Optional[str] = None

# 在API端点中使用Pydantic模型作为响应模型
@router.get("/positions/{id}", response_model=schemas.JobPosition)
def get_position(id: int):
    db_position = db.query(JobPositionSchema).get(id)
    return db_position  # FastAPI会自动将SQLAlchemy模型转换为Pydantic模型
```

### 3.2 API端点结构

- **用户API**：用户注册、登录、个人信息管理
- **面试API**：面试文件上传、面试记录管理
- **分析API**：面试分析请求、分析结果获取
- **职位API**：职位信息管理

## 4. 安装与部署

### 4.1 环境要求与准备

- **Python**: 3.8或更高版本。
- **Node.js**: 16.0或更高版本（用于前端开发）。
- **npm**: 7.0或更高版本（用于前端包管理）。
- **PostgreSQL**: 12或更高版本。请确保已安装并运行PostgreSQL服务。
- **FFmpeg**: (可选，但推荐) 用于音视频处理。请确保已安装并将其添加到系统PATH环境变量中。
- **讯飞开放平台账户及API密钥**: 你需要注册讯飞开放平台账户，并创建应用以获取 `APPID`, `APIKey`, 和 `APISecret` 用于语音识别、语音评测和情感分析服务。
    1. 访问 [讯飞开放平台](https://www.xfyun.cn/) 并注册账户。
    2. 登录后，进入控制台，创建新应用。
    3. 在应用中添加需要的服务：语音听写（用于识别）、语音评测（ISE）、情感分析等。
    4. 获取对应服务的 `APPID`, `APIKey`, 和 `APISecret`。

### 3.2. 环境变量配置 (`.env` 文件)

在项目**根目录**下创建一个名为 `.env` 的文件。这是最关键的一步，你需要将从讯飞开放平台获取的凭证和你的数据库配置填入此文件。

**`.env` 文件内容示例:**

```env
# PostgreSQL数据库配置
POSTGRES_SERVER=localhost
POSTGRES_USER=your_db_user         # 替换为你的PostgreSQL用户名
POSTGRES_PASSWORD=your_db_password   # 替换为你的PostgreSQL密码
POSTGRES_DB=interview_analysis_db  # 替换为你的数据库名称
POSTGRES_PORT=5432                 # PostgreSQL默认端口

# FastAPI后端配置
SECRET_KEY=a_very_strong_and_unique_secret_key # 用于JWT令牌签名等，请生成一个随机强密钥

# 讯飞API配置 (从讯飞开放平台获取)
XUNFEI_APPID=your_xunfei_appid
XUNFEI_API_KEY=your_xunfei_api_key
XUNFEI_API_SECRET=your_xunfei_api_secret

# 讯飞服务URL (通常不需要修改，除非讯飞官方更新)
XUNFEI_ISE_URL=https://api.xfyun.cn/v1/service/v1/ise
XUNFEI_IAT_URL=https://api.xfyun.cn/v1/service/v1/iat
XUNFEI_EMOTION_URL=https://api.xfyun.cn/v1/service/v1/emotion

# 前端连接后端的API地址
# 注意: 如果前端和后端在同一台机器上运行，通常是localhost。如果分开部署，请修改为后端可访问的地址。
API_URL=http://localhost:8000/api/v1 
```

**重要提示:**
- 将上述示例中的 `your_...` 占位符替换为你的实际配置。
- **切勿将包含真实密钥的 `.env` 文件提交到公共代码仓库 (如GitHub)。** 已在 `.gitignore` 文件中包含 `.env` 以防止意外提交。

### 3.3. 后端部署 (FastAPI)

1.  **进入后端目录**:
    ```bash
    cd backend
    ```

2.  **创建并激活虚拟环境** (推荐):
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    # source venv/bin/activate
    ```

3.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **数据库迁移** (如果使用Alembic等工具进行数据库版本控制，请执行相应命令。对于初次运行，确保数据库已创建)。
    *本项目示例中可能直接通过SQLAlchemy在应用启动时创建表，请检查 `backend/app/db/database.py` 或 `main.py` 中的相关逻辑。*

5.  **启动后端服务**:
    ```bash
    cd app  # 进入app目录以正确解析相对导入
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```
    服务将在 `http://localhost:8000` 启动。

### 3.4. 前端部署 (Streamlit)

1.  **进入前端目录** (从项目根目录):
    ```bash
    cd frontend
    ```

2.  **创建并激活虚拟环境** (推荐，如果尚未为后端创建或希望独立环境):
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    # source venv/bin/activate
    ```

3.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **启动前端服务**:
    ```bash
    streamlit run Home.py
    ```
    Streamlit应用通常会自动在浏览器中打开，默认地址为 `http://localhost:8501`。

## 4. 功能模块简介

### 4.1 后端 (`backend/app`)

-   **`main.py`**: FastAPI应用的入口点，初始化应用，挂载API路由。
-   **`api/`**: 定义API端点。
    -   `endpoints/interviews.py`: 处理面试相关的操作（上传、列表、详情）。
    -   `endpoints/analysis.py`: 处理面试分析请求。
-   **`core/config.py`**: 应用的基础配置，如数据库连接字符串、密钥等，通过Pydantic从 `.env` 文件加载。
-   **`core/xunfei_config.py`**: 专门用于加载讯飞API相关的配置。
-   **`db/database.py`**: 设置数据库连接 (SQLAlchemy)。
-   **`db/models.py`**: 定义数据库表结构 (SQLAlchemy ORM模型)。
-   **`models/schemas.py`**: 定义Pydantic模型，用于API请求/响应的数据验证和序列化。
-   **`services/xunfei_service.py`**: 封装与讯飞API的交互逻辑，包括鉴权、请求发送和结果解析。
    -   `speech_recognition()`: 语音识别。
    -   `speech_assessment()`: 语音评测。
    -   `emotion_analysis()`: 情感分析。
-   **`services/analysis_service.py`** (假设存在): 协调各个分析步骤，整合结果。

### 4.2 前端 (`frontend/`)

-   **`Home.py`**: 应用的主页面或导航页面。
-   **`pages/`**: Streamlit的多页面应用结构。
    -   `01_上传面试.py`: 用户上传面试音视频文件的界面。
    -   `02_分析结果.py`: 展示历史面试分析结果列表的界面。
    -   `03_详细报告.py`: 展示单个面试的详细多模态分析报告。

## 5. API接口文档 (后端)

当后端服务成功启动后，您可以在浏览器中访问 `http://localhost:8000/docs` 来查看由FastAPI自动生成的Swagger UI交互式API文档，或者访问 `http://localhost:8000/redoc` 查看ReDoc文档。

主要API接口示例 (具体请参照 `/docs`):

-   **用户认证 (若实现)**
    -   `POST /api/v1/users/register`
    -   `POST /api/v1/users/login`
-   **面试管理**
    -   `POST /api/v1/interviews/upload/`: 上传面试文件并触发分析。
    -   `GET /api/v1/interviews/`: 获取用户的所有面试记录。
    -   `GET /api/v1/interviews/{interview_id}`: 获取特定面试的详细信息和分析结果。

## 6. 使用指南

### 6.1 启动服务

1. **启动后端服务**:

```bash
# 进入后端目录
cd backend
# 激活虚拟环境（如果有）
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
# 进入app目录
cd app
# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **启动前端服务**:

```bash
# 进入前端目录
cd frontend-vue
# 安装依赖（如果尚未安装）
npm install
# 启动开发服务器
npm run dev
```

### 6.2 运行测试

1. **运行后端测试**:

```bash
# 进入后端目录
cd backend
# 运行所有测试
pytest
# 运行特定测试文件
pytest tests/test_api.py
# 生成测试覆盖率报告
pytest --cov=app tests/
```

2. **运行前端测试**:

```bash
# 进入前端目录
cd frontend-vue
# 运行单元测试
npm run test:unit
# 运行端到端测试（如果配置了）
npm run test:e2e
```

### 6.3 使用应用

1. **完成安装与配置**: 确保后端和前端均已按上述步骤正确安装、配置 `.env` 文件并成功启动。
2. **访问前端应用**: 打开浏览器，访问 `http://localhost:5173` (Vue前端的默认地址)。
3. **上传面试**: 
   - 登录系统（如果尚未登录）。
   - 在导航菜单中点击"上传面试"。
   - 按提示填写面试信息（标题、描述、技术领域、岗位类型等）。
   - 选择你的面试视频或音频文件进行上传。
   - 点击"提交"按钮，系统后端将开始处理和分析文件。
4. **查看分析结果**:
   - 分析完成后，系统会自动跳转到结果页面，或者你可以在"分析结果"页面查看所有面试记录。
   - 点击特定面试记录查看详细报告。
   - 报告将包含语音清晰度、流畅度、语速、情感状态等维度的评分和建议，以及能力雷达图和改进建议。

## 7. 注意事项与未来工作

-   **错误处理**: 当前项目可能需要进一步完善错误处理和用户反馈机制。
-   **安全性**: `SECRET_KEY` 务必保密且足够复杂。对于生产环境，考虑更严格的安全措施。
-   **扩展性**: 可以考虑引入任务队列 (如Celery) 处理耗时的分析任务，以提高API响应速度。
-   **视觉分析**: 当前README主要侧重语音，如需实现视觉分析，需集成相应模型和服务。

祝您使用愉快！如果您在部署或使用过程中遇到任何问题，请检查配置或查阅相关技术的官方文档。