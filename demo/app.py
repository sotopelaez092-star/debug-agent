import streamlit as st

st.set_page_config(layout="wide", page_title="AI Debug Agent")

# ---- 全局样式，让页面更 Cursor ----
st.markdown("""
<style>
body {
    background-color: #0d1117 !important;
}
.big-title {
    font-size: 32px;
    font-weight: 600;
    letter-spacing: -0.5px;
}
.card {
    padding: 28px;
    border-radius: 12px;
    background: #161b22;
    border: 1px solid rgba(255,255,255,0.06);
}
.button-primary {
    background: linear-gradient(90deg, #4e9eff, #306dff);
    padding: 10px 0;
    border-radius: 8px;
    color: white;
    font-size: 16px;
    text-align: center;
    margin-top: 12px;
}
</style>
""", unsafe_allow_html=True)


# ---- 顶部 logo 很简洁 ----
st.markdown("### 🐛 AI Debug Agent")
st.write("")
st.write("")  # 留白


# ---- 主区域要居中，并且非常简洁 ----
col_center = st.columns([1, 1, 1])[1]

with col_center:

    # 打开项目卡片
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 📁 打开本地项目")

    project_path = st.text_input("", placeholder="/Users/.../project")

    if st.button("🚀 进入调试工作台", use_container_width=True):
        pass

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.write("")

    # 最近打开
    st.markdown("#### 🕒 最近打开")
    recent = []

    if not recent:
        st.markdown(
            '<div style="padding:16px;border-radius:8px;background:#11223333;color:#9aa;">暂无记录</div>',
            unsafe_allow_html=True
        )
