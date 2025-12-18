"""AttributeError 处理策略"""
import re
from typing import Optional
try:
    from Levenshtein import distance as levenshtein
except ImportError:
    def levenshtein(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

from .base import BaseErrorStrategy
from src.models.results import SearchResult


class AttributeErrorStrategy(BaseErrorStrategy):
    """AttributeError 策略：处理属性或方法名错误"""

    def __init__(self, confidence_threshold: float = 0.75):
        # AttributeError 使用固定置信度，阈值参数保留用于一致性
        super().__init__(confidence_threshold)

    @property
    def error_type(self) -> str:
        return "AttributeError"

    def extract(self, error_message: str) -> dict:
        """提取类名和属性名"""
        # 'Foo' object has no attribute 'bar'
        match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error_message)
        if match:
            return {
                "class_name": match.group(1),
                "attr_name": match.group(2)
            }
        return {}

    def fast_search(self, extracted: dict, tools, error_file: str = "") -> Optional[SearchResult]:
        """快速搜索类方法"""
        class_name = extracted.get("class_name")
        attr_name = extracted.get("attr_name")

        if not class_name or not attr_name:
            return None

        # 获取类的所有方法
        methods = tools.get_class_methods(class_name)

        # 如果是内置类型（如 list, dict, str），使用 Python 内置方法
        if not methods and class_name in ('list', 'dict', 'str', 'set', 'tuple', 'int', 'float', 'bytes'):
            try:
                builtin_type = eval(class_name)  # 获取内置类型对象
                methods = [m for m in dir(builtin_type) if not m.startswith('_')]
            except:
                pass

        if not methods:
            return None

        # 模糊匹配属性名
        best_match = None
        best_distance = float('inf')

        for method in methods:
            dist = levenshtein(attr_name.lower(), method.lower())
            if dist < best_distance and dist <= 2:  # 最多2个编辑距离
                best_distance = dist
                best_match = method

        if best_match:
            class_info = tools.class_table.get(class_name, {})
            # 对于内置类型，使用通用的置信度和位置
            confidence = 0.85 if best_distance <= 1 else 0.75
            return SearchResult(
                symbol=best_match,
                file=class_info.get('file', error_file or 'builtin'),
                line=class_info.get('line', 0),
                confidence=confidence,
                suggestion=f"'{class_name}' 对象没有属性 '{attr_name}'，可能是 '{best_match}' 的拼写错误"
            )

        return None
