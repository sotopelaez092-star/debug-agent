"""LLM 客户端适配器 - 支持 function calling"""
import json
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

from .config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 客户端 - 封装 OpenAI 兼容的 API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """
        初始化 LLM 客户端

        Args:
            api_key: API 密钥
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
        """
        settings = get_settings()

        self.api_key = api_key or settings.deepseek_api_key
        self.model = model or settings.llm_model or "deepseek-chat"
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 创建异步客户端（OpenAI 兼容）
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=settings.deepseek_base_url or "https://api.deepseek.com/v1",
            timeout=60.0  # 60秒超时，避免卡死
        )

        logger.info(f"LLM 客户端初始化完成: model={self.model}")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        发送聊天请求

        Args:
            messages: 消息列表
                [
                    {"role": "system", "content": "..."},
                    {"role": "user", "content": "..."},
                    {"role": "assistant", "content": "...", "tool_calls": [...]},
                    {"role": "tool", "tool_call_id": "...", "content": "..."}
                ]
            tools: 工具列表（function calling schema）

        Returns:
            {
                "content": str,
                "tool_calls": [
                    {
                        "id": str,
                        "name": str,
                        "arguments": dict or str
                    }
                ]
            }
        """
        try:
            # 准备请求参数
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }

            # 如果提供了 tools，添加到请求中
            if tools:
                request_params["tools"] = tools

            # 调用 API
            response = await self.client.chat.completions.create(**request_params)

            # 解析响应
            message = response.choices[0].message

            result = {
                "content": message.content or "",
                "tool_calls": []
            }

            # 提取 tool_calls
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    })

            logger.debug(f"LLM 响应: content_length={len(result['content'])}, tool_calls={len(result['tool_calls'])}")
            return result

        except Exception as e:
            logger.error(f"LLM 调用失败: {e}", exc_info=True)
            raise RuntimeError(f"LLM 调用失败: {e}")

    async def chat_simple(self, prompt: str) -> str:
        """
        简单的聊天接口（无 tool calling）

        Args:
            prompt: 提示词

        Returns:
            LLM 响应文本
        """
        messages = [{"role": "user", "content": prompt}]
        result = await self.chat(messages)
        return result["content"]
