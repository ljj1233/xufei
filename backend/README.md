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