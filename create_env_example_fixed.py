"""
创建环境配置示例文件（修复编码问题）

此脚本用于创建后端和智能体的环境配置示例文件，确保使用正确的编码
"""

import os

# 后端环境配置示例
backend_env_example = """# Backend Environment Configuration Example
# Database Configuration
MYSQL_SERVER=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=interview_analysis
MYSQL_PORT=3306

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Database Connection Pool Configuration
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# Security Configuration
SECRET_KEY=your-secret-key-here

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Xunfei API Configuration
XUNFEI_APPID=your_xunfei_appid
XUNFEI_API_KEY=your_xunfei_api_key
XUNFEI_API_SECRET=your_xunfei_api_secret

# LLM Service Configuration (New)
# ModelScope Configuration
OPENAI_API_KEY=your_modelscope_api_key
OPENAI_API_BASE=https://api-inference.modelscope.cn/v1/
OPENAI_MODEL=Qwen/Qwen2.5-7B-Instruct

# Spark Big Model Configuration (New)
SPARK_APPID=your_spark_appid
SPARK_API_KEY=your_spark_api_key
SPARK_API_SECRET=your_spark_api_secret
SPARK_API_URL=wss://spark-api.xfyun.cn/v1.1/chat

# LLM Provider Selection (New)
# Options: modelscope, xunfei
LLM_PROVIDER=modelscope
"""

# 智能体环境配置示例
agent_env_example = """# Agent Environment Configuration Example
# Xunfei API Configuration
XUNFEI_APPID=your_xunfei_appid
XUNFEI_API_KEY=your_xunfei_api_key
XUNFEI_API_SECRET=your_xunfei_api_secret

# Xunfei Service URLs
XUNFEI_ISE_URL=https://api.xfyun.cn/v1/service/v1/ise
XUNFEI_IAT_URL=https://api.xfyun.cn/v1/service/v1/iat
XUNFEI_EMOTION_URL=https://api.xfyun.cn/v1/service/v1/emotion

# LLM Service Configuration (New)
# ModelScope Configuration
OPENAI_API_KEY=your_modelscope_api_key
OPENAI_API_BASE=https://api-inference.modelscope.cn/v1/
OPENAI_MODEL=Qwen/Qwen2.5-7B-Instruct

# Spark Big Model Configuration (New)
SPARK_APPID=your_spark_appid
SPARK_API_KEY=your_spark_api_key
SPARK_API_SECRET=your_spark_api_secret
SPARK_API_URL=wss://spark-api.xfyun.cn/v1.1/chat

# LLM Provider Selection (New)
# Options: modelscope, xunfei
LLM_PROVIDER=modelscope

# Question Generation Service Configuration
QUESTION_CACHE_EXPIRATION=3600  # Cache expiration time in seconds
QUESTION_GENERATION_MODEL=Qwen/Qwen2.5-7B-Instruct  # Model for question generation
"""

# 创建后端环境配置示例文件
with open("backend/.env.example", "w", encoding="utf-8") as f:
    f.write(backend_env_example)
    print("创建后端环境配置示例文件成功: backend/.env.example")

# 创建智能体环境配置示例文件
with open("agent/.env.example", "w", encoding="utf-8") as f:
    f.write(agent_env_example)
    print("创建智能体环境配置示例文件成功: agent/.env.example")

print("环境配置示例文件创建完成") 