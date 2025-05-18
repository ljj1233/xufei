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

## 页面与导航
- 首页（/）：系统入口，展示系统简介和主要功能
- 登录页（/login）：用户登录入口
- 注册页（/register）：已重定向到登录页的注册模式
- 上传页（/upload）：从用户中心或导航栏"开始面试"进入，用于上传面试视频
- 结果页（/results）：从用户中心"历史记录"进入，展示所有面试记录
- 报告页（/report/:id）：从结果页点击具体记录进入，查看详细分析报告
- 用户中心页（/user）：个人信息管理，也是访问上传和历史记录的主要入口
- 关于页（/about）：系统说明和帮助文档

## 安装与配置
### 环境要求
- Node.js 16+
- npm 7+

### 安装步骤
1. 克隆项目并进入frontend目录
2. 安装依赖：`npm install`
3. 配置环境变量：复制`.env.example`为`.env`，填写API_URL等信息

### 模式切换说明
本前端支持"测试模式"与"上线模式"两种运行方式：
- **测试模式**：所有页面均可访问，无需登录，便于开发和测试。默认提供测试账号：
  - 用户名：test_user
  - 密码：test123
  - 权限：可访问所有功能，包括上传、查看报告和历史记录
- **上线模式**：启用正常权限控制，需登录后访问受限页面。

#### 切换方式
1. 在`.env`文件中增加或修改如下变量：
   - `VITE_APP_MODE=test`  启用测试模式
   - `VITE_APP_MODE=production`  启用上线模式
2. 重新启动开发服务器或重新构建项目。
3. 代码中可通过`import.meta.env.VITE_APP_MODE`获取当前模式。

> 示例：
> ```env
> VITE_APP_MODE=test
> ```

如需临时切换，可直接修改`.env`后重启服务。

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
### 主题规范（科大讯飞风格）
- 主色调：
  - 主要：#1E88E5（科大讯飞蓝）
  - 辅助：#4CAF50（活力绿）
  - 强调：#FF5722（醒目橙）
- 字体规范：
  - 标题：Microsoft YaHei, 18-24px, 加粗
  - 正文：PingFang SC, 14-16px
  - 辅助文本：12px
- 布局：
  - 响应式设计，适配桌面端和移动端
  - 顶部导航固定，内容区域流式布局
  - 卡片式设计，圆角8px
- 交互：
  - 按钮悬浮效果：轻微上浮阴影
  - 加载动画：科大讯飞logo旋转
  - 过渡动画：300ms ease-in-out
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