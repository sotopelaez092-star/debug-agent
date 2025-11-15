# src/rag/vector_store.py
"""向量数据库管理"""
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings

class VectorStore:
    """向量数据库管理类"""
    
    def __init__(self, collection_name: str = "stackoverflow_qa", persist_directory: str = "./data/chroma_db"):
        """初始化向量数据库
        
        Args:
            collection_name: 集合名称（类似表名）
            persist_directory: 数据保存路径
        """
        print(f"📦 初始化向量数据库: {collection_name}")

        # 创建Chroma客户端
        self.client = chromadb.PersistentClient(path=persist_directory)

        # 获取或创建collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"} 
        )
        
        print(f"✅ 向量数据库初始化完成")
        print(f"   当前文档数: {self.collection.count()}")

    def add_documents(self, chunks_with_embeddings: List[Dict]):
        """添加文档到向量数据库
        
        Args:
            chunks_with_embeddings: 带有embedding的文本块列表
                每项包含: text, embedding, source_id等
        """
        print(f"📝 开始添加 {len(chunks_with_embeddings)} 个文档...")
        # 准备数据
        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for idx, chunk in enumerate(chunks_with_embeddings):
            ids.append(f"doc_{chunk['source_id']}_{chunk['chunk_index']}")
            embeddings.append(chunk['embedding'])
            documents.append(chunk['text'])
            metadatas.append({
                'source_id': str(chunk['source_id']),
                'chunk_index': chunk['chunk_index'],
                'question': chunk.get('question', '')
            })

        # 添加到collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✅ 添加完成！当前总数: {self.collection.count()}")

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """搜索最相似的文档

        Args:
            query_embedding: 查询向量
            top_k: 返回的文档数量
            
        Returns:
            包含文档内容和元数据的列表
        """
        print(f"🔍 开始搜索最相似的 {top_k} 个文档...")

        # 调用Chroma的query方法
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # 格式化返回结果
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        print(f"✅ 找到 {len(formatted_results)} 个相关文档")
        return formatted_results