"""对话压缩器 - 管理长对话上下文"""
import logging
from typing import List, Dict

try:
    import tiktoken
except ImportError:
    tiktoken = None

from src.models.scratchpad import Scratchpad

logger = logging.getLogger(__name__)


class ConversationCompressor:
    """对话压缩器 - 滑动窗口 + LLM 总结"""

    def __init__(
        self,
        max_tokens: int = 8000,
        preserve_ratio: float = 0.3,
        model: str = "gpt-4"
    ):
        """
        初始化对话压缩器

        Args:
            max_tokens: 最大 token 数（触发压缩的阈值）
            preserve_ratio: 保留最近消息的比例
            model: 用于 token 计数的模型名称
        """
        self.max_tokens = max_tokens
        self.preserve_ratio = preserve_ratio

        # 初始化 token 编码器
        if tiktoken:
            try:
                self.encoder = tiktoken.encoding_for_model(model)
            except:
                self.encoder = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoder = None
            logger.warning("tiktoken 未安装，使用近似 token 计数")

    def _count_tokens(self, messages: List[Dict]) -> int:
        """计算消息列表的 token 数"""
        if self.encoder:
            total = 0
            for msg in messages:
                content = msg.get("content", "")
                if isinstance(content, str):
                    total += len(self.encoder.encode(content))
            return total
        else:
            # 简单近似：每个字符约 0.3 个 token
            total_chars = sum(len(msg.get("content", "")) for msg in messages)
            return int(total_chars * 0.3)

    async def compress_if_needed(
        self,
        messages: List[Dict],
        llm,
        scratchpad: Scratchpad
    ) -> List[Dict]:
        """
        如果需要则压缩对话

        Args:
            messages: 消息列表
            llm: LLM 客户端（用于总结）
            scratchpad: Scratchpad 实例

        Returns:
            压缩后的消息列表
        """
        token_count = self._count_tokens(messages)

        # 未达到阈值，不压缩
        if token_count < self.max_tokens * 0.5:
            logger.debug(f"Token 数 {token_count} 未超过阈值，不压缩")
            return messages

        logger.info(f"Token 数 {token_count} 超过阈值，开始压缩")

        # 保留 system prompt
        system_msg = messages[0]
        other_msgs = messages[1:]

        # 计算分割点
        split_idx = int(len(other_msgs) * (1 - self.preserve_ratio))
        early_messages = other_msgs[:split_idx]
        recent_messages = other_msgs[split_idx:]

        logger.debug(f"保留最近 {len(recent_messages)} 条消息，压缩早期 {len(early_messages)} 条")

        # 总结早期对话
        summary = await self._summarize(early_messages, llm)

        # 构建压缩后的消息列表
        compressed = [
            system_msg,
            {
                "role": "user",
                "content": f"## 之前的调查总结\n{summary}\n\n{scratchpad.to_markdown()}"
            },
            *recent_messages
        ]

        new_token_count = self._count_tokens(compressed)
        logger.info(f"压缩完成: {token_count} → {new_token_count} tokens")

        return compressed

    async def _summarize(self, messages: List[Dict], llm) -> str:
        """
        总结早期消息

        Args:
            messages: 要总结的消息列表
            llm: LLM 客户端

        Returns:
            总结文本
        """
        if not messages:
            return "无早期对话"

        # 提取消息内容（限制长度）
        content_parts = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                # 每条消息最多取 200 字符
                truncated = content[:200]
                if len(content) > 200:
                    truncated += "..."
                content_parts.append(f"- {msg.get('role', 'unknown')}: {truncated}")

        combined = "\n".join(content_parts)

        # 使用 LLM 总结
        prompt = f"""请用 100-150 字总结以下调查过程的关键发现和行动：

{combined}

总结要点：
1. 执行了哪些关键操作
2. 发现了哪些重要信息
3. 当前的结论或方向"""

        try:
            # 注意：这里假设 llm 有 chat 方法
            response = await llm.chat([{"role": "user", "content": prompt}])

            if hasattr(response, 'content'):
                summary = response.content
            elif isinstance(response, str):
                summary = response
            else:
                summary = str(response)

            logger.debug(f"LLM 总结: {summary[:100]}...")
            return summary

        except Exception as e:
            logger.warning(f"LLM 总结失败: {e}，使用简单总结")
            return self._simple_summary(messages)

    def _simple_summary(self, messages: List[Dict]) -> str:
        """简单总结（不使用 LLM）"""
        summary_parts = [
            f"早期调查共 {len(messages)} 轮对话",
            "执行的操作：search_symbol, read_file, grep 等",
            "关键发现记录在 Scratchpad 中"
        ]
        return "\n".join(summary_parts)
