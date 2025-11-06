# src/rag/config.py
"""RAAG系统配置"""
import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class RAGConfig:
    """RAAG系统配置"""

    def __init__(self):
        # ===== LLM配置 =====
        self.llm_provider = os.getenv("LLM_PROVIDER", "deepseek")
        self.llm_model = os.getenv("LLM_MODEL", "deepseek-chat")
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1024"))

        # DeepSeek配置
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_base_url = os.getenv("DEEPSEEK_BASE_URL")

        # ===== Embedding配置 =====
        self.embedding_model = os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.embedding_device = os .getenv("EMBEDDING_DEVICE", "cpu")

        # ===== 向量数据库配置 =====
        self.chroma_persist_dir = os.getenv(
            "CHROMA_PERSIST_DIR", 
            "./data/chroma_db"
        )

        # ===== RAG参数 =====
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "500"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "50"))
        self.top_k = int(os.getenv("TOP_K", "5"))
        
        # 验证必需配置
        self._validate()

    def _validate(self):
        """验证必需的配置"""
        if not self.deepseek_api_key:
            raise ValueError("❌ 未找到DEEPSEEK_API_KEY")
        
        if not self.deepseek_base_url:
            raise ValueError("❌ 未找到DEEPSEEK_BASE_URL")
    
    def __repr__(self):
        """打印配置信息"""
        return f"""
RAG配置:
  LLM Provider: {self.llm_provider}
  LLM Model: {self.llm_model}
  Embedding Model: {self.embedding_model}
  Chunk Size: {self.chunk_size}
  Top K: {self.top_k}
  Chroma DB: {self.chroma_persist_dir}
"""

# 创建全局配置实例
config = RAGConfig()

