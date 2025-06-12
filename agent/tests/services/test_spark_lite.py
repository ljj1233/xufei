"""
测试讯飞星火Lite大模型功能

这个测试脚本专门用于验证星火Lite大模型API的功能，与语音识别API分开测试
"""

import os
import sys
import json
import asyncio
import time
import logging
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 将项目根目录添加到路径
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, '..', '..', '..'))
sys.path.insert(0, project_root)

from agent.src.services.async_xunfei_service import AsyncXunFeiService
from agent.src.core.system.config import AgentConfig

# 加载环境变量
load_dotenv()
DOTENV_PATH = os.path.join(project_root, 'agent', '.env')
if os.path.exists(DOTENV_PATH):
    load_dotenv(DOTENV_PATH)

async def test_spark_lite_chat():
    """测试星火Lite大模型的对话功能，包含详细的错误处理和日志记录"""
    print("\n" + "-" * 60)
    print("测试1: 星火Lite大模型对话功能测试")
    print("-" * 60)
    
    # 打印环境变量状态
    print("\n[环境变量检查]")
    env_vars = {
        'SPARK_APPID': os.environ.get('SPARK_APPID'),
        'SPARK_API_KEY': os.environ.get('SPARK_API_KEY'),
        'SPARK_API_SECRET': os.environ.get('SPARK_API_SECRET'),
        'SPARK_API_URL': os.environ.get('SPARK_API_URL', 'wss://spark-api.xf-yun.com/v1.1/chat')
    }
    
    for key, value in env_vars.items():
        status = '✅ 已设置' if value else '❌ 未设置'
        masked_value = value if not value or len(value) <= 4 else f"{value[:2]}******{value[-2:]}"
        print(f"{key}: {status} ({masked_value})")
    
    # 检查必要的环境变量
    required_vars = ['SPARK_APPID', 'SPARK_API_KEY', 'SPARK_API_SECRET']
    missing_vars = [var for var in required_vars if not env_vars[var]]
    
    if missing_vars:
        print(f"\n[错误] 以下环境变量未设置: {', '.join(missing_vars)}")
        print("请确保在.env文件中正确配置星火API的认证信息")
        return
    
    try:
        # 初始化配置
        config = AgentConfig()
        
        # 从环境变量更新配置
        if os.environ.get('SPARK_APPID'):
            config.config["services"]["xunfei"]["spark_app_id"] = os.environ.get('SPARK_APPID')
        if os.environ.get('SPARK_API_KEY'):
            config.config["services"]["xunfei"]["spark_api_key"] = os.environ.get('SPARK_API_KEY')
        if os.environ.get('SPARK_API_SECRET'):
            config.config["services"]["xunfei"]["spark_api_secret"] = os.environ.get('SPARK_API_SECRET')
        if os.environ.get('SPARK_API_URL'):
            config.config["services"]["xunfei"]["spark_api_url"] = os.environ.get('SPARK_API_URL')
            
        # 创建服务实例
        xunfei_service = AsyncXunFeiService(config)
        
        # 显示使用的配置
        print(f"\n[使用的配置]")
        print(f"  星火API URL: {xunfei_service.spark_api_url}")
        print(f"  星火APPID: {xunfei_service.spark_app_id[:4] + '****' if len(xunfei_service.spark_app_id) > 4 else '****'}")
        
        # 准备测试消息 - 包含一个需要联网搜索的问题
        messages = [
            {
                "role": "user", 
                "content": "请告诉我今天的日期和时间，以及当前北京的天气情况（需要实时数据）"
            }
        ]
        
        print("\n[发送请求到星火Lite大模型]")
        start_time = time.time()
        
        # 调用星火大模型，设置合理的超时时间
        try:
            result = await asyncio.wait_for(
                xunfei_service.chat_spark(messages, temperature=0.4, max_tokens=2048),
                timeout=15  # 设置15秒超时
            )
        except asyncio.TimeoutError:
            print("\n[错误] 请求超时，请检查网络连接或API服务状态")
            return
        
        # 计算耗时
        duration = time.time() - start_time
        print(f"  耗时: {duration:.2f}秒")
        
        # 详细处理返回结果
        if result.get('status') == 'success':
            print("\n[星火Lite回答]")
            print("-" * 60)
            print(result)
            print("-" * 60)
            print("[测试结果] 星火Lite对话功能测试成功!")
        else:
            error_msg = result.get('error', '未知错误')
            print(f"\n[测试结果] 星火Lite对话功能测试失败: {error_msg}")
            # 尝试解析错误码
            if "Code " in error_msg:
                error_code = error_msg.split("Code ")[1].split(":")[0]
                error_desc = error_msg.split(": ")[1]
                print(f"  错误码: {error_code}")
                print(f"  错误描述: {error_desc}")
                # 常见错误码提示
                error_tips = {
                    "10105": "应用未授权或IP地址不在白名单中，请检查讯飞控制台的应用配置",
                    "10104": "签名计算错误，请检查API_KEY和API_SECRET是否正确",
                    "10013": "内容包含违规信息，请修改输入内容",
                    "11200": "AppID未授权，请确认AppID已开通星火大模型服务"
                }
                if error_code in error_tips:
                    print(f"  解决方案: {error_tips[error_code]}")
            
    except aiohttp.ClientError as e:
        print(f"\n[网络错误] 连接星火API时发生错误: {str(e)}")
        print("  请检查网络连接是否正常，或API地址是否正确")
    except json.JSONDecodeError:
        print("\n[解析错误] 无法解析API响应，可能是响应格式不正确")
    except Exception as e:
        print(f"\n[未知错误] 测试过程中发生异常: {str(e)}")
        logger.exception("测试异常")

async def run_tests():
    """运行所有测试用例，包含更友好的界面显示"""
    # 设置控制台编码，解决中文乱码问题
    if sys.platform.startswith('win'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        
    print("\n" + "=" * 80)
    print("                        讯飞星火Lite大模型功能测试                        ")
    print("=" * 80)
    
    await test_spark_lite_chat()
    
    print("\n" + "=" * 80)
    print("                          星火Lite大模型测试完成                          ")
    print("=" * 80)

if __name__ == "__main__":
    try:
        asyncio.run(run_tests())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试框架发生错误: {str(e)}")
        sys.exit(1)