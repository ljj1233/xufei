# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.database import Base
from app.models import User, Interview, InterviewAnalysis
# 确保使用正确的JobPosition模型
from app.models.job_position import JobPosition, TechField, PositionType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func