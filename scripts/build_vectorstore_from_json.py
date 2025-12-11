#!/usr/bin/env python3
"""
从 Stack Overflow JSON 数据构建向量数据库

用法:
    python scripts/build_vectorstore_from_json.py
"""

import sys
import json
import logging
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import chromadb
from chromadb.config import Settings
from tqdm import tqdm
from src.rag.embedder import Embedder

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def build_vectorstore(
    input_json: str = "data/raw/stackoverflow_python_errors.json",
    output_path: str = "data/vectorstore/chroma_s1",
    batch_size: int = 32
):
    """从 JSON 文件构建向量数据库"""

    logger.info("=" * 60)
    logger.info("从 Stack Overflow JSON 构建向量数据库")
    logger.info("=" * 60)

    # 1. 读取 JSON 数据
    logger.info(f"\n1. 读取数据: {input_json}")

    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"   ✅ 读取到 {len(data)} 条记录")

    # 检查数据格式并提取文档
    documents = []
    ids = []
    metadatas = []

    for i, item in enumerate(data):
        # 尝试不同的字段名格式
        if isinstance(item, dict):
            # 尝试获取内容
            content = (
                item.get('content') or
                item.get('text') or
                item.get('question', '') + '\n' + item.get('answer', '') or
                item.get('body') or
                str(item)
            )

            # 获取 ID
            doc_id = item.get('id') or item.get('_id') or f"doc_{i}"

            # 获取 metadata
            metadata = {
                "error_type": item.get('error_type', item.get('type', 'unknown')),
                "source": item.get('source', 'stackoverflow'),
            }

            # 添加其他可能有用的字段
            if 'title' in item:
                metadata['title'] = item['title']
            if 'score' in item:
                metadata['score'] = item['score']

        else:
            # 如果是字符串
            content = str(item)
            doc_id = f"doc_{i}"
            metadata = {"source": "stackoverflow"}

        if content and len(content.strip()) > 10:  # 过滤太短的内容
            documents.append(content)
            ids.append(str(doc_id))
            metadatas.append(metadata)

    logger.info(f"   ✅ 有效文档: {len(documents)} 条")

    if not documents:
        logger.error("❌ 没有找到有效文档！")
        return

    # 打印示例
    logger.info(f"\n   示例文档 (前 200 字符):")
    logger.info(f"   {documents[0][:200]}...")

    # 2. 初始化 Embedder
    logger.info(f"\n2. 初始化 Embedding 模型...")
    embedder = Embedder(model_name="BAAI/bge-small-en-v1.5")
    logger.info("   ✅ 模型加载完成")

    # 3. 初始化 ChromaDB
    logger.info(f"\n3. 初始化 ChromaDB: {output_path}")

    Path(output_path).mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=output_path,
        settings=Settings(anonymized_telemetry=False, allow_reset=True)
    )

    # 删除已存在的 collection
    try:
        client.delete_collection("stackoverflow_kb")
        logger.info("   删除已存在的 collection")
    except:
        pass

    collection = client.create_collection(
        name="stackoverflow_kb",
        metadata={"description": "Stack Overflow Python 错误问答知识库"}
    )
    logger.info("   ✅ Collection 创建完成")

    # 4. 批量生成 Embeddings 并添加数据
    logger.info(f"\n4. 生成 Embeddings 并添加数据...")

    total = len(documents)
    num_batches = (total + batch_size - 1) // batch_size

    for batch_idx in tqdm(range(num_batches), desc="处理中"):
        start = batch_idx * batch_size
        end = min(start + batch_size, total)

        batch_docs = documents[start:end]
        batch_ids = ids[start:end]
        batch_metas = metadatas[start:end]

        try:
            # 生成 embeddings
            batch_embeddings = embedder.encode_batch(batch_docs)

            # 添加到 collection
            collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas,
                embeddings=batch_embeddings.tolist()
            )
        except Exception as e:
            logger.error(f"   Batch {batch_idx} 失败: {e}")
            continue

    # 5. 验证
    count = collection.count()
    logger.info(f"\n5. 验证: {count} 条数据已添加")

    # 测试检索
    logger.info("\n6. 测试检索...")
    test_query = "NameError variable not defined"
    test_embedding = embedder.encode_text(test_query)

    results = collection.query(
        query_embeddings=[test_embedding.tolist()],
        n_results=3
    )

    logger.info(f"   查询: '{test_query}'")
    logger.info(f"   返回 {len(results['ids'][0])} 条结果")

    if results['documents'][0]:
        logger.info(f"   最相关结果: {results['documents'][0][0][:100]}...")

    logger.info("\n" + "=" * 60)
    logger.info("✅ 向量数据库构建完成！")
    logger.info(f"   路径: {output_path}")
    logger.info(f"   文档数: {count}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="从 JSON 构建向量数据库")
    parser.add_argument("--input", type=str, default="data/raw/stackoverflow_python_errors.json",
                        help="输入 JSON 文件路径")
    parser.add_argument("--output", type=str, default="data/vectorstore/chroma_s1",
                        help="输出向量数据库路径")
    parser.add_argument("--batch-size", type=int, default=32,
                        help="批处理大小")
    args = parser.parse_args()

    build_vectorstore(args.input, args.output, args.batch_size)
