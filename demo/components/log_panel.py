# demo/components/log_panel.py
import streamlit as st
from typing import List, Tuple


def log_panel_ui(logs: List[Tuple[str, str]]):
    """
    日志区域
    logs: [(level, message)]  level: info/success/error
    """
    level_color = {
        "info": "#9ca3af",
        "success": "#22c55e",
        "error": "#f97373",
    }

    st.markdown("#### 📝 调试日志")

    if not logs:
        st.caption("暂无日志，点击右上角按钮启动一次调试吧。")
        return

    for level, msg in logs:
        color = level_color.get(level, "#9ca3af")
        st.markdown(
            f"""
            <div style="
                padding: 6px 10px;
                margin-bottom: 6px;
                border-radius: 6px;
                background: rgba(31,41,55,0.75);
                border: 1px solid rgba(55,65,81,0.7);
                font-size: 13px;
            ">
              <span style="color:{color};font-weight:600;text-transform:uppercase;margin-right:6px;">
                [{level}]
              </span>
              <span style="color:#e5e7eb;">{msg}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
