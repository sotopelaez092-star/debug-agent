"""KeyError 处理策略 - 增强版，支持嵌套字典键追踪"""
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


class KeyErrorStrategy(BaseErrorStrategy):
    """KeyError 策略：处理字典键错误，支持嵌套结构追踪"""

    def __init__(self, confidence_threshold: float = 0.7):
        super().__init__(confidence_threshold)

    @property
    def error_type(self) -> str:
        return "KeyError"

    def extract(self, error_message: str) -> dict:
        """提取缺失的键名"""
        # KeyError: 'missing_key'
        match = re.search(r"KeyError: ['\"](\w+)['\"]", error_message)
        if match:
            return {"missing_key": match.group(1)}
        return {}

    def fast_search(self, extracted: dict, tools, error_file: str = "") -> Optional[SearchResult]:
        """快速搜索相似的字典键，支持嵌套结构追踪"""
        missing_key = extracted.get("missing_key")
        if not missing_key:
            return None

        # 1. 首先使用增强的嵌套键搜索（处理 log_level → logging.level 的情况）
        origin_results = tools.search_dict_key_origin(missing_key)
        if origin_results:
            top_result = origin_results[0]
            if top_result['confidence'] >= self.confidence_threshold:
                suggestion = self._build_suggestion(missing_key, top_result)
                return SearchResult(
                    symbol=top_result['key'],
                    file=top_result.get('file', ''),
                    confidence=top_result['confidence'],
                    suggestion=suggestion
                )

        # 2. 回退到简单的模糊匹配
        all_keys = tools.search_dict_keys()
        if not all_keys:
            return None

        best_match = None
        best_distance = float('inf')

        for key in all_keys:
            dist = levenshtein(missing_key.lower(), key.lower())
            if dist < best_distance and dist <= 2:  # 最多2个编辑距离
                best_distance = dist
                best_match = key

        if best_match:
            confidence = 0.85 if best_distance <= 1 else 0.75
            return SearchResult(
                symbol=best_match,
                confidence=confidence,
                suggestion=f"字典键 '{missing_key}' 不存在，可能是 '{best_match}' 的拼写错误"
            )

        return None

    def _build_suggestion(self, missing_key: str, result: dict) -> str:
        """根据搜索结果类型构建修复建议"""
        result_type = result.get('type', 'exact')
        access_path = result.get('access_path', '')
        func_name = result.get('function', '')
        file_path = result.get('file', '')

        if result_type == 'nested':
            return (
                f"键 '{missing_key}' 在嵌套结构中\n"
                f"【修复方法】将 config[\"{missing_key}\"] 改为 config{access_path}\n"
                f"来源: {file_path} 的 {func_name}() 函数"
            )
        elif result_type == 'restructured':
            return (
                f"键 '{missing_key}' 已重构为嵌套结构\n"
                f"【修复方法】将 config[\"{missing_key}\"] 改为 config{access_path}\n"
                f"来源: {file_path} 的 {func_name}() 函数\n"
                f"提示: 配置结构已从扁平化改为嵌套形式"
            )
        elif result_type == 'fuzzy':
            return result.get('suggestion', f"'{missing_key}' 可能是拼写错误")
        else:
            return f"字典键 '{missing_key}' 不存在，可能是 '{result['key']}' 的拼写错误"

    def get_fix_context(self, extracted: dict, tools, error_file: str = "") -> dict:
        """获取修复上下文，包含嵌套结构的完整信息"""
        missing_key = extracted.get("missing_key")
        if not missing_key:
            return {}

        # 搜索键的来源
        origin_results = tools.search_dict_key_origin(missing_key)
        if not origin_results:
            return {}

        top_result = origin_results[0]
        context = {
            "missing_key": missing_key,
            "fix_type": top_result.get('type', 'unknown'),
            "access_path": top_result.get('access_path', ''),
            "source_function": top_result.get('function', ''),
            "source_file": top_result.get('file', ''),
        }

        # 如果是嵌套或重构类型，添加具体的修复代码
        if top_result.get('type') in ['nested', 'restructured']:
            access_path = top_result.get('access_path', '')
            context["fix_code"] = f'config{access_path}'
            context["original_code"] = f'config["{missing_key}"]'

        return context
