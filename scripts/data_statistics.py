# scripts/data_statistics.py
"""
数据集统计分析
"""

import json
from pathlib import Path
from collections import Counter


def analyze_dataset(file_path: str):
    """分析单个数据集"""

    path = Path(file_path)
    if not path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return

    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    print(f"\n{'=' * 60}")
    print(f"📊 数据集统计分析: {path.name}")
    print(f"{'=' * 60}")

    if "errors" in data:
        errors = data["errors"]
        print(f"总数：{len(errors)}")

        # 按类别统计
        categories = Counter(e["category"] for e in errors)
        print(f"\n按类别分布:")
        for cat, count in categories.most_common():
            print(f"  {cat}: {count}")

        # 按难度统计
        difficulties = Counter(e["difficulty"] for e in errors)
        print(f"\n按难度分布:")
        for diff, count in difficulties.most_common():
            print(f"  {diff}: {count}")

    elif "bugs" in data:
        bugs = data["bugs"]
        print(f"总数：{len(bugs)}")

        # 按项目统计
        projects = Counter(b["project"] for b in bugs)
        print(f"\n按项目分布:")
        for proj, count in projects.most_common():
            print(f"  {proj}: {count}")

def main():
    """统计所有数据集"""
    print("\n🔍 数据集统计分析")

    # 基础数据集
    analyze_dataset("data/processed/python_errors_base.json")
    
    # BugsInPy数据
    analyze_dataset("data/processed/bugsinpy_sample.json")

    # 汇总
    print(f"\n{'=' * 60}")
    print("📈 总体统计")
    print(f"{'=' * 60}")

    base_path = Path("data/processed/python_errors_base.json")
    bugsinpy_path = Path("data/processed/bugsinpy_sample.json")

    total = 0
    if base_path.exists():
        with open(base_path) as f:
            total += len(json.load(f)["errors"])
    
    if bugsinpy_path.exists():
        with open(bugsinpy_path) as f:
            total += len(json.load(f)["bugs"])
    
    print(f"数据总量: {total} 个错误案例")
    print(f"数据来源: 基础数据集 + BugsInPy")
    print(f"质量: ✅ 结构化 + ✅ 真实bug")

if __name__ == "__main__":
    main()