# 多模态面试评测智能体 - 后端服务

本模块为多模态面试评测系统的后端，基于FastAPI开发，数据库已统一为MySQL，负责业务逻辑、数据存储、AI服务对接。

## 技术栈
- **FastAPI**：高性能Python Web框架
- **SQLAlchemy**：ORM框架
- **MySQL**：关系型数据库（已统一）
- **Pydantic**：数据验证
- **Python-Multipart**：文件上传
- **讯飞开放平台API**：语音识别、评测、情感分析

## 目录结构
```
backend/
├── app/           # 应用核心代码
│   ├── api/       # API路由
│   ├── core/      # 配置
│   ├── db/        # 数据库相关
│   ├── models/    # Pydantic模型
│   ├── services/  # 业务逻辑
│   ├── utils/     # 工具函数
│   └── main.py    # FastAPI入口
├── tests/         # 测试
├── requirements.txt
├── .env.example   # 环境变量示例
├── MYSQL_MIGRATION_GUIDE.md # MySQL迁移说明
└── README.md
```

## 安装与配置
### 环境要求
- Python 3.8+
- MySQL 8.0+
- 讯飞开放平台API密钥

### 安装步骤
1. 克隆项目并进入backend目录
2. 创建虚拟环境并激活
3. 安装依赖：`pip install -r requirements.txt`
4. 配置环境变量：复制`.env.example`为`.env`，填写MySQL和讯飞API信息
5. 初始化数据库，详见`MYSQL_MIGRATION_GUIDE.md`

### 启动服务
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
服务默认运行在 `http://localhost:8000`

## API文档
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 测试
```bash
pytest
```

## 部署
- 推荐使用Docker或Gunicorn，详见根目录README

## 常见问题
- 数据库连接失败：请检查MySQL服务和`.env`配置
- 讯飞API调用失败：检查API密钥和服务权限

## 贡献指南
1. Fork项目
2. 创建分支
3. 提交PR

---
> 数据库已统一为MySQL，详细迁移与配置请见`MYSQL_MIGRATION_GUIDE.md`。

## 数据库设计与使用

### 数据库类型
本项目后端数据库采用 **MySQL**，推荐版本为 MySQL 8.0+。

### 主要表结构
- **users** 用户表：
  - id：主键，自增
  - username：用户名，唯一
  - email：邮箱，唯一
  - hashed_password：加密密码
  - is_active：是否激活
  - is_admin：是否管理员
  - created_at/updated_at：创建与更新时间

- **job_positions** 职位表：
  - id：主键，自增
  - title：职位名称
  - tech_field：技术领域（如AI、大数据等）
  - position_type：岗位类型（技术、运维、产品等）
  - required_skills：所需技能
  - job_description：岗位描述
  - evaluation_criteria：评估标准
  - created_at/updated_at：创建与更新时间

- **interviews** 面试表：
  - id：主键，自增
  - user_id：关联用户ID
  - job_position_id：关联职位ID
  - title：面试标题
  - description：面试描述
  - file_path：音视频文件路径
  - file_type：文件类型（audio/video）
  - duration：时长
  - created_at/updated_at：创建与更新时间

- **analysis** 分析结果表（如有）：
  - id：主键，自增
  - interview_id：关联面试ID
  - result_json：分析结果（JSON）
  - created_at/updated_at：创建与更新时间

### 数据库初始化与迁移
1. 安装依赖：`pip install -r requirements.txt`
2. 配置数据库（详见`MYSQL_MIGRATION_GUIDE.md`）：
   - 创建数据库和用户
   - 配置字符集为utf8mb4
3. 配置环境变量：复制`.env.mysql.example`为`.env`，填写MySQL连接信息
4. 初始化表结构：
   - 推荐使用 Alembic 迁移：
     ```bash
     alembic revision --autogenerate -m "init mysql tables"
     alembic upgrade head
     ```
   - 或手动执行SQL建表（见models定义）

### 数据库连接配置
`.env`文件需包含如下参数：
```
MYSQL_SERVER=localhost
MYSQL_USER=interview_user
MYSQL_PASSWORD=your_password
MYSQL_DB=interview_analysis_db
MYSQL_PORT=3306
```

### 后端与数据库交互流程
- 使用 SQLAlchemy 作为ORM，所有模型定义见`app/models/`
- 数据库连接配置见`app/core/config_mysql.py`和`app/db/database.py`
- FastAPI 路由通过依赖注入获取数据库会话（Session），进行增删改查
- 典型流程：
  1. API 接收请求参数
  2. 通过Session操作模型对象（如User、Interview等）
  3. 提交事务并返回结果

### 常见数据库操作示例
- 创建用户（POST `/api/user/`）：
  - 请求体：`{"username": "test", "email": "test@test.com", "password": "123456"}`
  - 后端自动加密密码并写入users表
- 查询职位列表（GET `/api/job_position/`）：
  - 返回所有职位信息
- 创建面试记录（POST `/api/interview/`）：
  - 包含用户ID、职位ID、音视频文件等
- 获取分析结果（GET `/api/analysis/{interview_id}`）：
  - 返回指定面试的分析JSON

### 测试数据库说明
- 测试用例见`tests/`目录，覆盖用户、面试、职位、分析等API
- 运行测试：
  ```bash
  pytest
  ```
- 测试前建议使用测试数据库或隔离环境，避免污染正式数据

更多数据库迁移、配置和故障排查请参考`MYSQL_MIGRATION_GUIDE.md`。