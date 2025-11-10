# tests/test_reranker.py
"""测试RerankerRetriever"""
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import logging
import chromadb
from src.rag.retriever import BaseRetriever
from src.rag.reranker_retriever import RerankerRetriever

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_compare_retrievers():
    """对比BaseRetriever和RerankerRetriever"""
    print("\n" + "="*60)
    print("对比测试：BaseRetriever vs RerankerRetriever")
    print("="*60)
    
    # 1. 初始化
    client = chromadb.PersistentClient(path="./data/chroma_db")
    collection = client.get_collection(name="test_stackoverflow")
    
    # 2. 创建两个检索器
    base_retriever = BaseRetriever(
        collection=collection,
        min_similarity=-0.5,
        recall_factor=4
    )
    
    reranker_retriever = RerankerRetriever(
        collection=collection,
        reranker_model_name="BAAI/bge-reranker-base",
        min_similarity=-0.5,
        recall_factor=4
    )
    
    # 3. 测试query
    query = "AttributeError: 'NoneType' object has no attribute 'name'"
    print(f"\n查询: {query}\n")
    
    # 4. BaseRetriever检索
    print("\n" + "-"*60)
    print("【方法1】BaseRetriever (只有向量检索)")
    print("-"*60)
    base_results = base_retriever.search(query, top_k=5)
    
    if base_results:
        for r in base_results:
            print(f"\nRank {r['rank']}: similarity={r['similarity']:.3f}")
            print(f"  ID: {r['id']}")
            print(f"  内容: {r['content'][:100]}...")
    else:
        print("⚠️ 没有结果")
    
    # 5. RerankerRetriever检索
    print("\n" + "-"*60)
    print("【方法2】RerankerRetriever (向量检索 + Reranker)")
    print("-"*60)
    reranker_results = reranker_retriever.search(query, top_k=5)
    
    if reranker_results:
        for r in reranker_results:
            print(f"\nRank {r['rank']}: rerank_score={r['rerank_score']:.3f}, similarity={r['similarity']:.3f}")
            print(f"  ID: {r['id']}")
            print(f"  内容: {r['content'][:100]}...")
    else:
        print("⚠️ 没有结果")
    
    # 6. 对比分析
    print("\n" + "="*60)
    print("对比分析")
    print("="*60)
    print(f"BaseRetriever: 找到 {len(base_results)} 个结果")
    print(f"RerankerRetriever: 找到 {len(reranker_results)} 个结果")
    
    if base_results and reranker_results:
        print("\n排序是否改变？")
        base_ids = [r['id'] for r in base_results]
        reranker_ids = [r['id'] for r in reranker_results]
        
        if base_ids == reranker_ids:
            print("  ❌ 排序完全相同（Reranker没起作用）")
        else:
            print("  ✅ 排序发生变化（Reranker重新排序了）")
            print(f"  BaseRetriever Top-1: {base_ids[0]}")
            print(f"  RerankerRetriever Top-1: {reranker_ids[0]}")

if __name__ == "__main__":
    test_compare_retrievers()