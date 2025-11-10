"""
RAG检索系统评估器

提供评估指标：
- Recall@K: Top-K召回率
- MRR: 平均倒数排名
- 平均检索时间
"""

from typing import List, Dict, Union, Any
import logging
import statistics
import time

logger = logging.getLogger(__name__)


class RetrievalEvaluator:
    """RAG检索系统评估器"""
    
    def __init__(self):
        """初始化评估器"""
        logger.info("初始化RetrievalEvaluator")
    
    def calculate_recall_at_k(
        self,
        retrieved_docs: List[int],
        ground_truth: List[int],
        k: int = 5
    ) -> Dict[str, Union[float, int]]:
        """
        计算Top-K召回率
        
        召回率 = (检索结果前K个中相关文档数量) / (总相关文档数量)
        
        Args:
            retrieved_docs: 检索到的文档ID列表，按相关度排序
            ground_truth: 真实相关文档ID列表（会自动去重）
            k: Top-K的K值，默认5
        
        Returns:
            包含以下字段的字典：
            - recall (float): Top-K召回率，范围[0.0, 1.0]
            - found (int): 前K个结果中找到的相关文档数量
            - total (int): ground_truth中相关文档总数
            - k (int): 使用的K值
        
        Raises:
            ValueError: 当ground_truth为空时（无法计算召回率）
            ValueError: 当k < 1时（k必须为正整数）
        
        Example:
            >>> evaluator = RetrievalEvaluator()
            >>> retrieved_docs = [1, 2, 3, 4, 5]
            >>> ground_truth = [1, 3, 5, 7, 9]
            >>> result = evaluator.calculate_recall_at_k(retrieved_docs, ground_truth, k=3)
            >>> result
            {'recall': 0.4, 'found': 2, 'total': 5, 'k': 3}
        """
        # 输入验证
        if not ground_truth:
            raise ValueError('ground_truth不能为空')
        if k < 1:
            raise ValueError('k必须大于等于1')
        
        # 去重
        ground_truth = list(set(ground_truth))
        
        # 获取前k个检索结果
        top_k_docs = retrieved_docs[:k]
        
        # 计算交集
        found_docs = set(top_k_docs) & set(ground_truth)
        
        # 计算召回率
        recall = len(found_docs) / len(ground_truth)
        
        # 日志记录
        logger.info(
            f"Recall@{k}: {recall:.3f} "
            f"(found {len(found_docs)}/{len(ground_truth)})"
        )
        
        # 返回结果
        return {
            'recall': recall,
            'found': len(found_docs),
            'total': len(ground_truth),
            'k': k
        }
    
    def calculate_mrr(
        self,
        retrieved_docs: List[int],
        ground_truth: List[int]
    ) -> Dict[str, Union[float, int]]:
        """
        计算倒数排名（Reciprocal Rank）
        
        RR = 1 / (第一个相关文档的排名位置)
        如果没有找到任何相关文档，RR = 0
        
        Args:
            retrieved_docs: 检索到的文档ID列表，按相关度排序
            ground_truth: 真实相关文档ID列表（会自动去重）
        
        Returns:
            包含以下字段的字典：
            - rr (float): 倒数排名值，范围[0.0, 1.0]
            - first_relevant_rank (int): 第一个相关文档的位置（1-based），如果未找到则为0
        
        Raises:
            ValueError: 当ground_truth为空时
        
        Example:
            >>> evaluator = RetrievalEvaluator()
            >>> retrieved_docs = [3, 2, 7, 10, 15]
            >>> ground_truth = [2, 5, 10]
            >>> result = evaluator.calculate_mrr(retrieved_docs, ground_truth)
            >>> result
            {'rr': 0.5, 'first_relevant_rank': 2}
        """
        # 输入验证
        if not ground_truth:
            raise ValueError('ground_truth不能为空')
        
        # 去重（保持set以提高查找性能）
        ground_truth_set = set(ground_truth)
        
        # 计算第一个相关文档的排名位置
        first_rank = next(
            (i+1 for i, doc in enumerate(retrieved_docs) if doc in ground_truth_set), 
            0
        )
        
        # 计算RR
        rr = 1.0 / first_rank if first_rank > 0 else 0.0
        
        # 日志
        logger.info(f"MRR: {rr:.3f} (first relevant rank: {first_rank})")
        
        # 返回结果
        return {
            'rr': rr,
            'first_relevant_rank': first_rank
        }
    
    def calculate_avg_time(
        self,
        times: List[float]
    ) -> Dict[str, float]:
        """
        计算检索时间统计
        
        Args:
            times: 检索时间列表，单位为秒
        
        Returns:
            包含以下字段的字典：
            - avg_time (float): 平均检索时间，单位秒
            - min_time (float): 最小检索时间，单位秒
            - max_time (float): 最大检索时间，单位秒
            - std_time (float): 标准差，衡量时间稳定性
        
        Raises:
            ValueError: 当times为空时
        
        Example:
            >>> evaluator = RetrievalEvaluator()
            >>> times = [0.1, 0.2, 0.3, 0.4, 0.5]
            >>> result = evaluator.calculate_avg_time(times)
            >>> result
            {'avg_time': 0.3, 'min_time': 0.1, 'max_time': 0.5, 'std_time': 0.158}
        """
        # 输入验证
        if not times:
            raise ValueError('times不能为空')
        
        # 计算统计量（必须先计算！）
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0.0
        
        # 日志（在计算之后！）
        logger.info(
            f"Time stats: avg={avg_time:.3f}s, "
            f"min={min_time:.3f}s, max={max_time:.3f}s, "
            f"std={std_time:.3f}s"
        )
        
        # 返回结果
        return {
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'std_time': std_time
        }
    
    def compare_retrievers(
        self,
        retriever_a: Any,
        retriever_b: Any,
        test_cases: List[Dict[str, Any]],
        k: int = 5
    ) -> Dict[str, Any]:
        """对比两个检索器的性能"""
        # 输入验证
        if not test_cases:
            raise ValueError('test_cases不能为空')
        if not hasattr(retriever_a, 'search'):
            raise AttributeError('retriever_a必须有search方法')
        if not hasattr(retriever_b, 'search'):
            raise AttributeError('retriever_b必须有search方法')
        
        logger.info(f"开始对比两个检索器，测试用例数: {len(test_cases)}")
        
        # 初始化指标收集列表
        recalls_a, mrrs_a, times_a = [], [], []
        recalls_b, mrrs_b, times_b = [], [], []
        
        # 遍历每个test_case
        for i, case in enumerate(test_cases):
            query = case['query']
            ground_truth = case['ground_truth']
            
            # === 测试 Retriever A ===
            start_time = time.time()
            retrieved_a = retriever_a.search(query, top_k=k)
            time_a = time.time() - start_time
            
            # 计算指标
            recall_result_a = self.calculate_recall_at_k(retrieved_a, ground_truth, k)
            mrr_result_a = self.calculate_mrr(retrieved_a, ground_truth)
            
            recalls_a.append(recall_result_a['recall'])
            mrrs_a.append(mrr_result_a['rr'])
            times_a.append(time_a)
            
            # === 测试 Retriever B ===
            start_time = time.time()
            retrieved_b = retriever_b.search(query, top_k=k)
            time_b = time.time() - start_time
            
            # 计算指标
            recall_result_b = self.calculate_recall_at_k(retrieved_b, ground_truth, k)
            mrr_result_b = self.calculate_mrr(retrieved_b, ground_truth)
            
            recalls_b.append(recall_result_b['recall'])
            mrrs_b.append(mrr_result_b['rr'])
            times_b.append(time_b)
        
        # 计算平均值
        avg_recall_a = sum(recalls_a) / len(recalls_a)
        avg_mrr_a = sum(mrrs_a) / len(mrrs_a)
        time_stats_a = self.calculate_avg_time(times_a)
        
        avg_recall_b = sum(recalls_b) / len(recalls_b)
        avg_mrr_b = sum(mrrs_b) / len(mrrs_b)
        time_stats_b = self.calculate_avg_time(times_b)
        
        # 计算提升幅度
        recall_improvement = avg_recall_b - avg_recall_a
        mrr_improvement = avg_mrr_b - avg_mrr_a
        time_overhead = time_stats_b['avg_time'] - time_stats_a['avg_time']
        
        logger.info(
            f"对比完成: A(recall={avg_recall_a:.3f}, mrr={avg_mrr_a:.3f}), "
            f"B(recall={avg_recall_b:.3f}, mrr={avg_mrr_b:.3f})"
        )
        
        # 返回结果
        return {
            'retriever_a': {
                'name': retriever_a.__class__.__name__,
                'recall@k': avg_recall_a,
                'mrr': avg_mrr_a,
                'avg_time': time_stats_a['avg_time'],
                'total_queries': len(test_cases)
            },
            'retriever_b': {
                'name': retriever_b.__class__.__name__,
                'recall@k': avg_recall_b,
                'mrr': avg_mrr_b,
                'avg_time': time_stats_b['avg_time'],
                'total_queries': len(test_cases)
            },
            'comparison': {
                'recall_improvement': recall_improvement,
                'mrr_improvement': mrr_improvement,
                'time_overhead': time_overhead
            }
        }
    
    def generate_report(
        self,
        comparison_result: Dict[str, Any],
        output_file: str = None
    ) -> str:
        """生成评估报告"""
        from datetime import datetime
        
        # 验证输入
        required_keys = ['retriever_a', 'retriever_b', 'comparison']
        if not all(key in comparison_result for key in required_keys):
            raise ValueError('comparison_result格式错误')
        
        # 提取数据
        a = comparison_result['retriever_a']
        b = comparison_result['retriever_b']
        comp = comparison_result['comparison']
        
        # 构建报告
        report = f"""# RAG检索器评估报告

## 测试概览

- **测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **测试用例数**: {a['total_queries']}个
- **Top-K值**: 5

## 检索器对比

| 指标 | {a['name']} | {b['name']} | 提升 |
|------|-------------|-------------|------|
| **Recall@5** | {a['recall@k']:.1%} | {b['recall@k']:.1%} | {comp['recall_improvement']:+.1%} |
| **MRR** | {a['mrr']:.3f} | {b['mrr']:.3f} | {comp['mrr_improvement']:+.3f} |
| **平均时间** | {a['avg_time']:.3f}s | {b['avg_time']:.3f}s | {comp['time_overhead']:+.3f}s |

## 结论

{b['name']}相比{a['name']}:
- 召回率提升{comp['recall_improvement']:+.1%}
- MRR提升{comp['mrr_improvement']:+.3f}
- 时间开销{comp['time_overhead']:+.3f}秒
"""
        
        # 保存文件
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                logger.info(f"报告已保存到: {output_file}")
            except IOError as e:
                logger.error(f"无法保存报告: {e}")
                raise
        
        return report