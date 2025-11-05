import json
from pathlib import Path

# 查看基础数据集的第一条
with open("data/processed/python_errors_base.json", 'r', encoding='utf-8') as f:
    base_data = json.load(f)
    print("📝 基础数据集第一条的字段:")
    print(list(base_data[0].keys()))
    print("\n示例数据:")
    for key, value in base_data[0].items():
        if isinstance(value, str) and len(value) > 100:
            print(f"  {key}: {value[:50]}...")
        else:
            print(f"  {key}: {value}")

print("\n" + "="*60 + "\n")

# 查看BugsInPy数据集的第一条
with open("data/processed/bugsinpy_sample.json", 'r', encoding='utf-8') as f:
    bugsinpy_data = json.load(f)
    print("📝 BugsInPy数据集第一条的字段:")
    print(list(bugsinpy_data[0].keys()))
    print("\n示例数据:")
    for key, value in bugsinpy_data[0].items():
        if isinstance(value, str) and len(value) > 100:
            print(f"  {key}: {value[:50]}...")
        else:
            print(f"  {key}: {value}")
