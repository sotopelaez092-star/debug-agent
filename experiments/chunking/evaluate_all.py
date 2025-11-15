# experiments/chunking/evaluate_all.py
"""批量评估Chunking策略"""
import sys
from pathlib import Path

# 添加src到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

import json
import logging
from typing import Dict, List, Any
import chromadb

from src.rag.evaluator import ChunkingEvaluator
from src.rag.retriever import BaseRetriever
from src.rag.embedder import Embedder


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 定义6个策略
STRATEGIES = {
    'S0': {'name': 'Full Document', 'vectorstore': 'chroma_s0'},
    'S1': {'name': 'Semantic', 'vectorstore': 'chroma_s1'},
    'S2': {'name': 'Answer-Only', 'vectorstore': 'chroma_s2'},
    'S3': {'name': 'Title+Answer', 'vectorstore': 'chroma_s3'},
    'S4': {'name': 'Fixed-200', 'vectorstore': 'chroma_s4'},
    'S5': {'name': 'Fixed-300', 'vectorstore': 'chroma_s5'},
}

# 数据路径
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
QUERIES_PATH = DATA_DIR / 'test_cases' / 'test_queries_realistic.json'
GT_PATH = DATA_DIR / 'evaluation' / 'llm_annotated_gt.json'
VECTORSTORE_DIR = DATA_DIR / 'vectorstore'




def load_queries() -> List[Dict[str, str]]:
    """
    加载测试queries
    
    Returns:
        queries列表，格式：[{'id': 'test-001', 'text': 'query text'}, ...]
    """
    if not QUERIES_PATH.exists():
        logger.error(f"查询文件不存在: {QUERIES_PATH}")
        raise FileNotFoundError(f"查询文件不存在: {QUERIES_PATH}")
    
    try:
        with open(QUERIES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            raw_queries = data.get('queries', [])
            
            # ✅ 格式转换：query_id -> id, query -> text
            queries = []
            for q in raw_queries:
                queries.append({
                    'id': q['query_id'],      # ← 转换字段名
                    'text': q['query']        # ← 转换字段名
                })
            
            logger.info(f"成功加载 {len(queries)} 个查询")
            return queries
            
    except json.JSONDecodeError:
        logger.error(f"查询文件 {QUERIES_PATH} 格式错误")
        raise ValueError(f"查询文件 {QUERIES_PATH} 格式错误")

def load_ground_truth() -> Dict[str, List[str]]:
    """
    加载ground truth
    
    Returns:
        ground truth字典，格式：{'test-001': ['doc-1', 'doc-2'], ...}
    """
    # 检查 GT_PATH 文件是否存在
    # 读取 JSON 文件
    # 返回 ground truth 字典
    if not GT_PATH.exists():
        logger.error(f"ground truth 文件不存在: {GT_PATH}")
        raise FileNotFoundError(f"ground truth 文件不存在: {GT_PATH}")
    
    try:
        with open(GT_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            annotations = data.get('annotations', [])
            
            # 转换格式
            ground_truth = {}
            for anno in annotations:
                query_id = anno['query_id']
                relevant_docs = anno.get('relevant_docs', [])
                ground_truth[query_id] = relevant_docs
            
            logger.info(f"成功加载 {len(ground_truth)} 个ground truth")
            return ground_truth
    except json.JSONDecodeError:
        logger.error(f"ground truth 文件 {GT_PATH} 格式错误")
        raise ValueError(f"ground truth 文件 {GT_PATH} 格式错误")

def evaluate_strategy(
    strategy_id: str,
    config: Dict[str, str],
    queries: List[Dict[str, str]],
    ground_truth: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    评估单个chunking策略
    
    Args:
        strategy_id: 策略ID（如 'S0'）
        config: 策略配置 {'name': 'Full Document', 'vectorstore': 'chroma_s0'}
        queries: 测试queries
        ground_truth: ground truth
        
    Returns:
        评估结果字典
        
    Raises:
        FileNotFoundError: 当向量库不存在时
        Exception: 其他评估错误
    """
    strategy_name = config['name']
    vectorstore_name = config['vectorstore']
    
    logger.info(f"\n{'='*60}")
    logger.info(f"评估策略: {strategy_id} - {strategy_name}")
    logger.info(f"向量库: {vectorstore_name}")
    logger.info(f"{'='*60}")
    
    try:
        # 1. 初始化ChromaDB client
        vectorstore_path = VECTORSTORE_DIR / vectorstore_name
        if not vectorstore_path.exists():
            raise FileNotFoundError(f"向量库不存在: {vectorstore_path}")
        
        logger.info(f"加载向量库: {vectorstore_path}")
        client = chromadb.PersistentClient(path=str(vectorstore_path))
        
        # 2. 获取collection
        collection = client.get_collection(name="stackoverflow_kb")
        doc_count = collection.count()
        logger.info(f"Collection包含 {doc_count} 个文档")
        
        # 3. 创建Embedder实例
        embedder = Embedder(model_name="BAAI/bge-small-en-v1.5")
        logger.info("Embedder已创建")

        # 4. 创建BaseRetriever
        retriever = BaseRetriever(
            collection=collection,
            embedding_function=embedder,  # ✅ 直接传入embedder
            min_similarity=0.5,
            recall_factor=4
        )
        logger.info("Retriever已初始化")
        
        # 5. 创建ChunkingEvaluator
        evaluator = ChunkingEvaluator(retriever=retriever)
        
        # 6. 调用evaluate()
        logger.info("开始评估...")
        results = evaluator.evaluate(
            queries=queries,
            ground_truth=ground_truth,
            k_values=[1, 3, 5, 10]
        )
        
        # 7. 添加策略信息到结果中
        results['strategy_id'] = strategy_id
        results['strategy_name'] = strategy_name
        results['vectorstore'] = vectorstore_name
        results['doc_count'] = doc_count
        
        # 8. 打印结果摘要
        logger.info(f"\n{'='*60}")
        logger.info(f"策略 {strategy_id} 评估完成！")
        logger.info(f"  Recall@1:  {results['recall'].get(1, 0):.3f}")
        logger.info(f"  Recall@3:  {results['recall'].get(3, 0):.3f}")
        logger.info(f"  Recall@5:  {results['recall'].get(5, 0):.3f}")
        logger.info(f"  Recall@10: {results['recall'].get(10, 0):.3f}")
        logger.info(f"  MRR:       {results['mrr']:.3f}")
        logger.info(f"  平均时间:   {results['avg_retrieval_time']:.3f}s")
        logger.info(f"  失败率:     {results['failure_rate']:.2%}")
        logger.info(f"{'='*60}\n")
        
        return results
        
    except FileNotFoundError as e:
        logger.error(f"向量库文件错误: {e}")
        raise
    except Exception as e:
        logger.error(f"评估策略 {strategy_id} 失败: {e}", exc_info=True)
        raise
def print_comparison_table(all_results: Dict[str, Dict]):
    """打印对比表格"""
    print("\n" + "=" * 100)
    print("📊 Chunking策略对比")
    print("=" * 100)
    
    # 表头
    header = f"{'策略':<8} {'名称':<20} {'R@1':<8} {'R@3':<8} {'R@5':<8} {'R@10':<8} {'MRR':<8} {'速度(ms)':<10} {'失败率':<8}"
    print(header)
    print("-" * 100)
    
    # 每个策略的结果
    for strategy_id in sorted(all_results.keys()):
        results = all_results[strategy_id]
        
        row = (
            f"{strategy_id:<8} "
            f"{results['strategy_name']:<20} "
            f"{results['recall'].get(1, 0):.3f}    "
            f"{results['recall'].get(3, 0):.3f}    "
            f"{results['recall'].get(5, 0):.3f}    "
            f"{results['recall'].get(10, 0):.3f}    "
            f"{results['mrr']:.3f}    "
            f"{results['avg_retrieval_time']*1000:.1f}      "
            f"{results['failure_rate']:.2%}"
        )
        print(row)
    
    print("=" * 100)
    
    # 找出最佳策略
    best_recall5 = max(all_results.items(), key=lambda x: x[1]['recall'].get(5, 0))
    best_mrr = max(all_results.items(), key=lambda x: x[1]['mrr'])
    best_speed = min(all_results.items(), key=lambda x: x[1]['avg_retrieval_time'])
    
    print(f"\n🏆 最佳策略:")
    print(f"  - Recall@5: {best_recall5[0]} ({best_recall5[1]['recall'].get(5, 0):.3f})")
    print(f"  - MRR:      {best_mrr[0]} ({best_mrr[1]['mrr']:.3f})")
    print(f"  - 速度:      {best_speed[0]} ({best_speed[1]['avg_retrieval_time']*1000:.1f}ms)")
    print()


def save_results(all_results: Dict[str, Dict]):
    """保存结果到文件"""
    results_dir = Path(__file__).parent / 'results'
    results_dir.mkdir(exist_ok=True)
    
    # 保存JSON
    json_path = results_dir / 'evaluation_results.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    logger.info(f"结果已保存: {json_path}")
    
    # 保存CSV（方便Excel打开）
    csv_path = results_dir / 'evaluation_results.csv'
    with open(csv_path, 'w', encoding='utf-8') as f:
        # CSV表头
        f.write("Strategy,Name,Recall@1,Recall@3,Recall@5,Recall@10,MRR,AvgTime(ms),FailureRate\n")
        
        # 每行数据
        for strategy_id in sorted(all_results.keys()):
            r = all_results[strategy_id]
            f.write(
                f"{strategy_id},"
                f"{r['strategy_name']},"
                f"{r['recall'].get(1, 0):.3f},"
                f"{r['recall'].get(3, 0):.3f},"
                f"{r['recall'].get(5, 0):.3f},"
                f"{r['recall'].get(10, 0):.3f},"
                f"{r['mrr']:.3f},"
                f"{r['avg_retrieval_time']*1000:.1f},"
                f"{r['failure_rate']:.2%}\n"
            )
    logger.info(f"CSV已保存: {csv_path}")

def main():
    """主函数"""
    try:
        # 1. 加载数据
        logger.info("=" * 80)
        logger.info("开始批量评估Chunking策略")
        logger.info("=" * 80)
        
        queries = load_queries()
        ground_truth = load_ground_truth()
        
        logger.info(f"\n加载完成:")
        logger.info(f"  - Queries: {len(queries)} 个")
        logger.info(f"  - Ground Truth: {len(ground_truth)} 个")
        
        # 2. 评估所有策略
        all_results = {}
        
        for strategy_id, config in STRATEGIES.items():
            try:
                results = evaluate_strategy(
                    strategy_id=strategy_id,
                    config=config,
                    queries=queries,
                    ground_truth=ground_truth
                )
                all_results[strategy_id] = results
            except Exception as e:
                logger.error(f"跳过策略 {strategy_id}: {e}")
                continue
        
        # 3. 生成对比报告
        if all_results:
            print_comparison_table(all_results)
            save_results(all_results)
        else:
            logger.error("没有成功评估的策略！")
            return
        
        logger.info("\n" + "=" * 80)
        logger.info("批量评估完成！")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"主函数执行失败: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()