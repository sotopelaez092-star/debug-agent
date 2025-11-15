"""
Reranker完整评估

目标：
- 用30个真实query测试BaseRetriever vs Reranker
- 计算Recall@5对比
- 分析性能差异

预计耗时：20-30分钟
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time
import logging
import json
from typing import List, Dict, Any
from collections import defaultdict
import chromadb
from sentence_transformers import CrossEncoder

from src.rag.retriever import BaseRetriever
from src.rag.embedder import Embedder

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
CONFIG = {
    'test_file': 'data/test_cases/test_queries_realistic.json',
    'vectorstore_path': 'data/vectorstore/chroma_s1',
    'embedding_model': 'BAAI/bge-small-en-v1.5',
    'reranker_model': 'tomaarsen/Qwen3-Reranker-0.6B-seq-cls',
    'recall_k': 40,  # 召回40个
    'top_k': 5       # 评估Top 5
}


def load_test_queries(test_file: str) -> List[Dict[str, Any]]:
    """
    加载测试查询
    
    Args:
        test_file: 测试文件路径
        
    Returns:
        查询列表
        
    Raises:
        FileNotFoundError: 如果文件不存在
        ValueError: 如果格式不正确
    """
    test_path = Path(test_file)
    
    if not test_path.exists():
        raise FileNotFoundError(f"测试文件不存在: {test_path}")
    
    logger.info(f"📂 加载测试集: {test_file}")
    
    with open(test_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'queries' not in data:
        raise ValueError("测试文件格式错误：缺少'queries'字段")
    
    queries = data['queries']
    logger.info(f"✅ 加载成功，共 {len(queries)} 个测试query")
    
    return queries


def load_models() -> tuple[BaseRetriever, CrossEncoder]:
    """
    加载检索器和Reranker
    
    Returns:
        (base_retriever, reranker)
    """
    logger.info("🤖 加载模型...")
    
    # 1. 加载向量数据库
    vectorstore_path = Path(CONFIG['vectorstore_path'])
    client = chromadb.PersistentClient(path=str(vectorstore_path))
    collection = client.get_collection(name="stackoverflow_kb")
    
    logger.info(f"✅ Vectorstore加载成功，文档数：{collection.count()}")
    
    # 2. 加载Embedder
    embedder = Embedder(model_name=CONFIG['embedding_model'])
    logger.info(f"✅ Embedder加载成功")
    
    # 3. 创建BaseRetriever
    retriever = BaseRetriever(
        collection=collection,
        embedding_function=embedder,
        min_similarity=0.5,
        recall_factor=4
    )
    logger.info("✅ BaseRetriever创建成功")
    
    # 4. 加载Qwen3-Reranker
    reranker = CrossEncoder(CONFIG['reranker_model'])
    logger.info(f"✅ Qwen3-Reranker加载成功: {CONFIG['reranker_model']}")
        
    return retriever, reranker


def calculate_recall_at_k(
    retrieved_ids: List[str],
    ground_truth_ids: List[str],
    k: int
) -> float:
    """
    计算Recall@K
    
    Args:
        retrieved_ids: 检索到的文档ID列表
        ground_truth_ids: 真实相关文档ID列表
        k: 评估前K个
        
    Returns:
        Recall@K分数
    """
    if not ground_truth_ids:
        return 0.0
    
    # 只看前K个
    top_k_ids = retrieved_ids[:k]
    
    # 提取文档ID（去掉chunk后缀）
    def extract_doc_id(doc_id: str) -> str:
        """提取文档ID（去掉_chunk_X）"""
        if '_chunk_' in doc_id:
            return doc_id.split('_chunk_')[0]
        return doc_id
    
    top_k_doc_ids = {extract_doc_id(id) for id in top_k_ids}
    gt_doc_ids = {extract_doc_id(id) for id in ground_truth_ids}
    
    # 计算召回
    hits = len(top_k_doc_ids & gt_doc_ids)
    recall = hits / len(gt_doc_ids)
    
    return recall


def evaluate_retriever(
    retriever: BaseRetriever,
    test_queries: List[Dict[str, Any]],
    top_k: int,
    name: str = "BaseRetriever"
) -> Dict[str, Any]:
    """
    评估检索器
    
    Args:
        retriever: 检索器
        test_queries: 测试查询列表
        top_k: 评估前K个
        name: 检索器名称
        
    Returns:
        评估结果
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"🔍 评估 {name}")
    logger.info(f"{'='*80}")
    
    recalls = []
    total_time = 0
    detailed_results = []
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case['query']
        ground_truth = test_case['ground_truth']
        
        # 检索
        start_time = time.time()
        results = retriever.search(query, top_k=CONFIG['recall_k'])
        query_time = time.time() - start_time
        total_time += query_time
        
        # 提取ID
        retrieved_ids = [r['id'] for r in results]
        
        # 计算Recall@K
        recall = calculate_recall_at_k(retrieved_ids, ground_truth, top_k)
        recalls.append(recall)
        
        # 记录详细结果
        detailed_results.append({
            'query_id': test_case['query_id'],
            'query': query,
            'ground_truth': ground_truth,
            'retrieved_top5': retrieved_ids[:top_k],
            'recall': recall,
            'time_ms': query_time * 1000
        })
        
        # 每10个打印一次进度
        if i % 10 == 0:
            logger.info(f"  进度: {i}/{len(test_queries)}, 当前平均Recall@{top_k}: {sum(recalls)/len(recalls):.4f}")
    
    # 统计
    avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
    avg_time = total_time / len(test_queries) if test_queries else 0.0
    
    logger.info(f"\n📊 {name} 结果:")
    logger.info(f"   Recall@{top_k}: {avg_recall:.4f}")
    logger.info(f"   平均耗时: {avg_time*1000:.2f}ms")
    logger.info(f"   总耗时: {total_time:.2f}秒")
    
    return {
        'name': name,
        'recall_at_k': avg_recall,
        'avg_time_ms': avg_time * 1000,
        'total_time_s': total_time,
        'detailed_results': detailed_results
    }


def evaluate_reranker(
    retriever: BaseRetriever,
    reranker: CrossEncoder,
    test_queries: List[Dict[str, Any]],
    top_k: int
) -> Dict[str, Any]:
    """
    评估Reranker
    
    Args:
        retriever: 基础检索器
        reranker: Reranker模型
        test_queries: 测试查询列表
        top_k: 评估前K个
        
    Returns:
        评估结果
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"🎯 评估 Reranker")
    logger.info(f"{'='*80}")
    
    recalls = []
    total_retrieval_time = 0
    total_rerank_time = 0
    detailed_results = []
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case['query']
        ground_truth = test_case['ground_truth']
        
        # 1. 基础检索
        start_time = time.time()
        candidates = retriever.search(query, top_k=CONFIG['recall_k'])
        retrieval_time = time.time() - start_time
        total_retrieval_time += retrieval_time
        
        if not candidates:
            recalls.append(0.0)
            continue
        
        # 2. Rerank
        pairs = [[query, doc['content']] for doc in candidates]
        
        start_time = time.time()
        try:
            scores = reranker.predict(pairs)  
            if hasattr(scores, 'tolist'):
                scores = scores.tolist()
            elif not isinstance(scores, list):
                scores = [float(scores)]
        except Exception as e:
            logger.error(f"Query {i} Rerank失败: {e}")
            recalls.append(0.0)
            continue
        
        rerank_time = time.time() - start_time
        total_rerank_time += rerank_time
        
        # 3. 处理分数
        if not isinstance(scores, list):
            scores = [scores]
        
        # 4. 添加分数并排序
        for doc, score in zip(candidates, scores):
            doc['rerank_score'] = float(score)
        
        reranked = sorted(
            candidates,
            key=lambda x: x['rerank_score'],
            reverse=True
        )
        
        # 5. 提取ID
        retrieved_ids = [r['id'] for r in reranked]
        
        # 6. 计算Recall@K
        recall = calculate_recall_at_k(retrieved_ids, ground_truth, top_k)
        recalls.append(recall)
        
        # 7. 记录详细结果
        detailed_results.append({
            'query_id': test_case['query_id'],
            'query': query,
            'ground_truth': ground_truth,
            'retrieved_top5': retrieved_ids[:top_k],
            'recall': recall,
            'retrieval_time_ms': retrieval_time * 1000,
            'rerank_time_ms': rerank_time * 1000,
            'total_time_ms': (retrieval_time + rerank_time) * 1000
        })
        
        # 每10个打印一次进度
        if i % 10 == 0:
            logger.info(f"  进度: {i}/{len(test_queries)}, 当前平均Recall@{top_k}: {sum(recalls)/len(recalls):.4f}")
    
    # 统计
    avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
    avg_retrieval_time = total_retrieval_time / len(test_queries) if test_queries else 0.0
    avg_rerank_time = total_rerank_time / len(test_queries) if test_queries else 0.0
    avg_total_time = avg_retrieval_time + avg_rerank_time
    
    logger.info(f"\n📊 Reranker 结果:")
    logger.info(f"   Recall@{top_k}: {avg_recall:.4f}")
    logger.info(f"   平均检索耗时: {avg_retrieval_time*1000:.2f}ms")
    logger.info(f"   平均Rerank耗时: {avg_rerank_time*1000:.2f}ms")
    logger.info(f"   平均总耗时: {avg_total_time*1000:.2f}ms")
    logger.info(f"   总耗时: {(total_retrieval_time + total_rerank_time):.2f}秒")
    
    return {
        'name': 'Reranker',
        'recall_at_k': avg_recall,
        'avg_retrieval_time_ms': avg_retrieval_time * 1000,
        'avg_rerank_time_ms': avg_rerank_time * 1000,
        'avg_total_time_ms': avg_total_time * 1000,
        'total_time_s': total_retrieval_time + total_rerank_time,
        'detailed_results': detailed_results
    }


def compare_results(
    base_result: Dict[str, Any],
    rerank_result: Dict[str, Any],
    top_k: int
) -> None:
    """
    对比两种方法的结果
    
    Args:
        base_result: BaseRetriever结果
        rerank_result: Reranker结果
        top_k: 评估的K值
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 对比分析")
    logger.info(f"{'='*80}")
    
    # 1. 整体对比
    base_recall = base_result['recall_at_k']
    rerank_recall = rerank_result['recall_at_k']
    diff = rerank_recall - base_recall
    diff_pct = (diff / base_recall * 100) if base_recall > 0 else 0
    
    logger.info(f"\n🎯 Recall@{top_k} 对比:")
    logger.info(f"   BaseRetriever:  {base_recall:.4f}")
    logger.info(f"   Reranker:       {rerank_recall:.4f}")
    logger.info(f"   差异:           {diff:+.4f} ({diff_pct:+.2f}%)")
    
    if diff > 0:
        logger.info(f"   ✅ Reranker提升了 {diff_pct:.2f}%")
    elif diff < 0:
        logger.info(f"   ❌ Reranker降低了 {abs(diff_pct):.2f}%")
    else:
        logger.info(f"   ⚖️  两者相同")
    
    # 2. 性能对比
    base_time = base_result['avg_time_ms']
    rerank_time = rerank_result['avg_total_time_ms']
    time_ratio = rerank_time / base_time if base_time > 0 else 0
    
    logger.info(f"\n⏱️  性能对比:")
    logger.info(f"   BaseRetriever:  {base_time:.2f}ms")
    logger.info(f"   Reranker:       {rerank_time:.2f}ms")
    logger.info(f"   慢了:           {time_ratio:.1f}倍")
    
    # 3. 逐query分析
    logger.info(f"\n📈 逐Query分析:")
    
    better = 0
    worse = 0
    same = 0
    
    for base_detail, rerank_detail in zip(
        base_result['detailed_results'],
        rerank_result['detailed_results']
    ):
        base_r = base_detail['recall']
        rerank_r = rerank_detail['recall']
        
        if rerank_r > base_r:
            better += 1
        elif rerank_r < base_r:
            worse += 1
        else:
            same += 1
    
    total = len(base_result['detailed_results'])
    logger.info(f"   更好: {better}/{total} ({better/total*100:.1f}%)")
    logger.info(f"   更差: {worse}/{total} ({worse/total*100:.1f}%)")
    logger.info(f"   相同: {same}/{total} ({same/total*100:.1f}%)")
    
    # 4. 找出变化最大的cases
    logger.info(f"\n🔍 变化最大的cases:")
    
    changes = []
    for base_detail, rerank_detail in zip(
        base_result['detailed_results'],
        rerank_result['detailed_results']
    ):
        change = rerank_detail['recall'] - base_detail['recall']
        changes.append({
            'query_id': base_detail['query_id'],
            'query': base_detail['query'][:50],
            'base_recall': base_detail['recall'],
            'rerank_recall': rerank_detail['recall'],
            'change': change
        })
    
    # 排序：变化最大的（正向和负向各5个）
    changes_sorted = sorted(changes, key=lambda x: x['change'], reverse=True)
    
    logger.info(f"\n   📈 提升最大的5个:")
    for i, c in enumerate(changes_sorted[:5], 1):
        if c['change'] > 0:
            logger.info(
                f"      {i}. {c['query_id']}: {c['query']}... "
                f"({c['base_recall']:.2f} → {c['rerank_recall']:.2f}, +{c['change']:.2f})"
            )
    
    logger.info(f"\n   📉 下降最大的5个:")
    for i, c in enumerate(changes_sorted[-5:][::-1], 1):
        if c['change'] < 0:
            logger.info(
                f"      {i}. {c['query_id']}: {c['query']}... "
                f"({c['base_recall']:.2f} → {c['rerank_recall']:.2f}, {c['change']:.2f})"
            )


def save_results(
    base_result: Dict[str, Any],
    rerank_result: Dict[str, Any]
) -> None:
    """
    保存评估结果
    
    Args:
        base_result: BaseRetriever结果
        rerank_result: Reranker结果
    """
    output_path = Path("tests/results/reranker_debug/full_evaluation.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 准备数据
    data = {
        'config': CONFIG,
        'base_retriever': base_result,
        'reranker': rerank_result,
        'comparison': {
            'recall_diff': rerank_result['recall_at_k'] - base_result['recall_at_k'],
            'recall_diff_pct': (rerank_result['recall_at_k'] - base_result['recall_at_k']) / base_result['recall_at_k'] * 100 if base_result['recall_at_k'] > 0 else 0,
            'time_ratio': rerank_result['avg_total_time_ms'] / base_result['avg_time_ms'] if base_result['avg_time_ms'] > 0 else 0
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n💾 详细结果已保存到: {output_path}")


def main():
    """主函数"""
    logger.info("🚀 开始Reranker完整评估\n")
    
    try:
        # 1. 加载测试集
        test_queries = load_test_queries(CONFIG['test_file'])
        
        # 2. 加载模型
        retriever, reranker = load_models()
        
        # 3. 评估BaseRetriever
        base_result = evaluate_retriever(
            retriever,
            test_queries,
            top_k=CONFIG['top_k'],
            name="BaseRetriever"
        )
        
        # 4. 评估Reranker
        rerank_result = evaluate_reranker(
            retriever,
            reranker,
            test_queries,
            top_k=CONFIG['top_k']
        )
        
        # 5. 对比分析
        compare_results(base_result, rerank_result, CONFIG['top_k'])
        
        # 6. 保存结果
        save_results(base_result, rerank_result)
        
        # 7. 总结
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ 评估完成!")
        logger.info(f"{'='*80}")
        
    except Exception as e:
        logger.error(f"❌ 评估失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()