# 此文件用于向后兼容，实际模型已移至app.schemas包
# 重定向导入以保持现有代码兼容性

from app.schemas.user import UserBase, UserCreate, UserInDB, User
from app.schemas.interview import InterviewBase, InterviewCreate, InterviewInDB, Interview
from app.schemas.analysis import AnalysisBase, SpeechAnalysis, VisualAnalysis, ContentAnalysis, OverallAnalysis, AnalysisCreate, AnalysisInDB, Analysis
from app.schemas.job_position import JobPositionBase, JobPositionCreate, JobPositionInDB, JobPosition, TechField, PositionType
from app.schemas.token import Token, TokenPayload
from app.schemas.file import FileUploadResponse

# 导出所有模型
__all__ = [
    # 用户模型
    'UserBase', 'UserCreate', 'UserInDB', 'User',
    # 面试模型
    'InterviewBase', 'InterviewCreate', 'InterviewInDB', 'Interview',
    # 分析模型
    'AnalysisBase', 'SpeechAnalysis', 'VisualAnalysis', 'ContentAnalysis', 
    'OverallAnalysis', 'AnalysisCreate', 'AnalysisInDB', 'Analysis',
    # 职位模型
    'JobPositionBase', 'JobPositionCreate', 'JobPositionInDB', 'JobPosition',
    'TechField', 'PositionType',
    # 令牌模型
    'Token', 'TokenPayload',
    # 文件模型
    'FileUploadResponse'
]