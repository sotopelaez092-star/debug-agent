"""
失败案例分析脚本

分析Recall@5失败的查询案例，找出优化方向
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
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
    # 输入验证
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Query file not found: {file_path}")

    # 读取json文件
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误：{e}")
        raise ValueError(f"Invalid query file format: {file_path}")

    # 提取queries数据
    raw_queries = data.get('queries', [])
    if not raw_queries:
        raise ValueError(f"Empty queries array in file: {file_path}")

    # 转换格式（适配实际文件格式）
    queries = []
    for item in raw_queries:
        # ✅ 修改：适配实际的字段名
        if 'query_id' not in item or 'query' not in item:
            logger.warning(f"Invalid query item format: {item}")
            continue
        
        queries.append({
            'id': item['query_id'],      # ✅ query_id → id
            'text': item['query']        # ✅ query → text
        })

    if not queries:
        raise ValueError(f"All query items are invalid in file: {file_path}")

    logger.info(f"Loaded {len(queries)} valid queries from {file_path}")

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


def initialize_retriever(
    vectorstore_path: str,
    model_name: str = "BAAI/bge-small-en-v1.5"
) -> Tuple[BaseRetriever, QueryRewriter]:
    """
    初始化检索器和改写器
    
    Args:
        vectorstore_path: 向量库路径
        model_name: Embedding模型名称
        
    Returns:
        (retriever, rewriter)
        
    Raises:
        RuntimeError: 初始化失败
    """
    try:
        logger.info(f"Initializing retriever with vectorstore: {vectorstore_path}")
        logger.info(f"Using embedding model: {model_name}")
        
        # 1. 创建Embedder
        embedder = Embedder(model_name)
        logger.info("Embedder created")
        
        # 2. 连接ChromaDB
        client = chromadb.PersistentClient(path=str(vectorstore_path))
        collection = client.get_collection(name="stackoverflow_kb")
        logger.info(f"Connected to ChromaDB collection: stackoverflow_kb")
        
        # 3. 创建BaseRetriever
        retriever = BaseRetriever(
            collection=collection,
            embedding_function=embedder,
            min_similarity=0.5,
            recall_factor=4
        )
        logger.info("BaseRetriever initialized with min_similarity=0.5, recall_factor=4")
        
        # 4. 创建QueryRewriter（不需要参数）
        rewriter = QueryRewriter()
        logger.info("QueryRewriter initialized")
        
        # 5. 返回两者
        return retriever, rewriter
        
    except Exception as e:
        logger.error(f"初始化失败: {e}", exc_info=True)
        raise RuntimeError(f"初始化检索器失败: {e}")

def retrieve_and_check(
    query: Dict[str, Any],
    ground_truth: List[str],
    retriever: BaseRetriever,
    rewriter: QueryRewriter,
    top_k: int = 20
) -> Dict[str, Any]:
    """
    检索并检查Recall@5
    
    Args:
        query: 查询字典，包含 'id' 和 'text'
        ground_truth: 正确文档ID列表
        retriever: 检索器
        rewriter: 改写器
        top_k: 返回Top-K结果（用于分析遗漏文档）
        
    Returns:
        {
            'query_id': str,
            'original_query': str,
            'rewritten_query': str,
            'ground_truth': List[str],
            'ground_truth_count': int,
            'top5_results': List[Dict],
            'top20_results': List[Dict],
            'recall_at_5': float,
            'hits_count': int,
            'hit_docs': List[Dict],
            'missed_docs': List[Dict]
        }
    """
    # 1. 提取原始查询
    query_id = query['id']
    original_query = query['text']
    
    logger.info(f"Processing query {query_id}: {original_query[:50]}...")

    # 2. 用QueryRewriter改写
    rewritten_query = rewriter.rewrite(original_query)
    logger.debug(f"Rewritten query: {rewritten_query[:100]}...")
    
    # 3. 用BaseRetriever检索Top-K
    top_k_results = retriever.search(rewritten_query, top_k=top_k)
    logger.debug(f"Retrieved {len(top_k_results)} results")
    
    # 4. 提取base doc_id（去掉_chunk后缀）
    def extract_base_doc_id(doc_id: str) -> str:
        """提取基础文档ID，去掉_chunk_X后缀"""
        if '_chunk_' in doc_id:
            return doc_id.split('_chunk_')[0]
        return doc_id
    
    retrieved_base_ids = [extract_base_doc_id(result['id']) for result in top_k_results]
    
    # 5. 找出Top5中命中的文档
    hit_docs = []
    for i in range(min(5, len(top_k_results))):
        base_id = retrieved_base_ids[i]
        if base_id in ground_truth:
            hit_docs.append({
                'doc_id': base_id,
                'rank': i + 1,
                'similarity': top_k_results[i]['similarity'],
                'content_preview': top_k_results[i]['content'][:100]
            })
    
    # 6. 计算Recall@5
    hits_count = len(hit_docs)
    recall_at_5 = hits_count / len(ground_truth) if ground_truth else 0.0
    
    logger.info(f"Recall@5: {recall_at_5:.2%} ({hits_count}/{len(ground_truth)})")
    
    # 7. 找出遗漏的文档
    hit_doc_ids = {doc['doc_id'] for doc in hit_docs}
    missed_gt_docs = set(ground_truth) - hit_doc_ids
    
    # 8. 查找遗漏文档在Top-K中的排名
    missed_docs = []
    for doc_id in missed_gt_docs:
        # 在Top-K中查找
        found = False
        for i, base_id in enumerate(retrieved_base_ids):
            if base_id == doc_id:
                missed_docs.append({
                    'doc_id': doc_id,
                    'rank': i + 1,
                    'similarity': top_k_results[i]['similarity'],
                    'status': 'in_top20'
                })
                found = True
                break
        
        if not found:
            # 不在Top-K中
            missed_docs.append({
                'doc_id': doc_id,
                'rank': None,
                'similarity': None,
                'status': 'not_in_top20'
            })
    
    # 9. 按排名排序遗漏文档（未检索到的放最后）
    missed_docs.sort(key=lambda x: x['rank'] if x['rank'] is not None else 999)
    
    # 10. 返回完整信息
    return {
        'query_id': query_id,
        'original_query': original_query,
        'rewritten_query': rewritten_query,
        'ground_truth': ground_truth,
        'ground_truth_count': len(ground_truth),
        
        'top5_results': top_k_results[:5],
        'top20_results': top_k_results,
        
        'recall_at_5': recall_at_5,
        'hits_count': hits_count,
        'hit_docs': hit_docs,
        'missed_docs': missed_docs
    }


def analyze_failure_pattern(failure_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析失败案例的模式
    
    Args:
        failure_cases: 失败案例列表
        
    Returns:
        分析结果，包含：
        - 总失败数
        - 失败查询长度分布
        - 改写后长度分布
        - Top1相似度分布
        - 可能的失败原因分类
    """
    if not failure_cases:
        return {
            'total_failures': 0,
            'query_lengths': [],
            'rewritten_lengths': [],
            'top1_similarities': [],
            'low_sim_cases': [],
            'high_sim_cases': []
        }
    
    # 1. 统计失败案例特征
    total_failures = len(failure_cases)

    # 2. 分析查询长度
    query_lengths = [len(case['original_query']) for case in failure_cases]
    rewritten_lengths = [len(case['rewritten_query']) for case in failure_cases]

    # 3. 分析相似度分布
    top1_similarities = [
        case['results'][0]['similarity'] 
        for case in failure_cases 
        if case['results']
    ]

    # 4. 尝试分类失败原因
    # 根据Top1相似度分类
    low_sim_cases = [
        case for case in failure_cases 
        if case['results'] and case['results'][0]['similarity'] < 0.5
    ]
    high_sim_cases = [
        case for case in failure_cases 
        if case['results'] and case['results'][0]['similarity'] >= 0.5
    ]

    return {
        'total_failures': total_failures,
        'query_lengths': {
            'min': min(query_lengths) if query_lengths else 0,
            'max': max(query_lengths) if query_lengths else 0,
            'avg': sum(query_lengths) / len(query_lengths) if query_lengths else 0
        },
        'rewritten_lengths': {
            'min': min(rewritten_lengths) if rewritten_lengths else 0,
            'max': max(rewritten_lengths) if rewritten_lengths else 0,
            'avg': sum(rewritten_lengths) / len(rewritten_lengths) if rewritten_lengths else 0
        },
        'top1_similarities': {
            'min': min(top1_similarities) if top1_similarities else 0,
            'max': max(top1_similarities) if top1_similarities else 0,
            'avg': sum(top1_similarities) / len(top1_similarities) if top1_similarities else 0
        },
        'low_sim_count': len(low_sim_cases),
        'high_sim_count': len(high_sim_cases)
    }


def print_failure_case(case: Dict[str, Any], index: int):
    """
    打印单个失败案例
    
    Args:
        case: 失败案例字典
        index: 案例编号
    """
    print(f"\n{'='*60}")
    print(f"失败案例 #{index}")
    print(f"{'='*60}")
    print(f"Query ID: {case['query_id']}")
    print(f"原始查询: {case['original_query']}")
    print(f"改写后: {case['rewritten_query']}")
    print(f"\nGround Truth: {case['ground_truth']}")
    print(f"\nTop5检索结果:")
    
    for i, result in enumerate(case['results'][:5], 1):
        print(f"\n  [{i}] Doc ID: {result['id']}")
        print(f"      相似度: {result['similarity']:.4f}")
        # 内容预览（最多100字符）
        content_preview = result.get('content', '')[:100]
        if len(result.get('content', '')) > 100:
            content_preview += "..."
        print(f"      内容: {content_preview}")

def main():
    """主函数"""
    # 配置路径
    TEST_QUERIES_PATH = "data/test_cases/test_queries_realistic.json"
    GROUND_TRUTH_PATH = "data/evaluation/llm_annotated_gt.json"
    VECTORSTORE_PATH = "data/vectorstore/chroma_s1"
    
    logger.info("="*60)
    logger.info("开始失败案例分析")
    logger.info("="*60)
    
    try:
        # 1. 加载数据
        logger.info("Step 1: 加载测试数据...")
        test_queries = load_queries(TEST_QUERIES_PATH)
        ground_truth = load_ground_truth(GROUND_TRUTH_PATH)
        
        # 2. 初始化检索器
        logger.info("Step 2: 初始化检索系统...")
        retriever, rewriter = initialize_retriever(VECTORSTORE_PATH)
        
        # 3. 对每个查询进行检索和检查
        logger.info("Step 3: 开始检索和检查...")
        logger.info(f"Total queries to process: {len(test_queries)}")
        
        # 分类容器
        perfect_cases = []      # Recall = 1.0
        good_cases = []         # 0.8 ≤ Recall < 1.0
        moderate_cases = []     # 0.5 ≤ Recall < 0.8
        poor_cases = []         # Recall < 0.5
        skipped = 0
        
        # 处理每个查询
        for idx, query in enumerate(test_queries, 1):
            query_id = query['id']
            
            logger.info(f"\n[{idx}/{len(test_queries)}] Processing {query_id}...")
            
            # 检查是否有ground truth
            if query_id not in ground_truth:
                logger.warning(f"Query {query_id} 没有ground truth，跳过")
                skipped += 1
                continue
            
            gt_docs = ground_truth[query_id]
            
            # 检索和检查
            result = retrieve_and_check(
                query=query,
                ground_truth=gt_docs,
                retriever=retriever,
                rewriter=rewriter,
                top_k=20  # 检索Top20用于分析
            )
            
            recall = result['recall_at_5']
            
            # 分类
            if recall == 1.0:
                perfect_cases.append(result)
                logger.info(f"✅ {query_id}: 完美 (Recall@5={recall:.2%})")
            elif recall >= 0.8:
                good_cases.append(result)
                logger.info(f"✅ {query_id}: 良好 (Recall@5={recall:.2%})")
            elif recall >= 0.5:
                moderate_cases.append(result)
                logger.warning(f"⚠️  {query_id}: 中等 (Recall@5={recall:.2%})")
            else:
                poor_cases.append(result)
                logger.warning(f"❌ {query_id}: 较差 (Recall@5={recall:.2%})")
    
        # 计算总体统计
        all_cases = perfect_cases + good_cases + moderate_cases + poor_cases
        total_processed = len(all_cases)
        all_recalls = [r['recall_at_5'] for r in all_cases]
        avg_recall = sum(all_recalls) / len(all_recalls) if all_recalls else 0.0
        
        # ============ 打印统计和详细信息 ============
        
        print("\n" + "="*60)
        print("分析结果统计")
        print("="*60)
        print(f"总查询数: {len(test_queries)}")
        print(f"处理查询: {total_processed}")
        print(f"跳过查询: {skipped}")
        
        print("\n" + "="*60)
        print("Recall@5 分布统计")
        print("="*60)
        print(f"完美 (Recall=1.0):           {len(perfect_cases)} 个 ({len(perfect_cases)/total_processed*100:.1f}%)")
        print(f"良好 (0.8≤Recall<1.0):       {len(good_cases)} 个 ({len(good_cases)/total_processed*100:.1f}%)")
        print(f"中等 (0.5≤Recall<0.8):       {len(moderate_cases)} 个 ({len(moderate_cases)/total_processed*100:.1f}%)")
        print(f"较差 (Recall<0.5):           {len(poor_cases)} 个 ({len(poor_cases)/total_processed*100:.1f}%)")
        print(f"\n平均Recall@5: {avg_recall:.2%}")
        
        # 2. 详细分析较差案例
        if poor_cases:
            print("\n" + "="*60)
            print(f"较差案例详情 (共 {len(poor_cases)} 个)")
            print("="*60)
            
            for i, case in enumerate(poor_cases, 1):
                print(f"\n{'='*60}")
                print(f"案例 #{i}: {case['query_id']}")
                print(f"{'='*60}")
                print(f"原始查询: {case['original_query']}")
                print(f"改写后: {case['rewritten_query'][:100]}...")
                print(f"Recall@5: {case['recall_at_5']:.2%} ({case['hits_count']}/{case['ground_truth_count']})")
                
                # 命中情况
                print(f"\n✅ Top5命中 ({len(case['hit_docs'])}个):")
                if case['hit_docs']:
                    for doc in case['hit_docs']:
                        print(f"  Rank {doc['rank']}: {doc['doc_id']} (相似度 {doc['similarity']:.4f})")
                else:
                    print("  (无)")
                
                # 遗漏情况
                print(f"\n❌ 遗漏文档 ({len(case['missed_docs'])}个):")
                for doc in case['missed_docs']:
                    if doc['status'] == 'in_top20':
                        print(f"  Rank {doc['rank']:2d}: {doc['doc_id']} (相似度 {doc['similarity']:.4f})")
                    else:
                        print(f"  Rank >20: {doc['doc_id']} (未检索到)")
        else:
            print("\n🎉 太棒了！没有较差案例！")
        
        # 3. 中等案例简要统计
        if moderate_cases:
            print("\n" + "="*60)
            print(f"中等案例统计 (共 {len(moderate_cases)} 个)")
            print("="*60)
            for case in moderate_cases:
                print(f"{case['query_id']}: Recall@5={case['recall_at_5']:.2%} ({case['hits_count']}/{case['ground_truth_count']})")
        
        # 4. 良好案例简要统计
        if good_cases:
            print("\n" + "="*60)
            print(f"良好案例统计 (共 {len(good_cases)} 个)")
            print("="*60)
            for case in good_cases:
                print(f"{case['query_id']}: Recall@5={case['recall_at_5']:.2%} ({case['hits_count']}/{case['ground_truth_count']})")
        
        # 5. 完美案例简要统计
        if perfect_cases:
            print("\n" + "="*60)
            print(f"完美案例 (共 {len(perfect_cases)} 个)")
            print("="*60)
            print(f"以下查询达到了Recall@5=100%:")
            for case in perfect_cases:
                print(f"  {case['query_id']} ({case['ground_truth_count']}个相关文档全部检索到)")
        
        # 6. 保存到文件
        output_dir = Path("experiments/query_rewrite/results")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "recall_analysis.json"
        
        # 保存详细结果
        output_data = {
            'summary': {
                'total_queries': len(test_queries),
                'processed_queries': total_processed,
                'skipped': skipped,
                'avg_recall_at_5': avg_recall,
                'distribution': {
                    'perfect': len(perfect_cases),
                    'good': len(good_cases),
                    'moderate': len(moderate_cases),
                    'poor': len(poor_cases)
                }
            },
            'poor_cases': poor_cases,
            'moderate_cases': moderate_cases,
            'good_cases': good_cases,
            'perfect_cases': perfect_cases
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n✅ 分析完成！结果已保存到 {output_path}")
        
    except Exception as e:
        logger.error(f"❌ 分析失败: {e}", exc_info=True)
        raise



if __name__ == "__main__":
    main()