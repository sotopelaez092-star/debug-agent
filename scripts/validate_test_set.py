import json
from pathlib import Path
from tkinter import N

def validate_test_set():
    """验证测试集质量"""

    # 1. 加载数据
    with open('data/test_cases/bugs_40.json', 'r') as f:
        data = json.load(f)

    bugs = data['errors']

    # 2. 统计信息

    # 2.1 基本统计
    print(f"📉 测试集统计")
    print(f"="*60)
    print(f"总样本数: {len(bugs)}")

    # 2.2 类别统计
    print("\n类别统计：")
    category_count = {}
    for bug in bugs:
        category = bug['category']
        category_count[category] = category_count.get(category, 0) + 1

    for category, count in sorted(category_count.items()):
        print(f"{category}: {count}")

    # 2.3 难度统计
    print("\n难度统计")
    difficulty_count = {}
    for bug in bugs:
        difficulty = bug['difficulty']
        difficulty_count[difficulty] = difficulty_count.get(difficulty, 0) + 1

    for difficulty, count in sorted(difficulty_count.items()):
        print(f"{difficulty}: {count}")
    # TODO: 添加更多统计

    # 2.4 字段完整性检查
    print("\n字段完整性检查")

    required_fields = ['buggy_code', 'error_message', 'fixed_code']
    missing_count = 0

    for bug in bugs:
        for field in required_fields:
            if not bug.get(field):
                missing_count += 1
                print(f"  ⚠️   {bug['id']} 缺少字段: {field}")
    
    if missing_count == 0:
        print("✅ 所有样本都包含所有必要字段")

if __name__ == "__main__":
    validate_test_set()
