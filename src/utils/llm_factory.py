# src/utils/llm_factory.py
"""
LLM工厂类
支持DeepSeek, OpenAI, Claude等多种LLM
"""

from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatAnthropic
from .config import get_settings

def get_llm(provider: str = None, **kwargs):
    """
    获取LLM实例

    Args:
        provider: LLM供应商 (deepseek/openai/claude)
        **kwargs: 额外参数（temperature, max_tokens等）

    Returns: 
        LLM实例
    """
   
    settings = get_settings()
    provider = provider or settings.llm_provider

    # 合并默认配置和自定义参数
    config = {
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        **kwargs
    }

    if provider == "deepseek":
        return ChatOpenAI(
        model=settings.llm_model,
        openai_api_key=settings.deepseek_api_key,
        openai_api_base=settings.deepseek_base_url,
        **config
    )

    elif provider == "openai":
        return ChatOpenAI(
            model=settings.llm_model,
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url,
            **config
        )
        
    elif provider == "claude":
        return ChatAnthropic(
            model=settings.llm_model,
            anthropic_api_key=settings.anthropic_api_key,
            **config
        )
        
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

if __name__ == "__main__":
    # 测试LLM调用
    llm = get_llm()
    response = llm.invoke("Say 'Hello from DeepSeek!' in Chinese")
    print(response.content)