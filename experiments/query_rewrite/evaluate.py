"""
Query改写效果评估脚本

对比两种方案：
1. Baseline: BaseRetriever（直接检索）
2. Rewrite: QueryRewriter + BaseRetriever（改写后检索）

目标：验证Query改写能否将Recall@5从58.74%提升到70%+
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
import chromadb

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.retriever import BaseRetriever
from src.rag.embedder import Embedder
from src.rag.evaluator import ChunkingEvaluator
from src.rag.query_rewriter import QueryRewriter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_queries(file_path: str) -> List[Dict[str, str]]:
    """
    加载测试查询
    
    Args:
        file_path: 查询文件路径
        
    Returns:
        查询列表，格式: [{'id': 'test-001', 'text': 'query text'}, ...]
        
    Raises:
        FileNotFoundError: 当文件不存在时
        ValueError: 当文件格式不正确时
    """
    logger.info(f"Loading queries from: {file_path}")

    # 输入验证
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Query file not found: {file_path}")
    
    # 读取JSON文件
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误：{e}")
        raise ValueError(f"Invalid query file format: {file_path}")
    
    # 提取queries数组
    raw_queries = data.get('queries', [])
    if not raw_queries:
        raise ValueError(f"Empty queries array in file: {file_path}")

    # 转换格式（跳过不完整的记录）
    queries = []
    for item in raw_queries:
        query_id = item.get('query_id')
        query_text = item.get('query')
        
        if not query_id or not query_text:
            logger.warning(f"Skipping incomplete query: {item}")
            continue
        
        queries.append({
            'id': query_id,
            'text': query_text
        })

    if not queries:
        raise ValueError(f"No valid queries found in file: {file_path}")


    # 记录日志
    logger.info(f"Loaded {len(queries)} queries from {file_path}")
    
    return queries


def load_ground_truth(file_path: str) -> Dict[str, List[str]]:
    """
    加载Ground Truth
    
    Args:
        file_path: Ground Truth文件路径
        
    Returns:
        Ground Truth字典，格式: {'test-001': ['doc-1', 'doc-2'], ...}
        
    Raises:
        FileNotFoundError: 当文件不存在时
        ValueError: 当文件格式不正确时
    """
    logger.info(f"Loading ground truth file: {file_path}")

    # 输入验证
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Ground truth file not found: {file_path}")
    
    # 读取json文件
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误：{e}")
        raise ValueError(f"Invalid ground truth file format: {file_path}")
    
    
    # 提取annotations数组
    raw_annotations = data.get('annotations', [])
    if not raw_annotations:
        raise ValueError(f"Empty annotations array in file: {file_path}")

    # 转换格式
    ground_truth = {}
    for anno in raw_annotations:
        query_id = anno.get('query_id')
        relevant_docs = anno.get('relevant_docs', [])

        if not query_id:
            logger.warning(f"Skipping annotation without query_id: {anno}")
            continue
        if not relevant_docs:
            logger.warning(f"Skipping query {query_id} with empty relevant_docs")
            continue 
        ground_truth[query_id] = relevant_docs
    
    if not ground_truth:
        raise ValueError(f"No valid annotations found in file: {file_path}")
    
    logger.info(f"Loaded {len(ground_truth)} ground truth items from {file_path}")

    return ground_truth


def evaluate_baseline(
    retriever: BaseRetriever,
    queries: List[Dict[str, str]],
    ground_truth: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    评估Baseline方案（不改写查询）
    
    Args:
        retriever: BaseRetriever实例
        queries: 测试查询列表
        ground_truth: Ground Truth
        
    Returns:
        评估结果字典
    """
    
    logger.info("=" * 60)
    logger.info("Evaluating Baseline: BaseRetriever (No Rewrite)")
    logger.info("=" * 60)
    
    try:
        # 创建评估器
        evaluator = ChunkingEvaluator(retriever)

        # 执行评估
        results = evaluator.evaluate(
            queries=queries,
            ground_truth=ground_truth,
            k_values=[1,3,5,10]
        )

        # 添加method字段
        results['method'] = 'BaseRetriever'

        # 记录关键指标
        logger.info(f"Recall@5: {results['recall'][5]:.2%}")
        logger.info(f"MRR: {results['mrr']:.3f}")
        logger.info(f"Avg retrieval time: {results['avg_retrieval_time']*1000:.1f}ms")

        return results

    except Exception as e:
        logger.error(f"Baseline evaluation failed: {e}", exc_info=True)
        raise


def evaluate_with_rewrite(
    retriever: BaseRetriever,
    rewriter: QueryRewriter,
    queries: List[Dict[str, str]],
    ground_truth: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    评估Query改写方案
    
    Args:
        retriever: BaseRetriever实例
        rewriter: QueryRewriter实例
        queries: 测试查询列表
        ground_truth: Ground Truth
        
    Returns:
        评估结果字典
    """
    
    logger.info("=" * 60)
    logger.info("Evaluating Rewrite: QueryRewriter + BaseRetriever")
    logger.info("=" * 60)
    
    try:
        logger.info("Rewriting all queries...")
        rewritten_queries = []
        for query in queries:
            original_text = query['text']
            rewritten_text = rewriter.rewrite(original_text)
            rewritten_queries.append({
                'id': query['id'],
                'text': rewritten_text
            })

        # 记录改写统计
        original_words = sum(len(q['text'].split()) for q in queries)
        rewritten_words = sum(len(q['text'].split()) for q in rewritten_queries)
        logger.info(f"Total words: {original_words} -> {rewritten_words} ({rewritten_words/original_words:.2f}x)")

        # 用改写后的查询评估
        evaluator = ChunkingEvaluator(retriever)
        results = evaluator.evaluate(
            queries=rewritten_queries,
            ground_truth=ground_truth,
            k_values=[1,3,5,10]
        )

        # 添加method字段
        results['method'] = 'QueryRewriter + BaseRetriever'
        
        # 记录关键指标
        logger.info(f"Recall@5: {results['recall'][5]:.2%}")
        logger.info(f"MRR: {results['mrr']:.3f}")
        logger.info(f"Avg retrieval time: {results['avg_retrieval_time']*1000:.1f}ms")

        return results

    except Exception as e:
        logger.error(f"Rewrite evaluation failed: {e}", exc_info=True)
        raise

def print_comparison(
    baseline_results: Dict[str, Any],
    rewrite_results: Dict[str, Any]
) -> None:
    """
    打印对比结果
    
    Args:
        baseline_results: Baseline评估结果
        rewrite_results: Rewrite评估结果
    """
    
    logger.info("\n" + "=" * 80)
    logger.info("Evaluation Results Comparison")
    logger.info("=" * 80)
    
    # Step 1: 提取数据
    baseline_recall = baseline_results['recall']
    rewrite_recall = rewrite_results['recall']
    baseline_mrr = baseline_results['mrr']
    rewrite_mrr = rewrite_results['mrr']
    baseline_time = baseline_results['avg_retrieval_time'] * 1000  # 转换为ms
    rewrite_time = rewrite_results['avg_retrieval_time'] * 1000
    
    # Step 2: 计算变化量
    change_recall = {
        k: rewrite_recall[k] - baseline_recall[k]
        for k in [1, 3, 5, 10]
    }
    change_mrr = rewrite_mrr - baseline_mrr
    change_time = rewrite_time - baseline_time
    
    # Step 3: 打印表头
    print("\nMethod                          Recall@1   Recall@3   Recall@5   Recall@10   MRR      Speed(ms)")
    print("-" * 96)
    
    # Step 4: 打印Baseline行
    print(f"{baseline_results['method']:<30} "
          f"{baseline_recall[1]:>7.2%}    "
          f"{baseline_recall[3]:>7.2%}    "
          f"{baseline_recall[5]:>7.2%}    "
          f"{baseline_recall[10]:>7.2%}    "
          f"{baseline_mrr:>5.3f}    "
          f"{baseline_time:>6.1f}")
    
    # Step 5: 打印Rewrite行
    print(f"{rewrite_results['method']:<30} "
          f"{rewrite_recall[1]:>7.2%}    "
          f"{rewrite_recall[3]:>7.2%}    "
          f"{rewrite_recall[5]:>7.2%}    "
          f"{rewrite_recall[10]:>7.2%}    "
          f"{rewrite_mrr:>5.3f}    "
          f"{rewrite_time:>6.1f}")
    
    # Step 6: 打印变化行
    print("-" * 96)
    print(f"{'Change':<30} "
          f"{change_recall[1]:>+7.2%}    "
          f"{change_recall[3]:>+7.2%}    "
          f"{change_recall[5]:>+7.2%}    "
          f"{change_recall[10]:>+7.2%}    "
          f"{change_mrr:>+6.3f}    "
          f"{change_time:>+7.1f}")


def save_results(
    baseline_results: Dict[str, Any],
    rewrite_results: Dict[str, Any],
    output_dir: str
) -> None:
    """
    保存评估结果到文件
    
    Args:
        baseline_results: Baseline评估结果
        rewrite_results: Rewrite评估结果
        output_dir: 输出目录
    """
    
    logger.info(f"\nSaving results to: {output_dir}")
    
    try:
        # Step 1: 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Step 2: 计算变化量
        comparison = {
            'recall_1_change': rewrite_results['recall'][1] - baseline_results['recall'][1],
            'recall_3_change': rewrite_results['recall'][3] - baseline_results['recall'][3],
            'recall_5_change': rewrite_results['recall'][5] - baseline_results['recall'][5],
            'recall_10_change': rewrite_results['recall'][10] - baseline_results['recall'][10],
            'mrr_change': rewrite_results['mrr'] - baseline_results['mrr'],
            'time_change_ms': (rewrite_results['avg_retrieval_time'] - baseline_results['avg_retrieval_time']) * 1000
        }
        
        # Step 3: 构建完整结果字典
        results = {
            'baseline': baseline_results,
            'rewrite': rewrite_results,
            'comparison': comparison
        }
        
        # Step 4: 保存为JSON
        output_file = output_path / 'evaluation_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Step 5: 记录日志
        logger.info(f"Results saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Failed to save results: {e}", exc_info=True)
        raise

def main():
    """
    主函数：执行完整评估流程
    """
    try:
        # ========== 配置 ==========
        QUERIES_FILE = "data/test_cases/test_queries_realistic.json"
        GT_FILE = "data/evaluation/llm_annotated_gt.json"
        VECTORSTORE_PATH = "data/vectorstore/chroma_s1"  # 使用S1 (Semantic)
        COLLECTION_NAME = "stackoverflow_kb"
        EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
        OUTPUT_DIR = "experiments/query_rewrite/results"
        
        logger.info("Starting Query Rewrite Evaluation")
        logger.info("=" * 80)
        
        # ========== Step 1: 加载数据 ==========
        logger.info("\n[Step 1/5] Loading test data...")
        
        queries = load_queries(QUERIES_FILE)
        ground_truth = load_ground_truth(GT_FILE)
        logger.info(f"Loaded {len(queries)} queries")
        
        # ========== Step 2: 初始化组件 ==========
        logger.info("\n[Step 2/5] Initializing components...")
        
        embedder = Embedder(model_name=EMBEDDING_MODEL)
        client = chromadb.PersistentClient(path=VECTORSTORE_PATH)
        collection = client.get_collection(name=COLLECTION_NAME)
        retriever = BaseRetriever(collection, embedder)
        rewriter = QueryRewriter()
        
        logger.info("All components initialized successfully")
        
        # ========== Step 3: 评估Baseline ==========
        logger.info("\n[Step 3/5] Evaluating Baseline...")
        
        baseline_results = evaluate_baseline(retriever, queries, ground_truth)
        
        # ========== Step 4: 评估Query改写 ==========
        logger.info("\n[Step 4/5] Evaluating Query Rewrite...")
        
        rewrite_results = evaluate_with_rewrite(
            retriever, rewriter, queries, ground_truth
        )
        
        # ========== Step 5: 对比和保存 ==========
        logger.info("\n[Step 5/5] Comparing results and saving...")
        
        print_comparison(baseline_results, rewrite_results)
        save_results(baseline_results, rewrite_results, OUTPUT_DIR)
        
        logger.info("\n" + "=" * 80)
        logger.info("Evaluation Complete!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()