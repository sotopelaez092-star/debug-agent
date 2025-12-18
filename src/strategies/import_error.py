"""ImportError 和 ModuleNotFoundError 处理策略"""
import re
from typing import Optional
from .base import BaseErrorStrategy
from src.models.results import SearchResult


def _levenshtein_distance(s1: str, s2: str) -> int:
    """计算两个字符串的编辑距离"""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
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


class ImportErrorStrategy(BaseErrorStrategy):
    """ImportError/ModuleNotFoundError 策略：处理模块导入错误"""

    def __init__(self, confidence_threshold: float = 0.7):
        # 降低默认阈值，允许更多模糊匹配（模块拼写错误很常见）
        super().__init__(confidence_threshold)

    @property
    def error_type(self) -> str:
        return "ImportError"

    def extract(self, error_message: str) -> dict:
        """提取模块名"""
        # ModuleNotFoundError: No module named 'xxx'
        match = re.search(r"No module named ['\"]?([\w.]+)['\"]?", error_message)
        if match:
            return {"module": match.group(1)}

        # ImportError: cannot import name 'xxx'
        match = re.search(r"cannot import name ['\"](\w+)['\"]", error_message)
        if match:
            return {"symbol": match.group(1)}

        return {}

    def fast_search(self, extracted: dict, tools, error_file: str = "") -> Optional[SearchResult]:
        """快速搜索模块或符号"""
        # 模块路径错误
        if "module" in extracted:
            module = extracted["module"]
            matches = tools.search_module(module, fuzzy=True)

            # 额外：如果基础搜索置信度不高，尝试用 Levenshtein 提升拼写错误的置信度
            if matches and matches[0]['confidence'] < 0.8:
                top_match = matches[0]
                # 提取模块名的最后一部分进行比较
                query_name = module.split('.')[-1].lower()
                found_name = top_match['module'].split('.')[-1].lower()

                # 计算编辑距离相似度
                dist = _levenshtein_distance(query_name, found_name)
                max_len = max(len(query_name), len(found_name))
                if max_len > 0:
                    lev_similarity = 1 - (dist / max_len)
                    # 如果 Levenshtein 相似度更高，使用它
                    if lev_similarity > top_match['confidence']:
                        matches[0] = dict(top_match)  # 复制以避免修改原对象
                        matches[0]['confidence'] = min(0.95, lev_similarity)  # 上限 95%
                        matches[0]['refactor_type'] = 'typo'
                        matches[0]['suggestion'] = f"模块名 '{module}' 可能是 '{top_match['module']}' 的拼写错误"

            # 使用可配置的阈值（>=，而不是 >）
            if matches and matches[0]['confidence'] >= self.confidence_threshold:
                top_match = matches[0]
                # 关键：修复的是 import 语句所在的文件（error_file），不是模块文件本身
                # 例如：main.py 中的 "from services.authentification" 需要改成 "from services.authentication"

                # 根据匹配类型生成合适的建议
                refactor_type = top_match.get('refactor_type', 'typo')
                if refactor_type == 'intermediate_missing':
                    # 缺少中间包层级
                    suggestion = top_match.get('suggestion', f"模块路径错误，正确路径: {top_match['module']}")
                elif refactor_type == 'prefix_added':
                    # 模块被移动到新包下
                    suggestion = top_match.get('suggestion', f"模块已移动，正确路径: {top_match['module']}")
                else:
                    # 默认：拼写错误
                    suggestion = f"模块 '{module}' 可能是 '{top_match['module']}' 的拼写错误，需要修复 import 语句"

                return SearchResult(
                    symbol=top_match['module'],
                    file=error_file or "main.py",  # 修复 import 语句所在的文件
                    confidence=top_match['confidence'],
                    suggestion=suggestion
                )

        # 符号导入错误
        if "symbol" in extracted:
            symbol = extracted["symbol"]
            matches = tools.search_symbol(symbol, fuzzy=True, error_file=error_file)
            # 使用可配置的阈值（>=，而不是 >）
            if matches and matches[0].confidence >= self.confidence_threshold:
                top_match = matches[0]
                return SearchResult(
                    symbol=top_match.name,
                    file=top_match.file,
                    line=top_match.line,
                    confidence=top_match.confidence,
                    suggestion=f"无法导入 '{symbol}'，可能是 '{top_match.name}' 的拼写错误\n位置: {top_match.file}:{top_match.line}"
                )

        return None
