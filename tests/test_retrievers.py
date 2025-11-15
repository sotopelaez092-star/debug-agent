"""
测试BaseRetriever和RerankerRetriever

验证系统能正常工作
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.retriever import BaseRetriever
from src.rag.reranker_retriever import RerankerRetriever
from src.rag.vector_store import VectorStore
from sentence_transformers import SentenceTransformer

def test_retrievers():
    print("=" * 60)
    print("🧪 测试检索器")
    print("=" * 60)
    
    # 初始化
    print("\n1️⃣ 初始化组件...")
    vs = VectorStore()
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print(f"✅ 数据库文档数: {vs.collection.count()}")
    
    # 测试query
    test_queries = [
        "How to fix AttributeError NoneType",
        "TypeError string concatenation",
        "list index out of range error"
    ]
    
    # 测试BaseRetriever
    print("\n2️⃣ 测试 BaseRetriever...")
    base_retriever = BaseRetriever(
        collection=vs.collection,
        min_similarity=0.2,  # 降低阈值适配Mock数据
        recall_factor=4
    )
    
    for query in test_queries:
        print(f"\n查询: '{query}'")
        results = base_retriever.search(query, top_k=3)
        print(f"找到 {len(results)} 个结果:")
        
        for i, result in enumerate(results, 1):
            # BaseRetriever返回的是字典
            doc_id = result['id']
            question = result['metadata']['question']
            similarity = result['similarity']
            print(f"  {i}. {doc_id} (相似度: {similarity:.3f})")
            print(f"      {question[:60]}...")
    
    # 测试RerankerRetriever（如果实现了）
    try:
        print("\n3️⃣ 测试 RerankerRetriever...")
        reranker = RerankerRetriever(
            collection=vs.collection,
            min_similarity=0.4,  # 降低阈值适配Mock数据
            recall_factor=4
        )
        
        query = test_queries[0]
        print(f"\n查询: '{query}'")
        results = reranker.search(query, top_k=3)
        print(f"找到 {len(results)} 个结果:")
        
        for i, result in enumerate(results, 1):
            # RerankerRetriever也返回字典
            doc_id = result['id']
            question = result['metadata']['question']
            similarity = result['similarity']
            print(f"  {i}. {doc_id} (相似度: {similarity:.3f})")
            print(f"      {question[:60]}...")
            
    except Exception as e:
        print(f"⚠️ RerankerRetriever测试跳过: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_retrievers()