"""
RAGSearcher - RAG知识检索器
封装RAG系统
"""

import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.rag.query_rewriter import QueryRewriter
from src.rag.retriever import BaseRetriever
from src.rag.embedder import Embedder
import chromadb

logger = logging.getLogger(__name__)

class RAGSearcher:
    """
    RAG知识检索器
    
    功能：
    1. 封装RAG系统
    2. Query改写
    3. 向量检索
    4. 返回相关解决方案
    """

    def __init__(
        self,
        vectorstore_path: str = "data/vectorstore/chroma_s1",
        top_k: int = 5
    ):
        """
        初始化RAGSearcher

        Args:
            vectorstore_path: 向量数据库路径
            top_k: 检索TopK结果

        Raises:
            FileNotFounError: 当向量数据库不存在时
        """
        logger.info("开始初始化RAGSearcher...")

        # 1. 验证向量数据库路径
        self.vectorstore_path = vectorstore_path

        if not os.path.exists(self.vectorstore_path):
            raise FileNotFoundError(
            f"向量数据库不存在: {vectorstore_path}\n"
            f"请确认向量数据库已创建"
            )
        logger.info(f"向量数据库路径：{vectorstore_path}")

        # 2. 初始化Embedder
        try:
            self.embedder = Embedder(
                model_name="BAAI/bge-small-en-v1.5"
            )
            logger.info("Embedder初始化成功")
        except Exception as e:
            logger.error(f"Embedder初始化失败: {e}", exc_info=True)
            raise RuntimeError(f"Embedder初始化失败: {e}")
            
        # 3. 链接ChromaDB
        try:
            client = chromadb.PersistentClient(path=vectorstore_path)

            # 获取collection
            collections = client.list_collections()
            if not collections:
                raise ValueError(f"向量数据库中没有collection: {vectorstore_path}")
            
            # 使用第一个collection
            self.collection = collections[0]

            # 获取文档数量
            doc_count = self.collection.count()
            logger.info(f"collection文档数量: {doc_count}")
            
        except Exception as e:
            logger.error(f"ChromaDB初始化失败: {e}", exc_info=True)
            raise RuntimeError(f"ChromaDB初始化失败: {e}")

        # 4. 初始化QueryRewriter
        try:
            self.query_rewriter = QueryRewriter()
            logger.info("QueryRewriter初始化成功")
        except Exception as e:
            logger.error(f"QueryRewriter初始化失败: {e}", exc_info=True)
            raise RuntimeError(f"QueryRewriter初始化失败: {e}")

        # 5. 初始化BaseRetriever
        try:
            self.retriever = BaseRetriever(
                collection=self.collection,
                embedding_function=self.embedder,
                min_similarity=0.5,
                recall_factor=4
            )
            logger.info("BaseRetriever初始化成功")
        except Exception as e:
            logger.error(f"BaseRetriever初始化失败: {e}", exc_info=True)
            raise RuntimeError(f"BaseRetriever初始化失败: {e}")
        # 6. 保存配置
        self.top_k = top_k
    
        logger.info(
            f"RAGSearcher初始化完成 - "
            f"文档数: {doc_count}, "
            f"默认top_k: {top_k}"
        )



    def search(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        检索相关解决方案

        Args:
            query: 输入查询
            top_k: 检索TopK结果（可选）
            
        Returns:
            [
                {
                    "contest": "解决方案内容",
                    "similarity": 0.85,
                    "metadata": {...},
                    "rank": 1
                },
                ...
            ]

        Raises:
            ValueError: 当query为空时
        """
        # 1. 输入验证
        if not query or not isinstance(query, str):
            raise ValueError("query必须是非空字符串")

        # 去除首尾空白)
        query = query.strip()
    
        if len(query) == 0:
            raise ValueError("query不能为空")

        # 限制长度
        if len(query) > 1000:
            logger.warning(f"Query过长({len(query)}字符)，截断至1000")
            query = query[:1000]

        # 使用传入的top_k,或使用默认值
        k = top_k if top_k is not None else self.top_k

        if k <= 0 or k > 20:
            raise ValueError("top_k必须在1-20之间")

        logger.info(f"开始检索，query: {query[:50]}..., top_k: {k}")

        # 2. Query改写
        try:
            rewritten_query = self.query_rewriter.rewrite(query)
            logger.info(f"Query改写完成")
            logger.debug(f"原始Query: {query}")
            logger.debug(f"改写后: {rewritten_query}")
        except Exception as e:
            logger.warning(f"Query改写失败，使用原始query: {e}")
            rewritten_query = query
        
        # 3. 向量检索
        try:
            results = self.retriever.search(
                query=rewritten_query,
                top_k=k
            )
            logger.info(f"检索完成，返回{len(results)}个结果")
        except Exception as e:
            logger.error(f"检索失败: {e}", exc_info=True)
            raise RuntimeError(f"检索失败: {e}")
        
        # 4. 格式化返回结果
        formatted_results = []
        
        for result in results:
            formatted_results.append({
                "content": result.get("content", ""),
                "similarity": result.get("similarity", 0.0),
                "metadata": result.get("metadata", {}),
                "rank": result.get("rank", 0)
            })
        
        logger.info(f"返回{len(formatted_results)}个格式化结果")
        
        return formatted_results
        

# 测试代码
if __name__ == "__main__":
    # 初始化
    searcher = RAGSearcher()

    # 测试查询
    test_query = "AttributeError: 'NoneType' object has no attribute 'name'"
    
    results = searcher.search(test_query, top_k=3)
    
    print(f"\n查询: {test_query}")
    print(f"找到 {len(results)} 个相关方案:\n")
    
    for i, result in enumerate(results, 1):
        print(f"方案 {i}:")
        print(f"  相似度: {result.get('similarity', 0):.3f}")
        print(f"  内容: {result.get('content', '')[:100]}...")
        print()