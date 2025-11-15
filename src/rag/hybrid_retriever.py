"""混合检索器：结合BM25和向量检索"""

from typing import List, Dict, Any
import logging
from chromadb import Collection

from src.rag.bm25_retriever import BM25Retriever
from src.rag.retriever import BaseRetriever

logger = logging.getLogger(__name__)


class HybridRetriever:
    """混合检索器：BM25 + Vector"""
    
    def __init__(
        self,
        collection: Collection,
        embedding_function: Any,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
        k: int = 60
    ):
        """
        初始化混合检索器
        
        Args:
            collection: ChromaDB collection
            embedding_function: Embedding函数
            bm25_weight: BM25权重（为以后加权融合预留）
            vector_weight: Vector权重（为以后加权融合预留）
            k: RRF常数
            
        Raises:
            ValueError: 当参数无效时
        """
        # 1. 输入验证
        if collection is None:
            raise ValueError("collection不能为None")
        if embedding_function is None:
            raise ValueError("embedding_function不能为None")
        if k <= 0:
            raise ValueError(f"k必须大于0，当前值为{k}")
        
        # 2. 创建BM25检索器
        logger.info("创建BM25检索器...")
        self.bm25_retriever = BM25Retriever(collection)
        
        # 3. 创建向量检索器
        logger.info("创建向量检索器...")
        self.vector_retriever = BaseRetriever(collection, embedding_function)
        
        # 4. 保存参数
        self.k = k
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        
        logger.info(f"HybridRetriever初始化完成 (RRF k={k})")    
    def _rrf_fusion(
        self,
        bm25_results: List[Dict],
        vector_results: List[Dict],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        RRF融合算法
        
        Args:
            bm25_results: BM25检索结果
            vector_results: 向量检索结果
            top_k: 返回文档数量
            
        Returns:
            融合后的结果
        """
        # 1. 创建文档ID到信息的映射
        doc_scores = {}
        
        # 2. 处理BM25结果
        for r in bm25_results:
            doc_id = r['id']
            rank = r['rank']
            rrf_contribution = 1.0 / (self.k + rank)
            
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    'rrf_score': 0.0,
                    'content': r['content'],
                    'bm25_rank': None,
                    'vector_rank': None
                }
            
            doc_scores[doc_id]['rrf_score'] += rrf_contribution
            doc_scores[doc_id]['bm25_rank'] = rank
        
        # 3. 处理Vector结果
        for r in vector_results:
            doc_id = r['id']
            rank = r['rank']
            rrf_contribution = 1.0 / (self.k + rank)
            
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    'rrf_score': 0.0,
                    'content': r['content'],
                    'bm25_rank': None,
                    'vector_rank': None
                }
            
            doc_scores[doc_id]['rrf_score'] += rrf_contribution
            doc_scores[doc_id]['vector_rank'] = rank
        
        # 4. 按RRF分数排序
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1]['rrf_score'],
            reverse=True
        )[:top_k]
        
        # 5. 格式化返回结果
        results = []
        for rank, (doc_id, info) in enumerate(sorted_docs, 1):
            results.append({
                'id': doc_id,
                'content': info['content'],
                'score': info['rrf_score'],
                'rank': rank,
                'bm25_rank': info['bm25_rank'],
                'vector_rank': info['vector_rank']
            })
        
        return results

        
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        混合检索
        
        Args:
            query: 查询文本
            top_k: 返回文档数量
            
        Returns:
            检索结果列表
            
        Raises:
            ValueError: 当query为空或top_k无效时
        """
        # 1. 输入验证
        if not query:
            logger.error("query不能为空")
            raise ValueError("query不能为空")
        if top_k <= 0:
            logger.error(f"top_k必须大于0，当前值为 {top_k}")
            raise ValueError(f"top_k必须大于0，当前值为 {top_k}")
        
        try:
            logger.info(f"开始混合检索，query长度={len(query)}，top_k={top_k}")
            
            # 2. 调用BM25检索（召回更多候选，比如top_k*2）
            bm25_results = self.bm25_retriever.search(query, top_k=top_k*2)
            logger.info(f"BM25检索完成，召回{len(bm25_results)}个文档")
            
            # 3. 调用Vector检索（召回更多候选，比如top_k*2）
            vector_results = self.vector_retriever.search(query, top_k=top_k*2)
            logger.info(f"Vector检索完成，召回{len(vector_results)}个文档")
            
            # 4. RRF融合
            results = self._rrf_fusion(bm25_results, vector_results, top_k)
            logger.info(f"RRF融合完成，返回{len(results)}个结果")
            
            return results
            
        except Exception as e:
            logger.error(f"混合检索失败: {e}", exc_info=True)
            return []