"""
TokenManager - Token 管理器

管理 LLM 的上下文长度，智能压缩和截断内容
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Token 管理器

    功能：
    1. 估算文本的 token 数量
    2. 按优先级压缩上下文
    3. 智能截断长文本
    4. 生成上下文摘要

    Attributes:
        max_context_tokens: 最大上下文 token 数
        reserve_for_response: 为响应预留的 token 数
    """

    # 上下文内容的优先级（数字越小优先级越高）
    PRIORITY_ORDER = {
        'error_file_content': 1,      # 最高：错误文件
        'error_message': 2,            # 错误信息
        'related_symbols': 3,          # 相关符号定义
        'import_suggestions': 4,       # import 建议
        'rag_solutions': 5,            # RAG 解决方案
        'related_files': 6,            # 最低：其他相关文件
    }

    def __init__(
        self,
        max_context_tokens: int = 6000,
        reserve_for_response: int = 2000,
        chars_per_token: float = 3.5  # 中英混合的平均值
    ):
        """
        初始化 Token 管理器

        Args:
            max_context_tokens: 最大上下文 token 数
            reserve_for_response: 为 LLM 响应预留的 token 数
            chars_per_token: 每个 token 对应的平均字符数
        """
        self.max_context_tokens = max_context_tokens
        self.reserve_for_response = reserve_for_response
        self.chars_per_token = chars_per_token

        # 实际可用于上下文的 token 数
        self.available_tokens = max_context_tokens - reserve_for_response

        logger.info(f"TokenManager初始化: max={max_context_tokens}, "
                   f"available={self.available_tokens}")

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的 token 数量

        Args:
            text: 文本内容

        Returns:
            估算的 token 数量
        """
        if not text:
            return 0

        # 简单估算：字符数 / 平均每token字符数
        # 对于代码，这个估算会稍微偏高，但更安全
        return int(len(text) / self.chars_per_token)

    def estimate_context_tokens(self, context: Dict[str, Any]) -> Dict[str, int]:
        """
        估算上下文各部分的 token 数量

        Args:
            context: 上下文字典

        Returns:
            {部分名: token数} 的字典
        """
        estimates = {}

        for key, value in context.items():
            if isinstance(value, str):
                estimates[key] = self.estimate_tokens(value)
            elif isinstance(value, dict):
                # 对于字典类型（如 related_files），计算所有值的总 token
                total = sum(
                    self.estimate_tokens(str(v))
                    for v in value.values()
                )
                estimates[key] = total
            elif isinstance(value, list):
                # 对于列表类型（如 rag_solutions），计算所有元素的总 token
                total = sum(
                    self.estimate_tokens(str(item))
                    for item in value
                )
                estimates[key] = total
            else:
                estimates[key] = self.estimate_tokens(str(value))

        return estimates

    def compress_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        按优先级压缩上下文，使其符合 token 限制

        Args:
            context: 原始上下文字典

        Returns:
            压缩后的上下文字典
        """
        # 估算当前 token 使用
        estimates = self.estimate_context_tokens(context)
        total_tokens = sum(estimates.values())

        logger.info(f"压缩前 token 估算: {total_tokens}, 限制: {self.available_tokens}")

        # 如果未超限，直接返回
        if total_tokens <= self.available_tokens:
            logger.info("上下文未超限，无需压缩")
            return context

        # 按优先级排序
        sorted_keys = sorted(
            context.keys(),
            key=lambda k: self.PRIORITY_ORDER.get(k, 99)
        )

        # 逐步添加内容
        compressed = {}
        current_tokens = 0

        for key in sorted_keys:
            value = context[key]
            value_tokens = estimates.get(key, 0)

            remaining = self.available_tokens - current_tokens

            if value_tokens <= remaining:
                # 完整添加
                compressed[key] = value
                current_tokens += value_tokens
            elif remaining > 100:  # 至少留100 token 空间才值得截断
                # 需要截断
                compressed[key] = self._truncate_value(value, remaining)
                current_tokens += remaining
                logger.info(f"截断 '{key}': {value_tokens} -> {remaining} tokens")
            else:
                # 空间不足，跳过
                logger.info(f"跳过 '{key}': 剩余空间不足 ({remaining} tokens)")

        logger.info(f"压缩后 token 估算: {current_tokens}")
        return compressed

    def _truncate_value(self, value: Any, max_tokens: int) -> Any:
        """
        截断值到指定 token 数

        Args:
            value: 要截断的值
            max_tokens: 最大 token 数

        Returns:
            截断后的值
        """
        max_chars = int(max_tokens * self.chars_per_token)

        if isinstance(value, str):
            return self._truncate_string(value, max_chars)

        elif isinstance(value, dict):
            # 对于字典，逐个添加直到超限
            result = {}
            current_chars = 0

            for k, v in value.items():
                v_str = str(v)
                if current_chars + len(v_str) <= max_chars:
                    result[k] = v
                    current_chars += len(v_str)
                else:
                    # 截断这个值
                    remaining = max_chars - current_chars
                    if remaining > 50:
                        result[k] = self._truncate_string(v_str, remaining)
                    break

            return result

        elif isinstance(value, list):
            # 对于列表，保留前面的元素
            result = []
            current_chars = 0

            for item in value:
                item_str = str(item)
                if current_chars + len(item_str) <= max_chars:
                    result.append(item)
                    current_chars += len(item_str)
                else:
                    break

            return result

        else:
            return self._truncate_string(str(value), max_chars)

    def _truncate_string(self, text: str, max_chars: int) -> str:
        """
        智能截断字符串

        Args:
            text: 原始文本
            max_chars: 最大字符数

        Returns:
            截断后的文本
        """
        if len(text) <= max_chars:
            return text

        # 尝试在合适的位置截断
        # 优先在换行符处截断
        truncated = text[:max_chars]

        # 找最后一个换行符
        last_newline = truncated.rfind('\n')
        if last_newline > max_chars * 0.7:  # 如果换行符在70%之后的位置
            truncated = truncated[:last_newline]

        return truncated + "\n... [内容已截断]"

    def compress_rag_solutions(
        self,
        solutions: List[Dict],
        max_solutions: int = 3,
        max_chars_per_solution: int = 500
    ) -> List[Dict]:
        """
        压缩 RAG 解决方案

        Args:
            solutions: RAG 解决方案列表
            max_solutions: 最大保留数量
            max_chars_per_solution: 每个解决方案的最大字符数

        Returns:
            压缩后的解决方案列表
        """
        if not solutions:
            return []

        compressed = []

        for solution in solutions[:max_solutions]:
            compressed_solution = solution.copy()

            # 截断 content 字段
            content = solution.get('content', '')
            if len(content) > max_chars_per_solution:
                compressed_solution['content'] = (
                    content[:max_chars_per_solution] + "..."
                )

            compressed.append(compressed_solution)

        return compressed

    def compress_related_files(
        self,
        files: Dict[str, str],
        max_files: int = 3,
        max_chars_per_file: int = 1000
    ) -> Dict[str, str]:
        """
        压缩相关文件

        Args:
            files: {文件路径: 文件内容} 字典
            max_files: 最大保留文件数
            max_chars_per_file: 每个文件的最大字符数

        Returns:
            压缩后的文件字典
        """
        if not files:
            return {}

        # 按文件大小排序，优先保留小文件
        sorted_files = sorted(files.items(), key=lambda x: len(x[1]))

        compressed = {}

        for file_path, content in sorted_files[:max_files]:
            if len(content) > max_chars_per_file:
                # 截断文件内容
                compressed[file_path] = self._truncate_string(content, max_chars_per_file)
            else:
                compressed[file_path] = content

        return compressed

    def get_compression_summary(
        self,
        original: Dict[str, Any],
        compressed: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        获取压缩摘要

        Args:
            original: 原始上下文
            compressed: 压缩后的上下文

        Returns:
            压缩摘要
        """
        original_estimates = self.estimate_context_tokens(original)
        compressed_estimates = self.estimate_context_tokens(compressed)

        return {
            'original_tokens': sum(original_estimates.values()),
            'compressed_tokens': sum(compressed_estimates.values()),
            'reduction_ratio': 1 - sum(compressed_estimates.values()) / max(sum(original_estimates.values()), 1),
            'original_breakdown': original_estimates,
            'compressed_breakdown': compressed_estimates,
        }
