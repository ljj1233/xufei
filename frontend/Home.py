import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API配置
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

# 页面配置
st.set_page_config(
    page_title="多模态面试评测智能体",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
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
    .highlight {
        color: #1E88E5;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.title("多模态面试评测智能体")
    st.markdown("---")
    
    # 用户认证
    if "user_token" not in st.session_state:
        st.subheader("用户登录")
        login_tab, register_tab = st.tabs(["登录", "注册"])
        
        with login_tab:
            username = st.text_input("用户名", key="login_username")
            password = st.text_input("密码", type="password", key="login_password")
            
            if st.button("登录", key="login_button"):
                try:
                    response = requests.post(
                        f"{API_URL}/users/login",
                        data={"username": username, "password": password}
                    )
                    
                    if response.status_code == 200:
                        token_data = response.json()
                        st.session_state.user_token = token_data["access_token"]
                        st.success("登录成功！")
                        st.experimental_rerun()
                    else:
                        st.error("登录失败，请检查用户名和密码。")
                except Exception as e:
                    st.error(f"登录过程中出错: {str(e)}")
        
        with register_tab:
            reg_username = st.text_input("用户名", key="reg_username")
            reg_email = st.text_input("邮箱", key="reg_email")
            reg_password = st.text_input("密码", type="password", key="reg_password")
            reg_confirm = st.text_input("确认密码", type="password", key="reg_confirm")
            
            if st.button("注册", key="register_button"):
                if reg_password != reg_confirm:
                    st.error("两次输入的密码不一致！")
                else:
                    try:
                        response = requests.post(
                            f"{API_URL}/users/register",
                            json={
                                "username": reg_username,
                                "email": reg_email,
                                "password": reg_password
                            }
                        )
                        
                        if response.status_code == 200:
                            st.success("注册成功！请登录。")
                        else:
                            error_detail = response.json().get("detail", "未知错误")
                            st.error(f"注册失败: {error_detail}")
                    except Exception as e:
                        st.error(f"注册过程中出错: {str(e)}")
    else:
        # 已登录状态
        st.success("已登录")
        if st.button("退出登录"):
            del st.session_state.user_token
            st.experimental_rerun()
    
    st.markdown("---")
    st.markdown("© 2023 多模态面试评测智能体")

# 主页内容
st.markdown("<h1 class='main-header'>多模态面试评测智能体</h1>", unsafe_allow_html=True)

if "user_token" not in st.session_state:
    # 未登录状态显示介绍信息
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h2 class='sub-header'>欢迎使用多模态面试评测系统</h2>", unsafe_allow_html=True)
    st.markdown("""
    本系统利用人工智能技术对面试过程进行多维度分析，帮助您提升面试表现。
    
    请先登录或注册以使用完整功能。
    """)    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 功能介绍
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>语音分析</h3>", unsafe_allow_html=True)
        st.markdown("评估语音清晰度、语速和情感表达，帮助您优化口头表达。")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>视觉分析</h3>", unsafe_allow_html=True)
        st.markdown("分析面部表情、眼神接触和肢体语言，提升非语言沟通能力。")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>内容分析</h3>", unsafe_allow_html=True)
        st.markdown("评估回答内容的相关性、结构和关键点，增强面试回答质量。")
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # 已登录状态显示功能入口
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h2 class='sub-header'>开始使用</h2>", unsafe_allow_html=True)
    st.markdown("选择以下功能开始使用多模态面试评测系统：")
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>上传面试视频</h3>", unsafe_allow_html=True)
        st.markdown("上传您的面试视频或音频，系统将自动进行多模态分析。")
        if st.button("上传面试", key="upload_button"):
            st.switch_page("pages/01_上传面试.py")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>查看分析结果</h3>", unsafe_allow_html=True)
        st.markdown("查看您的面试分析结果，获取详细评估和改进建议。")
        if st.button("查看结果", key="results_button"):
            st.switch_page("pages/02_分析结果.py")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 最近分析
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h2 class='sub-header'>最近分析</h2>", unsafe_allow_html=True)
    
    try:
        headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
        response = requests.get(f"{API_URL}/interviews", headers=headers)
        
        if response.status_code == 200:
            interviews = response.json()
            
            if interviews:
                for interview in interviews[:3]:  # 只显示最近3个
                    st.markdown(f"**{interview['title']}** - {interview['created_at'][:10]}")
                    st.markdown(f"类型: {interview['file_type']}")
                    if st.button("查看详情", key=f"view_{interview['id']}"):
                        st.session_state.selected_interview = interview['id']
                        st.switch_page("pages/03_详细报告.py")
                    st.markdown("---")
            else:
                st.info("暂无面试记录，请先上传面试视频或音频。")
        else:
            st.error("获取面试记录失败，请重新登录。")
    except Exception as e:
        st.error(f"获取数据时出错: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)