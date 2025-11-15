#!/usr/bin/env python3
"""
构建不同Embedding模型的向量库

功能：
1. 从chroma_s1读取已有的chunks
2. 用指定的embedding模型重新编码
3. 保存到新的vectorstore

用法:
    python scripts/build_vectorstore_for_embedding.py \
        --model-name "BAAI/bge-base-en-v1.5" \
        --output-dir "data/vectorstore/embed_m2"
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

import chromadb
from chromadb.config import Settings

from src.rag.embedder import Embedder

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmbeddingVectorStoreBuilder:
    """为不同Embedding模型构建向量库"""
    
    def __init__(
        self,
        source_db_path: str,
        output_db_path: str,
        model_name: str,
        batch_size: int = 32
    ):
        """
        初始化
        
        Args:
            source_db_path: 源向量库路径（chroma_s1）
            output_db_path: 输出向量库路径
            model_name: Embedding模型名称
            batch_size: 批处理大小
        
        Raises:
            ValueError: 当参数无效时
        """
        # ✅ 生产级实践：输入验证
        if not source_db_path or not isinstance(source_db_path, str):
            raise ValueError("source_db_path必须是非空字符串")
        if not output_db_path or not isinstance(output_db_path, str):
            raise ValueError("output_db_path必须是非空字符串")
        if not model_name or not isinstance(model_name, str):
            raise ValueError("model_name必须是非空字符串")
        if batch_size < 1 or batch_size > 1000:
            raise ValueError("batch_size必须在1-1000之间")
        
        self.source_db_path = source_db_path
        self.output_db_path = output_db_path
        self.model_name = model_name
        self.batch_size = batch_size
        
        # 初始化为None，后续再赋值
        self.embedder = None
        self.source_collection = None
        self.target_collection = None
    
    def load_source_data(self) -> Dict[str, Any]:
        """
        从源向量库读取所有数据
        
        Returns:
            包含ids, documents, metadatas的字典
            
        Raises:
            FileNotFoundError: 当源向量库不存在时
            ValueError: 当源向量库为空时
        """
        logger.info(f"📂 从源向量库读取数据: {self.source_db_path}")
        
        # ✅ 生产级实践：验证路径存在
        source_path = Path(self.source_db_path)
        if not source_path.exists():
            raise FileNotFoundError(f"源向量库不存在: {self.source_db_path}")
        
        try:
            # ✅ 关键修复1：使用新版API
            # chromadb.PersistentClient 而不是 chromadb.Client
            client = chromadb.PersistentClient(path=self.source_db_path)
            
            # 获取collection
            self.source_collection = client.get_collection("stackoverflow_kb")
            
            # 获取所有数据
            source_data = self.source_collection.get(
                include=['documents', 'metadatas']
            )
            
            # ✅ 生产级实践：验证数据有效性
            if not source_data['ids']:
                raise ValueError("源向量库为空，没有数据")
            
            logger.info(f"  ✅ 成功读取 {len(source_data['ids'])} 个chunks")
            
            # 打印一些统计信息
            logger.info(f"  ℹ️  第一个chunk长度: {len(source_data['documents'][0])} 字符")
            
            return source_data
            
        except Exception as e:
            logger.error(f"读取源数据失败: {e}", exc_info=True)
            raise
    
    def init_embedder(self) -> None:
        """
        初始化Embedding模型
        
        Raises:
            Exception: 当模型加载失败时
        """
        logger.info(f"🤖 初始化Embedding模型: {self.model_name}")
        
        try:
            # 创建Embedder实例
            self.embedder = Embedder(model_name=self.model_name)
            
            # ✅ 关键修复2：使用正确的方法名 encode_text
            test_text = "This is a test sentence."
            test_embedding = self.embedder.encode_text(test_text)
            
            logger.info(f"  ✅ 模型加载成功")
            logger.info(f"  ℹ️  Embedding维度: {len(test_embedding)}")
            
        except Exception as e:
            logger.error(f"Embedding模型初始化失败: {e}", exc_info=True)
            raise
    
    def init_target_db(self) -> None:
        """
        初始化目标向量库
        
        Raises:
            Exception: 当数据库初始化失败时
        """
        logger.info(f"💾 初始化目标向量库: {self.output_db_path}")
        
        try:
            # ✅ 生产级实践：确保目录存在
            output_path = Path(self.output_db_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # ✅ 关键修复3：使用新版API
            client = chromadb.PersistentClient(
                path=self.output_db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            collection_name = "stackoverflow_kb"
            
            # ✅ 关键修复4：正确处理已存在的collection
            # 如果collection已存在，先删除
            try:
                client.delete_collection(name=collection_name)
                logger.info(f"  ℹ️  删除已存在的Collection: {collection_name}")
            except:
                # 如果不存在，忽略错误
                pass
            
            # ✅ 关键修复5：创建collection时不传embedding_function
            # 因为我们会手动传入embeddings
            self.target_collection = client.create_collection(
                name=collection_name,
                metadata={"description": "Stack Overflow Python错误问答知识库"}
            )
            
            logger.info(f"  ✅ Collection创建成功: {collection_name}")
            
        except Exception as e:
            logger.error(f"目标向量库初始化失败: {e}", exc_info=True)
            raise
    
    def build_vectorstore(self, source_data: Dict[str, Any]) -> None:
        """
        构建新的向量库
        
        Args:
            source_data: 从源库读取的数据
            
        Raises:
            Exception: 当构建失败时
        """
        logger.info("🔨 开始构建新向量库")
        
        ids = source_data['ids']
        documents = source_data['documents']
        metadatas = source_data['metadatas']
        
        total = len(ids)
        logger.info(f"  需要处理 {total} 个chunks")
        
        # 计算batch数量
        num_batches = (total + self.batch_size - 1) // self.batch_size
        logger.info(f"  将分 {num_batches} 个批次处理 (batch_size={self.batch_size})")
        
        # ✅ 生产级实践：使用tqdm显示进度
        for batch_idx in tqdm(range(num_batches), desc="构建索引"):
            start_idx = batch_idx * self.batch_size
            end_idx = min(start_idx + self.batch_size, total)
            
            # 提取batch数据
            batch_ids = ids[start_idx:end_idx]
            batch_docs = documents[start_idx:end_idx]
            batch_metas = metadatas[start_idx:end_idx]
            
            try:
                # 生成embeddings
                batch_embeddings = self.embedder.encode_batch(batch_docs)
                
                # ✅ 关键修复6：简化tolist()转换
                # encode_batch返回np.ndarray，直接tolist()即可
                batch_embeddings_list = batch_embeddings.tolist()
                
                # 添加到ChromaDB
                self.target_collection.add(
                    ids=batch_ids,
                    documents=batch_docs,
                    metadatas=batch_metas,
                    embeddings=batch_embeddings_list
                )
                
            except Exception as e:
                # ✅ 生产级实践：batch失败不应该终止整个流程
                logger.error(f"Batch {batch_idx} 处理失败: {e}", exc_info=True)
                continue
        
        # 验证最终结果
        final_count = self.target_collection.count()
        logger.info(f"\n  ✅ 向量数据库构建完成")
        logger.info(f"  ℹ️  索引了 {final_count} 个chunks")
        
        # ✅ 生产级实践：验证数据完整性
        if final_count != total:
            logger.warning(f"  ⚠️  警告: 预期 {total} 个，实际 {final_count} 个")
    
    def run(self) -> None:
        """执行完整流程"""
        logger.info("\n" + "🚀" * 40)
        logger.info(f"构建Embedding向量库: {self.model_name}")
        logger.info("🚀" * 40 + "\n")
        
        try:
            # 1. 读取源数据
            source_data = self.load_source_data()
            
            # 2. 初始化embedder
            self.init_embedder()
            
            # 3. 初始化目标数据库
            self.init_target_db()
            
            # 4. 构建向量库
            self.build_vectorstore(source_data)
            
            logger.info("\n" + "="*80)
            logger.info("✅ 向量库构建完成！")
            logger.info("="*80 + "\n")
            
        except Exception as e:
            logger.error(f"\n❌ 构建失败: {e}", exc_info=True)
            raise


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="为不同Embedding模型构建向量库",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--source-db",
        type=str,
        default="data/vectorstore/chroma_s1",
        help="源向量库路径"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="输出向量库路径"
    )
    
    parser.add_argument(
        "--model-name",
        type=str,
        required=True,
        help="Embedding模型名称 (例如: BAAI/bge-base-en-v1.5)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="批处理大小"
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 打印配置
    logger.info("\n📋 配置信息:")
    logger.info(f"  源向量库: {args.source_db}")
    logger.info(f"  输出目录: {args.output_dir}")
    logger.info(f"  模型名称: {args.model_name}")
    logger.info(f"  批次大小: {args.batch_size}\n")
    
    builder = EmbeddingVectorStoreBuilder(
        source_db_path=args.source_db,
        output_db_path=args.output_dir,
        model_name=args.model_name,
        batch_size=args.batch_size
    )
    
    builder.run()


if __name__ == "__main__":
    main()