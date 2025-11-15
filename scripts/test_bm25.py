"""测试BM25Retriever基本功能"""

import sys
sys.path.append('.')

from src.rag.bm25_retriever import BM25Retriever
import chromadb
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def test_bm25_basic():
    """测试BM25基本功能"""
    
    # 1. 加载ChromaDB collection
    logger.info("加载向量库...")
    client = chromadb.PersistentClient(path="data/vectorstore/chroma_s1")
    collection = client.get_collection(name="stackoverflow_kb")
    
    # 2. 创建BM25Retriever
    logger.info("创建BM25检索器...")
    retriever = BM25Retriever(collection)
    
    # 3. 测试检索
    test_queries = [
        "AttributeError: 'NoneType' object has no attribute",
        "TypeError: unsupported operand type",
        "KeyError dictionary key not found"
    ]
    
    for query in test_queries:
        logger.info(f"\n查询: {query}")
        results = retriever.search(query, top_k=3)
        
        for r in results:
            print(f"  [{r['rank']}] {r['id']} (score: {r['score']:.2f})")
            print(f"      {r['content'][:100]}...")

def compare_bm25_vs_vector():
    """对比BM25和向量检索"""
    
    # 1. 加载collection
    client = chromadb.PersistentClient(path="data/vectorstore/chroma_s1")
    collection = client.get_collection("stackoverflow_kb")
    
    # 2. 创建两个检索器
    from src.rag.bm25_retriever import BM25Retriever
    from src.rag.retriever import BaseRetriever
    from src.rag.embedder import Embedder
    
    bm25_retriever = BM25Retriever(collection)
    
    embedder = Embedder(model_name="BAAI/bge-small-en-v1.5")
    vector_retriever = BaseRetriever(collection, embedder)
    
    # 3. 测试查询
    test_queries = [
        "AttributeError: 'NoneType' object has no attribute",
        "how to fix import error in python"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print(f"{'='*60}")
        
        # BM25结果
        print("\n[BM25结果]")
        bm25_results = bm25_retriever.search(query, top_k=3)
        for r in bm25_results:
            print(f"  {r['rank']}. {r['id']} (score: {r['score']:.2f})")
        
        # Vector结果
        print("\n[向量检索结果]")
        vector_results = vector_retriever.search(query, top_k=3)
        for r in vector_results:
            print(f"  {r['rank']}. {r['id']} (similarity: {r['similarity']:.2f})")
        
        # 对比
        bm25_ids = set(r['id'] for r in bm25_results)
        vector_ids = set(r['id'] for r in vector_results)
        overlap = bm25_ids & vector_ids
        
        print(f"\n[重叠度] {len(overlap)}/3 个文档相同")


if __name__ == '__main__':
    compare_bm25_vs_vector()
