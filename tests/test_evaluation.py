# test_evaluation.py
"""测试评估器（使用真实检索器）"""
from src.evaluation.retrieval_eval import RetrievalEvaluator
from src.rag.vector_store import VectorStore
from src.rag.retriever import BaseRetriever
from src.rag.reranker_retriever import RerankerRetriever
import json

print("=" * 50)
print("开始测试评估器（真实数据）")
print("=" * 50)

# 1. 初始化VectorStore
print("\n1. 初始化VectorStore...")
vectorstore = VectorStore(collection_name="test_stackoverflow")
print(f"✅ VectorStore初始化完成，文档数: {vectorstore.collection.count()}")

# 2. 正确初始化检索器（传入collection）
print("\n2. 初始化检索器...")
base = BaseRetriever(
    collection=vectorstore.collection,
    min_similarity=0.5
)
print("✅ BaseRetriever初始化完成")

reranker = RerankerRetriever(
    collection=vectorstore.collection,
    min_similarity=0.5
)
print("✅ RerankerRetriever初始化完成")

# 3. 准备测试数据
print("\n3. 准备测试数据...")
# 你可以从文件加载，或者手动构造
test_cases = [
    {
        'query': 'AttributeError: NoneType object has no attribute get',
        'ground_truth': [0, 1, 2]  # 假设这些是相关文档的ID
    },
    {
        'query': 'TypeError: can only concatenate str not int to str',
        'ground_truth': [3, 4, 5]
    },
    {
        'query': 'ValueError: invalid literal for int with base 10',
        'ground_truth': [6, 7, 8]
    },
    # 添加更多测试案例...
]
print(f"✅ 准备了 {len(test_cases)} 个测试案例")

# 4. 创建评估器
print("\n4. 创建评估器...")
evaluator = RetrievalEvaluator()
print("✅ 评估器创建成功")

# 5. 运行对比
print("\n5. 开始对比两个检索器...")
result = evaluator.compare_retrievers(
    retriever_a=base,
    retriever_b=reranker,
    test_cases=test_cases,
    k=5
)

print(f"\n✅ 对比完成！")
print(f"  - BaseRetriever: Recall={result['retriever_a']['recall@k']:.2%}, MRR={result['retriever_a']['mrr']:.3f}")
print(f"  - RerankerRetriever: Recall={result['retriever_b']['recall@k']:.2%}, MRR={result['retriever_b']['mrr']:.3f}")
print(f"  - 提升: Recall={result['comparison']['recall_improvement']:+.2%}, MRR={result['comparison']['mrr_improvement']:+.3f}")

# 6. 生成报告
print("\n6. 生成报告...")
report = evaluator.generate_report(result, output_file='docs/week2_report.md')
print("✅ 报告已保存到: docs/week2_report.md")

print("\n" + "=" * 50)
print("🎉 所有测试完成！")
print("=" * 50)