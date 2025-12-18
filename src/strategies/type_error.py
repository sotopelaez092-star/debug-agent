"""TypeError 处理策略"""
import re
from typing import Optional
from .base import BaseErrorStrategy
from src.models.results import SearchResult


class TypeErrorStrategy(BaseErrorStrategy):
    """TypeError 策略：处理函数参数不匹配"""

    def __init__(self, confidence_threshold: float = 0.7):
        super().__init__(confidence_threshold)

    @property
    def error_type(self) -> str:
        return "TypeError"

    def extract(self, error_message: str) -> dict:
        """提取函数名和参数信息"""
        # func() takes 2 positional arguments but 3 were given
        match = re.search(
            r"(\w+)\(\) takes (\d+) .+? (\d+) .+? given",
            error_message
        )
        if match:
            return {
                "func_name": match.group(1),
                "expected": int(match.group(2)),
                "got": int(match.group(3))
            }

        # func() missing 1 required positional argument: 'x'
        match = re.search(
            r"(\w+)\(\) missing (\d+) required .+? argument",
            error_message
        )
        if match:
            return {
                "func_name": match.group(1),
                "missing": int(match.group(2))
            }

        return {}

    def fast_search(self, extracted: dict, tools, error_file: str = "") -> Optional[SearchResult]:
        """快速查找函数签名"""
        func_name = extracted.get("func_name")
        if not func_name:
            return None

        signature = tools.get_function_signature(func_name)
        if signature:
            suggestion_parts = [f"函数 '{func_name}' 的签名: {signature}"]

            if "expected" in extracted and "got" in extracted:
                expected = extracted["expected"]
                got = extracted["got"]
                suggestion_parts.append(
                    f"期望 {expected} 个参数，但传入了 {got} 个"
                )
            elif "missing" in extracted:
                missing = extracted["missing"]
                suggestion_parts.append(f"缺少 {missing} 个必需参数")

            return SearchResult(
                symbol=func_name,
                confidence=0.9,
                suggestion="\n".join(suggestion_parts)
            )

        return None
