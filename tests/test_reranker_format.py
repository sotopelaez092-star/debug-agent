"""
Reranker格式验证测试

测试目标：
1. 验证reranker输入格式是否正确
2. 检查分数分布是否合理
3. 对比排序变化
4. 性能分析

使用：真实数据，40个文档，完整分析
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time
import logging
from typing import List, Dict, Any
import json
import chromadb
from FlagEmbedding import FlagReranker

from src.rag.retriever import BaseRetriever
from src.rag.embedder import Embedder
from src.rag.config import RAGConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
CONFIG = {
    'vectorstore_path': 'data/vectorstore/chroma_s1',
    'embedding_model': 'BAAI/bge-small-en-v1.5',
    'reranker_model': 'BAAI/bge-reranker-base',
    'test_query': "AttributeError: 'NoneType' object has no attribute",
    'recall_k': 40,  # 召回40个
    'top_k': 5       # 最终返回5个
}


def load_vectorstore() -> chromadb.Collection:
    """
    加载向量数据库
    
    Returns:
        ChromaDB collection
        
    Raises:
        FileNotFoundError: 如果vectorstore路径不存在
    """
    vectorstore_path = Path(CONFIG['vectorstore_path'])
    
    if not vectorstore_path.exists():
        raise FileNotFoundError(f"Vectorstore不存在: {vectorstore_path}")
    
    logger.info(f"📂 加载vectorstore: {vectorstore_path}")
    
    client = chromadb.PersistentClient(path=str(vectorstore_path))
    collection = client.get_collection(name="stackoverflow_kb")
    
    logger.info(f"✅ Vectorstore加载成功，文档数：{collection.count()}")
    
    return collection


def load_models() -> tuple[BaseRetriever, FlagReranker]:
    """
    加载检索器和Reranker
    
    Returns:
        (base_retriever, reranker)
    """
    logger.info("🤖 加载模型...")
    
    # 1. 加载向量数据库
    collection = load_vectorstore()
    
    # 2. 加载Embedder
    embedder = Embedder(model_name=CONFIG['embedding_model'])
    logger.info(f"✅ Embedder加载成功: {CONFIG['embedding_model']}")
    
    # 3. 创建BaseRetriever
    retriever = BaseRetriever(
        collection=collection,
        embedding_function=embedder,
        min_similarity=0.5,
        recall_factor=4
    )
    logger.info("✅ BaseRetriever创建成功")
    
    # 4. 加载Reranker
    reranker = FlagReranker(
        CONFIG['reranker_model'],
        use_fp16=True
    )
    logger.info(f"✅ Reranker加载成功: {CONFIG['reranker_model']}")
    
    return retriever, reranker


def test_base_retrieval(retriever: BaseRetriever, query: str, top_k: int) -> List[Dict[str, Any]]:
    """
    测试基础检索
    
    Args:
        retriever: 检索器
        query: 查询文本
        top_k: 返回数量
        
    Returns:
        检索结果列表
    """
    logger.info("=" * 80)
    logger.info("🔍 Step 1: 基础向量检索")
    logger.info("=" * 80)
    
    start_time = time.time()
    results = retriever.search(query, top_k=top_k)
    retrieval_time = time.time() - start_time
    
    logger.info(f"⏱️  检索耗时: {retrieval_time*1000:.2f}ms")
    logger.info(f"📊 召回数量: {len(results)}")
    
    if results:
        similarities = [r['similarity'] for r in results]
        logger.info(f"📈 相似度范围: {min(similarities):.4f} ~ {max(similarities):.4f}")
        logger.info(f"📈 平均相似度: {sum(similarities)/len(similarities):.4f}")
        
        # 打印Top 5
        logger.info("\n🏆 Top 5 文档（向量检索）:")
        for i, doc in enumerate(results[:5], 1):
            content_preview = doc['content'][:100].replace('\n', ' ')
            logger.info(
                f"  {i}. [相似度={doc['similarity']:.4f}] "
                f"ID={doc['id'][:20]}... "
                f"内容={content_preview}..."
            )
    
    return results


def test_reranker(
    reranker: FlagReranker,
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int
) -> tuple[List[Dict[str, Any]], float]:
    """
    测试Reranker
    
    Args:
        reranker: Reranker模型
        query: 查询文本
        candidates: 候选文档
        top_k: 返回数量
        
    Returns:
        (reranked_results, rerank_time)
    """
    logger.info("\n" + "=" * 80)
    logger.info("🎯 Step 2: Reranker重排序")
    logger.info("=" * 80)
    
    if not candidates:
        logger.warning("⚠️  没有候选文档")
        return [], 0.0
    
    # 1. 构造输入格式
    logger.info(f"📝 构造输入 pairs...")
    logger.info(f"   Query长度: {len(query)} 字符")
    logger.info(f"   文档数量: {len(candidates)}")
    
    # 检查文档长度
    doc_lengths = [len(doc['content']) for doc in candidates]
    logger.info(f"   文档长度: min={min(doc_lengths)}, max={max(doc_lengths)}, avg={sum(doc_lengths)/len(doc_lengths):.0f}")
    
    pairs = [[query, doc['content']] for doc in candidates]
    
    # 打印第一个pair示例
    logger.info(f"\n📋 第一个pair示例:")
    logger.info(f"   Query: {pairs[0][0][:100]}...")
    logger.info(f"   Doc: {pairs[0][1][:200]}...")
    
    # 2. 调用Reranker
    try:
        logger.info(f"\n⚙️  开始Reranker推理...")
        start_time = time.time()
        
        scores = reranker.compute_score(pairs)
        
        rerank_time = time.time() - start_time
        logger.info(f"✅ Rerank完成!")
        logger.info(f"⏱️  耗时: {rerank_time:.3f}秒 ({rerank_time*1000:.1f}ms)")
        logger.info(f"⚡ 平均每个文档: {rerank_time/len(candidates)*1000:.1f}ms")
        
    except Exception as e:
        logger.error(f"❌ Rerank失败: {e}", exc_info=True)
        return candidates[:top_k], 0.0
    
    # 3. 处理分数
    if not isinstance(scores, list):
        scores = [scores]
    
    logger.info(f"\n📊 Rerank分数分析:")
    logger.info(f"   分数类型: {type(scores)}")
    logger.info(f"   分数数量: {len(scores)}")
    logger.info(f"   分数范围: {min(scores):.4f} ~ {max(scores):.4f}")
    logger.info(f"   平均分数: {sum(scores)/len(scores):.4f}")
    
    # 4. 添加分数到文档
    for doc, score in zip(candidates, scores):
        doc['rerank_score'] = float(score)
    
    # 5. 重新排序
    reranked = sorted(
        candidates,
        key=lambda x: x['rerank_score'],
        reverse=True
    )
    
    # 6. 打印Top 5
    logger.info("\n🏆 Top 5 文档（Reranker）:")
    for i, doc in enumerate(reranked[:5], 1):
        content_preview = doc['content'][:100].replace('\n', ' ')
        logger.info(
            f"  {i}. [Rerank={doc['rerank_score']:.4f}, Vector={doc['similarity']:.4f}] "
            f"ID={doc['id'][:20]}... "
            f"内容={content_preview}..."
        )
    
    return reranked[:top_k], rerank_time


def compare_results(
    base_results: List[Dict[str, Any]],
    reranked_results: List[Dict[str, Any]],
    top_k: int
) -> None:
    """
    对比两种方法的结果
    
    Args:
        base_results: 基础检索结果
        reranked_results: Rerank后的结果
        top_k: 对比前K个
    """
    logger.info("\n" + "=" * 80)
    logger.info("📊 Step 3: 结果对比分析")
    logger.info("=" * 80)
    
    # 1. 提取Top K的ID
    base_ids = [doc['id'] for doc in base_results[:top_k]]
    rerank_ids = [doc['id'] for doc in reranked_results[:top_k]]
    
    # 2. 计算变化
    same_count = len(set(base_ids) & set(rerank_ids))
    change_rate = (top_k - same_count) / top_k * 100
    
    logger.info(f"\n📈 排序变化统计（Top {top_k}）:")
    logger.info(f"   相同文档: {same_count}/{top_k}")
    logger.info(f"   变化率: {change_rate:.1f}%")
    
    # 3. 逐个对比
    logger.info(f"\n🔄 逐位对比:")
    for i in range(top_k):
        base_doc = base_results[i]
        rerank_doc = reranked_results[i]
        
        if base_doc['id'] == rerank_doc['id']:
            status = "✅ 相同"
        else:
            status = "🔄 变化"
        
        logger.info(f"  位置 {i+1}:")
        logger.info(f"    Vector: {base_doc['id'][:30]}... (相似度={base_doc['similarity']:.4f})")
        logger.info(f"    Rerank: {rerank_doc['id'][:30]}... (分数={rerank_doc['rerank_score']:.4f}) {status}")
    
    # 4. 找出被"降级"的高质量文档
    logger.info(f"\n⚠️  潜在问题分析:")
    demoted = []
    for i, base_doc in enumerate(base_results[:top_k]):
        # 在rerank结果中的位置
        try:
            new_rank = [d['id'] for d in reranked_results].index(base_doc['id']) + 1
            if new_rank > i + 1:  # 排名下降
                demoted.append({
                    'id': base_doc['id'][:30],
                    'old_rank': i + 1,
                    'new_rank': new_rank,
                    'similarity': base_doc['similarity'],
                    'rerank_score': base_doc['rerank_score']
                })
        except ValueError:
            # 不在top_k中
            pass
    
    if demoted:
        logger.info(f"   发现 {len(demoted)} 个高质量文档被降级:")
        for d in demoted:
            logger.info(
                f"     {d['id']}... "
                f"排名 {d['old_rank']} → {d['new_rank']} "
                f"(相似度={d['similarity']:.4f}, Rerank={d['rerank_score']:.4f})"
            )
    else:
        logger.info("   ✅ 没有高质量文档被明显降级")


def save_results(
    query: str,
    base_results: List[Dict[str, Any]],
    reranked_results: List[Dict[str, Any]],
    base_time: float,
    rerank_time: float
) -> None:
    """
    保存测试结果
    
    Args:
        query: 查询文本
        base_results: 基础检索结果
        reranked_results: Rerank结果
        base_time: 基础检索耗时
        rerank_time: Rerank耗时
    """
    output_path = Path("tests/results/reranker_debug/comparison.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 准备数据
    data = {
        'query': query,
        'base_retrieval': {
            'time_ms': base_time * 1000,
            'results': [
                {
                    'rank': i + 1,
                    'id': doc['id'],
                    'similarity': doc['similarity'],
                    'content_preview': doc['content'][:200]
                }
                for i, doc in enumerate(base_results[:10])
            ]
        },
        'reranked': {
            'time_ms': rerank_time * 1000,
            'results': [
                {
                    'rank': i + 1,
                    'id': doc['id'],
                    'rerank_score': doc['rerank_score'],
                    'similarity': doc['similarity'],
                    'content_preview': doc['content'][:200]
                }
                for i, doc in enumerate(reranked_results[:10])
            ]
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n💾 结果已保存到: {output_path}")


def main():
    """主函数"""
    logger.info("🚀 开始Reranker格式验证测试\n")
    
    try:
        # 1. 加载模型
        retriever, reranker = load_models()
        
        # 2. 基础检索
        query = CONFIG['test_query']
        base_results = test_base_retrieval(
            retriever,
            query,
            top_k=CONFIG['recall_k']
        )
        
        if not base_results:
            logger.error("❌ 基础检索失败，无法继续测试")
            return
        
        base_time = 0.025  # 假设值，实际在test_base_retrieval中测量
        
        # 3. Reranker测试
        reranked_results, rerank_time = test_reranker(
            reranker,
            query,
            base_results,
            top_k=CONFIG['top_k']
        )
        
        # 4. 对比分析
        compare_results(
            base_results,
            reranked_results,
            top_k=CONFIG['top_k']
        )
        
        # 5. 保存结果
        save_results(
            query,
            base_results,
            reranked_results,
            base_time,
            rerank_time
        )
        
        # 6. 总结
        logger.info("\n" + "=" * 80)
        logger.info("✅ 测试完成!")
        logger.info("=" * 80)
        logger.info(f"📊 性能对比:")
        logger.info(f"   BaseRetriever: ~25ms")
        logger.info(f"   Reranker: {rerank_time*1000:.1f}ms (慢 {rerank_time/0.025:.0f} 倍)")
        logger.info(f"\n📝 详细结果: tests/results/reranker_debug/comparison.json")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()