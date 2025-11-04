# src/utils/config.py
"""
配置管理模块
支持从.env文件加载配置，并提供默认值
"""

from pydantic_settings import BaseSettings
from typing import Literal
class Settings(BaseSettings):
    """应用配置"""

    # ===== API配置 =====
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    anthropic_api_key: str = ""

    # ===== 模型配置 =====
    llm_provider: Literal["deepseek", "openai", "anthropic"] = "deepseek"
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000

    # ===== Embedding配置 =====
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"

    # ===== 数据库配置 =====
    chroma_persist_dir: str = "./data/chroma_db"

    # ===== 日志配置 =====
    log_level: str = "INFO"
    log_dir: str = "./logs"

    # ===== RAG配置 =====
    chunk_size: int = 500
    chunk_overlap: int =50
    top_k: int = 5

    # ===== Agent配置 =====
    max_retry_attempts: int = 3
    sandbox_timeput: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive =  False
        extra = "ignore"


# 全局配置实例
settings = Settings()

def get_settings() -> Settings:
    """获取全局配置实例"""
    return settings

if __name__ == "__main__":
    # 测试配置加载
    config = get_settings()
    print(f"LLM Provider: {config.llm_provider}")
    print(f"LLM Model: {config.llm_model}")
    print(f"DeepSeek API Key: {'***' + config.deepseek_api_key[-4:] if config.deepseek_api_key else 'Not Set'}")