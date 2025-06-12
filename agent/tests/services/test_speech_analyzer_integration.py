"""
测试 SpeechAnalyzer 类的集成测试

使用真实讯飞API测试语音分析功能
"""

import os
import sys
import json
import wave
import math
import asyncio
import numpy as np
from dotenv import load_dotenv
import time

# 将项目根目录添加到路径
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path, '..', '..', '..'))
sys.path.insert(0, project_root)

from agent.src.analyzers.speech.speech_analyzer import SpeechAnalyzer
from agent.src.core.system.config import AgentConfig

# 测试配置
TEST_AUDIO_PATH = os.path.join(os.path.dirname(current_path), "test_integration_audio.wav")
DOTENV_PATH = os.path.join(project_root, 'agent', '.env')

# 加载环境变量
load_dotenv(dotenv_path=DOTENV_PATH, override=True)

def create_test_audio_file(filepath: str, duration: int = 10, sr: int = 16000):
    """创建一个测试用的WAV音频文件，包含正弦波音频内容
    
    Args:
        filepath: 音频文件保存路径
        duration: 音频时长（秒）
        sr: 采样率
    """
    print(f"\n正在创建测试音频文件: {filepath}")
    num_samples = duration * sr
    
    # 生成有实际内容的音频数据（使用正弦波）
    # 创建一个渐变音调的正弦波，更接近人声的频率特性
    audio_data = np.zeros(num_samples, dtype=np.int16)
    
    # 生成一个频率从300Hz到800Hz渐变的音调，模拟人声频率范围
    for i in range(num_samples):
        # 在时间上变化的频率 (300Hz 到 800Hz)
        freq = 300 + 500 * (i / num_samples)
        # 在时间上变化的音量 (先增大后减小)
        if i < num_samples / 2:
            amplitude = 10000 * (i / (num_samples / 2))
        else:
            amplitude = 10000 * (1 - (i - num_samples / 2) / (num_samples / 2))
        # 生成正弦波
        audio_data[i] = int(amplitude * math.sin(2 * math.pi * freq * i / sr))
    
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(1)  # 单声道
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sr) # 16kHz 采样率
        wf.writeframes(audio_data.tobytes())
    
    print(f"测试音频文件创建成功: {duration}秒, {sr}Hz 采样率")
    print(f"音频文件大小: {os.path.getsize(filepath)} 字节")

async def run_integration_test():
    """执行完整的端到端测试，使用真实的讯飞API"""
    start_time = time.time()
    
    # 设置控制台编码，解决中文乱码问题
    if sys.platform.startswith('win'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("\n" + "="*50)
    print("开始 SpeechAnalyzer 集成测试 - 使用真实讯飞API")
    print("="*50)
    
    # 打印环境变量状态
    print("\n环境变量状态:")
    env_vars = {
        'XUNFEI_APPID': os.environ.get('XUNFEI_APPID'),
        'XUNFEI_API_KEY': os.environ.get('XUNFEI_API_KEY'),
        'XUNFEI_API_SECRET': os.environ.get('XUNFEI_API_SECRET')
    }
    
    for key, value in env_vars.items():
        status = '已设置' if value else '未设置'
        if value and len(value) > 4:
            # 只显示密钥的前后两个字符，中间用星号代替
            masked_value = value[:2] + '*' * (len(value) - 4) + value[-2:]
            print(f"{key}: {status} ({masked_value})")
        else:
            print(f"{key}: {status}")
    
    if not all(env_vars.values()):
        print("\n警告: 讯飞API配置不完整，测试将失败!")
        missing_vars = [key for key, value in env_vars.items() if not value]
        print(f"缺失的环境变量: {', '.join(missing_vars)}")
        print(f"请确保在 {DOTENV_PATH} 文件中设置这些变量")
        
        # 创建示例.env文件
        print("\n可以创建一个包含以下内容的.env文件:")
        print("-----------------------------------")
        print("# 讯飞API配置")
        print("XUNFEI_APPID=你的讯飞APPID")
        print("XUNFEI_API_KEY=你的讯飞API_KEY")
        print("XUNFEI_API_SECRET=你的讯飞API_SECRET")
        print("-----------------------------------")
        return
    
    try:
        # 创建测试音频文件
        create_test_audio_file(TEST_AUDIO_PATH)
        
        # 初始化服务
        print("\n正在初始化 AgentConfig 和 SpeechAnalyzer...")
        config = AgentConfig()
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
                timeout=20.0  # 20秒超时
            )
            test_duration = time.time() - test_start
            
            print(f"语音转文字结果 ({test_duration:.2f}秒):")
            if transcript:
                print(f"'{transcript}'")
            else:
                print("(空结果 - 这可能是正常的，因为测试音频不包含实际语音)")
        except asyncio.TimeoutError:
            print("错误: 语音转文字超时 (>20秒)")
        except Exception as e:
            print(f"错误: 语音转文字失败: {e}")
        
        # 测试2: 提取特征
        print("\n" + "-"*40)
        print("测试2: 提取音频特征...")
        print("-"*40)
        
        try:
            test_start = time.time()
            features = await asyncio.wait_for(
                speech_analyzer.extract_features_async(TEST_AUDIO_PATH),
                timeout=20.0  # 20秒超时
            )
            test_duration = time.time() - test_start
            
            if features:
                print(f"提取到 {len(features)} 个特征 ({test_duration:.2f}秒)")
                # 显示主要特征名称
                print("特征列表:", ", ".join(list(features.keys())[:5]) + 
                      (f" 和 {len(features)-5} 个其他特征..." if len(features) > 5 else ""))
                # 保存特征到文件以便分析
                save_to_file(features, "speech_features.json")
            else:
                print(f"警告: 未提取到特征 ({test_duration:.2f}秒)")
        except asyncio.TimeoutError:
            print("错误: 特征提取超时 (>20秒)")
        except Exception as e:
            print(f"错误: 特征提取失败: {e}")
        
        # 测试3: 异步分析 - 基于规则
        print("\n" + "-"*40)
        print("测试3: 异步分析 (规则方法)...")
        print("-"*40)
        
        try:
            test_start = time.time()
            result = await asyncio.wait_for(
                speech_analyzer.analyze_async(TEST_AUDIO_PATH),
                timeout=30.0  # 30秒超时
            )
            test_duration = time.time() - test_start
            
            if result:
                print(f"规则分析完成 ({test_duration:.2f}秒)")
                total_score = result.get("total_score", "N/A")
                print(f"总分: {total_score}")
                
                # 显示维度评分
                dimensions = result.get("dimensions", {})
                if dimensions:
                    print("\n维度评分:")
                    for dim_name, dim_data in dimensions.items():
                        score = dim_data.get("score", "N/A")
                        print(f"- {dim_name}: {score}")
                
                # 保存结果到文件
                save_to_file(result, "speech_analysis_rule.json")
            else:
                print(f"警告: 分析返回空结果 ({test_duration:.2f}秒)")
        except asyncio.TimeoutError:
            print("错误: 规则分析超时 (>30秒)")
        except Exception as e:
            print(f"错误: 规则分析失败: {e}")
        
        # 测试4: 异步分析 - 使用LLM (如果可用)
        print("\n" + "-"*40)
        print("测试4: 异步分析 (LLM方法)...")
        print("-"*40)
        
        if speech_analyzer.use_xunfei_llm:
            try:
                print("正在调用讯飞星火大模型，这可能需要较长时间...")
                test_start = time.time()
                llm_result = await asyncio.wait_for(
                    speech_analyzer.analyze_with_llm(TEST_AUDIO_PATH),
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
                    
                    # 保存结果到文件
                    save_to_file(llm_result, "speech_analysis_llm.json")
                else:
                    print(f"警告: LLM分析返回空结果 ({test_duration:.2f}秒)")
            except asyncio.TimeoutError:
                print("错误: LLM分析超时 (>60秒)")
            except Exception as e:
                print(f"错误: LLM分析失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("LLM分析未启用，跳过此测试")
        
        total_duration = time.time() - start_time
        print("\n" + "="*50)
        print(f"集成测试完成! 总耗时: {total_duration:.2f}秒")
        print("="*50)
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试文件
        if os.path.exists(TEST_AUDIO_PATH):
            os.remove(TEST_AUDIO_PATH)
            print(f"\n已清理测试音频文件: {TEST_AUDIO_PATH}")

def save_to_file(data, filename):
    """将数据保存到JSON文件"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 {filename}")
    except Exception as e:
        print(f"保存数据到文件失败: {e}")

# 直接运行脚本时执行集成测试
if __name__ == "__main__":
    # 在Windows上，设置事件循环策略以避免一些异步错误
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # 运行集成测试
    asyncio.run(run_integration_test()) 