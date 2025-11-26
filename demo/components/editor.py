# demo/components/editor.py
from streamlit_ace import st_ace


def code_editor_ui(code: str, language: str = "python", key: str = "editor"):
    """显示代码编辑器"""
    content = st_ace(
        value=code,
        language=language,
        theme="monokai",
        key=key,
        height=520,
        auto_update=True,
        show_print_margin=False,
        wrap=True,
    )
    return content
