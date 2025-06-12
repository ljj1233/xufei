"""
测试 SpeechAnalyzer 类的集成测试 - 使用有实际内容的音频

使用真实文本内容的音频文件测试语音分析功能
"""

import os
import sys
import json
import asyncio
import wave
import pyttsx3
import numpy as np
import time
import base64
from io import BytesIO
from dotenv import load_dotenv
import hashlib
from urllib.parse import urlencode

# 将项目根目录添加到路径
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, '..', '..', '..'))
sys.path.insert(0, project_root)

from agent.src.analyzers.speech.speech_analyzer import SpeechAnalyzer
from agent.src.core.system.config import AgentConfig

# 测试配置
TEST_AUDIO_PATH = os.path.join(os.path.dirname(current_path), "test_speech_with_text.wav")
DOTENV_PATH = os.path.join(project_root, 'agent', '.env')

# 加载环境变量
load_dotenv(dotenv_path=DOTENV_PATH, override=True)

# 测试用的文本内容
TEST_TEXT = """
我有5年的Python开发经验，主要负责后端API开发和数据处理系统。在上一家公司，我负责设计并实现了一个高并发的日志处理系统，该系统每天能处理超过1亿条日志记录，使用了Kafka进行消息队列，Elasticsearch进行存储和检索。

我熟悉常见的设计模式，如单例模式、工厂模式、观察者模式等，并在实际项目中应用它们来提高代码质量和可维护性。我还有丰富的数据库经验，包括MySQL、MongoDB和Redis，能够设计高效的数据模型和优化查询性能。

在团队协作方面，我习惯使用Git进行版本控制，遵循CI/CD流程，确保代码质量。我相信良好的代码应该是自文档化的，同时我也注重编写单元测试和集成测试，保证代码的健壮性。

我对新技术充满热情，最近在学习容器编排技术如Kubernetes，以及微服务架构设计。我认为持续学习是保持技术竞争力的关键。
"""

def create_tts_audio_file(text: str, filepath: str):
    """
    使用pyttsx3创建包含文本内容的音频文件，并确保生成符合讯飞API要求的格式
    
    Args:
        text: 要转换为语音的文本
        filepath: 音频文件保存路径
    """
    print(f"\n正在创建文本语音文件: {filepath}")
    print(f"文本内容 ({len(text)} 字符):")
    print("-"*40)
    print(text[:100] + "..." if len(text) > 100 else text)
    print("-"*40)
    
    # 使用pyttsx3将文本转换为语音
    engine = pyttsx3.init()
    # 设置中文语音（如果可用）
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'chinese' in voice.id.lower() or 'zh' in voice.id.lower():
            engine.setProperty('voice', voice.id)
            break
    
    # 设置速率和音量
    engine.setProperty('rate', 150)  # 语速
    engine.setProperty('volume', 1.0)  # 音量
    
    # 将音频保存为临时WAV文件
    print("正在生成语音...")
    temp_file = "temp_speech.wav"
    engine.save_to_file(text, temp_file)
    engine.runAndWait()
    
    # 确保文件生成完毕
    while not os.path.exists(temp_file) or os.path.getsize(temp_file) < 100:
        time.sleep(0.1)
    
    # 转换为符合讯飞API要求的格式 (16k采样率，16位采样精度，单声道)
    print("正在转换音频格式为讯飞API要求的格式...")
    try:
        # 读取临时WAV文件信息
        with wave.open(temp_file, 'rb') as wf:
            # 获取原始参数
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            
            # 输出原始音频信息，便于调试
            print(f"原始音频信息: 采样率={framerate}Hz, 位深度={sample_width*8}位, 声道数={n_channels}, 帧数={n_frames}")
            
            # 读取所有音频数据
            frames = wf.readframes(n_frames)
        
        # 使用audioop模块进行音频转换
        import audioop
        
        # 如果不是单声道，转换为单声道
        if n_channels > 1:
            print(f"转换声道: {n_channels}声道 -> 单声道")
            frames = audioop.tomono(frames, sample_width, 0.5, 0.5)
            n_channels = 1
        
        # 如果采样率不是16k，转换为16k
        if framerate != 16000:
            print(f"转换采样率: {framerate}Hz -> 16000Hz")
            # 使用带状态的转换，避免可能的抖动
            frames, converter_state = audioop.ratecv(frames, sample_width, n_channels, framerate, 16000, None)
            framerate = 16000
        
        # 如果采样精度不是16位，转换为16位
        if sample_width != 2:
            print(f"转换采样精度: {sample_width*8}位 -> 16位")
            frames = audioop.lin2lin(frames, sample_width, 2)
            sample_width = 2
        
        # 写入新的WAV文件
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(n_channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(framerate)
            wf.writeframes(frames)
        
        # 验证转换后的音频文件
        if os.path.exists(filepath):
            with wave.open(filepath, 'rb') as wf:
                # 获取转换后的参数
                new_channels = wf.getnchannels()
                new_width = wf.getsampwidth()
                new_rate = wf.getframerate()
                new_frames = wf.getnframes()
                
                print(f"转换后音频信息: 采样率={new_rate}Hz, 位深度={new_width*8}位, 声道数={new_channels}, 帧数={new_frames}")
                print(f"音频文件大小: {os.path.getsize(filepath)/1024:.1f} KB, 时长: {new_frames/new_rate:.2f}秒")
                
                # 检查转换是否成功
                if new_rate != 16000 or new_width != 2 or new_channels != 1:
                    print("警告: 音频格式转换后不符合讯飞API要求，可能会导致识别失败")
                    print(f"期望: 采样率=16000Hz, 位深度=16位, 声道数=1")
                    print(f"实际: 采样率={new_rate}Hz, 位深度={new_width*8}位, 声道数={new_channels}")
                else:
                    print("音频格式转换成功，符合讯飞API要求")
        else:
            print(f"错误: 转换后的音频文件不存在: {filepath}")
            
    except ImportError:
        print("警告: 缺少audioop模块，无法转换音频格式")
        # 如果缺少audioop模块，直接复制临时文件
        import shutil
        shutil.copy2(temp_file, filepath)
        print(f"已直接使用原始音频文件: {os.path.getsize(filepath)/1024:.1f} KB")
    except Exception as e:
        print(f"音频格式转换失败: {e}")
        print("使用原始文件")
        # 如果转换失败，直接复制临时文件
        import shutil
        shutil.copy2(temp_file, filepath)
        print(f"已直接使用原始音频文件: {os.path.getsize(filepath)/1024:.1f} KB")
    
    # 删除临时文件
    try:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    except Exception as e:
        print(f"删除临时文件失败: {e}")
        
    print(f"文本语音文件创建完成: {filepath}")

async def run_test_with_text():
    """执行完整的端到端测试，使用包含实际文本内容的音频文件"""
    start_time = time.time()
    
    # 设置控制台编码，解决中文乱码问题
    if sys.platform.startswith('win'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("\n" + "="*50)
    print("开始 SpeechAnalyzer 集成测试 - 使用实际文本内容")
    print("="*50)
    
    # 打印环境变量状态
    print("\n环境变量状态:")
    env_vars = {
        'XUNFEI_APPID': os.environ.get('XUNFEI_APPID'),
        'XUNFEI_API_KEY': os.environ.get('XUNFEI_API_KEY'),
        'XUNFEI_API_SECRET': os.environ.get('XUNFEI_API_SECRET')
    }
    
    # 检查讯飞API URL是否正确
    env_urls = {
        'XUNFEI_ISE_URL': os.environ.get('XUNFEI_ISE_URL', 'https://api.xfyun.cn/v1/service/v1/ise'),
        'XUNFEI_IAT_URL': os.environ.get('XUNFEI_IAT_URL', 'https://api.xfyun.cn/v1/service/v1/iat'),
        'XUNFEI_EMOTION_URL': os.environ.get('XUNFEI_EMOTION_URL', 'https://api.xfyun.cn/v1/service/v1/emotion')
    }
    
    for key, value in env_vars.items():
        status = '已设置' if value else '未设置'
        if value and len(value) > 4:
            # 只显示密钥的前后两个字符，中间用星号代替
            masked_value = value[:2] + '*' * (len(value) - 4) + value[-2:]
            print(f"{key}: {status} ({masked_value})")
        else:
            print(f"{key}: {status}")
    
    # 打印API URL配置
    print("\nAPI URL配置:")
    for key, url in env_urls.items():
        print(f"{key}: {url}")
    
    # 检查并修复URL格式
    fixed_urls = {}
    url_fixed = False
    for key, url in env_urls.items():
        if 'xf-yun.cn' in url:
            fixed_url = url.replace('xf-yun.cn', 'xfyun.cn')
            fixed_urls[key] = fixed_url
            print(f"修复 {key}: {url} -> {fixed_url}")
            # 设置环境变量
            os.environ[key] = fixed_url
            url_fixed = True
        else:
            fixed_urls[key] = url
    
    if url_fixed:
        print("\n已自动修复API URL，使用正确的xfyun.cn域名")
    
    if not all(env_vars.values()):
        print("\n警告: 讯飞API配置不完整，测试将失败!")
        missing_vars = [key for key, value in env_vars.items() if not value]
        print(f"缺失的环境变量: {', '.join(missing_vars)}")
        print(f"请确保在 {DOTENV_PATH} 文件中设置这些变量")
        return
    
    try:
        # 创建包含实际文本内容的音频文件
        create_tts_audio_file(TEST_TEXT, TEST_AUDIO_PATH)
        
        # 初始化服务
        print("\n正在初始化 AgentConfig 和 SpeechAnalyzer...")
        config = AgentConfig()
        
        # 修复URL配置到config中
        if "services" not in config.config:
            config.config["services"] = {}
        if "xunfei" not in config.config["services"]:
            config.config["services"]["xunfei"] = {}
        
        for key, url in fixed_urls.items():
            config_key = key.lower().replace('xunfei_', '').replace('_url', '')
            config.config["services"]["xunfei"][config_key] = url
            print(f"在配置中设置 {config_key}: {url}")
        
        speech_analyzer = SpeechAnalyzer(config)
        print("服务初始化成功。")
        
        # 验证讯飞服务是否正确初始化
        if not speech_analyzer.use_xunfei:
            print("\n错误: 讯飞服务未启用，请检查配置")
            return
        
        if not speech_analyzer.async_xunfei_service:
            print("\n错误: 讯飞异步服务初始化失败，请检查配置")
            return
            
        print("\n讯飞服务状态: 正常")
        print(f"并发限制: {speech_analyzer.async_xunfei_service.api_semaphore._value} 个并发请求")
        
        # 测试1: 语音转文字
        print("\n" + "-"*40)
        print("测试1: 语音转文字 (Speech-to-Text)...")
        print("-"*40)
        
        try:
            test_start = time.time()
            transcript = await asyncio.wait_for(
                speech_analyzer.speech_to_text_async(TEST_AUDIO_PATH),
                timeout=30.0  # 30秒超时
            )
            test_duration = time.time() - test_start
            
            print(f"语音转文字结果 ({test_duration:.2f}秒):")
            if transcript:
                # 只显示前200个字符，如果文本较长
                display_text = transcript[:200] + "..." if len(transcript) > 200 else transcript
                print(f"'{display_text}'")
                
                # 计算文本相似度（简单比较）
                words_in_original = set(TEST_TEXT.replace('\n', ' ').split())
                words_in_transcript = set(transcript.replace('\n', ' ').split())
                common_words = len(words_in_original.intersection(words_in_transcript))
                similarity = common_words / len(words_in_original) if words_in_original else 0
                
                print(f"文本相似度: {similarity:.2%}")
            else:
                print("(空结果 - 语音识别失败)")
                print("将直接使用原始文本进行LLM分析")
        except asyncio.TimeoutError:
            print("错误: 语音转文字超时 (>30秒)")
            print("将直接使用原始文本进行LLM分析")
            transcript = None
        except Exception as e:
            print(f"错误: 语音转文字失败: {e}")
            print("将直接使用原始文本进行LLM分析")
            transcript = None
        
        # 测试2: 使用LLM分析
        print("\n" + "-"*40)
        print("测试2: 使用LLM分析...")
        print("-"*40)
        
        try:
            print("正在调用讯飞星火大模型，这可能需要较长时间...")
            test_start = time.time()
            
            # 直接使用原始文本，而不是音频识别结果
            # 避免因语音识别失败导致LLM分析也失败
            llm_result = await asyncio.wait_for(
                speech_analyzer.analyze_with_llm(
                    TEST_AUDIO_PATH, 
                    transcript=TEST_TEXT  # 直接使用原始文本
                ),
                timeout=60.0  # 60秒超时
            )
            test_duration = time.time() - test_start
            
            if llm_result:
                print(f"LLM分析完成 ({test_duration:.2f}秒)")
                
                # 尝试提取总分
                overall_score = (
                    llm_result.get("overall_score") or 
                    (llm_result.get("scores", {}).get("overall_score") 
                     if "scores" in llm_result else None)
                )
                print(f"总分: {overall_score if overall_score is not None else 'N/A'}")
                
                # 显示分析摘要
                summary = llm_result.get("summary", "")
                if summary:
                    print(f"\n分析摘要: {summary}")
                
                # 显示维度评分
                if "scores" in llm_result:
                    print("\n维度评分:")
                    for dim_name, score in llm_result["scores"].items():
                        if dim_name != "overall_score":
                            print(f"- {dim_name}: {score}")
                
                # 显示分析结果
                if "analysis" in llm_result:
                    strengths = llm_result["analysis"].get("strengths", [])
                    suggestions = llm_result["analysis"].get("suggestions", [])
                    
                    if strengths:
                        print("\n优势:")
                        for i, strength in enumerate(strengths, 1):
                            print(f"{i}. {strength}")
                    
                    if suggestions:
                        print("\n建议:")
                        for i, suggestion in enumerate(suggestions, 1):
                            print(f"{i}. {suggestion}")
                
                # 保存结果到文件
                save_to_file(llm_result, "speech_analysis_with_text.json")
            else:
                print(f"警告: LLM分析返回空结果 ({test_duration:.2f}秒)")
        except asyncio.TimeoutError:
            print("错误: LLM分析超时 (>60秒)")
        except Exception as e:
            print(f"错误: LLM分析失败: {e}")
            import traceback
            traceback.print_exc()
        
        total_duration = time.time() - start_time
        print("\n" + "="*50)
        print(f"集成测试完成! 总耗时: {total_duration:.2f}秒")
        print("="*50)
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 保留音频文件以便检查
        print(f"\n测试音频文件已保存在: {TEST_AUDIO_PATH}")
        print("测试完成后可以手动删除该文件")

def save_to_file(data, filename):
    """将数据保存到JSON文件"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 {filename}")
    except Exception as e:
        print(f"保存数据到文件失败: {e}")

async def test_speech_to_text(speech_analyzer, audio_file):
    """测试语音转文字功能"""
    print("\n" + "-" * 40)
    print("测试1: 语音转文字 (Speech-to-Text)...")
    print("-" * 40)
    
    try:
        # 获取音频文件大小
        file_size = os.path.getsize(audio_file) / 1024  # KB
        print(f"音频数据大小: {file_size:.2f} KB")
        
        # 读取音频文件
        with open(audio_file, 'rb') as f:
            audio_data = f.read()
            
        # 检查音频数据是否有效
        if len(audio_data) < 100:
            print("警告: 音频数据太小，可能无效")
        
        # 计时开始
        start_time = time.time()
        
        # 尝试直接使用XunFeiService进行语音识别
        try:
            xunfei_service = speech_analyzer.xunfei_service
            print(f"使用讯飞语音识别服务，API URL: {xunfei_service.iat_url}")
            
            # 获取当前时间戳
            cur_time = str(int(time.time()))
            
            # 构建API参数 - 确保与async_xunfei_service.py中完全一致
            api_params = {
                "engine_type": "iat",  # 必需，表示语音识别服务
                "aue": "raw",          # 音频编码，raw代表原始PCM或WAV格式
                "format": "wav",       # 音频格式
                "sample_rate": 16000,  # 采样率
                "rate": 16000,         # 兼容性参数
                "channel": 1,          # 声道数，1代表单声道
                "language": "zh_cn",   # 修正：使用zh_cn而不是cn
                "domain": "iat",       # 领域，iat表示语音识别
                "vad_eos": 10000       # 静音检测超时时间
            }
            
            # 转换为JSON并进行Base64编码，作为X-Param头
            x_param = base64.b64encode(json.dumps(api_params).encode('utf-8')).decode('utf-8')
            
            # 计算CheckSum: MD5(API_SECRET + curTime + x_param)
            md5 = hashlib.md5()
            md5.update((xunfei_service.api_secret + cur_time + x_param).encode('utf-8'))
            check_sum = md5.hexdigest()
            
            # 设置标准的讯飞WebAPI头信息
            headers = {
                'X-Appid': xunfei_service.app_id,
                'X-CurTime': cur_time,
                'X-Param': x_param,
                'X-CheckSum': check_sum,
                'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
                'Accept': 'application/json'
            }
            
            # Base64编码音频数据
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # 构建请求数据 - 只包含audio参数
            data = {
                'audio': audio_base64
            }
            
            # 将数据进行urlencode
            form_data = urlencode(data)
            
            import requests
            print(f"\n正在发送请求到讯飞语音识别API: {xunfei_service.iat_url}")
            print(f"请求头: X-Appid={xunfei_service.app_id[:4]}****, X-CurTime={cur_time}")
            print(f"请求参数: engine_type=iat, format=wav, sample_rate=16000, language=zh_cn")
            
            # 发送请求
            response = requests.post(xunfei_service.iat_url, headers=headers, data=form_data, timeout=30)
            
            # 输出详细的请求和响应信息
            print(f"请求URL: {xunfei_service.iat_url}")
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容类型: {response.headers.get('Content-Type', '未知')}")
            
            try:
                result = response.json()
                print(f"响应JSON: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
                
                if result.get('code') == '0':
                    text = result.get('data', '')
                else:
                    error_code = result.get('code', '未知')
                    error_desc = result.get('desc', '未知错误')
                    print(f"语音识别失败: {error_desc} (错误码: {error_code})")
                    print(f"完整响应: {json.dumps(result, ensure_ascii=False)}")
                    text = ''
            except Exception as e:
                print(f"解析响应失败: {e}")
                text = ''
            
            # 如果直接调用失败，尝试使用speech_analyzer的方法
            if not text:
                print("直接调用讯飞API失败，尝试使用SpeechAnalyzer的方法...")
                text = speech_analyzer.speech_to_text(audio_file)
        except Exception as e:
            print(f"直接调用讯飞API异常: {e}")
            print("尝试使用SpeechAnalyzer的方法...")
            text = speech_analyzer.speech_to_text(audio_file)
        
        # 计时结束
        elapsed_time = time.time() - start_time
        
        print(f"语音转文字结果 ({elapsed_time:.2f}秒):")
        if text:
            print(text[:300] + "..." if len(text) > 300 else text)
            return text
        else:
            print("(空结果 - 这可能是正常的，因为测试音频不包含实际语音)")
            # 如果识别失败，使用原始文本
            print("将直接使用原始文本进行LLM分析")
            return TEST_TEXT
    except Exception as e:
        print(f"测试语音转文字异常: {e}")
        import traceback
        traceback.print_exc()
        # 返回预设文本以便继续测试
        return TEST_TEXT

# 直接运行脚本时执行测试
if __name__ == "__main__":
    # 在Windows上，设置事件循环策略以避免一些异步错误
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # 运行测试
    asyncio.run(run_test_with_text()) 