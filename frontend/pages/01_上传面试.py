import streamlit as st
import requests
import os
import time
import json
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
        
        # 职位选择
        st.markdown("### 选择面试职位")
        col1, col2 = st.columns(2)
        with col1:
            tech_field = st.selectbox(
                "技术领域",
                options=["artificial_intelligence", "big_data", "internet_of_things", "intelligent_system"],
                format_func=lambda x: {
                    "artificial_intelligence": "人工智能",
                    "big_data": "大数据",
                    "internet_of_things": "物联网",
                    "intelligent_system": "智能系统"
                }.get(x, x)
            )
        with col2:
            position_type = st.selectbox(
                "岗位类型",
                options=["technical", "operation", "product"],
                format_func=lambda x: {
                    "technical": "技术岗",
                    "operation": "运维测试岗",
                    "product": "产品岗"
                }.get(x, x)
            )
        
        job_position_id = st.selectbox(
            "选择具体职位",
            options=[],
            placeholder="请先选择职位或创建新职位"
        )
        
        # 如果没有合适的职位，可以创建新职位
        with st.expander("创建新职位"):
            new_position_title = st.text_input("职位名称", placeholder="例如：高级AI工程师")
            required_skills = st.text_area("所需技能", placeholder="例如：Python, TensorFlow, 计算机视觉")
            job_description = st.text_area("岗位描述", placeholder="详细描述该职位的工作内容和要求")
            evaluation_criteria = st.text_area("评估标准", placeholder="面试评估的关键指标和标准")
        
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
    
        # 获取职位列表
    @st.cache_data(ttl=300)  # 缓存5分钟
    def get_job_positions():
        try:
            headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
            response = requests.get(f"{API_URL}/job-positions", headers=headers)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            st.error(f"获取职位列表失败: {str(e)}")
            return []
    
    # 创建新职位
    def create_job_position(position_data):
        try:
            headers = {
                "Authorization": f"Bearer {st.session_state.user_token}",
                "Content-Type": "application/json"
            }
            response = requests.post(
                f"{API_URL}/job-positions",
                headers=headers,
                json=position_data
            )
            if response.status_code == 200:
                st.success("职位创建成功！")
                # 清除缓存，刷新职位列表
                get_job_positions.clear()
                return response.json()["id"]
            else:
                st.error(f"创建职位失败: {response.text}")
                return None
        except Exception as e:
            st.error(f"创建职位失败: {str(e)}")
            return None
    
    # 加载职位列表
    job_positions = get_job_positions()
    position_options = [(p["id"], f"{p['title']} ({p['tech_field']}/{p['position_type']})")
                        for p in job_positions]
    
    # 更新职位选择框
    job_position_id = st.selectbox(
        "选择具体职位",
        options=[p[0] for p in position_options] if position_options else [],
        format_func=lambda x: next((p[1] for p in position_options if p[0] == x), "未知职位"),
        index=None
    )
    
    # 处理表单提交
    if submit_button:
        if not title:
            st.error("请输入面试标题")
        elif not uploaded_file:
            st.error("请上传面试文件")
        elif not job_position_id and not new_position_title:
            st.error("请选择职位或创建新职位")
        # 如果选择创建新职位
        elif not job_position_id and new_position_title:
            # 创建新职位
            new_position_data = {
                "title": new_position_title,
                "tech_field": tech_field,
                "position_type": position_type,
                "required_skills": required_skills,
                "job_description": job_description,
                "evaluation_criteria": evaluation_criteria
            }
            job_position_id = create_job_position(new_position_data)
            if not job_position_id:
                st.stop()
                
            # 继续上传流程
            # 显示进度
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 准备上传数据
            try:
                headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
                
                # 文件上传进度模拟
                status_text.text("正在上传文件...")
                for i in range(1, 101):
                    progress_bar.progress(i)
                    time.sleep(0.01)  # 模拟上传时间
                
                # 上传文件
                files = {"file": uploaded_file}
                data = {
                    "title": title, 
                    "description": description if description else None,
                    "job_position_id": job_position_id
                }
                
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
                data = {
                    "title": title, 
                    "description": description if description else None,
                    "job_position_id": job_position_id
                }
                
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