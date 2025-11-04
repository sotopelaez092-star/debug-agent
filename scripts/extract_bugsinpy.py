# scripts/extract_bugsinpy.py
"""
从BugsInPy提取真实bug数据
选择部分有代表性的bug
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict


def get_bug_info(project: str, bug_id: str) -> Dict:
    """
    提取单个bug信息
    
    Args:
        project: 项目名称（如pandas）
        bug_id: bug编号
    
    Returns:
        bug信息字典
    """
    bug_path = Path(f"data/raw/BugsInPy/projects/{project}/bugs/{bug_id}")
    
    if not bug_path.exists():
        return None
    
    bug_info = {
        "id": f"{project}-{bug_id}",
        "project": project,
        "bug_id": bug_id,
        "category": "Real Bug",
        "difficulty": "medium",
        "source": "BugsInPy"
    }
    
    # 读取bug信息文件
    info_file = bug_path / "bug.info"
    if info_file.exists():
        with open(info_file) as f:
            content = f.read()
            bug_info["description"] = content[:200]  # 取前200字符
    
    return bug_info


def extract_bugs(max_per_project: int = 3):
    """
    提取bug数据
    
    Args:
        max_per_project: 每个项目最多提取几个bug
    """
    bugsinpy_path = Path("data/raw/BugsInPy/projects")
    
    if not bugsinpy_path.exists():
        print("❌ BugsInPy未下载")
        print("请运行: cd data/raw && git clone https://github.com/soarsmu/BugsInPy.git")
        return
    
    # 选择几个代表性项目
    target_projects = ["pandas", "matplotlib", "scrapy", "tornado", "flask"]
    
    all_bugs = []
    
    for project in target_projects:
        project_path = bugsinpy_path / project / "bugs"
        
        if not project_path.exists():
            continue
        
        # 获取bug列表
        bug_dirs = sorted([d for d in project_path.iterdir() if d.is_dir()])[:max_per_project]
        
        print(f"📦 {project}: 提取 {len(bug_dirs)} 个bug")
        
        for bug_dir in bug_dirs:
            bug_id = bug_dir.name
            bug_info = get_bug_info(project, bug_id)
            
            if bug_info:
                all_bugs.append(bug_info)
    
    # 保存
    output = {
        "metadata": {
            "source": "BugsInPy",
            "total_bugs": len(all_bugs),
            "projects": target_projects
        },
        "bugs": all_bugs
    }
    
    output_path = Path("data/processed/bugsinpy_sample.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ BugsInPy数据提取完成")
    print(f"📁 保存路径: {output_path}")
    print(f"📊 Bug数量: {len(all_bugs)}")


if __name__ == "__main__":
    extract_bugs()