# experiments/retriever/evaluate_all.py
"""批量评估Retriever策略"""
import sys
from pathlib import Path

# 添加src到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

import json
import logging
from typing import Dict, List, Any
import chromadb

from src.rag.evaluator import ChunkingEvaluator  # 复用现有的评估器
from src.rag.retriever import BaseRetriever
from src.rag.reranker_retriever import RerankerRetriever
from src.rag.hyde_retriever import HyDERetriever
from src.rag.embedder import Embedder


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 定义要对比的Retrievers
RETRIEVERS = {
    'R1': {
        'name': 'BaseRetriever',
        'type': 'base',
        'description': '纯向量检索'
    },
    'R2': {
        'name': 'RerankerRetriever', 
        'type': 'reranker',
        'reranker_model': 'BAAI/bge-reranker-base',
        'description': '向量检索 + Reranker重排序'
    },
    'R3': {
        'name': 'HyDERetriever',
        'type': 'hyde',
        'description': 'LLM生成假设文档 + 向量检索'
    }
}

# 数据路径
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
QUERIES_PATH = DATA_DIR / 'test_cases' / 'test_queries_realistic.json'
GT_PATH = DATA_DIR / 'evaluation' / 'llm_annotated_gt.json'

# ✅ 关键：使用同一个vectorstore（S1-Semantic）
VECTORSTORE_PATH = DATA_DIR / 'vectorstore' / 'chroma_s1'

# Embedding模型（必须和构建向量库时一致）
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

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
                    'id': q['query_id'],
                    'text': q['query']
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

def evaluate_retriever(
    retriever_id: str,
    config: Dict[str, str],
    queries: List[Dict[str, str]],
    ground_truth: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    评估单个retriever
    
    Args:
        retriever_id: Retriever ID（如 'R1'）
        config: Retriever配置
        queries: 测试queries
        ground_truth: ground truth
        
    Returns:
        评估结果字典
    """
    retriever_name = config['name']
    retriever_type = config['type']
    
    logger.info(f"\n{'='*60}")
    logger.info(f"评估Retriever: {retriever_id} - {retriever_name}")
    logger.info(f"类型: {retriever_type}")
    logger.info(f"{'='*60}")
    
    try:
        # 1. 加载向量库（所有retriever用同一个）
        if not VECTORSTORE_PATH.exists():
            raise FileNotFoundError(f"向量库不存在: {VECTORSTORE_PATH}")
        
        logger.info(f"加载向量库: {VECTORSTORE_PATH}")
        client = chromadb.PersistentClient(path=str(VECTORSTORE_PATH))
        collection = client.get_collection(name="stackoverflow_kb")
        doc_count = collection.count()
        logger.info(f"Collection包含 {doc_count} 个文档")
        
        # 2. 创建Embedder（所有retriever用同一个）
        embedder = Embedder(model_name=EMBEDDING_MODEL)
        logger.info("Embedder已创建")
        
        # 3. 🔑 关键：根据type初始化不同的retriever
        if retriever_type == 'base':
            retriever = BaseRetriever(
                collection=collection,
                embedding_function=embedder,  # ✅ 修正参数名
                min_similarity=0.5,
                recall_factor=4
            )
            logger.info("BaseRetriever已初始化")
            
        elif retriever_type == 'reranker':
            retriever = RerankerRetriever(
                collection=collection,
                embedding_function=embedder,  # ✅ 修正参数名
                reranker_model_name=config['reranker_model'],  # ✅ 修正参数名
                min_similarity=0.5,
                recall_factor=4
            )
            logger.info("RerankerRetriever已初始化")
        
        elif retriever_type == 'hyde':  # ✅ 添加这个分支
            # HyDE需要先创建BaseRetriever
            base_retriever = BaseRetriever(
                collection=collection,
                embedding_function=embedder,
                min_similarity=0.5,
                recall_factor=4
            )
            # 然后创建HyDERetriever
            retriever = HyDERetriever(
                base_retriever=base_retriever,
                llm=None,  # 使用默认LLM（DeepSeek）
                enable_cache=False  # 不启用缓存（确保每次都重新生成）
            )
            logger.info("HyDERetriever已初始化")
            
        else:
            raise ValueError(f"未知的retriever类型: {retriever_type}")
        
        # 4. 创建评估器
        evaluator = ChunkingEvaluator(retriever=retriever)
        logger.info("评估器已创建")
        
        # 5. 执行评估
        logger.info("开始评估...")
        results = evaluator.evaluate(
            queries=queries,
            ground_truth=ground_truth,
            k_values=[1, 3, 5, 10]
        )
        
        # 6. 添加retriever信息到结果
        results['retriever_id'] = retriever_id
        results['retriever_name'] = retriever_name
        results['retriever_type'] = retriever_type
        results['description'] = config['description']
        results['doc_count'] = doc_count
        
        # 7. 打印结果摘要
        logger.info(f"\n{'='*60}")
        logger.info(f"Retriever {retriever_id} 评估完成！")
        logger.info(f"  Recall@1:  {results['recall'].get(1, 0):.3f}")
        logger.info(f"  Recall@3:  {results['recall'].get(3, 0):.3f}")
        logger.info(f"  Recall@5:  {results['recall'].get(5, 0):.3f}")
        logger.info(f"  Recall@10: {results['recall'].get(10, 0):.3f}")
        logger.info(f"  MRR:       {results['mrr']:.3f}")
        logger.info(f"  平均时间:   {results['avg_retrieval_time']:.3f}s")
        logger.info(f"  失败率:     {results['failure_rate']:.2%}")
        logger.info(f"{'='*60}\n")
        
        return results
        
    except Exception as e:
        logger.error(f"评估Retriever {retriever_id} 失败: {e}", exc_info=True)
        raise


def print_comparison_table(all_results: Dict[str, Dict]):
    """打印对比表格"""
    print("\n" + "=" * 100)
    print("📊 Retriever策略对比")
    print("=" * 100)
    
    # 表头
    header = f"{'ID':<6} {'名称':<20} {'描述':<25} {'R@1':<8} {'R@3':<8} {'R@5':<8} {'R@10':<8} {'MRR':<8} {'速度(ms)':<10}"
    print(header)
    print("-" * 100)
    
    # 每个retriever的结果
    for retriever_id in sorted(all_results.keys()):
        results = all_results[retriever_id]
        
        row = (
            f"{retriever_id:<6} "
            f"{results['retriever_name']:<20} "
            f"{results['description']:<25} "
            f"{results['recall'].get(1, 0):.3f}    "
            f"{results['recall'].get(3, 0):.3f}    "
            f"{results['recall'].get(5, 0):.3f}    "
            f"{results['recall'].get(10, 0):.3f}    "
            f"{results['mrr']:.3f}    "
            f"{results['avg_retrieval_time']*1000:.1f}"
        )
        print(row)
    
    print("=" * 100)
    
    # 找出最佳retriever
    best_recall5 = max(all_results.items(), key=lambda x: x[1]['recall'].get(5, 0))
    best_mrr = max(all_results.items(), key=lambda x: x[1]['mrr'])
    best_speed = min(all_results.items(), key=lambda x: x[1]['avg_retrieval_time'])
    
    print(f"\n🏆 最佳Retriever:")
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
    
    # 保存CSV
    csv_path = results_dir / 'evaluation_results.csv'
    with open(csv_path, 'w', encoding='utf-8') as f:
        # CSV表头
        f.write("Retriever,Name,Description,Recall@1,Recall@3,Recall@5,Recall@10,MRR,AvgTime(ms),FailureRate\n")
        
        # 每行数据
        for retriever_id in sorted(all_results.keys()):
            r = all_results[retriever_id]
            f.write(
                f"{retriever_id},"
                f"{r['retriever_name']},"
                f"{r['description']},"
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
        logger.info("开始批量评估Retriever策略")
        logger.info("=" * 80)
        
        queries = load_queries()
        ground_truth = load_ground_truth()
        
        logger.info(f"\n加载完成:")
        logger.info(f"  - Queries: {len(queries)} 个")
        logger.info(f"  - Ground Truth: {len(ground_truth)} 个")
        logger.info(f"  - Vectorstore: {VECTORSTORE_PATH}")
        logger.info(f"  - Embedding Model: {EMBEDDING_MODEL}")
        
        # 2. 评估所有retriever
        all_results = {}
        
        for retriever_id, config in RETRIEVERS.items():
            try:
                results = evaluate_retriever(
                    retriever_id=retriever_id,
                    config=config,
                    queries=queries,
                    ground_truth=ground_truth
                )
                all_results[retriever_id] = results
            except Exception as e:
                logger.error(f"跳过Retriever {retriever_id}: {e}")
                continue
        
        # 3. 生成对比报告
        if all_results:
            print_comparison_table(all_results)
            save_results(all_results)
        else:
            logger.error("没有成功评估的Retriever！")
            return
        
        logger.info("\n" + "=" * 80)
        logger.info("批量评估完成！")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"主函数执行失败: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()