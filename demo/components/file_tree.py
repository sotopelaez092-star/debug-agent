# demo/components/file_tree.py
import os
import streamlit as st


def list_files(base_path):
    """生成文件树结构（只列出.py文件）"""
    tree = {}
    for root, dirs, files in os.walk(base_path):
        rel_root = os.path.relpath(root, base_path)
        tree[rel_root] = [
            f for f in files if f.endswith(".py")
        ]
    return tree


def file_tree_ui(container, base_path: str):
    """
    在指定 container 中显示文件树，返回用户选中的文件路径
    """
    with container:
        st.markdown("#### 📁 项目文件")

        if not os.path.isdir(base_path):
            st.info("项目路径无效")
            return None

        tree = list_files(base_path)
        selected = None

        for folder, files in tree.items():
            if folder == ".":
                label = "根目录"
            else:
                label = folder

            with st.expander(f"📂 {label}", expanded=(folder == ".")):
                for f in files:
                    full_path = os.path.join(base_path, folder, f)
                    if st.button(f"📝 {f}", key=full_path):
                        selected = full_path

        return selected
