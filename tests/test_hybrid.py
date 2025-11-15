"""测试HybridRetriever"""

import sys
sys.path.append('.')

from src.rag.hybrid_retriever import HybridRetriever
from src.rag.embedder import Embedder
import chromadb
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_hybrid_basic():
    """测试混合检索基本功能"""
    
    # 1. 加载ChromaDB
    logger.info("加载向量库...")
    client = chromadb.PersistentClient(path="data/vectorstore/chroma_s1")
    collection = client.get_collection("stackoverflow_kb")
    
    # 2. 创建Embedder
    embedder = Embedder(model_name="BAAI/bge-small-en-v1.5")
    
    # 3. 创建HybridRetriever
    logger.info("创建混合检索器...")
    hybrid_retriever = HybridRetriever(collection, embedder)
    
    # 4. 测试检索
    test_queries = [
        "AttributeError: 'NoneType' object has no attribute",
        "how to fix import error in python"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print(f"{'='*60}")
        
        results = hybrid_retriever.search(query, top_k=5)
        
        for r in results:
            bm25_r = f"BM25#{r['bm25_rank']}" if r['bm25_rank'] else "BM25:无"
            vector_r = f"Vec#{r['vector_rank']}" if r['vector_rank'] else "Vec:无"
            
            print(f"  {r['rank']}. {r['id']} (RRF: {r['score']:.4f})")
            print(f"     来源: {bm25_r}, {vector_r}")


if __name__ == '__main__':
    test_hybrid_basic()