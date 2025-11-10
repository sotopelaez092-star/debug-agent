# src/rag/reranker_retriever.py
"""带Reranker的检索器"""
from typing import List, Dict, Any
import logging
from FlagEmbedding import FlagReranker

from .retriever import BaseRetriever

logger = logging.getLogger(__name__)


class RerankerRetriever(BaseRetriever):
    """
    带Reranker的两阶段检索器
    
    流程：
    1. 向量检索召回候选（粗排）
    2. Reranker重新打分（精排）
    3. 返回Top-K
    """
    
    def __init__(
        self,
        collection,
        reranker_model_name: str = "BAAI/bge-reranker-base",
        min_similarity: float = 0.5,
        recall_factor: int = 4
    ):
        """
        初始化Reranker检索器
        
        Args:
            collection: ChromaDB collection
            reranker_model_name: Reranker模型名称
            min_similarity: 最低相似度阈值
            recall_factor: 召回倍数
            
        Raises:
            ValueError: 当参数不合法时
        """
        # 1. 验证reranker_model_name
        if not reranker_model_name or not isinstance(reranker_model_name, str):
            raise ValueError("reranker_model_name必须是非空字符串")
        
        # 2. 调用父类初始化
        super().__init__(collection, min_similarity, recall_factor)
        
        # 3. 加载Reranker模型
        logger.info(f"加载Reranker模型: {reranker_model_name}")
        try:
            self.reranker = FlagReranker(reranker_model_name, use_fp16=True)
            logger.info("✅ Reranker模型加载完成")
        except Exception as e:
            logger.error(f"❌ Reranker模型加载失败: {e}", exc_info=True)
            raise
    
    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        两阶段检索
        
        Args:
            query: 查询文本
            top_k: 最终返回数量
            
        Returns:
            Rerank后的结果列表
        """
        logger.info(f"开始两阶段检索，top_k={top_k}")
        
        # 第一阶段：向量检索
        n_candidates = top_k * self.recall_factor
        logger.debug(f"第一阶段：召回{n_candidates}个候选")
        candidates = super().search(query, top_k=n_candidates)
        
        # 第二阶段：Rerank
        logger.debug(f"第二阶段：Rerank {len(candidates)}个候选")
        reranked = self._rerank(query, candidates, top_k)
        
        logger.info(f"检索完成，返回{len(reranked)}个结果")
        
        return reranked
    
    def _rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        使用Reranker重新排序
        
        Args:
            query: 查询文本
            candidates: 候选文档列表
            top_k: 返回数量
            
        Returns:
            重新排序后的Top-K结果
        """
        # 1. 边界检查
        if not candidates:
            logger.warning("没有候选文档需要rerank")
            return []
        
        logger.info(f"开始Rerank，候选数量：{len(candidates)}")
        
        # 2. 准备query-document pairs
        pairs = [[query, doc['content']] for doc in candidates]
        
        # 3. 调用reranker打分
        try:
            scores = self.reranker.compute_score(pairs)
        except Exception as e:
            logger.error(f"Rerank失败：{e}", exc_info=True)
            logger.warning("返回原始排序")
            return candidates[:top_k]
        
        # 4. 如果scores是单个数字（只有一个候选），转成列表
        if not isinstance(scores, list):
            scores = [scores]
        
        # 5. 将分数添加到候选文档中
        for doc, score in zip(candidates, scores):
            doc['rerank_score'] = float(score)
        
        # 6. 按rerank_score排序
        reranked = sorted(
            candidates,
            key=lambda x: x['rerank_score'],
            reverse=True
        )
        
        # 7. 更新rank
        final_results = []
        for rank, doc in enumerate(reranked[:top_k], start=1):
            doc['rank'] = rank
            final_results.append(doc)
        
        logger.info(
            f"Rerank完成：{len(candidates)} -> {len(final_results)}, "
            f"最高分：{final_results[0]['rerank_score']:.3f}"
        )
        
        return final_results