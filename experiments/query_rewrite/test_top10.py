"""
Top10 vs Top5 Recall对比测试
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_queries(file_path: str) -> List[Dict[str, str]]:
    """加载测试查询"""
    logger.info(f"Loading queries from: {file_path}")
    
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
    logger.info(f"Loading ground truth from: {file_path}")
    
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
        OUTPUT_FILE = "experiments/query_rewrite/results/top10_comparison.json"
        
        logger.info("=" * 60)
        logger.info("Top10 vs Top5 Evaluation")
        logger.info("=" * 60)
        
        # Step 1: 加载数据
        logger.info("\n[Step 1/4] Loading data...")
        queries = load_queries(QUERIES_FILE)
        ground_truth = load_ground_truth(GT_FILE)
        
        # Step 2: 初始化
        logger.info("\n[Step 2/4] Initializing...")
        embedder = Embedder("BAAI/bge-small-en-v1.5")
        client = chromadb.PersistentClient(path=VECTORSTORE_PATH)
        collection = client.get_collection(name="stackoverflow_kb")
        retriever = BaseRetriever(collection, embedder, min_similarity=0.5, recall_factor=4)
        rewriter = QueryRewriter()
        logger.info("Components initialized")
        
        # Step 3: 评估
        logger.info("\n[Step 3/4] Evaluating...")
        results = []
        total_r5 = 0.0
        total_r10 = 0.0
        total_hits = 0
        
        for idx, query in enumerate(queries, 1):
            query_id = query['id']
            
            if query_id not in ground_truth:
                continue
            
            # 改写并检索
            rewritten = rewriter.rewrite(query['text'])
            docs = retriever.search(rewritten, top_k=20)
            retrieved_ids = [d['id'] for d in docs]
            gt_ids = ground_truth[query_id]
            
            # 计算Recall
            r5 = calculate_recall(retrieved_ids, gt_ids, 5)
            r10 = calculate_recall(retrieved_ids, gt_ids, 10)
            
            # Rank 6-10新增文档
            top5 = set(extract_base_doc_id(i) for i in retrieved_ids[:5])
            top10 = set(extract_base_doc_id(i) for i in retrieved_ids[:10])
            gt = set(extract_base_doc_id(i) for i in gt_ids)
            new_hits = len((top10 & gt) - top5)
            
            results.append({
                'query_id': query_id,
                'recall_5': r5,
                'recall_10': r10,
                'improvement': r10 - r5,
                'new_hits': new_hits
            })
            
            total_r5 += r5
            total_r10 += r10
            total_hits += new_hits
            
            logger.info(f"[{idx}/{len(queries)}] {query_id}: R@5={r5:.2%}, R@10={r10:.2%}, +{new_hits}docs")
        
        # Step 4: 汇总
        n = len(results)
        avg_r5 = total_r5 / n
        avg_r10 = total_r10 / n
        improvement_pct = (avg_r10 - avg_r5) / avg_r5 * 100
        
        print("\n" + "=" * 60)
        print("📊 结果")
        print("=" * 60)
        print(f"查询数: {n}")
        print(f"平均 Recall@5:  {avg_r5:.2%}")
        print(f"平均 Recall@10: {avg_r10:.2%}")
        print(f"绝对提升: +{avg_r10-avg_r5:.2%}")
        print(f"相对提升: +{improvement_pct:.1f}%")
        print(f"Rank 6-10新增: {total_hits}个文档")
        print("=" * 60)
        
        # 保存
        Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w') as f:
            json.dump({
                'summary': {
                    'total': n,
                    'avg_recall_5': avg_r5,
                    'avg_recall_10': avg_r10,
                    'improvement': avg_r10 - avg_r5,
                    'improvement_pct': improvement_pct,
                    'total_new_hits': total_hits
                },
                'results': results
            }, f, indent=2)
        
        logger.info(f"\n✅ 完成! 结果: {OUTPUT_FILE}")
        
    except Exception as e:
        logger.error(f"❌ 失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()