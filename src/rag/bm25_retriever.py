"""BM25关键词检索器"""

from typing import List, Dict, Any
import logging
import numpy as np
from rank_bm25 import BM25Okapi
from chromadb import Collection

logger = logging.getLogger(__name__)

    
        
class BM25Retriever:
    """基于BM25的关键词检索器"""
    
    def __init__(
        self, 
        collection: Collection,
        min_score: float = 0.0
    ):
        """
        初始化BM25检索器
        
        Args:
            collection: ChromaDB collection对象
            min_score: 最小BM25分数阈值
        """
        # 1.输入验证
        if not collection:
            logger.error("collection不能为空")
            raise ValueError("collection不能为空")
        if min_score < 0.0 or min_score > 1.0:
            logger.error(f"min_score必须在0.0到1.0之间，当前值为 {min_score}")
            raise ValueError(f"min_score必须在0.0到1.0之间，当前值为 {min_score}")
        
        self.collection = collection
        self.min_score = min_score

        logger.info("开始加载文档并构建BM25索引")

        
        try:
            # 2. 从collection加载所有文档
            documents = collection.get()

            if not documents['ids'] or not documents['documents']:
                logger.error("文档列表为空，无法构建BM25索引")
                raise ValueError("文档列表为空")

            logger.info(f"成功加载 {len(documents['ids'])} 个文档")

            # 3. 保存文档
            self.doc_ids = documents["ids"]
            self.doc_contents = documents["documents"]

            # 5. 验证文档内容
            if not self.doc_ids or not self.doc_contents:
                logger.error("文档列表为空，无法构建BM25索引")
                raise ValueError("文档列表为空")

            # 6. 分词
            tokenized_docs = [self._tokenize(doc) for doc in self.doc_contents]

            # 7. 构建BM25索引
            self.bm25 = BM25Okapi(tokenized_docs)

            logger.info(f"BM25索引构建完成，共 {len(self.doc_ids)} 个文档")

        except Exception as e:
            logger.error(f"构建BM25索引失败: {e}", exc_info=True)
            raise
    
    def _tokenize(self, text: str) -> List[str]:
        """
        分词方法
        
        Args:
            text: 待分词的文本
            
        Returns:
            词列表
        """
        if not text:
            return []
        # 转小写
        tokens = text.lower()
        # 简单分词，按空格分隔
        tokens = tokens.split()
        # 过滤空字符串
        tokens = [t for t in tokens if t]

        return tokens
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回文档数量
            
        Returns:
            检索结果列表

        Raises:
            ValueError: 当query为空时或top_k无效
        """
        # 1. 输入验证
        if not query:
            logger.error("查询文本不能为空")
            raise ValueError("查询文本不能为空")
        if top_k <= 0:
            logger.error(f"top_k必须大于0，当前值为 {top_k}")
            raise ValueError(f"top_k必须大于0，当前值为 {top_k}")
        try:
            # 2. 对query分词
            tokenized_query = self._tokenize(query)

            # 3. 用BM25检索，获取所有分数
            bm25_scores = self.bm25.get_scores(tokenized_query)

            # 4. 获取top_k索引（按分数从高到低）
            top_indices = np.argsort(bm25_scores)[::-1][:top_k]

            # 5. 过滤低分结果（score < min_score)
            valid_indices = [i for i in top_indices if bm25_scores[i] >= self.min_score]

            # 6. 格式化返回结果
            results = []
            for rank, idx in enumerate(valid_indices, 1):
                results.append({
                    'id': self.doc_ids[idx],
                    'content': self.doc_contents[idx],
                    'score': float(bm25_scores[idx]),
                    'rank': rank
                })
            return results
        except Exception as e:
            logger.error(f"BM25检索文档失败: {e}", exc_info=True)
            return []

        


        