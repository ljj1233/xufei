# 导出所有模型
from .user import UserBase, UserCreate, UserInDB, User
from .interview import InterviewBase, InterviewCreate, InterviewInDB, Interview
from .analysis import AnalysisBase, SpeechAnalysis, VisualAnalysis, ContentAnalysis, OverallAnalysis, AnalysisCreate, AnalysisInDB, Analysis
from .job_position import JobPositionBase, JobPositionCreate, JobPositionInDB, JobPosition
from .token import Token, TokenPayload
from .file import FileUploadResponse

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
    # 令牌模型
    'Token', 'TokenPayload',
    # 文件模型
    'FileUploadResponse'
]