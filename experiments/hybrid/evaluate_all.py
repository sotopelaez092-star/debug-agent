"""评估三个检索器：Vector、BM25、Hybrid"""

import sys
sys.path.append('.')

import json
import logging
from typing import List, Dict
import chromadb

from src.rag.retriever import BaseRetriever
from src.rag.bm25_retriever import BM25Retriever
from src.rag.hybrid_retriever import HybridRetriever
from src.rag.embedder import Embedder
from src.rag.evaluator import ChunkingEvaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_test_data():
    """加载测试数据"""
    # 加载queries
    with open('data/test_cases/test_queries_realistic.json', 'r') as f:
        data = json.load(f)
        queries = [{'id': q['query_id'], 'text': q['query']} for q in data['queries']]
    
    # 加载ground truth
    with open('data/evaluation/llm_annotated_gt.json', 'r') as f:
        data = json.load(f)
        ground_truth = {a['query_id']: a['relevant_docs'] for a in data['annotations']}
    
    return queries, ground_truth



def evaluate_retriever(retriever_name: str, retriever, queries, ground_truth):
    """评估单个检索器"""
    logger.info(f"\n{'='*60}")
    logger.info(f"开始评估: {retriever_name}")
    logger.info(f"{'='*60}")
    
    # 创建评估器
    evaluator = ChunkingEvaluator(retriever)
    
    # 运行评估
    results = evaluator.evaluate(queries, ground_truth, k_values=[1, 3, 5, 10])
    
    # 打印结果
    logger.info(f"\n{retriever_name} 评估结果:")
    logger.info(f"  Recall@1:  {results['recall'][1]:.2%}")
    logger.info(f"  Recall@3:  {results['recall'][3]:.2%}")
    logger.info(f"  Recall@5:  {results['recall'][5]:.2%}")
    logger.info(f"  Recall@10: {results['recall'][10]:.2%}")
    logger.info(f"  MRR:       {results['mrr']:.3f}")
    logger.info(f"  平均速度:   {results['avg_retrieval_time']*1000:.1f}ms")
    
    return results

def main():
    """主函数"""
    # 1. 加载测试数据
    logger.info("加载测试数据...")
    queries, ground_truth = load_test_data()
    logger.info(f"加载完成: {len(queries)}个查询, {len(ground_truth)}个ground truth")
    
    # 2. 初始化ChromaDB和Embedder
    logger.info("\n初始化向量库和模型...")
    client = chromadb.PersistentClient(path="data/vectorstore/chroma_s1")
    collection = client.get_collection("stackoverflow_kb")
    embedder = Embedder(model_name="BAAI/bge-small-en-v1.5")
    
    # 3. 评估三个检索器
    all_results = {}
    
    # 评估R1-Vector
    logger.info("\n" + "="*60)
    logger.info("R1: Vector-only (BaseRetriever)")
    logger.info("="*60)
    vector_retriever = BaseRetriever(collection, embedder)
    all_results['R1-Vector'] = evaluate_retriever('R1-Vector', vector_retriever, queries, ground_truth)
    
    # 评估R2-BM25
    logger.info("\n" + "="*60)
    logger.info("R2: BM25-only (BM25Retriever)")
    logger.info("="*60)
    bm25_retriever = BM25Retriever(collection)
    all_results['R2-BM25'] = evaluate_retriever('R2-BM25', bm25_retriever, queries, ground_truth)
    
    # 评估R3-Hybrid
    logger.info("\n" + "="*60)
    logger.info("R3: Hybrid (HybridRetriever)")
    logger.info("="*60)
    hybrid_retriever = HybridRetriever(collection, embedder)
    all_results['R3-Hybrid'] = evaluate_retriever('R3-Hybrid', hybrid_retriever, queries, ground_truth)
    
    # 4. 生成对比报告
    logger.info("\n" + "="*60)
    logger.info("对比表格")
    logger.info("="*60)
    
    # 打印表头
    print(f"\n{'Retriever':<15} {'Recall@1':<10} {'Recall@3':<10} {'Recall@5':<10} {'Recall@10':<11} {'MRR':<8} {'Speed(ms)':<10}")
    print("-" * 80)
    
    # 打印每个检索器的结果
    for retriever_name, results in all_results.items():
        print(f"{retriever_name:<15} "
              f"{results['recall'][1]:<10.2%} "
              f"{results['recall'][3]:<10.2%} "
              f"{results['recall'][5]:<10.2%} "
              f"{results['recall'][10]:<11.2%} "
              f"{results['mrr']:<8.3f} "
              f"{results['avg_retrieval_time']*1000:<10.1f}")
    
    # 5. 保存结果到JSON
    import os
    os.makedirs('experiments/hybrid/results', exist_ok=True)
    
    output_file = 'experiments/hybrid/results/evaluation_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✅ 结果已保存到: {output_file}")
    logger.info("✅ 评估完成！")

 
if __name__ == '__main__':
    main()