# src/rag/embedder.py
"""Embedding生成器"""
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer

# ============ 全局单例 ============
_global_embedder_instance = None

def get_embedder_instance(model_name: str = "BAAI/bge-small-en-v1.5") -> 'Embedder':
    """
    获取全局Embedder单例
    
    Args:
        model_name: 模型名称
        
    Returns:
        Embedder实例（全局唯一）
    """
    global _global_embedder_instance
    
    if _global_embedder_instance is None:
        print(f"🔧 首次创建Embedder单例...")
        _global_embedder_instance = Embedder(model_name)
    else:
        print(f"✅ 复用已有的Embedder实例")
    
    return _global_embedder_instance
class Embedder:
    """初始化Embedding生成器"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """初始化Embedder
        
        Args:
            model_name: 模型名称（默认用轻量级模型）
        """
        print(f"📦 加载Embedding模型: {model_name}")

        # 加载模型
        self.model = SentenceTransformer(model_name)

        # 获取向量维度
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        print(f"✅ 模型加载完成！向量维度: {self.embedding_dim}")

    def encode_text(self, text: str) -> np.ndarray:
        """把一段文本转换成向量

        Args:
            text: 输入文本，比如 "How to reverse a list?"

        Returns:
            向量 (向量（numpy数组），比如 [0.2, -0.5, 0.8, ...])
        """
        return self.model.encode(text, show_progress_bar=False)

    def encode_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """批量编码多个文本
        
        Args:
            texts: 文本列表，比如 ["text1", "text2", "text3"]
            batch_size: 每批处理多少个（32是平衡速度和内存的好选择）
            
        Returns:
            向量矩阵，shape=(文本数量, 384)
        """
        print(f"🔄 开始编码 {len(texts)} 条文本...")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True
        )
        
        print(f"✅ 编码完成")
        return embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        LangChain兼容接口：批量编码文档
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表（每个向量是float列表）
        """
        # 使用现有的 encode_batch 方法
        embeddings = self.encode_batch(texts)
        
        # 转换为 List[List[float]] 格式（BaseRetriever期望的格式）
        return embeddings.tolist()

    def process_chunks_with_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """为文本块生成embeddings
        
        Args:
            chunks: 文本块列表（来自TextChunker）
            
        Returns:
            带有embedding的文本块列表
        """
        # 提取所有文本
        texts = [chunk['text'] for chunk in chunks]
        
        # 批量生成embeddings
        embeddings = self.encode_batch(texts)
        
        # 将embedding添加到每个块
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding.tolist()
        
        return chunks


