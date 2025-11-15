# src/rag/evaluator.py
"""检索器评估模块"""
from typing import List, Dict, Any
import logging
import time

logger = logging.getLogger(__name__)


class ChunkingEvaluator:
    """Chunking策略评估器"""
    
    def __init__(self, retriever: 'BaseRetriever'):
        """
        初始化评估器
        
        Args:
            retriever: 已初始化的检索器
        """
        # 验证retriever是否为空
        if not retriever:
            raise ValueError("retriever不能为空")
        
        # 保存检索器
        self.retriever = retriever
        
        # 打印日志
        logger.info(f"初始化ChunkingEvaluator，绑定检索器: {retriever.__class__.__name__}")
    
    def evaluate(
        self,
        queries: List[Dict[str, str]],      # [{'id': 'test-001', 'text': 'query text'}, ...]
        ground_truth: Dict[str, List[str]], # {'test-001': ['doc-1', 'doc-2'], ...}
        k_values: List[int] = None          # [1, 3, 5, 10]
    ) -> Dict[str, Any]:
        """
        评估检索性能
        
        Args:
            queries: 测试查询列表，每个元素包含 'id' 和 'text' 字段
            ground_truth: 每个query的相关文档ID列表
            k_values: 计算Recall@k的k值列表
            
        Returns:
            评估结果字典，格式：
            {
                'recall': {1: 0.33, 3: 0.50, 5: 0.58, 10: 0.67},
                'mrr': 0.45,
                'avg_retrieval_time': 0.123,
                'failure_rate': 0.20,
                'total_queries': 30,
                'successful_queries': 24,
                'failed_queries': 6
            }
            
        Raises:
            ValueError: 当输入不合法时
        """
        # 输入验证
        if not queries or not ground_truth:
            raise ValueError("queries和ground_truth不能为空")
        
        if not isinstance(queries, list) or not isinstance(ground_truth, dict):
            raise TypeError("queries必须是list，ground_truth必须是dict")
        
        # 验证k_values
        if k_values is None:
            k_values = [1, 3, 5, 10]
        elif not isinstance(k_values, list):
            raise TypeError("k_values必须是list")
        elif not all(isinstance(k, int) and k > 0 for k in k_values):
            raise ValueError("k_values中的所有值必须是正整数")
        
        # 初始化结果收集变量
        results = {
            'recall': {},           # {1: [], 3: [], 5: [], 10: []}
            'mrr_scores': [],       # 存储每个query的MRR
            'retrieval_times': [],  # 存储每个query的检索时间（秒）
            'failures': 0           # 统计失败次数
        }
        
        # 初始化recall的k值
        for k in k_values:
            results['recall'][k] = []
        
        # 打印开始日志
        logger.info(f"开始评估 {len(queries)} 个查询，k_values={k_values}")
        
        # 遍历所有query
        for query_data in queries:
            query_id = query_data['id']
            query_text = query_data['text']
            
            # 1. 获取这个query的ground truth
            true_docs = ground_truth.get(query_id, [])
            if not true_docs:
                logger.warning(f"查询 {query_id} 没有ground truth，跳过")
                results['failures'] += 1
                continue
            
            # 2. 记录开始时间
            start_time = time.time()
            
            # 3. 调用 retriever.search() 获取检索结果
            try:
                # 检索最大k值的文档数
                max_k = max(k_values)
                retrieved_results = self.retriever.search(query_text, top_k=max_k)
            except Exception as e:
                logger.error(f"查询 {query_id} 检索失败: {e}", exc_info=True)
                results['failures'] += 1
                continue
            
            # 4. 记录结束时间
            end_time = time.time()
            retrieval_time = end_time - start_time
            
            # 5. 提取检索到的文档ID列表（保持顺序，标准化格式）
            retrieved_ids = []
            for doc in retrieved_results:
                doc_id = doc['id']
                
                # 标准化doc_id：统一格式为 "so-XXXXXX"
                # 去掉各种后缀：_chunk_X, _answer, _title_answer
                if '_chunk_' in doc_id:
                    doc_id = doc_id.split('_chunk_')[0]
                elif '_title_answer' in doc_id:
                    doc_id = doc_id.split('_title_answer')[0]
                elif '_answer' in doc_id:
                    doc_id = doc_id.split('_answer')[0]
                
                retrieved_ids.append(doc_id)

            # 6. 计算这个query的各项指标
            # 记录检索时间
            results['retrieval_times'].append(retrieval_time)
            
            # 计算各个k值的Recall
            for k in k_values:
                recall_at_k = self._calculate_recall(true_docs, retrieved_ids, k)
                results['recall'][k].append(recall_at_k)
            
            # 计算MRR
            mrr = self._calculate_mrr(true_docs, retrieved_ids)
            results['mrr_scores'].append(mrr)
            
            logger.debug(
                f"查询 {query_id}: "
                f"检索时间={retrieval_time:.3f}s, "
                f"MRR={mrr:.3f}, "
                f"Recall@5={results['recall'][5][-1]:.3f}"
            )
        
        # 7. 汇总统计
        total_queries = len(queries)
        successful_queries = total_queries - results['failures']
        
        # 计算平均指标
        summary = {
            'recall': {},
            'mrr': 0.0,
            'avg_retrieval_time': 0.0,
            'failure_rate': 0.0,
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'failed_queries': results['failures']
        }
        
        # 平均Recall@k
        if successful_queries > 0:
            for k in k_values:
                if results['recall'][k]:
                    summary['recall'][k] = sum(results['recall'][k]) / len(results['recall'][k])
                else:
                    summary['recall'][k] = 0.0
            
            # 平均MRR
            if results['mrr_scores']:
                summary['mrr'] = sum(results['mrr_scores']) / len(results['mrr_scores'])
            
            # 平均检索时间
            if results['retrieval_times']:
                summary['avg_retrieval_time'] = sum(results['retrieval_times']) / len(results['retrieval_times'])
            
            # 失败率
            summary['failure_rate'] = results['failures'] / total_queries
        
        # 打印结束日志
        logger.info(
            f"评估完成！成功: {successful_queries}/{total_queries}, "
            f"失败: {results['failures']}, "
            f"MRR: {summary['mrr']:.3f}, "
            f"Recall@5: {summary['recall'].get(5, 0):.3f}"
        )
        
        return summary
    
    def _calculate_recall(
        self,
        true_docs: List[str],
        retrieved_docs: List[str],
        k: int
    ) -> float:
        """
        计算Recall@k
        
        Recall@k = (检索到的相关文档数) / (总相关文档数)
        
        Args:
            true_docs: 相关文档ID列表（ground truth）
            retrieved_docs: 检索到的文档ID列表（按排名顺序）
            k: 只考虑前k个检索结果
            
        Returns:
            Recall@k分数（0.0 - 1.0）
        """
        if not true_docs:
            return 0.0
        
        # 只看前k个检索结果
        top_k_docs = retrieved_docs[:k]
        
        # 转换为集合，计算交集
        true_set = set(true_docs)
        retrieved_set = set(top_k_docs)
        
        # 计算召回率
        hits = len(true_set & retrieved_set)
        recall = hits / len(true_set)
        
        return recall
    
    def _calculate_mrr(
        self,
        true_docs: List[str],
        retrieved_docs: List[str]
    ) -> float:
        """
        计算Mean Reciprocal Rank (MRR)
        
        MRR = 1 / (第一个相关文档的排名)
        如果没有相关文档，返回0
        
        Args:
            true_docs: 相关文档ID列表（ground truth）
            retrieved_docs: 检索到的文档ID列表（按排名顺序）
            
        Returns:
            MRR分数（0.0 - 1.0）
        """
        if not true_docs:
            return 0.0
        
        true_set = set(true_docs)
        
        # 找到第一个相关文档的位置
        for rank, doc_id in enumerate(retrieved_docs, start=1):
            if doc_id in true_set:
                return 1.0 / rank
        
        # 没有找到相关文档
        return 0.0