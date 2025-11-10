# src/rag/retriever.py
"""文档检索器"""
from typing import List, Dict, Any, Optional, final
import logging
from chromadb import Collection

logger = logging.getLogger(__name__)

class BaseRetriever:
    """
    基础检索器

    功能：
    1. 根据错误信息检索相关的解决方案
    2. 过滤低相关度结果
    3. 格式化输出
    """


    def __init__(
        self,
        collection: Collection,
        min_similarity: float = 0.5,
        recall_factor: int = 4
    ):
        """初始化检索器"""
        if not collection:
            raise ValueError('collection不能为空')
        if not isinstance(min_similarity, (int, float)):
            raise ValueError('min_similarity必须是数字')
        
        # ✅ 改这里：允许负数
        if min_similarity < -1 or min_similarity > 1:
            raise ValueError('min_similarity必须在-1到1之间')  # 改成 -1 到 1
        
        if not isinstance(recall_factor, int):
            raise TypeError('recall_factor必须是整数')
        if recall_factor < 1:
            raise ValueError('recall_factor必须大于等于1')
        
        self.collection = collection
        self.min_similarity = min_similarity
        self.recall_factor = recall_factor
        
        logger.info(
            f"初始化BaseRetriever: min_similarity={min_similarity},"
            f"recall_factor={recall_factor}"
        )

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        f"""
        检索相关文档

        Args:
            query: 查询文本（错误信息）
            top_k: 返回结果数量

        Returns:
            相关文档列表，格式：
            [
                {{
                    "id": 文档ID,
                    "content": 文档内容,
                    'similarity': 相似度分数
                    "metadata": 元数据字典,
                    "rank": 排名
                }}
                ...
            ]
        Raises:
            ValueError: 当query为空或top_k不合法时
        """

        # 1. 输入验证
        if not query or not isinstance(query, str):
            raise ValueError('query必须是非空字符串')
        if len(query) > 10000:
            logger.warning(f"query过长({len(query)}字符)，可能影响性能")
        if not isinstance(top_k, int):
            raise TypeError('top_k必须是整数')
        if top_k < 1:
            raise ValueError('top_k必须是正整数')
        if top_k > 100:
            raise ValueError('top_k不能超过100')

        logger.info(f"开始检索，query长度={len(query)}，top_k={top_k}")

        # 2. 查询预处理
        cleaned_query = self._preprocess_query(query)
        logger.debug(f"预处理后的query: {cleaned_query}")

        # 3. 向量检索（召回 top_k * recall_factor 个候选）
        n_results = top_k * self.recall_factor
        raw_results = self._vector_search(cleaned_query, n_results)
        
        # 4. 过滤低相关度
        filtered_results = self._filter_by_similarity(
            raw_results,
            self.min_similarity
        )

        # 5. 格式化输出
        final_results = self._format_results(filtered_results, top_k)

        logger.info(f"格式化完成，返回{len(final_results)}个结果")
        return final_results

    def _preprocess_query(self, query: str) -> str:
        """
        清理查询文本，提取关键信息

        处理步骤：
        1. 去除Traceback行
        2. 去除文件路径信息（File “xxx”， line xxx）
        3. 提取错误类型和消息
        4. 限制长度（避免超过embedding模型token限制)

        Args:
            query: 原始错误信息

        Returns:
            清理后的查询文本
        """
        # 1. 按行分割
        lines = query.split('\n')

        # 2. 过滤无用行
        cleaned_lines = []
        for line in lines:
            if line.strip().startswith('Traceback'):
                continue
            if line.strip().startswith('File'):
                continue
            if not line.strip():
                continue
            cleaned_lines.append(line.strip())

        MAX_LENGTH = 500
        # 3. 重新组合
        cleaned = '\n'.join(cleaned_lines)

        # 4. 保持长度
        if len(cleaned) > MAX_LENGTH:
            logger.warning(f"查询文本过长({len(cleaned)}字符)，已截断为{MAX_LENGTH}字符")
            cleaned = cleaned[:MAX_LENGTH]

        return cleaned

    def _vector_search(
        self,
        query: str,
        n_results: int
    ) -> Dict[str, List]:
        """
        向量搜索

        Args:
            query: 清理后的查询文档
            n_results: 找回文档数量 (top_k * recall_Factor)

        Returns:
            ChromaDB原始返回结果
            格式：
            {
                "id": [['id1', 'id2', ...]],
                "document": [['doc1', 'doc2', ...]],
                "metadata": [[{...}, {...}, {...}]],
                'distance': [[0.2, 0.3, ...]]
            }

        Raises:
            Exception: 当检索失败时
        """
        try:
            logger.debug(f"开始向量检索，n_results={n_results}")
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )

            num_results = len(results['ids'][0]) if results['ids'] else 0
            logger.info(f"检索完成，召回{num_results}个文档")

            return results          
        except Exception as e:
            logger.error(f"向量搜索失败: {e}", exc_info=True)
            raise

    def _filter_by_similarity(
        self,
        raw_results: Dict[str, List],
        min_similarity: float
    ) -> Dict[str, List]:
        """
        过滤低相关度的结果

        Args:
            raw_results: ChromaDB原始返回结果
            min_similarity: 最低相似度阈值

        Returns:
            过滤后的结果（仍然是ChromaDB格式）
        """
        # 1. 取出第一批次的数据（因为是嵌套列表）
        ids = raw_results['ids'][0] if raw_results['ids'] else []
        documents = raw_results['documents'][0] if raw_results['documents'] else []
        metadatas = raw_results['metadatas'][0] if raw_results['metadatas'] else []
        distances = raw_results['distances'][0] if raw_results['distances'] else []

        print("\n🔍 调试信息 - 相似度分数：")
        for i, (id, dist) in enumerate(zip(ids[:5], distances[:5])):  # 只看前5个
            similarity = 1 - dist
            print(f"  {i+1}. ID={id}: distance={dist:.4f}, similarity={similarity:.4f}")
        print()
        # 2. 过滤
        filtered_ids = []
        filtered_documents = []
        filtered_metadatas = []
        filtered_distances = []

        for id, doc, meta, dist in zip(ids, documents, metadatas, distances):
            similarity = 1- dist

            if similarity >= min_similarity:
                filtered_ids.append(id)
                filtered_documents.append(doc)
                filtered_metadatas.append(meta)
                filtered_distances.append(dist)

        # 3. 日志
        logger.info(
            f"过滤完成：{len(ids)} -> {len(filtered_ids)}"
            f"相似度阈值：{min_similarity}"
        )

        # 4. 组织返回结果
        filtered_results = {
            'ids': [filtered_ids],
            'documents': [filtered_documents],
            'metadatas': [filtered_metadatas],
            'distances': [filtered_distances]
        }

        return filtered_results

    def _format_results(
        self,
        raw_results: Dict[str, List],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        格式化检索结果

        Args:
            raw_results: ChromaDB原始返回结果（已过滤）
            top_k: 最终返回数量

        Returns:
            格式化的结果列表，按相似度降序排列
        """
        # 1. 取出第一批次的数据（因为是嵌套列表）
        ids = raw_results['ids'][0] if raw_results['ids'] else []
        documents = raw_results['documents'][0] if raw_results['documents'] else []
        metadatas = raw_results['metadatas'][0] if raw_results['metadatas'] else []
        distances = raw_results['distances'][0] if raw_results['distances'] else []

        # 2. 转换格式
        formatted_results = []
        for id, doc, meta, dist in zip(ids, documents, metadatas, distances):
            formatted_results.append({
                'id': id,
                'content': doc,
                'metadata': meta,
                'similarity': 1 - dist,
                'distance': dist
            })

        # 3. 排序
        formatted_results.sort(key=lambda x: x['similarity'], reverse=True)

        # 4. 限制数量 + 添加rank
        final_results = []
        for rank, result in enumerate(formatted_results[:top_k], start=1):
            result['rank'] = rank
            final_results.append(result)

        logger.info(f"格式化完成，返回{len(final_results)}个结果")

        return final_results
