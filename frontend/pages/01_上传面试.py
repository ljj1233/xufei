import streamlit as st
import requests
import os
import time
from datetime import datetime

# API配置
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

# 页面配置
st.set_page_config(
    page_title="上传面试 - 多模态面试评测智能体",
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
    .upload-area {
        border: 2px dashed #1E88E5;
        border-radius: 0.5rem;
        padding: 2rem;
        text-align: center;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 检查用户是否已登录
if "user_token" not in st.session_state:
    st.warning("请先登录后再使用此功能。")
    st.button("返回登录", on_click=lambda: st.switch_page("Home.py"))
else:
    # 页面标题
    st.markdown("<h1 class='main-header'>上传面试视频/音频</h1>", unsafe_allow_html=True)
    
    # 上传表单
    with st.form("upload_form"):
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        # 面试标题和描述
        title = st.text_input("面试标题", placeholder="例如：产品经理面试-XX公司")
        description = st.text_area("面试描述（可选）", placeholder="描述此次面试的背景、职位等信息")
        
        # 文件上传
        st.markdown("<div class='upload-area'>", unsafe_allow_html=True)
        st.markdown("### 上传面试文件")
        st.markdown("支持的格式：MP4, AVI, MOV, MP3, WAV (最大100MB)")
        uploaded_file = st.file_uploader(
            "选择文件", 
            type=["mp4", "avi", "mov", "mp3", "wav"],
            help="上传您的面试视频或音频文件"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 提交按钮
        submit_button = st.form_submit_button("上传并分析")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 处理表单提交
    if submit_button:
        if not title:
            st.error("请输入面试标题")
        elif not uploaded_file:
            st.error("请上传面试文件")
        else:
            # 显示进度
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 准备上传数据
                headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
                
                # 文件上传进度模拟
                status_text.text("正在上传文件...")
                for i in range(1, 101):
                    progress_bar.progress(i)
                    time.sleep(0.01)  # 模拟上传时间
                
                # 上传文件
                files = {"file": uploaded_file}
                data = {"title": title, "description": description if description else None}
                
                response = requests.post(
                    f"{API_URL}/interviews/upload/",
                    headers=headers,
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    interview_data = response.json()
                    st.session_state.last_uploaded_interview = interview_data
                    
                    # 显示成功消息
                    st.success("文件上传成功！")
                    
                    # 开始分析
                    status_text.text("正在进行多模态分析...")
                    progress_bar.progress(0)
                    
                    # 模拟分析过程
                    for i in range(1, 101):
                        progress_bar.progress(i)
                        time.sleep(0.05)  # 模拟分析时间
                    
                    # 分析完成后，调用分析API
                    analysis_response = requests.post(
                        f"{API_URL}/analysis/{interview_data['id']}",
                        headers=headers
                    )
                    
                    if analysis_response.status_code == 200:
                        analysis_data = analysis_response.json()
                        st.session_state.last_analysis = analysis_data
                        
                        # 显示成功消息并提供查看结果的按钮
                        st.success("分析完成！")
                        status_text.text("")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("查看分析结果"):
                                st.session_state.selected_interview = interview_data['id']
                                st.switch_page("pages/03_详细报告.py")
                        with col2:
                            if st.button("继续上传"):
                                st.experimental_rerun()
                    else:
                        st.error(f"分析失败: {analysis_response.json().get('detail', '未知错误')}")
                else:
                    st.error(f"上传失败: {response.json().get('detail', '未知错误')}")
            
            except Exception as e:
                st.error(f"处理过程中出错: {str(e)}")
                status_text.text("")
    
    # 显示上传说明
    with st.expander("上传说明"):
        st.markdown("""
        ### 如何获得最佳分析效果？
        
        1. **视频质量**：确保视频清晰，光线充足，面部可见
        2. **音频质量**：确保音频清晰，背景噪音小
        3. **时长建议**：建议上传3-10分钟的面试片段
        4. **文件大小**：文件大小不超过100MB
        5. **格式支持**：支持MP4、AVI、MOV视频格式和MP3、WAV音频格式
        
        ### 隐私说明
        
        您上传的面试视频/音频将仅用于分析目的，系统会保护您的隐私，不会将您的数据用于其他用途。
        """)

# 底部导航
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⬅️ 返回首页"):
        st.switch_page("Home.py")
with col3:
    if st.button("查看分析结果 ➡️"):
        st.switch_page("pages/02_分析结果.py")