"""用Mock数据测试评估器（不依赖数据库）"""
from src.evaluation.retrieval_eval import RetrievalEvaluator

print("=" * 60)
print("Mock测试：验证评估器功能")
print("=" * 60)

class MockRetriever:
    """模拟检索器
    
    BaseRetriever: 模拟60%召回率，MRR 0.5
    RerankerRetriever: 模拟75%召回率，MRR 0.7
    """
    
    def __init__(self, name, performance="base"):
        self._name = name
        self.performance = performance
        self.__class__.__name__ = name
    
    def search(self, query, top_k=5):
        """返回模拟检索结果"""
        # BaseRetriever: 简单顺序
        if self.performance == "base":
            return [1, 2, 3, 4, 5][:top_k]
        # RerankerRetriever: 更好的排序
        else:
            return [3, 1, 5, 2, 4][:top_k]

print("\n1️⃣  创建评估器...")
evaluator = RetrievalEvaluator()
print("✅ 评估器创建成功")

print("\n2️⃣  测试单个方法...")

# 测试 Recall@K
print("  - 测试 calculate_recall_at_k...")
result = evaluator.calculate_recall_at_k(
    retrieved_docs=[1, 2, 3, 4, 5],
    ground_truth=[1, 3, 5, 7, 9],
    k=3
)
print(f"    ✅ Recall@3 = {result['recall']:.1%} (找到 {result['found']}/{result['total']})")

# 测试 MRR
print("  - 测试 calculate_mrr...")
result = evaluator.calculate_mrr(
    retrieved_docs=[3, 2, 7, 10, 15],
    ground_truth=[2, 5, 10]
)
print(f"    ✅ MRR = {result['rr']:.3f} (第一个相关文档在第{result['first_relevant_rank']}位)")

# 测试时间统计
print("  - 测试 calculate_avg_time...")
result = evaluator.calculate_avg_time([0.1, 0.2, 0.3, 0.4, 0.5])
print(f"    ✅ 平均时间 = {result['avg_time']:.3f}s (范围: {result['min_time']:.3f}s - {result['max_time']:.3f}s)")

print("\n3️⃣  准备测试数据...")
# 20个测试案例，模拟真实场景
test_cases = [
    {'query': 'AttributeError: NoneType has no attribute get', 'ground_truth': [1, 3, 5]},
    {'query': 'TypeError: can only concatenate str not int', 'ground_truth': [2, 3, 4]},
    {'query': 'ValueError: invalid literal for int base 10', 'ground_truth': [1, 2, 5]},
    {'query': 'IndexError: list index out of range', 'ground_truth': [3, 4, 5]},
    {'query': 'KeyError: key not found in dictionary', 'ground_truth': [1, 4, 5]},
    {'query': 'NameError: name is not defined', 'ground_truth': [2, 4, 5]},
    {'query': 'ImportError: cannot import module', 'ground_truth': [1, 3, 4]},
    {'query': 'ZeroDivisionError: division by zero', 'ground_truth': [2, 3, 5]},
    {'query': 'FileNotFoundError: file does not exist', 'ground_truth': [1, 2, 3]},
    {'query': 'PermissionError: access denied', 'ground_truth': [3, 4, 5]},
    {'query': 'MemoryError: out of memory', 'ground_truth': [1, 3, 5]},
    {'query': 'RecursionError: maximum recursion depth', 'ground_truth': [2, 4, 5]},
    {'query': 'IndentationError: unexpected indent', 'ground_truth': [1, 2, 4]},
    {'query': 'SyntaxError: invalid syntax', 'ground_truth': [2, 3, 4]},
    {'query': 'StopIteration: iteration stopped', 'ground_truth': [1, 3, 4]},
    {'query': 'AssertionError: assertion failed', 'ground_truth': [2, 3, 5]},
    {'query': 'RuntimeError: runtime error occurred', 'ground_truth': [1, 4, 5]},
    {'query': 'NotImplementedError: method not implemented', 'ground_truth': [2, 3, 4]},
    {'query': 'UnicodeDecodeError: codec cannot decode', 'ground_truth': [1, 3, 5]},
    {'query': 'ConnectionError: connection failed', 'ground_truth': [2, 4, 5]},
]
print(f"✅ 准备了 {len(test_cases)} 个测试案例")

print("\n4️⃣  对比两个检索器...")
base = MockRetriever("BaseRetriever", performance="base")
reranker = MockRetriever("RerankerRetriever", performance="reranker")

result = evaluator.compare_retrievers(
    retriever_a=base,
    retriever_b=reranker,
    test_cases=test_cases,
    k=5
)

print("\n" + "=" * 60)
print("📊 对比结果")
print("=" * 60)
print(f"\n📌 BaseRetriever:")
print(f"   - Recall@5: {result['retriever_a']['recall@k']:.1%}")
print(f"   - MRR: {result['retriever_a']['mrr']:.3f}")
print(f"   - 平均时间: {result['retriever_a']['avg_time']:.3f}s")

print(f"\n📌 RerankerRetriever:")
print(f"   - Recall@5: {result['retriever_b']['recall@k']:.1%}")
print(f"   - MRR: {result['retriever_b']['mrr']:.3f}")
print(f"   - 平均时间: {result['retriever_b']['avg_time']:.3f}s")

print(f"\n📈 提升:")
print(f"   - Recall提升: {result['comparison']['recall_improvement']:+.1%}")
print(f"   - MRR提升: {result['comparison']['mrr_improvement']:+.3f}")
print(f"   - 时间增加: {result['comparison']['time_overhead']:+.3f}s")

print("\n5️⃣  生成报告...")
report = evaluator.generate_report(result, output_file='docs/week2_report_mock.md')
print("✅ Mock报告已保存到: docs/week2_report_mock.md")

print("\n" + "=" * 60)
print("🎉 Mock测试完成！")
print("=" * 60)

print("\n📄 报告预览:")
print("-" * 60)
print(report)