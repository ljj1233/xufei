import pytest
import os
import sys
import logging
from sqlalchemy import create_engine, text
from app.db.database import Base
from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_test_database():
    """设置测试数据库，确保有初始管理员账号"""
    try:
        # 连接数据库
        engine = create_engine(
            settings.DATABASE_URI,
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=3600,
            pool_pre_ping=True
        )
        
        # 创建所有表
        Base.metadata.create_all(engine)
        
        # 检查是否已有管理员账号
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        
        admin = session.query(User).filter(User.is_admin == True).first()
        if not admin:
            # 创建管理员账号
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_admin=True
            )
            session.add(admin_user)
            session.commit()
            logger.info("已创建管理员账号: admin@example.com / admin123")
        else:
            logger.info(f"已存在管理员账号: {admin.email}")
        
        session.close()
        return True
    except Exception as e:
        logger.error(f"设置测试数据库失败: {str(e)}")
        return False

def run_tests():
    """运行所有测试"""
    # 设置测试数据库
    if not setup_test_database():
        logger.error("测试数据库设置失败，无法运行测试")
        return False
    
    # 运行测试
    test_files = [
        "user/test_user_management_comprehensive.py"
    ]
    
    success = True
    for test_file in test_files:
        logger.info(f"运行测试: {test_file}")
        result = pytest.main([f"tests/{test_file}", "-v"])
        if result != 0:
            logger.error(f"测试失败: {test_file}")
            success = False
    
    return success

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    success = run_tests()
    sys.exit(0 if success else 1)