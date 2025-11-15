import json

with open('data/test_cases/test_queries.json') as f:
    data = json.load(f)

total = len(data)
has_gt = sum(1 for d in data if 'ground_truth' in d and d['ground_truth'])

print(f"总query数: {total}")
print(f"有ground_truth: {has_gt}")
print(f"没有ground_truth: {total - has_gt}")

if has_gt < total:
    print(f"\n⚠️ 有{total - has_gt}个query没有标注！")
    print(f"这会导致Recall计算不准确")
    
print("\n前5个样本的GT情况:")
for i, d in enumerate(data[:5], 1):
    has = 'ground_truth' in d and d['ground_truth']
    gt_count = len(d.get('ground_truth', [])) if has else 0
    print(f"{i}. {'✅' if has else '❌'} GT数量: {gt_count}")