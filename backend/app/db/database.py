from sqlalchemy import create_engine, text, Column, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.orm import sessionmaker
import datetime
import logging
import time

# 使用MySQL配置
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建SQLAlchemy引擎，添加连接池配置和重试机制
try:
    engine = create_engine(
        settings.DATABASE_URI,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=3600,  # 连接回收时间
        pool_pre_ping=True  # 连接前ping测试
    )
    logger.info(f"数据库连接成功: {settings.MYSQL_SERVER}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}")
except Exception as e:
    logger.error(f"数据库连接失败: {str(e)}")
    raise

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
class Base(DeclarativeBase):
    """SQLAlchemy声明性基类
    
    为所有数据库模型提供通用功能：
    - 自动生成表名
    - 创建和更新时间戳
    - 通用的JSON序列化方法
    """
    # 不要覆盖metadata，保持DeclarativeBase默认行为
    # metadata = None  # 删除此行，避免Base.metadata为None

    @declared_attr
    def __tablename__(cls) -> str:
        """自动生成表名，使用类名的小写形式"""
        return cls.__name__.lower()
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    
    def to_dict(self) -> dict:
        """将模型实例转换为字典"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


def get_db():
    """获取数据库会话
    
    创建一个数据库会话，用完后关闭
    
    Yields:
        Session: 数据库会话对象
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            db = SessionLocal()
            print("hello")
            # 测试连接是否有效
            # db.execute(text("SELECT 1"))
            # logger.debug("数据库会话创建成功")
            print("数据库会话创建成功")
            try:
                yield db
            finally:
                db.close()
                logger.debug("数据库会话已关闭")
            break  # 如果成功，跳出循环
        except Exception as e:
            retry_count += 1
            logger.error(f"数据库连接错误 (尝试 {retry_count}/{max_retries}): {str(e)}")
            if retry_count >= max_retries:
                logger.critical("数据库连接失败，已达到最大重试次数")
                raise
            time.sleep(1)  # 等待1秒后重试