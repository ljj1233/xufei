import streamlit as st
import requests
import pandas as pd
import json
import os
from datetime import datetime

# API配置
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

# 页面配置
st.set_page_config(
    page_title="用户中心 - 多模态面试评测智能体",
    page_icon="👤",
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
    .profile-card {
        text-align: center;
        padding: 2rem;
    }
    .profile-avatar {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        margin-bottom: 1rem;
    }
    .stat-card {
        text-align: center;
        padding: 1rem;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .stat-label {
        color: #616161;
    }
</style>
""", unsafe_allow_html=True)

# 检查用户是否已登录
if "user_token" not in st.session_state:
    st.warning("请先登录后再使用此功能。")
    st.button("返回登录", on_click=lambda: st.switch_page("Home.py"))
else:
    try:
        # 获取用户信息
        headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
        user_response = requests.get(
            f"{API_URL}/users/me",
            headers=headers
        )
        
        if user_response.status_code == 200:
            user = user_response.json()
            
            # 页面标题
            st.markdown("<h1 class='main-header'>用户中心</h1>", unsafe_allow_html=True)
            
            # 个人信息卡片
            st.markdown("<div class='card profile-card'>", unsafe_allow_html=True)
            # 用户头像（使用默认图标）
            st.markdown("👤", unsafe_allow_html=True)
            st.markdown(f"<h2>{user['username']}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p>{user['email']}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # 统计信息
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h2 class='sub-header'>数据统计</h2>", unsafe_allow_html=True)
            
            # 获取面试统计数据
            interviews_response = requests.get(
                f"{API_URL}/interviews",
                headers=headers
            )
            
            if interviews_response.status_code == 200:
                interviews = interviews_response.json()
                total_interviews = len(interviews)
                
                # 计算已分析的面试数量和平均分
                analyzed_interviews = 0
                total_score = 0
                
                for interview in interviews:
                    analysis_response = requests.get(
                        f"{API_URL}/analysis/{interview['id']}",
                        headers=headers
                    )
                    if analysis_response.status_code == 200:
                        analyzed_interviews += 1
                        analysis = analysis_response.json()
                        total_score += analysis.get("overall_score", 0)
                
                avg_score = total_score / analyzed_interviews if analyzed_interviews > 0 else 0
                
                # 显示统计数据
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='stat-value'>{total_interviews}</div>", unsafe_allow_html=True)
                    st.markdown("<div class='stat-label'>总面试数</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='stat-value'>{analyzed_interviews}</div>", unsafe_allow_html=True)
                    st.markdown("<div class='stat-label'>已分析数</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col3:
                    st.markdown("<div class='stat-card'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='stat-value'>{avg_score:.1f}</div>", unsafe_allow_html=True)
                    st.markdown("<div class='stat-label'>平均评分</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # 账号设置
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h2 class='sub-header'>账号设置</h2>", unsafe_allow_html=True)
            
            # 修改密码表单
            with st.form("change_password_form"):
                old_password = st.text_input("当前密码", type="password")
                new_password = st.text_input("新密码", type="password")
                confirm_password = st.text_input("确认新密码", type="password")
                
                if st.form_submit_button("修改密码"):
                    if new_password != confirm_password:
                        st.error("两次输入的新密码不一致！")
                    else:
                        try:
                            response = requests.post(
                                f"{API_URL}/users/change-password",
                                headers=headers,
                                json={
                                    "old_password": old_password,
                                    "new_password": new_password
                                }
                            )
                            
                            if response.status_code == 200:
                                st.success("密码修改成功！")
                            else:
                                st.error(f"密码修改失败: {response.json().get('detail', '未知错误')}")
                        except Exception as e:
                            st.error(f"修改密码时出错: {str(e)}")
            
            # 更新个人信息表单
            with st.form("update_profile_form"):
                email = st.text_input("邮箱", value=user['email'])
                
                if st.form_submit_button("更新信息"):
                    try:
                        response = requests.put(
                            f"{API_URL}/users/update",
                            headers=headers,
                            json={"email": email}
                        )
                        
                        if response.status_code == 200:
                            st.success("个人信息更新成功！")
                            st.experimental_rerun()
                        else:
                            st.error(f"更新失败: {response.json().get('detail', '未知错误')}")
                    except Exception as e:
                        st.error(f"更新信息时出错: {str(e)}")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # 面试历史
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h2 class='sub-header'>面试历史</h2>", unsafe_allow_html=True)
            
            if interviews_response.status_code == 200:
                if interviews:
                    # 创建数据表格
                    interview_data = []
                    for interview in interviews:
                        created_date = interview["created_at"].split("T")[0] if "T" in interview["created_at"] else interview["created_at"][:10]
                        
                        # 获取分析结果
                        analysis_response = requests.get(
                            f"{API_URL}/analysis/{interview['id']}",
                            headers=headers
                        )
                        
                        if analysis_response.status_code == 200:
                            analysis = analysis_response.json()
                            score = analysis.get("overall_score", "未分析")
                        else:
                            score = "未分析"
                        
                        interview_data.append({
                            "标题": interview["title"],
                            "类型": "视频" if interview["file_type"] == "video" else "音频",
                            "时长": f"{interview['duration']:.1f}秒" if interview['duration'] else "未知",
                            "上传日期": created_date,
                            "评分": score
                        })
                    
                    # 显示数据表格
                    df = pd.DataFrame(interview_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("暂无面试记录")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        else:
            st.error("获取用户信息失败，请重新登录。")
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
    if st.button("上传面试"):
        st.switch_page("pages/01_上传面试.py")
with col3:
    if st.button("查看分析结果 ➡️"):
        st.switch_page("pages/02_分析结果.py")