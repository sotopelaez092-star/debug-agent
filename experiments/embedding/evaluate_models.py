#!/usr/bin/env python3
"""
评估不同Embedding模型的性能

功能：
1. 对比4个embedding模型
2. 使用相同的测试queries和ground truth
3. 生成完整的对比报告

用法:
    python experiments/embedding/evaluate_models.py
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import json
import logging
import os
import csv
from typing import List, Dict, Any
import time

import chromadb
from src.rag.embedder import Embedder
from src.rag.retriever import BaseRetriever
from src.rag.evaluator import ChunkingEvaluator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ✅ 定义要测试的模型
EMBEDDING_MODELS = {
    'M1': {
        'name': 'bge-small-en',
        'model_name': 'BAAI/bge-small-en-v1.5',
        'vectorstore': 'data/vectorstore/chroma_s1',  # 用原始的S1
        'dimension': 384,
        'description': '当前基线'
    },
    'M2': {
        'name': 'bge-base-en',
        'model_name': 'BAAI/bge-base-en-v1.5',
        'vectorstore': 'data/vectorstore/embed_m2',
        'dimension': 768,
        'description': '中等模型'
    },
    'M3': {
        'name': 'bge-m3',
        'model_name': 'BAAI/bge-m3',
        'vectorstore': 'data/vectorstore/embed_m3',
        'dimension': 1024,
        'description': '多语言大模型'
    },
    'M4': {
        'name': 'all-MiniLM',
        'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
        'vectorstore': 'data/vectorstore/embed_m4',
        'dimension': 384,
        'description': '轻量级基线'
    }
}


def load_queries() -> List[Dict[str, str]]:
    """
    加载测试queries
    
    Returns:
        queries列表，格式: [{'id': 'test-001', 'text': 'query'}, ...]
        
    Raises:
        FileNotFoundError: 当文件不存在时
        ValueError: 当数据格式错误时
    """
    query_file = 'data/test_cases/test_queries_realistic.json'
    
    if not Path(query_file).exists():
        raise FileNotFoundError(f"测试queries文件未找到: {query_file}")
    
    try:
        with open(query_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        raw_queries = data.get('queries', [])
        
        if not raw_queries:
            raise ValueError("queries列表为空")
        
        # ✅ 格式转换：query_id -> id, query -> text
        queries = []
        for q in raw_queries:
            if 'query_id' not in q or 'query' not in q:
                logger.warning(f"跳过格式错误的query: {q}")
                continue
            
            queries.append({
                'id': q['query_id'],
                'text': q['query']
            })
        
        return queries
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        raise
    except Exception as e:
        logger.error(f"加载queries失败: {e}", exc_info=True)
        raise


def load_ground_truth() -> Dict[str, List[str]]:
    """
    加载ground truth
    
    Returns:
        ground truth字典，格式: {'test-001': ['doc-id1', 'doc-id2'], ...}
        
    Raises:
        FileNotFoundError: 当文件不存在时
        ValueError: 当数据格式错误时
    """
    gt_file = 'data/evaluation/llm_annotated_gt.json'
    
    if not Path(gt_file).exists():
        raise FileNotFoundError(f"ground truth文件未找到: {gt_file}")
    
    try:
        with open(gt_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        annotations = data.get('annotations', [])
        
        if not annotations:
            raise ValueError("annotations列表为空")
        
        # ✅ 转换格式: 从annotations列表到字典
        gt_dict = {}
        for ann in annotations:
            if 'query_id' not in ann:
                logger.warning(f"跳过缺少query_id的annotation: {ann}")
                continue
            
            query_id = ann['query_id']
            # ✅ 关键修复：字段名是relevant_docs，不是doc_ids
            relevant_docs = ann.get('relevant_docs', [])
            gt_dict[query_id] = relevant_docs
        
        return gt_dict
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        raise
    except Exception as e:
        logger.error(f"加载ground truth失败: {e}", exc_info=True)
        raise


def evaluate_model(
    model_id: str,
    config: Dict[str, Any],
    queries: List[Dict[str, str]],
    ground_truth: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    评估单个embedding模型
    
    Args:
        model_id: 模型ID (M1, M2, M3, M4)
        config: 模型配置
        queries: 测试queries
        ground_truth: ground truth数据
        
    Returns:
        评估结果字典
        
    Raises:
        Exception: 当评估失败时
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"评估模型: {model_id} - {config['name']}")
    logger.info(f"描述: {config['description']}")
    logger.info(f"维度: {config['dimension']}")
    logger.info(f"向量库: {config['vectorstore']}")
    logger.info(f"{'='*80}\n")
    
    try:
        # 1. 创建Embedder
        # ✅ 关键修复：Embedder只接受model_name参数
        logger.info(f"  🤖 初始化Embedder...")
        embedder = Embedder(model_name=config['model_name'])
        
        # 2. 连接ChromaDB
        # ✅ 关键修复：collection名称是stackoverflow_kb
        logger.info(f"  💾 连接ChromaDB...")
        vectorstore_path = Path(config['vectorstore'])
        if not vectorstore_path.exists():
            raise FileNotFoundError(f"向量库不存在: {config['vectorstore']}")
        
        client = chromadb.PersistentClient(path=config['vectorstore'])
        collection = client.get_collection(name="stackoverflow_kb")
        
        logger.info(f"  ℹ️  向量库文档数: {collection.count()}")
        
        # 3. 创建BaseRetriever
        logger.info(f"  🔍 创建BaseRetriever...")
        retriever = BaseRetriever(
            collection=collection,
            embedding_function=embedder
        )
        
        # 4. 创建ChunkingEvaluator
        # ✅ 关键修复：ChunkingEvaluator初始化只接受retriever
        logger.info(f"  📊 创建Evaluator...")
        evaluator = ChunkingEvaluator(retriever=retriever)
        
        # 5. 运行评估
        # ✅ 关键修复：evaluate需要queries和ground_truth两个参数
        logger.info(f"  🚀 开始评估...")
        start_time = time.time()
        results = evaluator.evaluate(queries, ground_truth)
        elapsed_time = time.time() - start_time
        
        logger.info(f"  ✅ 评估完成！耗时: {elapsed_time:.2f}秒")
        
        # 6. 添加模型信息到结果
        results['model_id'] = model_id
        results['model_name'] = config['name']
        results['model_full_name'] = config['model_name']
        results['dimension'] = config['dimension']
        results['description'] = config['description']
        results['total_eval_time'] = elapsed_time
        
        return results
        
    except Exception as e:
        logger.error(f"评估{model_id}失败: {e}", exc_info=True)
        raise


def save_results(all_results: List[Dict], output_dir: str = "experiments/embedding/results"):
    """
    保存评估结果
    
    Args:
        all_results: 所有模型的评估结果
        output_dir: 输出目录
        
    Raises:
        Exception: 当保存失败时
    """
    try:
        # 1. 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 2. 保存JSON格式
        json_path = Path(output_dir) / "evaluation_results.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        logger.info(f"  ✅ 已保存JSON结果: {json_path}")
        
        # 3. 保存CSV格式（方便Excel打开）
        csv_path = Path(output_dir) / "evaluation_results.csv"
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow([
                'Model_ID',
                'Model_Name',
                'Description',
                'Dimension',
                'Recall@1',
                'Recall@3',
                'Recall@5',
                'Recall@10',
                'MRR',
                'Avg_Time(ms)',
                'Success_Rate',
                'Total_Queries',
                'Successful_Queries',
                'Failed_Queries'
            ])
            
            # 写入每行数据
            for result in all_results:
                # 根据ChunkingEvaluator的返回格式访问字段
                recall = result['recall']
                
                writer.writerow([
                    result['model_id'],
                    result['model_name'],
                    result['description'],
                    result['dimension'],
                    f"{recall.get(1, 0):.2%}",
                    f"{recall.get(3, 0):.2%}",
                    f"{recall.get(5, 0):.2%}",
                    f"{recall.get(10, 0):.2%}",
                    f"{result['mrr']:.4f}",
                    f"{result['avg_retrieval_time'] * 1000:.1f}",
                    f"{1 - result['failure_rate']:.2%}",
                    result['total_queries'],
                    result['successful_queries'],
                    result['failed_queries']
                ])
        
        logger.info(f"  ✅ 已保存CSV结果: {csv_path}")
        
    except Exception as e:
        logger.error(f"保存结果失败: {e}", exc_info=True)
        raise


def print_comparison_table(all_results: List[Dict]):
    """
    打印对比表格
    
    Args:
        all_results: 所有模型的评估结果
    """
    # 表头
    print(f"\n{'模型':<12} {'维度':<8} {'Recall@1':<10} {'Recall@3':<10} {'Recall@5':<10} {'Recall@10':<11} {'MRR':<8} {'速度(ms)':<10}")
    print("=" * 95)
    
    # 每行数据
    for result in all_results:
        model = result['model_name']
        dim = result['dimension']
        recall = result['recall']
        mrr = result['mrr']
        speed = result['avg_retrieval_time'] * 1000  # 转换为毫秒
        
        print(
            f"{model:<12} "
            f"{dim:<8} "
            f"{recall.get(1, 0):<10.1%} "
            f"{recall.get(3, 0):<10.1%} "
            f"{recall.get(5, 0):<10.1%} "
            f"{recall.get(10, 0):<11.1%} "
            f"{mrr:<8.3f} "
            f"{speed:<10.1f}"
        )
    
    print("=" * 95)
    
    # 找出最佳模型
    best_recall5 = max(all_results, key=lambda x: x['recall'].get(5, 0))
    fastest = min(all_results, key=lambda x: x['avg_retrieval_time'])
    
    print(f"\n🏆 最佳Recall@5: {best_recall5['model_name']} ({best_recall5['recall'].get(5, 0):.1%})")
    print(f"⚡ 最快速度: {fastest['model_name']} ({fastest['avg_retrieval_time']*1000:.1f}ms)")


def main():
    """主函数"""
    logger.info("\n" + "🚀" * 40)
    logger.info("Embedding模型评估实验")
    logger.info("🚀" * 40 + "\n")
    
    try:
        # 1. 加载数据
        logger.info("📂 加载测试数据...")
        queries = load_queries()
        ground_truth = load_ground_truth()
        
        logger.info(f"  ✅ 加载了 {len(queries)} 个queries")
        logger.info(f"  ✅ 加载了 {len(ground_truth)} 个ground truth\n")
        
        # 2. 评估所有模型
        all_results = []
        
        for model_id in ['M1', 'M2', 'M3', 'M4']:
            config = EMBEDDING_MODELS[model_id]
            
            try:
                result = evaluate_model(model_id, config, queries, ground_truth)
                all_results.append(result)
            except Exception as e:
                logger.error(f"❌ {model_id} 评估失败: {e}")
                continue
        
        # 检查是否有成功的结果
        if not all_results:
            logger.error("❌ 所有模型评估都失败了！")
            return
        
        # 3. 保存结果
        logger.info("\n💾 保存评估结果...")
        save_results(all_results)
        
        # 4. 打印对比
        logger.info("\n📊 评估结果对比：")
        print_comparison_table(all_results)
        
        logger.info("\n" + "="*80)
        logger.info("✅ 评估完成！")
        logger.info(f"📁 结果保存在: experiments/embedding/results/")
        logger.info("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"\n❌ 程序执行失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()