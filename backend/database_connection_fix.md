# 数据库连接池超时问题解决方案

## 问题分析

根据错误信息：
```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00
```

这表明您的应用程序遇到了以下问题：

1. 数据库连接池已达到其最大限制（池大小5，最大溢出10）
2. 新的连接请求无法在30秒超时时间内获取连接
3. 这通常意味着：
   - 数据库服务器可能负载过高
   - 有连接未正确释放
   - 应用程序请求量超过了当前连接池配置能够处理的范围

## 立即解决方案

### 1. 修改连接池配置

编辑 `.env` 文件，增加连接池大小和溢出值：

```
# 原始值
# DB_POOL_SIZE=5
# DB_MAX_OVERFLOW=10
# DB_POOL_TIMEOUT=30

# 建议新值
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=60
```

### 2. 检查数据库服务状态

确保PostgreSQL服务正常运行：

```bash
# 在Linux上
sudo systemctl status postgresql

# 或在Windows上通过服务管理器检查PostgreSQL服务状态
```

### 3. 检查活跃连接

在PostgreSQL中执行以下查询检查当前连接情况：

```sql
SELECT count(*) FROM pg_stat_activity;
```

## 长期解决方案

### 1. 优化数据库查询

- 检查是否有长时间运行的查询占用连接
- 确保关键查询已添加适当的索引

### 2. 实现连接池监控

在 `main.py` 中添加连接池监控日志：

```python
import logging

# 在lifespan函数中添加
logging.info(f"Database connection pool initialized with size={settings.DB_POOL_SIZE}, max_overflow={settings.DB_MAX_OVERFLOW}")

# 添加定期检查连接池状态的函数
@app.get("/api/v1/admin/db-status", tags=["admin"])
async def check_db_pool_status():
    stats = {
        "pool_size": engine.pool.size(),
        "checkedin": engine.pool.checkedin(),
        "overflow": engine.pool.overflow(),
        "checkedout": engine.pool.checkedout(),
    }
    return stats
```

### 3. 实现连接重试机制

在关键服务中添加重试逻辑，例如在用户注册服务中：

```python
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def db_operation_with_retry(db_func, *args, **kwargs):
    try:
        return db_func(*args, **kwargs)
    except Exception as e:
        logging.error(f"Database operation failed: {e}")
        raise
```

### 4. 考虑使用连接池外部管理

对于高负载应用，考虑使用如PgBouncer等连接池管理工具。

## 前端改进

已经在前端注册组件中添加了更详细的错误处理和日志记录，这将帮助诊断问题。当发生连接池超时时，用户将看到更友好的错误消息。

## 下一步操作

1. 实施上述配置更改
2. 重启后端服务
3. 监控应用程序日志和数据库连接情况
4. 如果问题持续存在，考虑进一步增加连接池参数或实施更高级的连接管理策略