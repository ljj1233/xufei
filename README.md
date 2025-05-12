# 多模态面试评测智能体

基于FastAPI、PostgreSQL和Streamlit构建的多模态面试评测系统，通过AI技术对面试视频/音频进行全方位分析，提供专业评估和改进建议。

## 1. 项目概述

多模态面试评测智能体是一个综合性面试辅助系统，能够对用户上传的面试视频或音频进行多维度分析，包括语音表现、视觉表现（如面部表情、眼神接触）以及内容质量评估。系统通过AI技术自动生成评分和改进建议，帮助用户提升面试表现。

### 主要功能

- **面试视频/音频上传**：支持多种格式的面试视频和音频文件上传
- **多模态分析**：对语音、视觉和内容进行全方位分析
- **评分与反馈**：提供量化评分和具体改进建议
- **可视化报告**：通过图表直观展示分析结果
- **用户账户管理**：支持注册、登录和个人面试记录管理

## 2. 系统架构

### 整体架构

系统采用前后端分离架构：

- **前端**：基于Streamlit构建的交互式Web界面
- **后端**：基于FastAPI的RESTful API服务
- **数据库**：PostgreSQL关系型数据库
- **AI模型**：用于语音、视觉和文本分析的多模态AI模型

### 目录结构

```
├── backend/             # FastAPI后端
│   ├── app/            # 应用代码
│   │   ├── api/        # API路由
│   │   │   └── api_v1/ # API v1版本
│   │   │       ├── endpoints/ # 各模块API端点
│   │   │       └── api.py     # API路由注册
│   │   ├── core/       # 核心配置
│   │   │   └── config.py # 应用配置
│   │   ├── db/         # 数据库相关
│   │   │   ├── database.py # 数据库连接
│   │   │   └── models.py   # 数据库模型
│   │   ├── models/     # Pydantic模型
│   │   │   └── schemas.py  # 数据验证模式
│   │   ├── services/   # 业务逻辑
│   │   │   └── analysis.py # 分析服务
│   │   ├── utils/      # 工具函数
│   │   │   └── auth.py     # 认证工具
│   │   └── main.py     # 应用入口
│   └── requirements.txt # 后端依赖
├── frontend/           # Streamlit前端
│   ├── Home.py         # 首页
│   ├── pages/          # 页面组件
│   │   ├── 01_上传面试.py  # 上传面试页面
│   │   ├── 02_分析结果.py  # 分析结果列表页面
│   │   └── 03_详细报告.py  # 详细分析报告页面
│   └── requirements.txt # 前端依赖
└── uploads/            # 上传文件存储目录
```

## 3. 功能模块说明

### 3.1 用户模块

- **注册**：用户可以通过邮箱和用户名注册新账户
- **登录**：已注册用户可以登录系统
- **个人信息**：查看和管理个人账户信息

### 3.2 面试上传模块

- **文件上传**：支持MP4、AVI、MOV视频格式和MP3、WAV音频格式
- **基本信息**：设置面试标题和描述
- **文件验证**：检查文件类型和大小（最大100MB）

### 3.3 分析模块

#### 语音分析

- **语音清晰度**：评估发音清晰程度和语音质量
- **语速评估**：分析语速是否适中，节奏是否自然
- **情感分析**：识别语音中的情感特征（如自信、紧张等）

#### 视觉分析（仅视频）

- **面部表情**：分析面部表情的多样性和适当性
- **眼神接触**：评估与面试官的眼神接触程度
- **肢体语言**：分析肢体动作的自信度和开放性

#### 内容分析

- **内容相关性**：评估回答与问题的相关程度
- **结构清晰度**：分析回答的逻辑结构
- **关键点提取**：识别回答中的关键信息点

#### 综合评估

- **综合评分**：基于多维度分析给出总体评分
- **优势分析**：指出面试表现的优势
- **劣势分析**：指出需要改进的方面
- **改进建议**：提供具体的改进建议

### 3.4 报告展示模块

- **面试列表**：展示用户的所有面试记录
- **详细报告**：通过图表和文字展示分析结果
- **数据可视化**：使用雷达图、饼图等直观展示各项指标

## 4. 安装与部署

### 4.1 环境要求

- Python 3.8+
- PostgreSQL 12+
- FFmpeg（用于音视频处理）

### 4.2 后端部署

1. 克隆项目并进入后端目录

```bash
cd backend
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量（创建.env文件）

```
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=interview_analysis
POSTGRES_PORT=5432
SECRET_KEY=your_secret_key
```

4. 启动后端服务

```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4.3 前端部署

1. 进入前端目录

```bash
cd frontend
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量（创建.env文件）

```
API_URL=http://localhost:8000/api/v1
```

4. 启动前端服务

```bash
streamlit run Home.py
```

5. 在浏览器中访问 http://localhost:8501

## 5. API接口文档

系统启动后，可以通过访问 http://localhost:8000/docs 查看完整的API文档。以下是主要API接口：

### 5.1 用户接口

- `POST /api/v1/users/register` - 用户注册
- `POST /api/v1/users/login` - 用户登录
- `GET /api/v1/users/me` - 获取当前用户信息

### 5.2 面试接口

- `POST /api/v1/interviews/upload/` - 上传面试文件
- `GET /api/v1/interviews/` - 获取用户面试列表
- `GET /api/v1/interviews/{interview_id}` - 获取面试详情
- `DELETE /api/v1/interviews/{interview_id}` - 删除面试记录

### 5.3 分析接口

- `POST /api/v1/analysis/{interview_id}` - 创建面试分析
- `GET /api/v1/analysis/{interview_id}` - 获取面试分析结果

## 6. 使用指南

### 6.1 注册与登录

1. 访问系统首页，在侧边栏选择"注册"选项卡
2. 填写用户名、邮箱和密码，点击"注册"按钮
3. 注册成功后，切换到"登录"选项卡
4. 输入用户名和密码，点击"登录"按钮

### 6.2 上传面试

1. 登录后，点击首页的"上传面试"按钮
2. 填写面试标题和描述（可选）
3. 上传面试视频或音频文件（支持MP4、AVI、MOV、MP3、WAV格式）
4. 点击"上传并分析"按钮
5. 等待上传和分析完成

### 6.3 查看分析结果

1. 分析完成后，点击"查看分析结果