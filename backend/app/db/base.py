# 统一从database.py导入数据库相关组件
from app.db.database import engine, Base, get_db, SessionLocal
from app.models.user import User
from app.models.job_position import JobPosition
from app.models.interview import Interview
from app.models.analysis import Analysis

# 此文件仅用于向后兼容，所有数据库相关组件应从database.py导入
# 避免重复定义数据库连接和会话，防止连接池冲突

# 导出所有组件，保持API兼容性
__all__ = [
    'engine',
    'Base',
    'get_db',
    'SessionLocal',
    'User',
    'JobPosition',
    'Interview',
    'Analysis',
]