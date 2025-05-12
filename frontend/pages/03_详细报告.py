import streamlit as st
import requests
import pandas as pd
import numpy as np
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# API配置
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

# 页面配置
st.set_page_config(
    page_title="详细报告 - 多模态面试评测智能体",
    page_icon="🎯",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 1rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        box-shadow: 0 0.25rem 0.75rem rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .score-card {
        text-align: center;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .score-value {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .score-label {
        font-size: 1rem;
        color: #616161;
    }
    .good-score {
        background-color: #E8F5E9;
        color: #2E7D32;
    }
    .medium-score {
        background-color: #FFF8E1;
        color: #F57F17;
    }
    .bad-score {
        background-color: #FFEBEE;
        color: #C62828;
    }
    .highlight {
        background-color: #E3F2FD;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# 检查用户是否已登录
if "user_token" not in st.session_state:
    st.warning("请先登录后再使用此功能。")
    st.button("返回登录", on_click=lambda: st.switch_page("Home.py"))
elif "selected_interview" not in st.session_state:
    st.warning("请先选择一个面试记录。")
    st.button("查看面试列表", on_click=lambda: st.switch_page("pages/02_分析结果.py"))
else:
    # 获取选中的面试ID
    interview_id = st.session_state.selected_interview
    
    try:
        # 获取面试详情
        headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
        interview_response = requests.get(
            f"{API_URL}/interviews/{interview_id}",
            headers=headers
        )
        
        if interview_response.status_code != 200:
            st.error("获取面试详情失败，请返回重试。")
            st.button("返回面试列表", on_click=lambda: st.switch_page("pages/02_分析结果.py"))
        else:
            interview = interview_response.json()
            
            # 获取分析结果
            analysis_response = requests.get(
                f"{API_URL}/analysis/{interview_id}",
                headers=headers
            )
            
            if analysis_response.status_code != 200:
                st.error("获取分析结果失败，可能尚未进行分析。")
                if st.button("开始分析"):
                    # 调用分析API
                    start_analysis = requests.post(
                        f"{API_URL}/analysis/{interview_id}",
                        headers=headers
                    )
                    if start_analysis.status_code == 200:
                        st.success("分析已完成！")
                        st.experimental_rerun()
                    else:
                        st.error(f"分析失败: {start_analysis.json().get('detail', '未知错误')}")
            else:
                analysis = analysis_response.json()
                
                # 页面标题
                st.markdown(f"<h1 class='main-header'>{interview['title']} - 详细分析报告</h1>", unsafe_allow_html=True)
                
                # 基本信息
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("<h2 class='sub-header'>基本信息</h2>", unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**面试类型**")
                    st.markdown(f"{'视频' if interview['file_type'] == 'video' else '音频'}面试")
                
                with col2:
                    st.markdown("**时长**")
                    st.markdown(f"{interview['duration']:.1f}秒" if interview['duration'] else "未知")
                
                with col3:
                    st.markdown("**上传日期**")
                    created_date = interview["created_at"].split("T")[0] if "T" in interview["created_at"] else interview["created_at"][:10]
                    st.markdown(created_date)
                
                if interview.get("description"):
                    st.markdown("**描述**")
                    st.markdown(interview["description"])
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # 综合评分
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("<h2 class='sub-header'>综合评分</h2>", unsafe_allow_html=True)
                
                overall_score = analysis.get("overall_score", 0)
                score_class = "good-score" if overall_score >= 7 else "medium-score" if overall_score >= 5 else "bad-score"
                
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown(f"<div class='score-card {score_class}'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='score-value'>{overall_score:.1f}</div>", unsafe_allow_html=True)
                    st.markdown("<div class='score-label'>综合评分 (满分10分)</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col2:
                    # 解析JSON字符串
                    try:
                        strengths = json.loads(analysis.get("strengths", "[]"))
                        weaknesses = json.loads(analysis.get("weaknesses", "[]"))
                        suggestions = json.loads(analysis.get("suggestions", "[]"))
                    except:
                        strengths = []
                        weaknesses = []
                        suggestions = []
                    
                    # 显示优势、劣势和建议
                    st.markdown("**优势**")
                    for strength in strengths:
                        st.markdown(f"- {strength}")
                    
                    st.markdown("**需要改进的地方**")
                    for weakness in weaknesses:
                        st.markdown(f"- {weakness}")
                    
                    st.markdown("**改进建议**")
                    for suggestion in suggestions:
                        st.markdown(f"- {suggestion}")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # 详细分析结果
                tab1, tab2, tab3 = st.tabs(["语音分析", "视觉分析", "内容分析"])
                
                with tab1:
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.markdown("<h2 class='sub-header'>语音分析</h2>", unsafe_allow_html=True)
                    
                    # 语音分析数据
                    speech_clarity = analysis.get("speech_clarity", 0)
                    speech_pace = analysis.get("speech_pace", 0)
                    speech_emotion = analysis.get("speech_emotion", "未知")
                    
                    # 创建雷达图
                    categories = ['语音清晰度', '语速适中度']
                    values = [speech_clarity, speech_pace]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=values,
                        theta=categories,
                        fill='toself',
                        name='语音表现'
                    ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 10]
                            )),
                        showlegend=False
                    )
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.markdown("**语音评分详情**")
                        st.markdown(f"- 语音清晰度: **{speech_clarity:.1f}**/10")
                        st.markdown(f"- 语速适中度: **{speech_pace:.1f}**/10")
                        st.markdown(f"- 主要情感: **{speech_emotion}**")
                        
                        # 语音评价
                        st.markdown("**语音评价**")
                        if speech_clarity >= 7:
                            st.markdown("- 语音清晰，表达流畅")
                        elif speech_clarity >= 5:
                            st.markdown("- 语音基本清晰，偶有含糊")
                        else:
                            st.markdown("- 语音不够清晰，需要提高发音准确度")
                        
                        if speech_pace >= 7:
                            st.markdown("- 语速适中，节奏感好")
                        elif speech_pace >= 5:
                            st.markdown("- 语速基本适中，偶有快慢不一")
                        elif speech_pace >= 3:
                            st.markdown("- 语速偏慢，可能显得犹豫")
                        else:
                            st.markdown("- 语速过快或过慢，需要调整")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with tab2:
                    if interview['file_type'] == 'video':
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown("<h2 class='sub-header'>视觉分析</h2>", unsafe_allow_html=True)
                        
                        # 视觉分析数据
                        try:
                            facial_expressions = json.loads(analysis.get("facial_expressions", "{}"))
                            eye_contact = analysis.get("eye_contact", 0)
                            body_language = json.loads(analysis.get("body_language", "{}"))
                        except:
                            facial_expressions = {}
                            eye_contact = 0
                            body_language = {}
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # 面部表情饼图
                            if facial_expressions:
                                labels = list(facial_expressions.keys())
                                values = list(facial_expressions.values())
                                
                                fig = px.pie(
                                    names=labels,
                                    values=values,
                                    title="面部表情分布",
                                    color_discrete_sequence=px.colors.sequential.Blues
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("无面部表情数据")
                        
                        with col2:
                            # 肢体语言评分
                            if body_language:
                                confidence = body_language.get("confidence", 0)
                                openness = body_language.get("openness", 0)
                                
                                fig = go.Figure()
                                
                                fig.add_trace(go.Bar(
                                    x=['自信度', '开放度'],
                                    y=[confidence, openness],
                                    marker_color=['#1E88E5', '#FFC107']
                                ))
                                
                                fig.update_layout(
                                    title="肢体语言评分",
                                    yaxis=dict(range=[0, 10])
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("无肢体语言数据")
                        
                        # 眼神接触评分
                        st.markdown("**眼神接触评分**")
                        st.progress(eye_contact / 10)
                        st.markdown(f"**{eye_contact:.1f}**/10")
                        
                        # 视觉表现评价
                        st.markdown("**视觉表现评价**")
                        if eye_contact >= 7:
                            st.markdown("- 眼神接触良好，展现自信")
                        elif eye_contact >= 5:
                            st.markdown("- 眼神接触基本充分，偶有游离")
                        else:
                            st.markdown("- 眼神接触不足，需要增加与面试官的目光交流")
                        
                        if body_language.get("confidence", 0) >= 7:
                            st.markdown("- 肢体语言自信，姿态良好")
                        elif body_language.get("confidence", 0) >= 5:
                            st.markdown("- 肢体语言基本自然，偶有紧张")
                        else:
                            st.markdown("- 肢体语言不够自信，需要改善姿态")
                        
                        if body_language.get("openness", 0) >= 7:
                            st.markdown("- 肢体语言开放，展现积极态度")
                        elif body_language.get("openness", 0) >= 5:
                            st.markdown("- 肢体语言基本开放，偶有封闭姿势")
                        else:
                            st.markdown("- 肢体语言较为封闭，建议采用更开放的姿势")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.info("此面试为音频记录，无视觉分析数据。")
                
                with tab3:
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.markdown("<h2 class='sub-header'>内容分析</h2>", unsafe_allow_html=True)
                    
                    # 内容分析数据
                    content_relevance = analysis.get("content_relevance", 0)
                    content_structure = analysis.get("content_structure", 0)
                    
                    try:
                        key_points = json.loads(analysis.get("key_points", "[]"))
                    except:
                        key_points = []
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # 内容评分图表
                        fig = go.Figure()
                        
                        fig.add_trace(go.Bar(
                            x=['内容相关性', '结构清晰度'],
                            y=[content_relevance, content_structure],
                            marker_color=['#1E88E5', '#43A047']
                        ))
                        
                        fig.update_layout(
                            title="内容评分",
                            yaxis=dict(range=[0, 10])
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # 关键点
                        st.markdown("**关键点**")
                        if key_points:
                            for point in key_points:
                                st.markdown(f"- {point}")
                        else:
                            st.info("未提取到关键点")
                    
                    # 内容评价
                    st.markdown("**内容评价**")
                    if content_relevance >= 7:
                        st.markdown("- 内容高度相关，切中要点")
                    elif content_relevance >= 5:
                        st.markdown("- 内容基本相关，有一定针对性")
                    else:
                        st.markdown("- 内容相关性不足，未能充分回应问题要点")
                    
                    if content_structure >= 7:
                        st.markdown("- 结构清晰，逻辑性强")
                    elif content_structure >= 5:
                        st.markdown("- 结构基本清晰，逻辑性一般")
                    else:
                        st.markdown("- 结构不够清晰，逻辑性弱")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # 下载报告按钮
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("<h2 class='sub-header'>报告导出</h2>", unsafe_allow_html=True)
                
                if st.button("生成PDF报告"):
                    st.info("PDF报告生成功能正在开发中，敬请期待...")
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"获取数据时出错: {str(e)}")
        st.button("返回面试列表", on_click=lambda: st.switch_page("pages/02_分析结果.py"))

# 底部导航
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⬅️ 返回面试列表"):
        st.switch_page("pages/02_分析结果.py")
with col2:
    if st.button("返回首页"):
        st.switch_page("Home.py")
with col3:
    if st.button("上传新面试 ➡️"):
        st.switch_page("pages/01_上传面试.py")