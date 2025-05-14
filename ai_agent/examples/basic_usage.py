# ai_agent/examples/basic_usage.py

"""
多模态面试评测智能体库使用示例

本示例展示了如何使用AI智能体库进行面试分析
"""

import os
import json
from ai_agent.core.agent import InterviewAgent

# 创建智能体实例
agent = InterviewAgent()

def analyze_interview_file(file_path):
    """分析面试文件
    
    Args:
        file_path: 面试文件路径（视频或音频）
    """
    print(f"\n正在分析面试文件: {file_path}")
    
    # 自动检测文件类型
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".mp4", ".avi", ".mov", ".wmv"]:
        file_type = "video"
    elif ext in [".mp3", ".wav", ".ogg", ".flac"]:
        file_type = "audio"
    else:
        raise ValueError(f"不支持的文件类型: {ext}")
    
    print(f"文件类型: {file_type}")
    
    # 调用智能体进行分析
    result = agent.analyze(file_path=file_path)
    
    # 打印分析结果
    print("\n===== 分析结果 =====")
    
    # 打印语音分析结果
    speech_analysis = result.get_speech_analysis()
    print("\n语音分析:")
    print(f"  清晰度: {speech_analysis.get('clarity', 0):.1f}/10")
    print(f"  语速: {speech_analysis.get('pace', 0):.1f}/10")
    print(f"  情感: {speech_analysis.get('emotion', '未知')}")
    print(f"  语音总分: {speech_analysis.get('overall_score', 0):.1f}/10")
    
    # 如果是视频，打印视觉分析结果
    if file_type == "video":
        visual_analysis = result.get_visual_analysis()
        print("\n视觉分析:")
        print(f"  眼神接触: {visual_analysis.get('eye_contact', 0):.1f}/10")
        print(f"  面部表情: {visual_analysis.get('facial_expressions', {}).get('score', 0):.1f}/10")
        print(f"  肢体语言: {visual_analysis.get('body_language', {}).get('score', 0):.1f}/10")
        print(f"  视觉总分: {visual_analysis.get('overall_score', 0):.1f}/10")
    
    # 打印内容分析结果
    content_analysis = result.get_content_analysis()
    print("\n内容分析:")
    print(f"  相关性: {content_analysis.get('relevance', 0):.1f}/10")
    print(f"  结构: {content_analysis.get('structure', 0):.1f}/10")
    print("  关键点:")
    for point in content_analysis.get('key_points', []):
        print(f"    - {point}")
    print(f"  内容总分: {content_analysis.get('overall_score', 0):.1f}/10")
    
    # 打印综合评估
    print("\n综合评估:")
    print(f"  总分: {result.get_overall_score():.1f}/10")
    
    print("\n优势:")
    for strength in result.get_strengths():
        print(f"  - {strength}")
    
    print("\n劣势:")
    for weakness in result.get_weaknesses():
        print(f"  - {weakness}")
    
    print("\n改进建议:")
    for suggestion in result.get_suggestions():
        print(f"  - {suggestion}")


def analyze_with_custom_params(file_path):
    """使用自定义参数分析面试文件
    
    Args:
        file_path: 面试文件路径（视频或音频）
    """
    print(f"\n使用自定义参数分析面试文件: {file_path}")
    
    # 自定义分析参数
    custom_params = {
        # 调整权重
        "speech_weight": 0.4,       # 增加语音分析的权重
        "visual_weight": 0.2,       # 减少视觉分析的权重
        "content_weight": 0.4,      # 保持内容分析的权重
        
        # 指定关注领域
        "focus_areas": ["coding_skills", "communication"],
        
        # 调整输出数量
        "strengths_count": 2,       # 只输出2个优势
        "weaknesses_count": 2,      # 只输出2个劣势
        "suggestions_count": 3,     # 只输出3个建议
    }
    
    # 调用智能体进行分析，指定场景和自定义参数
    result = agent.analyze(
        file_path=file_path,
        scenario="tech_interview",  # 指定为技术面试场景
        params=custom_params
    )
    
    # 打印分析结果
    print("\n===== 自定义分析结果 =====")
    print(f"总分: {result.get_overall_score():.1f}/10")
    
    print("\n优势 (最多2项):")
    for strength in result.get_strengths():
        print(f"  - {strength}")
    
    print("\n劣势 (最多2项):")
    for weakness in result.get_weaknesses():
        print(f"  - {weakness}")
    
    print("\n改进建议 (最多3项):")
    for suggestion in result.get_suggestions():
        print(f"  - {suggestion}")


def save_analysis_to_json(file_path, output_path):
    """将分析结果保存为JSON文件
    
    Args:
        file_path: 面试文件路径（视频或音频）
        output_path: 输出JSON文件路径
    """
    print(f"\n分析面试文件并保存结果: {file_path} -> {output_path}")
    
    # 调用智能体进行分析
    result = agent.analyze(file_path=file_path)
    
    # 获取完整分析结果
    full_analysis = result.get_full_analysis()
    
    # 保存为JSON文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(full_analysis, f, ensure_ascii=False, indent=2)
    
    print(f"分析结果已保存到: {output_path}")


if __name__ == "__main__":
    # 示例面试文件路径（需要替换为实际文件路径）
    sample_video = "path/to/interview.mp4"
    sample_audio = "path/to/interview.mp3"
    
    # 检查示例文件是否存在
    if os.path.exists(sample_video):
        # 基本分析示例
        analyze_interview_file(sample_video)
        
        # 自定义参数分析示例
        analyze_with_custom_params(sample_video)
        
        # 保存分析结果示例
        save_analysis_to_json(sample_video, "interview_analysis.json")
    elif os.path.exists(sample_audio):
        # 使用音频文件作为替代
        analyze_interview_file(sample_audio)
    else:
        print("示例文件不存在，请修改文件路径后再运行。")
        print("您可以使用任何MP4视频文件或MP3音频文件进行测试。")