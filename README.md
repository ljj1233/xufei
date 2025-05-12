# 多模态面试评测智能体

基于FastAPI、PostgreSQL和Streamlit构建的多模态面试评测系统，通过AI技术对面试视频/音频进行全方位分析，提供专业评估和改进建议。

## 1. 项目概述

多模态面试评测智能体是一个综合性面试辅助系统，能够对用户上传的面试视频或音频进行多维度分析，包括语音表现（如清晰度、流畅度、语速、情感）、视觉表现（如面部表情、眼神接触，若提供视频）以及内容质量评估。系统通过AI技术自动生成评分和改进建议，帮助用户提升面试表现。

### 主要功能

- **面试文件上传**：支持多种格式的面试视频和音频文件上传。
- **多模态分析**：对语音、视觉（可选）和内容进行全方位分析。
- **AI驱动的评估**：利用讯飞开放平台的语音识别、语音评测和情感分析能力。
- **评分与反馈**：提供量化评分和具体改进建议。
- **可视化报告**：通过图表直观展示分析结果。
- **用户账户管理**：支持注册、登录和个人面试记录管理（当前版本简化，可后续扩展）。

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
│   │   ├── db/                 # 数据库相关 (例如: database.py, models.py - SQLAlchemy模型)
│   │   ├── models/             # Pydantic模型 (用于数据校验和序列化)
│   │   ├── services/           # 业务逻辑服务 (例如: xunfei_service.py, analysis_service.py)
│   │   ├── utils/              # 工具函数
│   │   └── main.py             # FastAPI应用入口
│   ├── requirements.txt        # 后端Python依赖
│   └── .env.example            # 后端环境变量示例 (指导用户创建.env)
├── frontend/                   # Streamlit前端应用
│   ├── Home.py                 # Streamlit应用首页
│   ├── pages/                  # 其他页面
│   │   ├── 01_上传面试.py
│   │   ├── 02_分析结果.py
│   │   └── 03_详细报告.py
│   ├── requirements.txt        # 前端Python依赖
│   └── .env.example            # 前端环境变量示例 (指导用户创建.env)
├── uploads/                    # (可选) 用户上传文件存储目录 (如果本地存储)
├── .env                        # (用户需自行创建) 项目根目录下的总环境变量文件或各应用下的.env文件
├── .gitignore
└── README.md                   # 本文件
```

## 3. 安装与部署

### 3.1 环境要求与准备

- **Python**: 3.8或更高版本。
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

1.  **完成安装与配置**: 确保后端和前端均已按上述步骤正确安装、配置 `.env` 文件并成功启动。
2.  **访问前端应用**: 打开浏览器，访问 `http://localhost:8501` (或Streamlit启动时指定的其他地址)。
3.  **上传面试**: 
    -   在前端界面找到“上传面试”或类似功能的页面。
    -   按提示填写面试信息（如标题）。
    -   选择你的面试视频或音频文件进行上传。
    -   提交后，系统后端将开始处理和分析文件。
4.  **查看分析结果**:
    -   分析完成后，你可以在“分析结果”或“详细报告”页面查看评估。
    -   报告将包含语音清晰度、流畅度、语速、情感状态等维度的评分和建议。

## 7. 注意事项与未来工作

-   **错误处理**: 当前项目可能需要进一步完善错误处理和用户反馈机制。
-   **安全性**: `SECRET_KEY` 务必保密且足够复杂。对于生产环境，考虑更严格的安全措施。
-   **扩展性**: 可以考虑引入任务队列 (如Celery) 处理耗时的分析任务，以提高API响应速度。
-   **视觉分析**: 当前README主要侧重语音，如需实现视觉分析，需集成相应模型和服务。

祝您使用愉快！如果您在部署或使用过程中遇到任何问题，请检查配置或查阅相关技术的官方文档。