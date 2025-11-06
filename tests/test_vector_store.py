"""测试向量数据库 - 完整RAG流程"""
import json
from src.rag.chunk import TextChunker
from src.rag.embedder import Embedder
from src.rag.vector_store import VectorStore

print("🧪 测试完整RAG流程\n")
print("=" * 50)

# 步骤1: 加载数据
print("\n📊 步骤1: 加载Stack Overflow数据")
with open("data/processed/stackoverflow_1k.json", 'r', encoding='utf-8') as f:
    qa_data = json.load(f)

print(f"✅ 加载 {len(qa_data)} 条数据")

# 步骤2: 文本分块（只用前20条测试）
print("\n📊 步骤2: 文本分块")
chunker = TextChunker(chunk_size=500, chunk_overlap=50)
chunks = chunker.process_qa_data(qa_data[:20])

# 步骤3: 生成embedding
print("\n📊 步骤3: 生成Embedding")
embedder = Embedder()
chunks_with_embeddings = embedder.process_chunks_with_embeddings(chunks)

# 步骤4: 存入向量数据库
print("\n📊 步骤4: 存入向量数据库")
vector_store = VectorStore(collection_name="test_stackoverflow")
vector_store.add_documents(chunks_with_embeddings)

# 步骤5: 测试检索
print("\n📊 步骤5: 测试检索功能")
test_question = "How to reverse a list in Python?"
print(f"查询问题: {test_question}")

# 将问题转成向量
question_embedding = embedder.encode_text(test_question)

# 搜索最相似的3个文档
results = vector_store.search(question_embedding, top_k=3)

# 显示结果
print("\n📝 检索结果:")
for i, result in enumerate(results, 1):
    print(f"\n结果 {i}:")
    print(f"  文本: {result['text'][:100]}...")
    print(f"  距离: {result['distance']:.4f}")
    print(f"  来源: {result['metadata']['question'][:50]}...")

print("\n✅ RAG完整流程测试通过！")