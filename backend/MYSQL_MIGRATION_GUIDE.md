# PostgreSQL 到 MySQL 迁移指南

本文档提供了将后端数据库从 PostgreSQL 迁移到 MySQL 的详细步骤和说明。

## 迁移步骤

### 1. 安装必要的依赖

首先，确保安装了 MySQL 相关的 Python 依赖：

```bash
pip install pymysql cryptography
```

这些依赖已经添加到 `requirements.txt` 文件中。

### 2. 配置 MySQL 数据库

1. 安装并启动 MySQL 服务器
2. 创建新的数据库：
   ```sql
   CREATE DATABASE interview_analysis_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. 创建数据库用户并授权：
   ```sql
   CREATE USER 'interview_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON interview_analysis_db.* TO 'interview_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

### 3. 更新环境变量

复制 `.env.mysql.example` 文件为 `.env`，并根据你的 MySQL 配置更新相关参数：

```
MYSQL_SERVER=localhost
MYSQL_USER=interview_user
MYSQL_PASSWORD=your_password
MYSQL_DB=interview_analysis_db
MYSQL_PORT=3306
```

### 4. 使用 MySQL 配置

项目已经更新为使用 MySQL 配置。主要更改包括：

1. 创建了新的配置文件 `app/core/config_mysql.py`
2. 更新了数据库连接模块 `app/db/database.py` 以使用 MySQL 配置
3. 更新了 `requirements.txt` 添加 MySQL 依赖并移除 PostgreSQL 依赖

### 5. 数据库迁移

如果需要从现有的 PostgreSQL 数据库迁移数据，可以使用以下方法：

#### 方法一：使用 Alembic 迁移

1. 确保 Alembic 配置正确指向 MySQL 数据库
2. 运行迁移命令创建表结构：
   ```bash
   alembic revision --autogenerate -m "migrate to mysql"
   alembic upgrade head
   ```

#### 方法二：手动导出导入数据

1. 从 PostgreSQL 导出数据为 CSV 或 JSON 格式
2. 将数据导入到 MySQL 数据库

### 6. 验证迁移

运行测试套件确保所有功能正常工作：

```bash
python -m pytest tests/
```

## 数据类型差异注意事项

从 PostgreSQL 迁移到 MySQL 时，需要注意以下数据类型差异：

1. **JSON 类型**：MySQL 5.7+ 支持原生 JSON 类型，但处理方式与 PostgreSQL 有所不同
2. **TEXT 类型**：MySQL 中 TEXT 类型有大小限制，可能需要使用 LONGTEXT
3. **布尔类型**：MySQL 使用 TINYINT(1) 代替 BOOLEAN
4. **时间戳**：MySQL 的 TIMESTAMP 类型与 PostgreSQL 有差异，特别是在时区处理方面

## 测试

项目包含全面的测试套件，涵盖：

1. 用户 API 测试 (`tests/test_user_api.py`)
2. 面试 API 测试 (`tests/test_interview_api.py`)
3. 职位 API 测试 (`tests/test_job_position_api.py`)
4. 分析服务测试 (`tests/test_analysis_service.py`)

这些测试确保在迁移到 MySQL 后所有功能正常工作。

## 故障排除

### 常见问题

1. **连接错误**：检查 MySQL 服务器是否运行，以及用户名/密码是否正确
2. **字符集问题**：确保使用 utf8mb4 字符集避免中文字符问题
3. **权限问题**：确保数据库用户有足够的权限

如有其他问题，请查阅 MySQL 官方文档或提交 issue。