"""NameError 错误处理策略"""
import re
from typing import Optional
from .base import BaseErrorStrategy
from src.models.results import SearchResult


class NameErrorStrategy(BaseErrorStrategy):
    """NameError 策略：处理未定义的变量名"""

    def __init__(self, confidence_threshold: float = 0.7):
        super().__init__(confidence_threshold)

    @property
    def error_type(self) -> str:
        return "NameError"

    def extract(self, error_message: str) -> dict:
        """提取未定义的符号名"""
        match = re.search(r"name '(\w+)' is not defined", error_message)
        if match:
            return {"symbol": match.group(1)}
        return {}

    def fast_search(self, extracted: dict, tools, error_file: str = "") -> Optional[SearchResult]:
        """快速搜索符号定义"""
        symbol = extracted.get("symbol")
        if not symbol:
            return None

        matches = tools.search_symbol(symbol, fuzzy=True, error_file=error_file)

        # 如果找到高置信度匹配
        if matches and matches[0].confidence > self.confidence_threshold:
            top_match = matches[0]
            return SearchResult(
                symbol=top_match.name,
                file=top_match.file,
                line=top_match.line,
                confidence=top_match.confidence,
                suggestion=f"'{symbol}' 可能是 '{top_match.name}' 的拼写错误\n位置: {top_match.file}:{top_match.line}"
            )

        return None
