# 多模态面试评测智能体

基于FastAPI、PostgreSQL和Streamlit构建的多模态面试评测系统。

## 项目结构

```
├── backend/             # FastAPI后端
│   ├── app/            # 应用代码
│   │   ├── api/        # API路由
│   │   ├── core/       # 核心配置
│   │   ├── db/         # 数据库模型和会话
│   │   ├── models/     # Pydantic模型
│   │   ├── services/   # 业务逻辑
│   │   └── utils/      # 工具函数
│   ├── tests/          # 测试
│   └── requirements.txt # 后端依赖
├── frontend/           # Streamlit前端
│   ├── pages/          # 页面组件
│   ├── utils/          # 前端工具函数
│   └── requirements.txt # 前端依赖
└── docker-compose.yml  # Docker配置
```

## 技术栈

- **后端**: FastAPI
- **数据库**: PostgreSQL
- **前端**: Streamlit
- **多模态处理**: 音频、视频、文本分析

## 功能特点

- 面试视频/音频上传与处理
- 多模态特征提取与分析
- 面试表现评估与打分
- 可视化数据展示
- 评估报告生成