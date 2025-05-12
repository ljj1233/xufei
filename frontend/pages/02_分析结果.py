import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

# API配置
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

# 页面配置
st.set_page_config(
    page_title="分析结果 - 多模态面试评测智能体",
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
</style>
""", unsafe_allow_html=True)

# 检查用户是否已登录
if "user_token" not in st.session_state:
    st.warning("请先登录后再使用此功能。")
    st.button("返回登录", on_click=lambda: st.switch_page("Home.py"))
else:
    # 页面标题
    st.markdown("<h1 class='main-header'>面试分析结果</h1>", unsafe_allow_html=True)
    
    # 获取面试列表
    try:
        headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
        response = requests.get(f"{API_URL}/interviews", headers=headers)
        
        if response.status_code == 200:
            interviews = response.json()
            
            if interviews:
                # 创建数据表格
                interview_data = []
                for interview in interviews:
                    # 获取分析结果（如果有）
                    try:
                        analysis_response = requests.get(
                            f"{API_URL}/analysis/{interview['id']}",
                            headers=headers
                        )
                        
                        if analysis_response.status_code == 200:
                            analysis = analysis_response.json()
                            overall_score = analysis.get("overall_score", "未分析")
                        else:
                            overall_score = "未分析"
                    except:
                        overall_score = "未分析"
                    
                    # 格式化日期
                    created_date = interview["created_at"].split("T")[0] if "T" in interview["created_at"] else interview["created_at"][:10]
                    
                    interview_data.append({
                        "ID": interview["id"],
                        "标题": interview["title"],
                        "类型": "视频" if interview["file_type"] == "video" else "音频",
                        "时长": f"{interview['duration']:.1f}秒" if interview["duration"] else "未知",
                        "上传日期": created_date,
                        "综合评分": overall_score if isinstance(overall_score, (int, float)) else overall_score
                    })
                
                # 创建DataFrame
                df = pd.DataFrame(interview_data)
                
                # 显示数据表格
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.subheader("您的面试记录")
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # 选择面试查看详情
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.subheader("查看详细分析")
                
                selected_interview = st.selectbox(
                    "选择面试记录查看详细分析",
                    options=df["ID"].tolist(),
                    format_func=lambda x: df[df["ID"] == x]["标题"].iloc[0]
                )
                
                if st.button("查看详细报告"):
                    st.session_state.selected_interview = selected_interview
                    st.switch_page("pages/03_详细报告.py")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # 分析统计
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.subheader("分析统计")
                
                # 计算已分析的面试数量
                analyzed_count = sum(1 for item in interview_data if isinstance(item["综合评分"], (int, float)))
                total_count = len(interview_data)
                
                # 计算平均分
                scores = [item["综合评分"] for item in interview_data if isinstance(item["综合评分"], (int, float))]
                avg_score = sum(scores) / len(scores) if scores else 0
                
                # 显示统计信息
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("<div class='score-card'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='score-value'>{total_count}</div>", unsafe_allow_html=True)
                    st.markdown("<div class='score-label'>总面试数</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown("<div class='score-card'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='score-value'>{analyzed_count}</div>", unsafe_allow_html=True)
                    st.markdown("<div class='score-label'>已分析数</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col3:
                    score_class = "good-score" if avg_score >= 7 else "medium-score" if avg_score >= 5 else "bad-score"
                    st.markdown(f"<div class='score-card {score_class}'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='score-value'>{avg_score:.1f}</div>", unsafe_allow_html=True)
                    st.markdown("<div class='score-label'>平均评分</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
            else:
                st.info("暂无面试记录，请先上传面试视频或音频。")
                if st.button("上传面试"):
                    st.switch_page("pages/01_上传面试.py")
        else:
            st.error("获取面试记录失败，请重新登录。")
            if st.button("返回首页"):
                st.switch_page("Home.py")
    
    except Exception as e:
        st.error(f"获取数据时出错: {str(e)}")
        if st.button("返回首页"):
            st.switch_page("Home.py")

# 底部导航
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⬅️ 返回首页"):
        st.switch_page("Home.py")
with col2:
    if st.button("上传新面试"):
        st.switch_page("pages/01_上传面试.py")