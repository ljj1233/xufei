# 多模态面试评测智能体 - 快速启动指南

本指南提供简单明了的步骤，帮助你快速设置和启动后端服务。

## 1. 环境准备

- Python 3.8+ (推荐3.9或3.10)
- MySQL 8.0+
- Git

## 2. 获取代码

```bash
# 克隆项目
git clone https://github.com/yourusername/interview-analysis.git
cd interview-analysis/backend
```

## 3. 创建并激活虚拟环境

### Windows
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate
```

### Linux/Mac
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

## 4. 安装依赖

```bash
# 安装依赖
pip install -r requirements.txt
```

## 5. 解决bcrypt兼容性问题

运行提供的修复脚本:

```bash
python fix_bcrypt.py
```

或手动安装兼容版本:

```bash
pip uninstall -y bcrypt passlib
pip install bcrypt==3.2.0 passlib==1.7.4
```

## 6. 配置环境变量

```bash
# 复制示例环境变量文件
cp .env.example .env
```

然后编辑`.env`文件，填写以下关键配置:

```
# 数据库配置
MYSQL_SERVER=localhost
MYSQL_PORT=3306
MYSQL_USER=面试系统用户名
MYSQL_PASSWORD=面试系统密码
MYSQL_DB=interview_analysis

# JWT配置
SECRET_KEY=生成一个随机密钥
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 服务配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

## 7. 初始化数据库

确保MySQL服务已启动，并创建了数据库:

```bash
# 在MySQL中创建数据库
mysql -u root -p
```

```sql
CREATE DATABASE interview_analysis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'interview_user'@'localhost' IDENTIFIED BY '你的密码';
GRANT ALL PRIVILEGES ON interview_analysis.* TO 'interview_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

使用Alembic创建表结构:

```bash
alembic revision --autogenerate -m "init mysql tables"
alembic upgrade head
```

## 8. 启动服务

```bash
# 开发模式 (自动重载)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用更详细的日志级别启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

## 9. 验证服务

服务启动后，访问以下URL验证服务是否正常运行:

- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/v1/health

## 故障排除

### 服务启动但立即关闭
- 请检查日志中的错误信息
- 确认MySQL服务已启动
- 检查`.env`文件中的数据库配置是否正确
- 尝试以debug日志级别启动

### 无法连接到数据库
- 确保MySQL服务正在运行
- 验证用户名和密码是否正确
- 检查数据库名称是否正确
- 确保用户有正确的权限

### 找不到模块或依赖问题
- 确保已激活虚拟环境
- 再次运行`pip install -r requirements.txt`
- 如果是bcrypt相关错误，运行修复脚本

## 默认登录信息

系统会自动创建一个默认管理员账号:

- 邮箱: admin@example.com
- 密码: admin123 