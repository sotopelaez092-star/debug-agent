from src.rag.vector_store import VectorStore

vs = VectorStore()
print(f'Collection名称: {vs.collection.name}')
print(f'文档数量: {vs.collection.count()}')

# 如果有数据，看看前几条
if vs.collection.count() > 0:
    results = vs.collection.get(limit=3)
    print(f'前3个文档ID: {results["ids"]}')
    print(f'元数据: {results["metadatas"]}')
else:
    print('❌ 数据库为空！')
