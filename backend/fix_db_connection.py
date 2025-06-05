#!/usr/bin/env python3
"""
数据库连接修复工具

用于测试和修复数据库连接问题
"""

import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_db_connection(db_uri):
    """测试数据库连接
    
    Args:
        db_uri: 数据库URI
        
    Returns:
        bool: 连接是否成功
    """
    try:
        # 创建引擎
        engine = create_engine(
            db_uri,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("数据库连接测试成功")
                return True
            else:
                logger.error("数据库连接测试失败: 返回值不正确")
                return False
    except Exception as e:
        logger.error(f"数据库连接测试失败: {str(e)}")
        return False

def test_session_management(db_uri):
    """测试会话管理
    
    Args:
        db_uri: 数据库URI
    """
    try:
        # 创建引擎
        engine = create_engine(db_uri, echo=False)
        
        # 创建会话工厂
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # 测试会话创建和关闭
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT 1"))
            row = result.fetchone()
            logger.info(f"会话测试查询结果: {row[0]}")
            
            # 测试事务回滚
            try:
                # 执行一个会失败的查询
                db.execute(text("SELECT * FROM non_existent_table"))
                db.commit()
            except Exception as e:
                logger.info(f"预期的查询错误: {str(e)}")
                db.rollback()
                logger.info("事务回滚成功")
        finally:
            db.close()
            logger.info("会话关闭成功")
    except Exception as e:
        logger.error(f"会话管理测试失败: {str(e)}")

if __name__ == "__main__":
    # 从环境变量或配置文件获取数据库URI
    from app.core.config import settings
    
    db_uri = settings.DATABASE_URI
    logger.info(f"使用数据库URI: {db_uri}")
    
    # 测试数据库连接
    if test_db_connection(db_uri):
        # 测试会话管理
        test_session_management(db_uri)
    else:
        logger.error("数据库连接失败，无法继续测试")
        sys.exit(1)
    
    logger.info("所有测试完成") 