"""
数据库初始化脚本

用于创建数据库表和初始化基础数据
"""

import logging
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from app.db.database import engine
from app.models import Base
import app.models.interview
import app.models.job_position
import app.models.user
import app.models.analysis
import app.models.interview_session

# 配置日志
logger = logging.getLogger(__name__)

def init_db():
    """
    初始化数据库：创建所有表
    
    如果表已存在，则不会重新创建
    """
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except SQLAlchemyError as e:
        logger.error(f"创建数据库表时出错: {str(e)}")
        raise

def check_db_structure():
    """
    检查数据库结构，打印表和列的信息
    """
    try:
        inspector = inspect(engine)
        
        # 获取所有表名
        tables = inspector.get_table_names()
        logger.info(f"数据库中的表: {', '.join(tables)}")
        
        # 打印每个表的列信息
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            column_info = [f"{col['name']} ({col['type']})" for col in columns]
            logger.info(f"表 {table_name} 的列: {', '.join(column_info)}")
            
    except SQLAlchemyError as e:
        logger.error(f"检查数据库结构时出错: {str(e)}")
        raise

def update_db_structure():
    """
    更新数据库结构，添加新的表和列
    
    注意：此方法仅创建新表和添加新列，不会删除现有表或列
    """
    try:
        # 检查interview_questions表是否存在
        inspector = inspect(engine)
        if 'interview_questions' not in inspector.get_table_names():
            # 如果表不存在，创建该表
            app.models.interview.InterviewQuestion.__table__.create(engine)
            logger.info("创建了新表: interview_questions")
        else:
            # 表已存在，检查是否有新的列需要添加
            existing_columns = [col['name'] for col in inspector.get_columns('interview_questions')]
            required_columns = ['id', 'position_id', 'content', 'skill_tags', 
                              'suggested_duration_seconds', 'reference_answer', 
                              'difficulty', 'created_at', 'updated_at']
            
            # 找出缺少的列
            missing_columns = [col for col in required_columns if col not in existing_columns]
            
            if missing_columns:
                logger.warning(f"表 interview_questions 缺少列: {', '.join(missing_columns)}")
                logger.warning("请手动添加这些列，或者删除表后重新运行此脚本")
            else:
                logger.info("表 interview_questions 结构已经是最新")
                
    except SQLAlchemyError as e:
        logger.error(f"更新数据库结构时出错: {str(e)}")
        raise

if __name__ == "__main__":
    # 当脚本直接运行时，初始化数据库
    logging.basicConfig(level=logging.INFO)
    logger.info("开始初始化数据库...")
    init_db()
    check_db_structure()
    logger.info("数据库初始化完成") 