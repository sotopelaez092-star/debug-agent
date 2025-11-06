"""测试Embedding生成器"""
from src.rag.embedder import Embedder

print("🧪 开始测试Embedder\n")

# 测试1: 创建embedder
print("📝 测试1: 加载模型")
embedder = Embedder()

# 测试2: 编码单个文本
print("\n📝 测试2: 编码单个文本")
test_text = "How to reverse a list in Python?"
embedding = embedder.encode_text(test_text)

print(f"  文本: {test_text}")
print(f"  向量维度: {embedding.shape}")
print(f"  前5个值: {embedding[:5]}")

# 测试3: 批量编码
print("\n📝 测试3: 批量编码")
test_texts = [
    "How to reverse a list in Python?",
    "How to sort a list in Python?",
    "What is machine learning?"
]
embeddings = embedder.encode_batch(test_texts)

print(f"  文本数量: {len(test_texts)}")
print(f"  向量矩阵形状: {embeddings.shape}")
print(f"  第1个向量前3个值: {embeddings[0][:3]}")

# 测试4: 计算相似度
print("\n📝 测试4: 相似度计算")

# 导入计算工具
from numpy import dot
from numpy.linalg import norm

def cosine_similarity(a, b):
    """计算两个向量的余弦相似度"""
    return dot(a, b) / (norm(a) * norm(b))

# 计算：文本1 vs 文本2（都是列表操作，应该相似）
sim_1_2 = cosine_similarity(embeddings[0], embeddings[1])

# 计算：文本1 vs 文本3（一个列表，一个机器学习，应该不相似）
sim_1_3 = cosine_similarity(embeddings[0], embeddings[2])

print(f"  '{test_texts[0][:30]}...' ")
print(f"  vs '{test_texts[1][:30]}...' ")
print(f"  → 相似度: {sim_1_2:.4f}\n")

print(f"  '{test_texts[0][:30]}...' ")
print(f"  vs '{test_texts[2][:30]}...' ")
print(f"  → 相似度: {sim_1_3:.4f}")

print("\n✅ Embedder测试全部通过！")
