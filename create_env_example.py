"""
创建环境配置示例文件

此脚本用于创建后端和智能体的环境配置示例文件
"""

import os

# 后端环境配置示例
backend_env_example = """# 后端环境配置示例文件
# 数据库配置
MYSQL_SERVER=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=interview_analysis
MYSQL_PORT=3306

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# 数据库连接池配置
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# 安全配置
SECRET_KEY=your-secret-key-here

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 讯飞API配置
XUNFEI_APPID=your_xunfei_appid
XUNFEI_API_KEY=your_xunfei_api_key
XUNFEI_API_SECRET=your_xunfei_api_secret

# LLM服务配置（新增）
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://api.openai.com/v1  # OpenAI API基础URL
OPENAI_MODEL=gpt-3.5-turbo

# 讯飞星火大模型配置（新增）
SPARK_APPID=your_spark_appid
SPARK_API_KEY=your_spark_api_key
SPARK_API_SECRET=your_spark_api_secret
SPARK_API_URL=wss://spark-api.xfyun.cn/v1.1/chat  # 讯飞星火API URL
SPARK_MODEL=v2.0

# 其他LLM服务配置
LLM_SERVICE_PROVIDER=openai  # 可选：openai, spark, azure_openai
LLM_TIMEOUT=30  # API请求超时时间（秒）
LLM_TEMPERATURE=0.7  # 模型创造性，0-1之间，越大越创新
"""

# 智能体环境配置示例
agent_env_example = """# 智能体环境配置示例文件
# 通用配置
DEBUG=false
LOG_LEVEL=INFO
TEMP_DIR=./temp

# 讯飞API配置
XUNFEI_APPID=your_xunfei_appid
XUNFEI_API_KEY=your_xunfei_api_key
XUNFEI_API_SECRET=your_xunfei_api_secret

# LLM服务配置（新增）
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://api.openai.com/v1  # OpenAI API基础URL
OPENAI_MODEL=gpt-3.5-turbo

# 讯飞星火大模型配置（新增）
SPARK_APPID=your_spark_appid
SPARK_API_KEY=your_spark_api_key
SPARK_API_SECRET=your_spark_api_secret
SPARK_API_URL=wss://spark-api.xfyun.cn/v1.1/chat  # 讯飞星火API URL
SPARK_MODEL=v2.0

# 问题生成服务配置（新增）
QUESTION_GEN_MODEL=gpt-3.5-turbo  # 用于生成问题的模型
QUESTION_GEN_TEMPERATURE=0.7      # 问题生成的创造性
QUESTION_CACHE_DAYS=30            # 问题缓存天数
REFERENCE_ANSWER_MIN_LENGTH=200   # 参考答案最小长度
REFERENCE_ANSWER_MAX_LENGTH=1000  # 参考答案最大长度

# 服务集成配置
SERVICE_BASE_URL=http://localhost:8000  # 后端服务基础URL
"""

# 创建后端环境配置示例文件
with open('backend/.env.example', 'w', encoding='utf-8') as f:
    f.write(backend_env_example)
    print("创建后端环境配置示例文件成功：backend/.env.example")

# 创建智能体环境配置示例文件
with open('agent/.env.example', 'w', encoding='utf-8') as f:
    f.write(agent_env_example)
    print("创建智能体环境配置示例文件成功：agent/.env.example")

print("环境配置示例文件创建完成！") 