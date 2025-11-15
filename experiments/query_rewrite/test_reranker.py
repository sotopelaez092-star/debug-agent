"""
测试 Query改写 + Reranker 的效果
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List
import chromadb

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.retriever import BaseRetriever
from src.rag.embedder import Embedder
from src.rag.query_rewriter import QueryRewriter
from src.rag.reranker_retriever import RerankerRetriever  # 你的Reranker

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
    
    logger.info(f"Loaded {len(queries)} queries")
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
    
    logger.info(f"Loaded {len(ground_truth)} ground truth items")
    return ground_truth


def extract_base_doc_id(doc_id: str) -> str:
    """提取基础文档ID"""
    if '_chunk_' in doc_id:
        return doc_id.split('_chunk_')[0]
    return doc_id


def calculate_recall(retrieved_ids: List[str], ground_truth_ids: List[str], k: int) -> float:
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
        OUTPUT_FILE = "experiments/query_rewrite/results/reranker_comparison.json"
        
        logger.info("=" * 60)
        logger.info("Query改写 + Reranker 测试")
        logger.info("=" * 60)
        
        # Step 1: 加载数据
        logger.info("\n[Step 1/4] Loading data...")
        queries = load_queries(QUERIES_FILE)
        ground_truth = load_ground_truth(GT_FILE)
        
        # Step 2: 初始化组件
        logger.info("\n[Step 2/4] Initializing...")
        embedder = Embedder("BAAI/bge-small-en-v1.5")
        client = chromadb.PersistentClient(path=VECTORSTORE_PATH)
        collection = client.get_collection(name="stackoverflow_kb")
        
        # BaseRetriever
        base_retriever = BaseRetriever(
            collection, embedder, 
            min_similarity=0.5, 
            recall_factor=4
        )
        
        # RerankerRetriever
        reranker_retriever = RerankerRetriever(
            collection=collection,
            embedding_function=embedder,
            min_similarity=0.5,
            recall_factor=4
        )
        
        # QueryRewriter
        rewriter = QueryRewriter()
        logger.info("Components initialized")
        
        # Step 3: 对比评估
        logger.info("\n[Step 3/4] Evaluating...")
        
        baseline_results = []  # Query改写 + Base
        reranker_results = []  # Query改写 + Reranker
        
        for idx, query in enumerate(queries, 1):
            query_id = query['id']
            
            if query_id not in ground_truth:
                continue
            
            gt_ids = ground_truth[query_id]
            original_query = query['text']              # ✅ 保存原始查询
            rewritten = rewriter.rewrite(query['text']) # 改写查询
            
            # 方案1: Base检索Top5（用改写后的查询）
            base_docs = base_retriever.search(rewritten, top_k=5)
            base_ids = [d['id'] for d in base_docs]
            base_r5 = calculate_recall(base_ids, gt_ids, 5)
            
            # 方案2: Reranker检索Top5（用原始查询）
            rerank_docs = reranker_retriever.search(original_query, top_k=5)  # ✅ 改成原始查询
            rerank_ids = [d['id'] for d in rerank_docs]
            rerank_r5 = calculate_recall(rerank_ids, gt_ids, 5)  
            baseline_results.append({
                'query_id': query_id,
                'recall_5': base_r5
            })
            
            reranker_results.append({
                'query_id': query_id,
                'recall_5': rerank_r5,
                'improvement': rerank_r5 - base_r5
            })
            
            logger.info(
                f"[{idx}/{len(queries)}] {query_id}: "
                f"Base={base_r5:.2%}, Rerank={rerank_r5:.2%}, "
                f"Δ={rerank_r5-base_r5:+.2%}"
            )
        
        # Step 4: 汇总结果
        n = len(baseline_results)
        
        avg_base = sum(r['recall_5'] for r in baseline_results) / n
        avg_rerank = sum(r['recall_5'] for r in reranker_results) / n
        improvement = avg_rerank - avg_base
        improvement_pct = (improvement / avg_base * 100) if avg_base > 0 else 0
        
        # 统计提升情况
        better = sum(1 for r in reranker_results if r['improvement'] > 0)
        worse = sum(1 for r in reranker_results if r['improvement'] < 0)
        same = sum(1 for r in reranker_results if r['improvement'] == 0)
        
        print("\n" + "=" * 60)
        print("📊 对比结果")
        print("=" * 60)
        print(f"查询数: {n}")
        print(f"\nBaseline (Query改写 + Base):")
        print(f"  平均 Recall@5: {avg_base:.2%}")
        print(f"\nReranker (Query改写 + Reranker):")
        print(f"  平均 Recall@5: {avg_rerank:.2%}")
        print(f"\n提升情况:")
        print(f"  绝对提升: {improvement:+.2%}")
        print(f"  相对提升: {improvement_pct:+.1f}%")
        print(f"\n查询分布:")
        print(f"  更好: {better}个 ({better/n*100:.1f}%)")
        print(f"  相同: {same}个 ({same/n*100:.1f}%)")
        print(f"  更差: {worse}个 ({worse/n*100:.1f}%)")
        print("=" * 60)
        
        # 打印提升最大的案例
        print("\n🔝 提升最大的Top5查询:")
        sorted_results = sorted(
            reranker_results,
            key=lambda x: x['improvement'],
            reverse=True
        )
        for r in sorted_results[:5]:
            base_r = next(b['recall_5'] for b in baseline_results if b['query_id'] == r['query_id'])
            print(f"  {r['query_id']}: {base_r:.2%} → {r['recall_5']:.2%} (+{r['improvement']:.2%})")
        
        # 保存结果
        Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w') as f:
            json.dump({
                'summary': {
                    'total': n,
                    'baseline_avg': avg_base,
                    'reranker_avg': avg_rerank,
                    'improvement': improvement,
                    'improvement_pct': improvement_pct,
                    'better_count': better,
                    'same_count': same,
                    'worse_count': worse
                },
                'baseline_results': baseline_results,
                'reranker_results': reranker_results
            }, f, indent=2)
        
        logger.info(f"\n✅ 完成! 结果: {OUTPUT_FILE}")
        
    except Exception as e:
        logger.error(f"❌ 失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()