import os
import numpy as np
import cv2
import librosa
import json
from typing import Dict, Any, List, Optional
import torch
from transformers import AutoTokenizer, AutoModel

from app.core.config import settings


def analyze_interview(file_path: str, file_type: str) -> Dict[str, Any]:
    """分析面试视频/音频
    
    对面试文件进行多模态分析，包括语音、视觉和内容分析
    
    Args:
        file_path: 文件路径
        file_type: 文件类型（video或audio）
        
    Returns:
        Dict[str, Any]: 分析结果
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 初始化结果
    result = {
        "speech": {},
        "visual": {},
        "content": {},
        "overall": {}
    }
    
    # 提取音频特征
    speech_features = extract_speech_features(file_path)
    result["speech"] = analyze_speech(speech_features)
    
    # 如果是视频，提取视觉特征
    if file_type == "video":
        visual_features = extract_visual_features(file_path)
        result["visual"] = analyze_visual(visual_features)
    
    # 提取文本内容（从语音转文本）
    text_content = speech_to_text(file_path)
    result["content"] = analyze_content(text_content)
    
    # 综合分析
    result["overall"] = generate_overall_analysis(result)
    
    return result


def extract_speech_features(file_path: str) -> Dict[str, Any]:
    """提取语音特征
    
    从音频文件中提取语音特征
    
    Args:
        file_path: 文件路径
        
    Returns:
        Dict[str, Any]: 语音特征
    """
    # 这里是示例实现，实际项目中应使用更复杂的语音处理
    try:
        # 加载音频文件
        y, sr = librosa.load(file_path, sr=None)
        
        # 提取特征
        features = {
            "mfcc": librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1),
            "spectral_centroid": librosa.feature.spectral_centroid(y=y, sr=sr).mean(),
            "spectral_bandwidth": librosa.feature.spectral_bandwidth(y=y, sr=sr).mean(),
            "spectral_rolloff": librosa.feature.spectral_rolloff(y=y, sr=sr).mean(),
            "zero_crossing_rate": librosa.feature.zero_crossing_rate(y).mean(),
            "tempo": librosa.beat.tempo(y=y, sr=sr)[0],
            "rms": librosa.feature.rms(y=y).mean(),
        }
        
        return features
    
    except Exception as e:
        print(f"提取语音特征失败: {e}")
        return {}


def analyze_speech(speech_features: Dict[str, Any]) -> Dict[str, Any]:
    """分析语音特征
    
    根据语音特征进行分析
    
    Args:
        speech_features: 语音特征
        
    Returns:
        Dict[str, Any]: 语音分析结果
    """
    # 这里是示例实现，实际项目中应使用机器学习模型
    if not speech_features:
        return {
            "clarity": 5.0,
            "pace": 5.0,
            "emotion": "中性"
        }
    
    # 计算语音清晰度（基于频谱特征）
    clarity = min(10.0, max(0.0, 5.0 + speech_features.get("spectral_centroid", 0) / 1000))
    
    # 计算语速（基于节奏和过零率）
    tempo = speech_features.get("tempo", 120)
    zcr = speech_features.get("zero_crossing_rate", 0.1)
    pace = min(10.0, max(0.0, 5.0 + (tempo / 120 - 1) * 3 + (zcr - 0.1) * 10))
    
    # 情感分析（简化版）
    rms = speech_features.get("rms", 0.1)
    if rms > 0.2:
        emotion = "热情"
    elif rms < 0.05:
        emotion = "平静"
    else:
        emotion = "中性"
    
    return {
        "clarity": float(clarity),
        "pace": float(pace),
        "emotion": emotion
    }


def extract_visual_features(video_path: str) -> Dict[str, Any]:
    """提取视觉特征
    
    从视频文件中提取视觉特征
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        Dict[str, Any]: 视觉特征
    """
    # 这里是示例实现，实际项目中应使用计算机视觉模型
    try:
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        
        # 初始化特征
        features = {
            "face_detections": [],
            "eye_positions": [],
            "body_positions": []
        }
        
        # 采样帧进行分析
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_rate = max(1, frame_count // 100)  # 最多分析100帧
        
        for i in range(0, frame_count, sample_rate):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret:
                break
            
            # 在这里应该使用人脸检测和姿态估计模型
            # 这里使用随机值作为示例
            features["face_detections"].append({
                "confidence": np.random.uniform(0.7, 1.0),
                "expression": np.random.choice(["neutral", "happy", "sad", "surprised"]),
                "frame": i
            })
            
            features["eye_positions"].append({
                "looking_at_camera": np.random.choice([True, False], p=[0.7, 0.3]),
                "frame": i
            })
            
            features["body_positions"].append({
                "posture": np.random.choice(["upright", "leaning", "slouched"]),
                "movement": np.random.uniform(0, 1),
                "frame": i
            })
        
        cap.release()
        return features
    
    except Exception as e:
        print(f"提取视觉特征失败: {e}")
        return {}


def analyze_visual(visual_features: Dict[str, Any]) -> Dict[str, Any]:
    """分析视觉特征
    
    根据视觉特征进行分析
    
    Args:
        visual_features: 视觉特征
        
    Returns:
        Dict[str, Any]: 视觉分析结果
    """
    # 这里是示例实现，实际项目中应使用更复杂的分析
    if not visual_features:
        return {
            "facial_expressions": {"neutral": 0.7, "happy": 0.2, "other": 0.1},
            "eye_contact": 5.0,
            "body_language": {"confidence": 5.0, "openness": 5.0}
        }
    
    # 分析面部表情
    expressions = visual_features.get("face_detections", [])
    expression_counts = {}
    for exp in expressions:
        expression = exp.get("expression", "neutral")
        expression_counts[expression] = expression_counts.get(expression, 0) + 1
    
    total = max(1, len(expressions))
    facial_expressions = {k: v / total for k, v in expression_counts.items()}
    
    # 分析眼神接触
    eye_positions = visual_features.get("eye_positions", [])
    looking_at_camera = sum(1 for pos in eye_positions if pos.get("looking_at_camera", False))
    eye_contact = min(10.0, max(0.0, looking_at_camera / max(1, len(eye_positions)) * 10))
    
    # 分析肢体语言
    body_positions = visual_features.get("body_positions", [])
    upright_posture = sum(1 for pos in body_positions if pos.get("posture") == "upright")
    posture_score = upright_posture / max(1, len(body_positions)) * 10
    
    avg_movement = np.mean([pos.get("movement", 0) for pos in body_positions]) if body_positions else 0.5
    openness_score = min(10.0, max(0.0, 5.0 + (avg_movement - 0.5) * 10))
    
    body_language = {
        "confidence": float(posture_score),
        "openness": float(openness_score)
    }
    
    return {
        "facial_expressions": facial_expressions,
        "eye_contact": float(eye_contact),
        "body_language": body_language
    }


def speech_to_text(file_path: str) -> str:
    """语音转文本
    
    将语音文件转换为文本
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 转换后的文本
    """
    # 这里是示例实现，实际项目中应使用语音识别API
    # 例如百度语音识别、讯飞语音识别等
    
    # 返回示例文本
    return "这是一个面试回答的示例文本。我认为我的优势在于团队协作能力和解决问题的能力。我曾经在项目中遇到过挑战，但通过与团队成员的合作成功解决了问题。我对贵公司的产品和文化非常感兴趣，希望能够加入贵公司的团队。"


def analyze_content(text: str) -> Dict[str, Any]:
    """分析文本内容
    
    对文本内容进行分析
    
    Args:
        text: 文本内容
        
    Returns:
        Dict[str, Any]: 内容分析结果
    """
    # 这里是示例实现，实际项目中应使用NLP模型
    if not text:
        return {
            "relevance": 5.0,
            "structure": 5.0,
            "key_points": ["无内容"]
        }
    
    # 加载预训练模型（实际使用时取消注释）
    # tokenizer = AutoTokenizer.from_pretrained(settings.TEXT_MODEL)
    # model = AutoModel.from_pretrained(settings.TEXT_MODEL)
    
    # 简单关键词匹配作为示例
    positive_keywords = ["团队", "协作", "解决问题", "经验", "项目", "成功", "优势", "能力"]
    structure_keywords = ["首先", "其次", "最后", "总结", "例如", "因此", "但是", "而且"]
    
    # 计算相关性分数
    relevance_score = sum(1 for kw in positive_keywords if kw in text) / len(positive_keywords) * 10
    relevance_score = min(10.0, max(0.0, relevance_score))
    
    # 计算结构分数
    structure_score = sum(1 for kw in structure_keywords if kw in text) / len(structure_keywords) * 5
    structure_score = min(10.0, max(0.0, 5.0 + structure_score))
    
    # 提取关键点（简化版）
    sentences = text.split("。")
    key_points = [s.strip() for s in sentences if any(kw in s for kw in positive_keywords)][:5]
    if not key_points and sentences:
        key_points = [sentences[0].strip()]
    
    return {
        "relevance": float(relevance_score),
        "structure": float(structure_score),
        "key_points": key_points
    }


def generate_overall_analysis(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """生成综合分析
    
    根据各部分分析结果生成综合分析
    
    Args:
        analysis_results: 各部分分析结果
        
    Returns:
        Dict[str, Any]: 综合分析结果
    """
    # 提取各部分分数
    speech = analysis_results.get("speech", {})
    visual = analysis_results.get("visual", {})
    content = analysis_results.get("content", {})
    
    speech_clarity = speech.get("clarity", 5.0)
    speech_pace = speech.get("pace", 5.0)
    speech_emotion = speech.get("emotion", "中性")
    
    eye_contact = visual.get("eye_contact", 5.0)
    body_language = visual.get("body_language", {"confidence": 5.0, "openness": 5.0})
    
    content_relevance = content.get("relevance", 5.0)
    content_structure = content.get("structure", 5.0)
    
    # 计算综合分数
    scores = [
        speech_clarity,
        speech_pace,
        eye_contact,
        body_language.get("confidence", 5.0),
        body_language.get("openness", 5.0),
        content_relevance,
        content_structure
    ]
    
    overall_score = sum(scores) / len(scores)
    
    # 确定优势
    strengths = []
    if speech_clarity > 7.0:
        strengths.append("语音清晰度高，表达清楚")
    if speech_pace > 4.0 and speech_pace < 6.0:
        strengths.append("语速适中，节奏感好")
    if eye_contact > 7.0:
        strengths.append("眼神交流良好，展现自信")
    if body_language.get("confidence", 0) > 7.0:
        strengths.append("肢体语言自信，姿态良好")
    if content_relevance > 7.0:
        strengths.append("回答内容相关性高，切中要点")
    if content_structure > 7.0:
        strengths.append("回答结构清晰，逻辑性强")
    if speech_emotion == "热情":
        strengths.append("语音情感热情，展现积极态度")
    
    # 确定劣势
    weaknesses = []
    if speech_clarity < 4.0:
        weaknesses.append("语音不够清晰，表达模糊")
    if speech_pace < 3.0:
        weaknesses.append("语速过慢，可能显得犹豫")
    if speech_pace > 7.0:
        weaknesses.append("语速过快，不易理解")
    if eye_contact < 4.0:
        weaknesses.append("眼神交流不足，可能显得缺乏自信")
    if body_language.get("confidence", 10) < 4.0:
        weaknesses.append("肢体语言不自信，姿态需改进")
    if content_relevance < 4.0:
        weaknesses.append("回答内容相关性不高，未切中要点")
    if content_structure < 4.0:
        weaknesses.append("回答结构不清晰，逻辑性弱")
    if speech_emotion == "平静" and overall_score < 5.0:
        weaknesses.append("语音情感平淡，缺乏热情")
    
    # 生成建议
    suggestions = []
    if speech_clarity < 6.0:
        suggestions.append("提高发音清晰度，注意语音表达")
    if speech_pace < 4.0 or speech_pace > 6.0:
        suggestions.append("调整语速至适中水平，不要过快或过慢")
    if eye_contact < 6.0:
        suggestions.append("增加眼神交流，展示自信和专注")
    if body_language.get("confidence", 10) < 6.0:
        suggestions.append("改善肢体语言，保持挺拔姿态")
    if body_language.get("openness", 10) < 5.0:
        suggestions.append("展现更开放的肢体语言，避免交叉手臂等封闭姿势")
    if content_relevance < 6.0:
        suggestions.append("提高回答的相关性，更好地针对问题要点")
    if content_structure < 6.0:
        suggestions.append("改善回答结构，使用清晰的逻辑框架")
    
    # 如果没有找到优势或劣势，添加默认项
    if not strengths:
        strengths.append("整体表现中等，无明显优势")
    if not weaknesses:
        weaknesses.append("整体表现良好，无明显劣势")
    if not suggestions:
        suggestions.append("继续保持良好表现，可尝试在细节上进一步提升")
    
    return {
        "score": float(overall_score),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions
    }