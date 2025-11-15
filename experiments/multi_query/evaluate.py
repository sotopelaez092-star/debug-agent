# experiments/multi_query/evaluate.py
"""
Multi-Query检索器评估脚本

对比：
- Baseline: Query改写 + BaseRetriever
- Multi-Query: MultiQueryRetriever

评估指标：
- Recall@5
- Recall@10
- 检索时间
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List

import chromadb

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.retriever import BaseRetriever
from src.rag.embedder import Embedder
from src.rag.query_rewriter import QueryRewriter
from src.rag.multi_query_retriever import MultiQueryRetriever

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_queries(file_path: str) -> List[Dict[str, str]]:
    """加载测试查询"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    queries = []
    for item in data.get('queries', []):
        query_id = item.get('query_id')
        query_text = item.get('query')
        if query_id and query_text:
            queries.append({'id': query_id, 'text': query_text})
    
    logger.info(f"加载{len(queries)}个测试查询")
    return queries


def load_ground_truth(file_path: str) -> Dict[str, List[str]]:
    """加载Ground Truth"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    ground_truth = {}
    for anno in data.get('annotations', []):
        query_id = anno.get('query_id')
        relevant_docs = anno.get('relevant_docs', [])
        if query_id and relevant_docs:
            ground_truth[query_id] = relevant_docs
    
    logger.info(f"加载{len(ground_truth)}个ground truth")
    return ground_truth


def extract_base_doc_id(doc_id: str) -> str:
    """提取基础文档ID"""
    if '_chunk_' in doc_id:
        return doc_id.split('_chunk_')[0]
    return doc_id


def calculate_recall(
    retrieved_ids: List[str], 
    ground_truth_ids: List[str], 
    k: int
) -> float:
    """计算Recall@k"""
    if not ground_truth_ids:
        return 0.0
    
    top_k_ids = retrieved_ids[:k]
    retrieved_base = set(extract_base_doc_id(id_) for id_ in top_k_ids)
    gt_base = set(extract_base_doc_id(id_) for id_ in ground_truth_ids)
    hits = retrieved_base & gt_base
    
    return len(hits) / len(gt_base)


def main():
    """主函数"""
    try:
        # 配置
        QUERIES_FILE = "data/test_cases/test_queries_realistic.json"
        GT_FILE = "data/evaluation/llm_annotated_gt.json"
        VECTORSTORE_PATH = "data/vectorstore/chroma_s1"
        OUTPUT_FILE = "experiments/multi_query/results/evaluation_results.json"
        
        logger.info("=" * 60)
        logger.info("Multi-Query检索器评估")
        logger.info("=" * 60)
        
        # Step 1: 加载数据
        logger.info("\n[Step 1/4] 加载数据...")
        queries = load_queries(QUERIES_FILE)
        ground_truth = load_ground_truth(GT_FILE)
        
        # Step 2: 初始化组件
        logger.info("\n[Step 2/4] 初始化组件...")
        embedder = Embedder("BAAI/bge-small-en-v1.5")
        client = chromadb.PersistentClient(path=VECTORSTORE_PATH)
        collection = client.get_collection(name="stackoverflow_kb")
        
        # BaseRetriever
        base_retriever = BaseRetriever(
            collection, 
            embedder, 
            min_similarity=0.5, 
            recall_factor=4
        )
        
        # QueryRewriter
        rewriter = QueryRewriter()
        
        # MultiQueryRetriever
        multi_query_retriever = MultiQueryRetriever(
            base_retriever=base_retriever,
            num_queries=3,
            top_k_per_query=10,
            temperature=0.7
        )
        
        logger.info("组件初始化完成")
        
        # Step 3: 评估
        logger.info("\n[Step 3/4] 开始评估...")
        
        baseline_results = []
        multiquery_results = []
        
        for idx, query in enumerate(queries, 1):
            query_id = query['id']
            
            if query_id not in ground_truth:
                continue
            
            gt_ids = ground_truth[query_id]
            original_query = query['text']
            
            # Baseline: Query改写 + Base检索
            rewritten = rewriter.rewrite(original_query)
            
            start_time = time.time()
            base_docs = base_retriever.search(rewritten, top_k=10)
            base_time = time.time() - start_time
            
            base_ids = [d['id'] for d in base_docs]
            base_r5 = calculate_recall(base_ids, gt_ids, 5)
            base_r10 = calculate_recall(base_ids, gt_ids, 10)
            
            # Multi-Query
            start_time = time.time()
            mq_docs = multi_query_retriever.search(original_query, top_k=10)
            mq_time = time.time() - start_time
            
            mq_ids = [d['id'] for d in mq_docs]
            mq_r5 = calculate_recall(mq_ids, gt_ids, 5)
            mq_r10 = calculate_recall(mq_ids, gt_ids, 10)
            
            baseline_results.append({
                'query_id': query_id,
                'recall_5': base_r5,
                'recall_10': base_r10,
                'time': base_time
            })
            
            multiquery_results.append({
                'query_id': query_id,
                'recall_5': mq_r5,
                'recall_10': mq_r10,
                'time': mq_time,
                'improvement_r5': mq_r5 - base_r5,
                'improvement_r10': mq_r10 - base_r10
            })
            
            logger.info(
                f"[{idx}/{len(queries)}] {query_id}:\n"
                f"  Baseline: R@5={base_r5:.2%}, R@10={base_r10:.2%}, "
                f"Time={base_time:.2f}s\n"
                f"  Multi-Q:  R@5={mq_r5:.2%}, R@10={mq_r10:.2%}, "
                f"Time={mq_time:.2f}s\n"
                f"  Change:   ΔR@5={mq_r5-base_r5:+.2%}, "
                f"ΔR@10={mq_r10-base_r10:+.2%}"
            )
        
        # Step 4: 汇总结果
        logger.info("\n[Step 4/4] 汇总结果...")
        
        n = len(baseline_results)
        
        avg_base_r5 = sum(r['recall_5'] for r in baseline_results) / n
        avg_base_r10 = sum(r['recall_10'] for r in baseline_results) / n
        avg_base_time = sum(r['time'] for r in baseline_results) / n
        
        avg_mq_r5 = sum(r['recall_5'] for r in multiquery_results) / n
        avg_mq_r10 = sum(r['recall_10'] for r in multiquery_results) / n
        avg_mq_time = sum(r['time'] for r in multiquery_results) / n
        
        imp_r5 = avg_mq_r5 - avg_base_r5
        imp_r10 = avg_mq_r10 - avg_base_r10
        imp_r5_pct = (imp_r5 / avg_base_r5 * 100) if avg_base_r5 > 0 else 0
        imp_r10_pct = (imp_r10 / avg_base_r10 * 100) if avg_base_r10 > 0 else 0
        
        # 统计提升情况
        better_r5 = sum(1 for r in multiquery_results if r['improvement_r5'] > 0)
        better_r10 = sum(1 for r in multiquery_results if r['improvement_r10'] > 0)
        worse_r5 = sum(1 for r in multiquery_results if r['improvement_r5'] < 0)
        worse_r10 = sum(1 for r in multiquery_results if r['improvement_r10'] < 0)
        same_r5 = n - better_r5 - worse_r5
        same_r10 = n - better_r10 - worse_r10
        
        print("\n" + "=" * 60)
        print("📊 评估结果")
        print("=" * 60)
        print(f"测试查询数: {n}")
        
        print(f"\n【Baseline - Query改写 + Base】")
        print(f"  平均 Recall@5:  {avg_base_r5:.2%}")
        print(f"  平均 Recall@10: {avg_base_r10:.2%}")
        print(f"  平均检索时间:   {avg_base_time:.3f}s")
        
        print(f"\n【Multi-Query】")
        print(f"  平均 Recall@5:  {avg_mq_r5:.2%}")
        print(f"  平均 Recall@10: {avg_mq_r10:.2%}")
        print(f"  平均检索时间:   {avg_mq_time:.3f}s")
        
        print(f"\n【提升情况】")
        print(f"  Recall@5:")
        print(f"    绝对提升: {imp_r5:+.2%}")
        print(f"    相对提升: {imp_r5_pct:+.1f}%")
        print(f"    更好: {better_r5}个 ({better_r5/n*100:.1f}%)")
        print(f"    相同: {same_r5}个 ({same_r5/n*100:.1f}%)")
        print(f"    更差: {worse_r5}个 ({worse_r5/n*100:.1f}%)")
        
        print(f"  Recall@10:")
        print(f"    绝对提升: {imp_r10:+.2%}")
        print(f"    相对提升: {imp_r10_pct:+.1f}%")
        print(f"    更好: {better_r10}个 ({better_r10/n*100:.1f}%)")
        print(f"    相同: {same_r10}个 ({same_r10/n*100:.1f}%)")
        print(f"    更差: {worse_r10}个 ({worse_r10/n*100:.1f}%)")
        
        print(f"  检索时间:")
        print(f"    增加: {avg_mq_time - avg_base_time:+.3f}s")
        print(f"    相对增加: {(avg_mq_time/avg_base_time-1)*100:+.1f}%")
        print("=" * 60)
        
        # 打印提升最大的案例
        print("\n🔝 Recall@10提升最大的Top5查询:")
        sorted_r10 = sorted(
            multiquery_results,
            key=lambda x: x['improvement_r10'],
            reverse=True
        )
        for r in sorted_r10[:5]:
            base_r = next(
                b['recall_10'] for b in baseline_results 
                if b['query_id'] == r['query_id']
            )
            print(
                f"  {r['query_id']}: {base_r:.2%} → {r['recall_10']:.2%} "
                f"({r['improvement_r10']:+.2%})"
            )
        
        # 保存结果
        Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total': n,
                    'baseline': {
                        'recall_5': avg_base_r5,
                        'recall_10': avg_base_r10,
                        'avg_time': avg_base_time
                    },
                    'multiquery': {
                        'recall_5': avg_mq_r5,
                        'recall_10': avg_mq_r10,
                        'avg_time': avg_mq_time
                    },
                    'improvement': {
                        'recall_5_abs': imp_r5,
                        'recall_5_rel': imp_r5_pct,
                        'recall_10_abs': imp_r10,
                        'recall_10_rel': imp_r10_pct,
                        'better_r5': better_r5,
                        'better_r10': better_r10,
                        'worse_r5': worse_r5,
                        'worse_r10': worse_r10
                    }
                },
                'baseline_results': baseline_results,
                'multiquery_results': multiquery_results
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ 完成! 结果已保存到: {OUTPUT_FILE}")
        
        # 决策建议
        print("\n💡 决策建议:")
        if imp_r10 >= 0.05:  # 提升≥5%
            print("  ✅ Multi-Query效果显著，建议采用！")
        elif 0.02 <= imp_r10 < 0.05:  # 提升2-5%
            print("  ⚠️ Multi-Query有一定效果，可以考虑采用")
            print("     但需要权衡检索时间增加的成本")
        else:  # 提升<2%
            print("  ❌ Multi-Query提升不明显，不建议采用")
            print("     当前Query改写 + Base已经足够好")
        
    except Exception as e:
        logger.error(f"❌ 评估失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
