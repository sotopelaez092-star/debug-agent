# tests/test_retriever.py
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import logging
import chromadb
from src.rag.retriever import BaseRetriever

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_basic_retrieval():
    print("\n" + "="*60)
    print("测试1：基础检索功能")
    print("="*60)
    
    client = chromadb.PersistentClient(path="./data/chroma_db")
    collection = client.get_collection(name="test_stackoverflow")  # ✅ 不指定embedding_function
    
    retriever = BaseRetriever(
        collection=collection,
        min_similarity=-0.5,  # ✅ 负数阈值
        recall_factor=4
    )
    
    query = "AttributeError: 'NoneType' object has no attribute 'name'"
    print(f"\n查询: {query}\n")
    
    results = retriever.search(query, top_k=5)
    
    print(f"找到 {len(results)} 个结果\n")
    
    if results:
        for r in results:
            print(f"Rank {r['rank']}: similarity={r['similarity']:.3f}, distance={r.get('distance', 'N/A'):.3f}")
            print(f"  ID: {r['id']}")
            print(f"  Metadata: {r['metadata']}")
            print(f"  内容预览: {r['content'][:150]}...")
            print()
    else:
        print("⚠️ 没有找到结果")

if __name__ == "__main__":
    test_basic_retrieval()