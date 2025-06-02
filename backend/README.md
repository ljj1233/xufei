# 多模态面试评测智能体 - 后端服务

本模块为多模态面试评测系统的后端，基于FastAPI开发，数据库已统一为MySQL，负责业务逻辑、数据存储、AI服务对接。

## 技术栈

- **FastAPI**：高性能Python Web框架，支持异步处理和自动API文档生成
- **SQLAlchemy**：强大的ORM框架，支持多种数据库
- **MySQL**：关系型数据库（已统一）
- **Pydantic**：数据验证和设置管理
- **Python-Multipart**：文件上传处理
- **讯飞开放平台API**：语音识别、评测、情感分析
- **JWT**：用户认证和授权
- **Librosa**：音频特征提取
- **OpenCV**：视频处理和特征提取
- **Transformers**：自然语言处理

## 目录结构

```
backend/
├── app/                    # 应用核心代码
│   ├── api/                # API路由
│   │   └── api_v1/         # API v1版本
│   │       ├── endpoints/  # API端点
│   │       └── api.py      # API路由聚合
│   ├── core/               # 核心配置
│   │   ├── config.py       # 应用配置
│   │   ├── security.py     # 安全相关
│   │   └── settings.py     # 设置管理
│   ├── db/                 # 数据库相关
│   │   ├── database.py     # 数据库连接
│   │   └── init_db.py      # 数据库初始化
│   ├── models/             # 数据模型
│   │   ├── user.py         # 用户模型
│   │   ├── interview.py    # 面试模型
│   │   ├── analysis.py     # 分析结果模型
│   │   ├── job_position.py # 职位模型
│   │   └── schemas.py      # Pydantic模型
│   ├── services/           # 业务逻辑
│   │   ├── analysis.py     # 分析服务
│   │   ├── xunfei_service.py # 讯飞API服务
│   │   └── ai_agent_service.py # AI智能体服务
│   ├── utils/              # 工具函数
│   │   ├── auth.py         # 认证工具
│   │   └── file_utils.py   # 文件处理工具
│   └── main.py             # FastAPI入口
├── tests/                  # 测试
│   ├── conftest.py         # 测试配置
│   ├── test_user_api.py    # 用户API测试
│   ├── test_interview_api.py # 面试API测试
│   └── test_analysis_service.py # 分析服务测试
├── alembic/                # 数据库迁移
├── requirements.txt        # 依赖项
├── .env.example            # 环境变量示例
├── MYSQL_MIGRATION_GUIDE.md # MySQL迁移说明
├── DEVELOPMENT_LOG.md      # 开发日志
└── README.md               # 项目说明
```

## 安装与配置

### 环境要求

- Python 3.8+
- MySQL 8.0+
- 讯飞开放平台API密钥

### 安装步骤

1. 克隆项目并进入backend目录
   ```bash
   git clone https://github.com/yourusername/interview-analysis.git
   cd interview-analysis/backend
   ```

2. 创建虚拟环境并激活
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量
   ```bash
   # 复制环境变量示例文件
   cp .env.example .env
   # 编辑.env文件，填写MySQL和讯飞API信息
   ```

5. 初始化数据库
   ```bash
   # 使用Alembic创建表结构
   alembic revision --autogenerate -m "init mysql tables"
   alembic upgrade head
   ```

### 启动服务

```bash
# 开发模式
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

服务默认运行在 `http://localhost:8000`

## API文档

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 主要功能

### 1. 用户管理

- 用户注册与登录
- 用户信息管理
- 权限控制

### 2. 面试管理

- 面试视频/音频上传
- 面试记录管理
- 面试文件处理

### 3. 多模态分析

- 语音分析（清晰度、语速、情感）
- 视觉分析（表情、眼神接触、肢体语言）
- 内容分析（相关性、结构、关键点）

### 4. 综合评测

- 能力评分
- 优势与劣势分析
- 改进建议生成

## 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_user_api.py

# 生成覆盖率报告
pytest --cov=app tests/
```

## 部署

### Docker部署

```bash
# 构建Docker镜像
docker build -t interview-backend .

# 运行容器
docker run -d -p 8000:8000 --name interview-backend interview-backend
```

### Gunicorn部署

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 常见问题

### 数据库连接失败

- 检查MySQL服务是否运行
- 确认`.env`文件中的数据库配置是否正确
- 检查数据库用户权限

### 讯飞API调用失败

- 检查API密钥是否正确
- 确认讯飞开放平台服务是否可用
- 检查网络连接

### 文件上传失败

- 检查上传目录权限
- 确认文件大小是否超过限制
- 检查文件类型是否支持

## 开发指南

详细的开发指南、代码规范和贡献流程请参考[DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)。

## 数据库设计

详细的数据库设计、表结构和迁移指南请参考[MYSQL_MIGRATION_GUIDE.md](MYSQL_MIGRATION_GUIDE.md)。

## 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交Pull Request

## 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件