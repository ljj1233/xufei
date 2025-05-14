# 多模态面试评测智能体 - 后端服务

基于FastAPI构建的多模态面试评测系统后端服务，负责业务逻辑处理、数据存储和与AI服务交互。

## 技术栈

- **FastAPI**: 高性能的Python Web框架
- **SQLAlchemy**: ORM框架
- **PostgreSQL**: 关系型数据库
- **Pydantic**: 数据验证
- **Python-Multipart**: 处理文件上传
- **讯飞开放平台API**: 语音识别、语音评测和情感分析

## 目录结构

```
backend/
├── app/                    # 应用核心代码
│   ├── api/                # API路由定义
│   │   └── api_v1/
│   │       ├── endpoints/  # 各模块API端点
│   │       └── api.py      # API路由聚合
│   ├── core/               # 核心配置
│   ├── db/                 # 数据库相关
│   ├── models/             # Pydantic模型
│   ├── services/           # 业务逻辑服务
│   ├── utils/              # 工具函数
│   └── main.py             # FastAPI应用入口
├── tests/                  # 测试代码
│   ├── test_api.py         # API测试
│   ├── test_services.py    # 服务测试
│   ├── test_db.py          # 数据库测试
│   └── test_data/          # 测试数据
├── requirements.txt        # 依赖包
├── .env.example            # 环境变量示例
└── README.md               # 本文件
```

## 安装与配置

### 环境要求

- **Python**: 3.8或更高版本
- **PostgreSQL**: 12或更高版本
- **讯飞开放平台账户及API密钥**

### 安装步骤

1. **克隆项目并进入后端目录**

```bash
git clone https://github.com/your-username/multimodal-interview-agent.git
cd multimodal-interview-agent/backend
```

2. **创建并激活虚拟环境**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境变量**

复制`.env.example`文件为`.env`，并填入相应的配置信息：

```bash
cp .env.example .env
# 然后编辑.env文件，填入数据库连接信息和讯飞API密钥
```

5. **创建数据库**


确保PostgreSQL服务已启动，并创建数据库：

```bash
psql -U postgres
CREATE DATABASE interview_analysis_db;
\q
```

## 运行服务

```bash
cd app  # 进入app目录以正确解析相对导入
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 启动。

## API文档

启动服务后，可以访问以下URL查看API文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 测试

### 运行测试

```bash
# 在backend目录下运行
pytest
```

### 测试覆盖率报告

```bash
pytest --cov=app tests/
```

## 开发指南

### 添加新的API端点

1. 在`app/api/api_v1/endpoints/`目录下创建新的路由文件
2. 在`app/api/api_v1/api.py`中注册新的路由

### 添加新的数据库模型

1. 在`app/db/models.py`中定义新的SQLAlchemy模型
2. 在`app/models/schemas.py`中定义对应的Pydantic模型

### 添加新的服务

在`app/services/`目录下创建新的服务文件，实现业务逻辑

## 部署

### 使用Docker部署（推荐）

1. 构建Docker镜像

```bash
docker build -t interview-backend .
```

2. 运行容器

```bash
docker run -d -p 8000:8000 --env-file .env --name interview-backend-container interview-backend
```

### 使用Gunicorn部署

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

## 常见问题

### 数据库连接问题

确保PostgreSQL服务已启动，并检查`.env`文件中的数据库连接信息是否正确。

### 讯飞API调用失败

检查`.env`文件中的讯飞API密钥是否正确，以及是否已开通相应的服务权限。

## 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request