import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.batch_evaluate import setup_project_files, run_single_case
import json

# 加载案例21
with open('data/test_cases/week6_test_set.json', 'r') as f:
    data = json.load(f)
    case_21 = data['test_cases'][20]  # 案例21是索引20

# 测试
result = run_single_case(case_21)

# 打印结果
print("\n" + "="*60)
if result['success'] and result['attempts'][0]['verification']['success']:
    print("✅ 案例21首次成功！")
else:
    print("❌ 案例21首次失败")
    
print(f"尝试次数: {len(result['attempts'])}")
print("="*60)