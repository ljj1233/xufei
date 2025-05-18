# 多模态面试评测智能体 - 前端应用

本模块为多模态面试评测系统的前端，基于Vue 3和Element Plus开发，提供直观美观的用户界面，支持与后端MySQL数据库统一对接。

## 技术栈
- **Vue 3**：现代渐进式JavaScript框架
- **Vite**：极速开发与构建工具
- **Element Plus**：UI组件库
- **Pinia**：状态管理
- **Vue Router**：路由管理
- **Chart.js & Vue-Chartjs**：数据可视化
- **Axios**：HTTP客户端

## 目录结构
```
frontend/
├── public/           # 静态资源
├── src/              # 源代码
│   ├── assets/       # 样式/图片
│   ├── components/   # 组件
│   ├── router/       # 路由
│   ├── stores/       # 状态管理
│   ├── views/        # 页面
│   ├── App.vue       # 根组件
│   └── main.js       # 入口
├── tests/            # 测试
├── index.html        # HTML模板
├── package.json      # 依赖
├── vite.config.js    # Vite配置
├── .env.example      # 环境变量示例
└── README.md
```

## 安装与配置
### 环境要求
- Node.js 16+
- npm 7+

### 安装步骤
1. 克隆项目并进入frontend目录
2. 安装依赖：`npm install`
3. 配置环境变量：复制`.env.example`为`.env`，填写API_URL等信息

### 启动开发服务器
```bash
npm run dev
```
访问 `http://localhost:5173`

### 构建生产版本
```bash
npm run build
```

### 预览生产版本
```bash
npm run preview
```

## 测试
- 单元测试：`npm run test:unit`
- 端到端测试：`npm run test:e2e`

## 主要功能
- 用户注册、登录、个人信息管理
- 面试音视频上传与进度展示
- 多模态分析结果可视化（能力雷达图、评分、建议等）
- 历史面试记录与详情查看

## UI与样式
- 主题色：#1E88E5（主）、#4CAF50（辅）等
- 响应式布局，适配多端
- 详见`src/components/`与`src/views/`

## 部署
- 推荐使用Nginx等静态服务器，详见根目录README

## 常见问题
- API连接失败：请检查`.env`中的API_URL配置，确保后端服务已启动
- 构建失败：请检查Node.js与依赖版本

## 贡献指南
1. Fork项目
2. 创建分支
3. 提交PR

---
> 前端与后端数据库已统一为MySQL，详细配置请见`backend/README.md`与`backend/MYSQL_MIGRATION_GUIDE.md`。