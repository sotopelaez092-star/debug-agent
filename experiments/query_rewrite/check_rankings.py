# 创建一个测试脚本
# experiments/query_rewrite/check_rankings.py

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.retriever import BaseRetriever
from src.rag.embedder import Embedder
from src.rag.query_rewriter import QueryRewriter
import chromadb
import json

# 初始化
embedder = Embedder("BAAI/bge-small-en-v1.5")
client = chromadb.PersistentClient("data/vectorstore/chroma_s1")
collection = client.get_collection("stackoverflow_kb")
retriever = BaseRetriever(collection, embedder)
rewriter = QueryRewriter()

# 加载测试数据
with open("data/test_cases/test_queries_realistic.json", 'r') as f:
    queries = json.load(f)['queries']

with open("data/evaluation/llm_annotated_gt.json", 'r') as f:
    gt = {anno['query_id']: anno['relevant_docs'] 
          for anno in json.load(f)['annotations']}

# 抽查前5个查询
print("Checking first 5 queries...\n")
for q in queries[:5]:
    query_id = q['query_id']
    query_text = q['query']
    relevant_docs = gt.get(query_id, [])
    
    print(f"Query: {query_id} - '{query_text}'")
    print(f"Ground Truth: {len(relevant_docs)} relevant docs")
    
    # 改写查询
    rewritten = rewriter.rewrite(query_text)
    print(f"Rewritten: '{rewritten}'")
    
    # 检索
    results = retriever.search(rewritten, top_k=10)
    
    # 查找第一个相关文档的排名
    first_relevant_rank = None
    for i, result in enumerate(results, 1):
        doc_id = result['id']
        # 标准化doc_id
        if '_chunk_' in doc_id:
            doc_id = doc_id.split('_chunk_')[0]
        
        if doc_id in relevant_docs:
            first_relevant_rank = i
            break
    
    print(f"First relevant doc rank: {first_relevant_rank}")
    print(f"Top 3 results: {[r['id'][:20] for r in results[:3]]}")
    print("-" * 80)
    print()