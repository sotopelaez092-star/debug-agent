"""
遗漏文档分布统计脚本

分析所有查询的遗漏文档，统计它们在不同排名区间的分布
"""

import json
import logging
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_recall_analysis(file_path: str) -> Dict:
    """
    加载Recall分析结果
    
    Args:
        file_path: recall_analysis.json文件路径
        
    Returns:
        分析结果字典
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded recall analysis from {file_path}")
    return data


def analyze_missed_distribution(data: Dict) -> Dict:
    """
    分析遗漏文档的排名分布
    
    Args:
        data: recall_analysis.json数据
        
    Returns:
        统计结果字典
    """
    # 统计容器
    stats = {
        'total_queries': 0,
        'total_ground_truth': 0,
        'total_hits': 0,
        'total_missed': 0,
        
        # 遗漏文档按排名分类
        'missed_in_6_10': [],      # Rank 6-10（差一点）
        'missed_in_11_20': [],     # Rank 11-20（靠后）
        'missed_beyond_20': [],    # Rank >20（完全遗漏）
        
        # 计数
        'count_6_10': 0,
        'count_11_20': 0,
        'count_beyond_20': 0,
    }
    
    # 合并所有案例
    all_cases = (
        data.get('poor_cases', []) +
        data.get('moderate_cases', []) +
        data.get('good_cases', []) +
        data.get('perfect_cases', [])
    )
    
    stats['total_queries'] = len(all_cases)
    
    # 遍历所有案例
    for case in all_cases:
        query_id = case['query_id']
        gt_count = case['ground_truth_count']
        hits_count = case['hits_count']
        missed_docs = case['missed_docs']
        
        stats['total_ground_truth'] += gt_count
        stats['total_hits'] += hits_count
        stats['total_missed'] += len(missed_docs)
        
        # 分析每个遗漏文档
        for doc in missed_docs:
            doc_id = doc['doc_id']
            rank = doc['rank']
            similarity = doc['similarity']
            status = doc['status']
            
            doc_info = {
                'query_id': query_id,
                'doc_id': doc_id,
                'rank': rank,
                'similarity': similarity,
                'status': status
            }
            
            # 按排名分类
            if status == 'not_in_top20':
                stats['missed_beyond_20'].append(doc_info)
                stats['count_beyond_20'] += 1
            elif 6 <= rank <= 10:
                stats['missed_in_6_10'].append(doc_info)
                stats['count_6_10'] += 1
            elif 11 <= rank <= 20:
                stats['missed_in_11_20'].append(doc_info)
                stats['count_11_20'] += 1
    
    return stats


def print_statistics(stats: Dict):
    """
    打印统计结果
    
    Args:
        stats: 统计结果字典
    """
    print("\n" + "="*60)
    print("遗漏文档分布统计")
    print("="*60)
    
    # 1. 总体统计
    print(f"\n【总体情况】")
    print(f"总查询数: {stats['total_queries']}")
    print(f"总Ground Truth文档: {stats['total_ground_truth']}")
    print(f"总命中文档: {stats['total_hits']}")
    print(f"总遗漏文档: {stats['total_missed']}")
    print(f"平均Recall@5: {stats['total_hits'] / stats['total_ground_truth'] * 100:.2f}%")
    
    # 2. 遗漏文档分布
    print(f"\n【遗漏文档排名分布】")
    total_missed = stats['total_missed']
    
    print(f"\nRank 6-10 (差一点进Top5):")
    print(f"  数量: {stats['count_6_10']} 个")
    print(f"  占比: {stats['count_6_10'] / total_missed * 100:.1f}% (所有遗漏)")
    
    print(f"\nRank 11-20 (排名靠后):")
    print(f"  数量: {stats['count_11_20']} 个")
    print(f"  占比: {stats['count_11_20'] / total_missed * 100:.1f}% (所有遗漏)")
    
    print(f"\nRank >20 (完全检索不到):")
    print(f"  数量: {stats['count_beyond_20']} 个")
    print(f"  占比: {stats['count_beyond_20'] / total_missed * 100:.1f}% (所有遗漏)")
    
    # 3. 相似度分析
    print(f"\n【相似度分析】")
    
    # Rank 6-10的相似度
    if stats['missed_in_6_10']:
        similarities_6_10 = [d['similarity'] for d in stats['missed_in_6_10'] if d['similarity']]
        if similarities_6_10:
            print(f"\nRank 6-10 相似度:")
            print(f"  最小值: {min(similarities_6_10):.4f}")
            print(f"  最大值: {max(similarities_6_10):.4f}")
            print(f"  平均值: {sum(similarities_6_10) / len(similarities_6_10):.4f}")
    
    # Rank 11-20的相似度
    if stats['missed_in_11_20']:
        similarities_11_20 = [d['similarity'] for d in stats['missed_in_11_20'] if d['similarity']]
        if similarities_11_20:
            print(f"\nRank 11-20 相似度:")
            print(f"  最小值: {min(similarities_11_20):.4f}")
            print(f"  最大值: {max(similarities_11_20):.4f}")
            print(f"  平均值: {sum(similarities_11_20) / len(similarities_11_20):.4f}")
    
    # 4. 严重问题案例（完全遗漏）
    if stats['missed_beyond_20']:
        print(f"\n【严重问题：完全检索不到的文档】")
        print(f"共 {len(stats['missed_beyond_20'])} 个文档\n")
        
        # 按查询分组
        by_query = defaultdict(list)
        for doc in stats['missed_beyond_20']:
            by_query[doc['query_id']].append(doc['doc_id'])
        
        for query_id, doc_ids in sorted(by_query.items()):
            print(f"{query_id}: {len(doc_ids)} 个遗漏")
            for doc_id in doc_ids:
                print(f"  - {doc_id}")
    
    # 5. 优化建议
    print(f"\n" + "="*60)
    print("优化建议")
    print("="*60)
    
    pct_6_10 = stats['count_6_10'] / total_missed * 100
    pct_beyond_20 = stats['count_beyond_20'] / total_missed * 100
    
    if pct_6_10 > 40:
        print("\n⚠️  【优先级1】边缘遗漏问题严重 (>40%在Rank 6-10)")
        print("   建议：")
        print("   - 检索Top10而不是Top5")
        print("   - 调整Reranker权重")
        print("   - 优化排序算法")
    
    if pct_beyond_20 > 20:
        print("\n❌ 【优先级2】完全遗漏问题严重 (>20%不在Top20)")
        print("   建议：")
        print("   - 改进Query改写策略")
        print("   - 增加同义词扩展")
        print("   - 尝试Multi-Query策略")
    
    if pct_6_10 <= 40 and pct_beyond_20 <= 20:
        print("\n✅ 【整体良好】遗漏主要集中在Rank 11-20")
        print("   建议：")
        print("   - 继续优化Query改写")
        print("   - 考虑使用更好的Embedding模型")


def main():
    """主函数"""
    # 文件路径
    RECALL_ANALYSIS_PATH = "experiments/query_rewrite/results/recall_analysis.json"
    
    logger.info("开始遗漏文档分布统计...")
    
    try:
        # 1. 加载数据
        data = load_recall_analysis(RECALL_ANALYSIS_PATH)
        
        # 2. 分析统计
        stats = analyze_missed_distribution(data)
        
        # 3. 打印结果
        print_statistics(stats)
        
        # 4. 保存统计结果
        output_path = "experiments/query_rewrite/results/missed_distribution.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 统计完成！结果已保存到 {output_path}")
        
    except Exception as e:
        logger.error(f"❌ 统计失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()