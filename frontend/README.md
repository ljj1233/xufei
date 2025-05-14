# 多模态面试评测智能体 - 前端应用

基于Vue 3和Element Plus构建的多模态面试评测系统前端应用，提供美观直观的用户界面，展示面试分析结果。

## 技术栈

- **Vue 3**: 渐进式JavaScript框架
- **Vite**: 现代前端构建工具
- **Element Plus**: 基于Vue 3的组件库
- **Pinia**: Vue的状态管理库
- **Vue Router**: 路由管理
- **Chart.js & Vue-Chartjs**: 数据可视化
- **Axios**: HTTP客户端

## 目录结构

```
frontend/
├── public/              # 静态资源
├── src/                 # 源代码
│   ├── assets/          # 资源文件（CSS、图片等）
│   ├── components/      # 可复用组件
│   ├── router/          # 路由配置
│   ├── stores/          # Pinia状态管理
│   ├── views/           # 页面组件
│   ├── App.vue          # 根组件
│   └── main.js          # 入口文件
├── tests/               # 测试代码
│   ├── unit/            # 单元测试
│   └── e2e/             # 端到端测试
├── index.html           # HTML模板
├── package.json         # 项目依赖
├── vite.config.js       # Vite配置
├── .env.example         # 环境变量示例
└── README.md            # 本文件
```

## 安装与配置

### 环境要求

- **Node.js**: 16.0或更高版本
- **npm**: 7.0或更高版本

### 安装步骤

1. **克隆项目并进入前端目录**

```bash
git clone https://github.com/your-username/multimodal-interview-agent.git
cd multimodal-interview-agent/frontend
```

2. **安装依赖**

```bash
npm install
```

3. **配置环境变量**

复制`.env.example`文件为`.env`，并填入相应的配置信息：

```bash
cp .env.example .env
# 然后编辑.env文件，设置API_URL等环境变量
```

## 开发

### 启动开发服务器

```bash
npm run dev
```

应用将在 `http://localhost:5173` 启动。

### 构建生产版本

```bash
npm run build
```

构建后的文件将生成在`dist`目录中。

### 预览生产版本

```bash
npm run preview
```

## 测试

### 运行单元测试

```bash
npm run test:unit
```

### 运行端到端测试

```bash
npm run test:e2e
```

## UI组件与样式指南

### 主题色彩

- **主色**: #1E88E5 (蓝色)
- **辅助色**: #4CAF50 (绿色), #FF9800 (橙色), #F44336 (红色)
- **背景色**: #F5F7FA (浅灰)
- **文本色**: #333333 (深灰)

### 组件使用指南

#### 按钮

```vue
<el-button type="primary">主要按钮</el-button>
<el-button>默认按钮</el-button>
<el-button type="success">成功按钮</el-button>
```

#### 表单

```vue
<el-form :model="form" label-position="top">
  <el-form-item label="标题">
    <el-input v-model="form.title" />
  </el-form-item>
</el-form>
```

#### 卡片

```vue
<el-card class="feature-card">
  <template #header>
    <div class="card-header">卡片标题</div>
  </template>
  <div class="card-content">卡片内容</div>
</el-card>
```

### 响应式设计

使用Element Plus的栅格系统实现响应式布局：

```vue
<el-row :gutter="20">
  <el-col :xs="24" :sm="12" :md="8">
    <!-- 内容 -->
  </el-col>
</el-row>
```

## 开发指南

### 添加新页面

1. 在`src/views/`目录下创建新的Vue组件
2. 在`src/router/index.js`中添加路由配置

### 添加新组件

在`src/components/`目录下创建新的Vue组件

### 添加新状态

在`src/stores/`目录下创建新的Pinia store

## 部署

### 使用Nginx部署

1. 构建生产版本

```bash
npm run build
```

2. 将`dist`目录中的文件复制到Nginx的网站根目录

3. 配置Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /path/to/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend-server:8000/;
    }
}
```

## 常见问题

### API连接问题

确保`.env`文件中的`API_URL`设置正确，指向后端服务的地址。

### 构建失败

检查Node.js和npm版本是否符合要求，并确保所有依赖已正确安装。

## 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request