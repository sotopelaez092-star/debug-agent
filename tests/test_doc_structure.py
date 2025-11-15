# tests/test_doc_structure.py
"""测试检索结果的文档结构"""
import sys
sys.path.insert(0, '.')

from src.rag.retriever import BaseRetriever
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings  # ✅ 用LangChain

# 初始化Embedding
print("📦 加载Embedding模型...")
embeddings = HuggingFaceEmbeddings(
    model_name='BAAI/bge-small-en-v1.5',
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)
print("✅ 加载完成")

# 连接数据库
client = chromadb.PersistentClient(path="data/chromadb/bge-small-en")
collection = client.get_collection(name="langchain")

# 初始化检索器
retriever = BaseRetriever(
    collection=collection,
    embedding_function=embeddings
)

# 测试检索
print("\n🔍 测试检索...")
docs = retriever.search("How to sort dict", top_k=3)

print("="*70)
print("🔍 检索结果结构分析")
print("="*70)
print(f"\n返回 {len(docs)} 个文档\n")

for i, doc in enumerate(docs[:2], 1):
    print(f"{i}. 文档结构:")
    print(f"   类型: {type(doc)}")
    print(f"   Keys: {doc.keys() if isinstance(doc, dict) else 'N/A'}")
    print(f"   ID: {doc.get('id', 'N/A')}")
    print(f"   Metadata: {doc.get('metadata', {})}")
    
    # 测试提取
    metadata = doc.get('metadata', {})
    doc_id = metadata.get('doc_id', 'NOT_FOUND')
    print(f"   ✅ metadata['doc_id'] = {doc_id} (类型: {type(doc_id)})")
    print()

print("\n🎯 Ground Truth示例:")
import json
with open('data/test_cases/test_queries.json') as f:
    test_data = json.load(f)
print(f"   {test_data[0]['ground_truth']} (类型: {type(test_data[0]['ground_truth'][0])})")