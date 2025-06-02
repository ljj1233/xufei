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

- **backend/**：后端API服务，业务逻辑、数据库、AI服务对接
- **frontend/**：前端SPA，用户交互与结果展示
- **agent/**：AI分析核心，能力评测、建议生成等

## 2. 主要功能亮点

- 支持多领域典型岗位面试场景（技术、产品、运维等）
- 支持音频/视频文件上传与多模态分析（语音、视觉、内容）
- AI驱动的能力评估与改进建议
- 能力雷达图、评分、问题定位与个性化反馈
- 用户注册、登录、面试记录管理

## 3. 快速上手

### 3.1 环境准备
- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- 讯飞开放平台API密钥

### 3.2 后端启动
详见 [backend/README.md](backend/README.md)

### 3.3 前端启动
详见 [frontend/README.md](frontend/README.md)

### 3.4 数据库配置
- 已统一为MySQL，详见 `backend/.env.example` 和 `backend/MYSQL_MIGRATION_GUIDE.md`

### 3.5 AI服务配置
- 需注册讯飞开放平台，获取API密钥，填入`.env`文件

## 4. 贡献与开发

- 欢迎提交PR、Issue，详见各子模块README
- 代码风格与分支管理请参考 [CONTRIBUTING.md](CONTRIBUTING.md)（如有）

## 5. 联系与支持

如有问题请在Issue区留言，或联系项目维护者。

---

> **各子模块详细说明请见对应目录下的README.md。**