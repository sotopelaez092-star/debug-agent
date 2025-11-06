"""测试文本分块器"""
import json
from src.rag.chunk import TextChunker

# 加载数据
print("📊 加载数据...")
with open("data/processed/stackoverflow_1k.json", 'r', encoding='utf-8') as f:
    qa_data = json.load(f)

print(f"✅ 加载 {len(qa_data)} 条数据")

# 创建分块器
chunker = TextChunker(chunk_size=500, chunk_overlap=50)

# 测试单个文本
print("\n🧪 测试单个文本分块:")
test_text = qa_data[0]['combined']
chunks = chunker.split_text(test_text)
print(f"原文长度: {len(test_text)} 字符")
print(f"分块数量: {len(chunks)} 块")
print(f"\n第1块内容:\n{chunks[0][:200]}...")

# 批量处理测试（前10条）
print("\n🧪 批量处理测试（前10条）:")
test_chunks = chunker.process_qa_data(qa_data[:10])

print(f"\n📝 样例块:")
print(f"  文本: {test_chunks[0]['text'][:100]}...")
print(f"  来源ID: {test_chunks[0]['source_id']}")
print(f"  块索引: {test_chunks[0]['chunk_index']}/{test_chunks[0]['total_chunks']}")
print(f"\n✅ 分块器测试通过！")