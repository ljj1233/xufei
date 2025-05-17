"""数据库连接测试脚本

用于测试数据库连接和初始化
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))

import logging
from sqlalchemy import text
from app.db.database import engine, Base, get_db, SessionLocal
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection():
    """测试数据库连接"""
    logger.info("开始测试数据库连接...")
    logger.info(f"数据库连接URI: {settings.DATABASE_URI}")
    
    try:
        # 测试数据库连接
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info(f"数据库连接测试结果: {result.fetchone()}")
            logger.info("数据库连接成功!")
        
        # 测试会话创建
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT 1"))
            logger.info(f"数据库会话测试结果: {result.fetchone()}")
            logger.info("数据库会话创建成功!")
        finally:
            db.close()
            logger.info("数据库会话已关闭")
        
        # 测试表是否存在
        with engine.connect() as connection:
            result = connection.execute(text(
                """SELECT table_name FROM information_schema.tables 
                   WHERE table_schema = 'public'"""))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"数据库中的表: {tables}")
            
            # 检查是否需要创建表
            if not tables or 'users' not in tables:
                logger.info("数据库表不存在，正在创建...")
                Base.metadata.create_all(bind=engine, checkfirst=True)
                logger.info("数据库表创建完成")
            else:
                logger.info("数据库表已存在")
        
        return True
    except Exception as e:
        logger.error(f"数据库连接测试失败: {str(e)}")
        return False

def test_get_db():
    """测试get_db函数"""
    logger.info("开始测试get_db函数...")
    
    try:
        # 获取数据库会话生成器
        db_generator = get_db()
        
        # 获取会话
        db = next(db_generator)
        
        # 测试会话
        result = db.execute(text("SELECT 1")).fetchone()
        logger.info(f"get_db测试结果: {result}")
        
        # 关闭会话
        try:
            db_generator.close()
        except:
            pass
        
        logger.info("get_db函数测试成功!")
        return True
    except Exception as e:
        logger.error(f"get_db函数测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== 数据库连接测试开始 ===")
    
    # 测试数据库连接
    connection_success = test_database_connection()
    
    if connection_success:
        # 测试get_db函数
        get_db_success = test_get_db()
        
        if get_db_success:
            logger.info("所有测试通过!")
        else:
            logger.error("get_db函数测试失败!")
    else:
        logger.error("数据库连接测试失败!")
    
    logger.info("=== 数据库连接测试结束 ===")