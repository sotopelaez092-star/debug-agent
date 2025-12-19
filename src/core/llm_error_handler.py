"""LLM 调用错误处理和重试逻辑"""
import asyncio
import logging
from typing import Optional, Callable, TypeVar, Any
from functools import wraps
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')


class LLMError(Exception):
    """LLM 调用基础异常"""
    pass


class LLMNetworkError(LLMError):
    """网络错误"""
    pass


class LLMRateLimitError(LLMError):
    """速率限制错误"""
    pass


class LLMAuthError(LLMError):
    """认证错误"""
    pass


class LLMTimeoutError(LLMError):
    """超时错误"""
    pass


class LLMJSONParseError(LLMError):
    """JSON 解析错误"""
    pass


async def retry_with_exponential_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (Exception,)
) -> Any:
    """使用指数退避重试异步函数

    Args:
        func: 要重试的异步函数
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        exponential_base: 指数基数
        retryable_exceptions: 可重试的异常类型

    Returns:
        函数执行结果

    Raises:
        最后一次执行的异常
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except retryable_exceptions as e:
            last_exception = e

            if attempt == max_retries:
                logger.error(
                    f"重试 {max_retries} 次后仍然失败: {type(e).__name__}: {e}"
                )
                raise

            # 计算下次重试的延迟
            wait_time = min(delay, max_delay)
            logger.warning(
                f"尝试 {attempt + 1}/{max_retries + 1} 失败: {type(e).__name__}: {e}, "
                f"{wait_time:.1f}s 后重试..."
            )

            await asyncio.sleep(wait_time)
            delay *= exponential_base

    # 不应该到达这里
    if last_exception:
        raise last_exception
    raise RuntimeError("重试逻辑异常")


def classify_llm_error(exception: Exception) -> Exception:
    """将原始异常分类为具体的 LLM 错误类型

    Args:
        exception: 原始异常

    Returns:
        分类后的异常
    """
    error_msg = str(exception).lower()
    exception_type = type(exception).__name__

    # 认证错误
    if "authentication" in error_msg or "api key" in error_msg or "unauthorized" in error_msg:
        return LLMAuthError(f"API 认证失败: {exception}")

    # 速率限制
    if "rate limit" in error_msg or "too many requests" in error_msg or "429" in error_msg:
        return LLMRateLimitError(f"API 速率限制: {exception}")

    # 超时
    if "timeout" in error_msg or "timed out" in error_msg:
        return LLMTimeoutError(f"请求超时: {exception}")

    # 网络错误
    if any(keyword in exception_type.lower() for keyword in ["connection", "network", "socket"]):
        return LLMNetworkError(f"网络连接错误: {exception}")

    # JSON 解析错误
    if "json" in error_msg or "parse" in error_msg:
        return LLMJSONParseError(f"JSON 解析失败: {exception}")

    # 其他错误
    return LLMError(f"LLM 调用失败: {exception}")


async def call_llm_with_retry(
    client,
    model: str,
    messages: list,
    temperature: float = 0.3,
    max_tokens: int = 2000,
    max_retries: int = 3,
    timeout: float = 60.0
) -> Any:
    """调用 LLM 并自动重试

    Args:
        client: OpenAI 客户端
        model: 模型名称
        messages: 消息列表
        temperature: 温度参数
        max_tokens: 最大 token 数
        max_retries: 最大重试次数
        timeout: 超时时间（秒）

    Returns:
        LLM 响应

    Raises:
        LLMError: LLM 调用失败
    """
    async def _make_request():
        try:
            # 使用 asyncio.wait_for 添加超时控制
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                ),
                timeout=timeout
            )
            return response
        except asyncio.TimeoutError as e:
            raise LLMTimeoutError(f"请求超时 (>{timeout}s)")
        except Exception as e:
            # 分类错误
            raise classify_llm_error(e)

    # 定义可重试的错误
    retryable_errors = (
        LLMNetworkError,
        LLMRateLimitError,
        LLMTimeoutError,
    )

    try:
        return await retry_with_exponential_backoff(
            _make_request,
            max_retries=max_retries,
            retryable_exceptions=retryable_errors
        )
    except LLMAuthError:
        # 认证错误不重试
        logger.error("API 认证失败，请检查 API Key")
        raise
    except Exception as e:
        # 其他错误也抛出
        logger.error(f"LLM 调用最终失败: {type(e).__name__}: {e}")
        raise


def parse_llm_response_safe(response_content: str, expected_format: str = "code") -> Optional[str]:
    """安全解析 LLM 响应

    Args:
        response_content: LLM 返回的内容
        expected_format: 期望的格式 ("code", "json", "text")

    Returns:
        解析后的内容，失败返回 None

    Raises:
        LLMJSONParseError: JSON 解析失败
    """
    if not response_content:
        logger.warning("LLM 响应为空")
        return None

    try:
        if expected_format == "code":
            # 提取代码块
            import re
            # 尝试提取 ```python ... ``` 代码块
            code_blocks = re.findall(r'```python\n(.*?)```', response_content, re.DOTALL)
            if code_blocks:
                return code_blocks[0].strip()

            # 尝试提取 ``` ... ``` 代码块
            code_blocks = re.findall(r'```\n(.*?)```', response_content, re.DOTALL)
            if code_blocks:
                return code_blocks[0].strip()

            # 没有代码块，返回全部内容
            logger.warning("未找到代码块标记，返回原始内容")
            return response_content.strip()

        elif expected_format == "json":
            # 解析 JSON
            import json
            try:
                return json.loads(response_content)
            except json.JSONDecodeError as e:
                # 尝试提取 JSON 代码块
                json_blocks = re.findall(r'```json\n(.*?)```', response_content, re.DOTALL)
                if json_blocks:
                    return json.loads(json_blocks[0].strip())

                raise LLMJSONParseError(f"无法解析 JSON: {e}")

        else:  # text
            return response_content.strip()

    except Exception as e:
        logger.error(f"解析 LLM 响应失败: {e}")
        raise
