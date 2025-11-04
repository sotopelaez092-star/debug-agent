# scripts/process_raw_data.py
"""
数据处理：整合所有数据源，统一格式
输出：data/processed/bugs_raw.json
"""

import json
from pathlib import Path
from typing import List, Dict

def process_base_errors() -> List[Dict]:
    """
    处理基础错误数据集
    从 data/raw/python_errors_base.json 读取并标准化
    """

    with open('data/processed/python_errors_base.json','r') as f:
        data = json.load(f)

    processed = []
    for error in data["errors"]:
        processed.append({
            'id': f"base_{error['id']}",
            'category': error['category'],
            'difficulty': error['difficulty'],
            'error_type': error.get('error_type', ''),
            'buggy_code': error['buggy_code'],
            'error_message': error['error_message'],
            'fixed_code': error['fixed_code'],
            'explanation': error['explanation'],
            'solution_steps': error['solution_steps'],
            'source': 'manual',
            'verified': True
        })
        
    return processed

def process_bugsinpy_data() -> List[Dict]:
    """
    处理BugsInPy数据
    从 bugsinpy_sample.json 读取并标准化
    """
    with open('data/processed/bugsinpy_sample.json','r') as f:
        data = json.load(f)

    processed = []
    for bug in data["bugs"]:
        processed.append({
            'id': bug['id'],
            'category': 'Real Bug',
            'difficulty': bug['difficulty'],
            'error_type': '',
            'buggy_code': '',
            'error_message': '',
            'fixed_code': '',
            'explanation': bug.get('description', ''),
            'solution_steps': [],
            'source': 'bugsinpy',
            'project': bug['project'],
            'bug_id': bug['bug_id'],
            'verified': False
        })
        
    return processed

def merge_and_clean(base_data: List[Dict], bugsinpy_data: List[Dict]) -> List[Dict]:
    """
    合并并清洗数据

    清洗规则：
    1. 去除重复
    2. 验证必填字段
    3. 统一格式
    """
    all_data = base_data + bugsinpy_data
    
    # 去重
    seen = set()
    cleaned = []

    for item in all_data:
        # 创建唯一标识
        category = item.get("category", "Unknown")
        buggy_code = item.get("buggy_code", "")
        unique_key = f"{item.get('id', '')}_{category}_{buggy_code}"

        if unique_key not in seen:
            seen.add(unique_key)
            cleaned.append(item)

    print(f'原始数据：{len(all_data)}')
    print(f"去重后：{len(cleaned)}")

    return cleaned

def categorize_errors(data: List[Dict]) -> Dict[str, List[Dict]]:
    """
    按错误类型分类
    """
    categories ={}

    for item in data:
        category = item['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
    return categories


def annotate_data(data: List[Dict]) -> List[Dict]:
    """
    数据标注：添加额外的元数据
    """
    for item in data:
        # 1. 添加复杂度评分（基于代码长度和错误类型）
        code_length = len(item['buggy_code'])
        if code_length < 50:
            complexity_score =1
        elif code_length < 100:
            complexity_score =2
        else:
            complexity_score =3
        
        item['complexity_score'] = complexity_score

        # 2. 添加标签
        tags = []
        if 'None' in item['buggy_code']:
            tags.append('none_check')
        if 'try' in item['buggy_code']:
            tags.append('try_except')
        if 'if' in item['buggy_code']:
            tags.append('if_statement')

        item['tags'] = tags

        # 3. 添加时间戳
        from datetime import datetime
        item['processed_at'] = datetime.now().isoformat()

    return data

def main():
    """主流程"""
    print("🔄 开始处理数据...")

    # 1. 读取基础数据
    print("\n📥 读取基础错误数据...")
    base_data = process_base_errors()
    print(f"✅ 基础数据: {len(base_data)} 条")

    # 2. 读取BugsInPy数据
    print("\n📥 读取BugsInPy数据...")
    bugsinpy_data = process_bugsinpy_data()
    print(f"✅ BugsInPy数据: {len(bugsinpy_data)} 条")

    # 3. 合并和清洗
    print("\n🧹 合并和清洗数据...")
    cleaned_data = merge_and_clean(base_data, bugsinpy_data)
    print(f"✅ 清洗后: {len(cleaned_data)} 条")

    # 4. 分类
    print("\n📂 按错误类型分类...")
    categorized = categorize_errors(cleaned_data)
    print(f"✅ 错误类型: {len(categorized)} 种")
    for cat, items in categorized.items():
        print(f"  - {cat}: {len(items)} 条")
    
    # 5. 标注
    print("\n🏷️  数据标注...")
    annotated_data = annotate_data(cleaned_data)
    print(f"✅ 标注完成")

    # 6. 保存
    output = {
        'metadata': {
            'version': '1.0',
            'total_count': len(annotated_data),
            'sources': ['manual', 'bugsinpy'],
            'categories': list(categorized.keys()),
            'processing_date': datetime.now().isoformat()
        },
        'categories': categorized,
        'all_bugs': annotated_data
    }
    
    output_path = Path('data/processed/bugs_raw.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 数据处理完成！")
    print(f"📁 保存路径: {output_path}")
    print(f"📊 总计: {len(annotated_data)} 条数据")

if __name__ == "__main__":
    from datetime import datetime
    main()