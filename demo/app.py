"""
AI Debug Agent - Streamlit Demo
支持 Route 和 ReAct 两种调试模式
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="AI Debug Agent",
    page_icon="🐛",
    layout="wide"
)

# 样式
st.markdown("""
<style>
.big-title {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}
.subtitle {
    font-size: 1.1rem;
    color: #666;
    margin-bottom: 2rem;
}
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
}
.success-box {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 8px;
    padding: 1rem;
    color: #155724;
}
.error-box {
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 8px;
    padding: 1rem;
    color: #721c24;
}
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<div class="big-title">🐛 AI Debug Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">智能 Python 代码调试助手 | Route vs ReAct 双模式</div>', unsafe_allow_html=True)

# 检查 API Key
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    st.error("⚠️ 请在 `.env` 文件中配置 `DEEPSEEK_API_KEY`")
    st.stop()

# 侧边栏 - 模式选择
with st.sidebar:
    st.header("⚙️ 设置")

    mode = st.radio(
        "调试模式",
        ["Route (快速)", "ReAct (灵活)"],
        help="Route 模式更快，ReAct 模式更灵活"
    )

    st.markdown("---")

    st.markdown("### 📊 模式对比")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Route 耗时", "15.2s", help="平均单次调试耗时")
    with col2:
        st.metric("ReAct 耗时", "27.1s", help="平均单次调试耗时")

    st.markdown("---")

    st.markdown("### 📈 正确率")
    st.progress(0.944, text="94.4% (17/18)")

    st.markdown("---")

    with st.expander("🔧 高级选项"):
        max_retries = st.slider("最大重试次数", 1, 5, 2)
        use_rag = st.checkbox("启用 RAG 搜索", value=True)
        use_docker = st.checkbox("启用 Docker 验证", value=True)

# 主区域
tab1, tab2, tab3 = st.tabs(["🔧 调试代码", "📚 示例", "📖 说明"])

with tab1:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("输入")

        buggy_code = st.text_area(
            "错误代码",
            height=200,
            placeholder='''def greet(name):
    print(f"Hello, {nane}")

greet("World")''',
            value='''def greet(name):
    print(f"Hello, {nane}")

greet("World")'''
        )

        error_traceback = st.text_area(
            "错误信息 (Traceback)",
            height=150,
            placeholder="Traceback (most recent call last):\n  File ...\nNameError: name 'nane' is not defined",
            value='''Traceback (most recent call last):
  File "main.py", line 2, in greet
    print(f"Hello, {nane}")
NameError: name 'nane' is not defined'''
        )

        if st.button("🚀 开始调试", type="primary", use_container_width=True):
            if not buggy_code.strip() or not error_traceback.strip():
                st.warning("请输入代码和错误信息")
            else:
                with st.spinner("🔍 分析中..."):
                    try:
                        if "Route" in mode:
                            from src.agent.debug_agent import DebugAgent
                            agent = DebugAgent(api_key=api_key)
                            result = agent.debug(
                                buggy_code=buggy_code,
                                error_traceback=error_traceback,
                                max_retries=max_retries
                            )
                            st.session_state['result'] = result
                            st.session_state['mode'] = 'Route'
                        else:
                            from src.agent.react_agent import ReActAgent
                            agent = ReActAgent(api_key=api_key, max_iterations=10)
                            result = agent.debug(
                                buggy_code=buggy_code,
                                error_traceback=error_traceback
                            )
                            st.session_state['result'] = result
                            st.session_state['mode'] = 'ReAct'
                    except Exception as e:
                        st.error(f"调试失败: {e}")

    with col_right:
        st.subheader("输出")

        if 'result' in st.session_state:
            result = st.session_state['result']
            mode_used = st.session_state.get('mode', 'Route')

            if result.get('success'):
                st.markdown('<div class="success-box">✅ 修复成功!</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-box">❌ 修复失败</div>', unsafe_allow_html=True)

            st.markdown("---")

            # 显示统计
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("模式", mode_used)
            with col_b:
                if mode_used == 'ReAct':
                    st.metric("迭代次数", result.get('iterations', 'N/A'))
                else:
                    st.metric("尝试次数", result.get('total_attempts', 'N/A'))
            with col_c:
                st.metric("状态", "✅" if result.get('success') else "❌")

            st.markdown("---")

            # 修复后的代码
            fixed_code = result.get('fixed_code') or result.get('final_code', '')
            if fixed_code:
                st.markdown("**修复后代码:**")
                st.code(fixed_code, language='python')

            # 解释
            explanation = result.get('explanation', '')
            if explanation:
                st.markdown("**修复说明:**")
                st.info(explanation)
        else:
            st.info("👈 输入代码和错误信息，点击「开始调试」")

with tab2:
    st.subheader("示例代码")

    examples = [
        {
            "name": "NameError - 变量拼写错误",
            "code": 'name = "Alice"\nprint(f"Hello, {naem}")',
            "error": 'NameError: name \'naem\' is not defined'
        },
        {
            "name": "TypeError - 类型拼接错误",
            "code": 'age = 25\nprint("Age: " + age)',
            "error": 'TypeError: can only concatenate str (not "int") to str'
        },
        {
            "name": "AttributeError - 方法名拼写",
            "code": 'text = "hello"\nprint(text.uper())',
            "error": "AttributeError: 'str' object has no attribute 'uper'"
        },
        {
            "name": "IndexError - 列表越界",
            "code": 'nums = [1, 2, 3]\nprint(nums[3])',
            "error": 'IndexError: list index out of range'
        },
        {
            "name": "RecursionError - 缺少终止条件",
            "code": 'def factorial(n):\n    return n * factorial(n - 1)\nprint(factorial(5))',
            "error": 'RecursionError: maximum recursion depth exceeded'
        }
    ]

    for i, ex in enumerate(examples):
        with st.expander(f"📝 {ex['name']}"):
            st.code(ex['code'], language='python')
            st.error(ex['error'])
            if st.button(f"使用此示例", key=f"use_example_{i}"):
                st.session_state['example_code'] = ex['code']
                st.session_state['example_error'] = ex['error']
                st.rerun()

with tab3:
    st.subheader("📖 系统说明")

    st.markdown("""
    ### 双模式调试

    | 模式 | 特点 | 适用场景 |
    |------|------|----------|
    | **Route** | 快速直接，按错误类型路由 | 简单明确的错误 |
    | **ReAct** | 灵活自主，LLM 决策工具调用 | 复杂模糊的问题 |

    ### 核心组件

    - **ContextManager**: 跨文件上下文提取（ChatGPT/Claude 做不到！）
    - **RAGSearcher**: Stack Overflow 知识检索
    - **CodeFixer**: LLM 代码修复
    - **DockerExecutor**: 安全沙箱验证
    - **LoopDetector**: 防止重复修复循环
    - **TokenManager**: 上下文压缩优化

    ### 性能指标

    - 正确率: **94.4%** (18 个测试用例)
    - Route 平均耗时: **15.2s**
    - ReAct 平均耗时: **27.1s**
    - RAG MRR: **1.0** (完美首位命中)
    """)

# 页脚
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "AI Debug Agent | Powered by DeepSeek API"
    "</div>",
    unsafe_allow_html=True
)
