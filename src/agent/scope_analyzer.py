"""ScopeAnalyzer - 判断错误范围（单文件 vs 跨文件）"""
import ast
import re
import logging
from pathlib import Path
from typing import Optional

from src.models.error_context import ErrorContext

logger = logging.getLogger(__name__)


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


# 常见标准库模块列表
STDLIB_MODULES = {
    'math', 'os', 'sys', 'json', 're', 'time', 'datetime', 'random',
    'collections', 'itertools', 'functools', 'typing', 'pathlib',
    'subprocess', 'threading', 'multiprocessing', 'asyncio', 'socket',
    'http', 'urllib', 'email', 'html', 'xml', 'logging', 'unittest',
    'copy', 'pickle', 'sqlite3', 'csv', 'io', 'string', 'textwrap',
    'struct', 'hashlib', 'hmac', 'secrets', 'base64', 'binascii',
    'operator', 'contextlib', 'abc', 'dataclasses', 'enum', 'heapq',
    'bisect', 'array', 'weakref', 'types', 'pprint', 'reprlib',
    'calendar', 'locale', 'gettext', 'argparse', 'optparse', 'shutil',
    'tempfile', 'glob', 'fnmatch', 'linecache', 'tokenize', 'keyword',
    'traceback', 'warnings', 'inspect', 'importlib', 'zipfile', 'tarfile',
    'gzip', 'bz2', 'lzma', 'zlib', 'platform', 'ctypes', 'concurrent'
}


class ScopeAnalyzer:
    """分析错误范围：单文件 or 跨文件"""

    def __init__(self, project_path: Path, context_tools):
        self.project_path = project_path
        self.context_tools = context_tools

    def is_cross_file(self, error: ErrorContext, code: str) -> bool:
        """判断是否跨文件错误"""
        try:
            if error.error_type in ["ImportError", "ModuleNotFoundError"]:
                result = self._check_import_error(error, code)
                if result is not None:
                    return result

            if error.error_type == "AttributeError":
                result = self._check_attribute_error(error, code)
                if result is not None:
                    return result

            return self._check_symbol_scope(error, code)

        except SyntaxError:
            logger.warning("代码解析失败，假定为单文件错误")
            return False

    def extract_symbol(self, error: ErrorContext) -> str:
        """从错误中提取符号名"""
        patterns = [
            r"name '(\w+)'",
            r"module named '([\w.]+)'",
            r"attribute '(\w+)'",
            r"'(\w+)' is not defined",
        ]
        for pattern in patterns:
            match = re.search(pattern, error.error_message)
            if match:
                return match.group(1)
        return "unknown"

    def _check_import_error(self, error: ErrorContext, code: str) -> Optional[bool]:
        """检查 ImportError 的范围"""
        # 动态导入检查
        if 'importlib.import_module' in code or 'import_module(' in code:
            module_match = re.search(r"No module named ['\"]?([\w.]+)['\"]?", error.error_message)
            if module_match:
                missing_module = module_match.group(1)
                if f'"{missing_module}"' in code or f"'{missing_module}'" in code:
                    return False

        module_match = re.search(r"No module named ['\"]?([\w.]+)['\"]?", error.error_message)
        if module_match:
            full_module = module_match.group(1)
            missing_module = full_module.split('.')[0]

            # 多级模块路径
            if '.' in full_module:
                return True

            # 标准库拼写错误
            for stdlib in STDLIB_MODULES:
                dist = _levenshtein_distance(missing_module, stdlib)
                max_len = max(len(missing_module), len(stdlib))
                if max_len > 0 and dist / max_len < 0.4:
                    return False

            # 项目中相似模块
            try:
                results = self.context_tools.search_module(missing_module, fuzzy=True)
                if results and results[0]['confidence'] > 0.7:
                    return True
            except Exception:
                pass

            # 同名目录
            try:
                module_dir = self.project_path / missing_module
                if module_dir.is_dir():
                    return True
            except Exception:
                pass

            return True

        return None

    def _check_attribute_error(self, error: ErrorContext, code: str) -> Optional[bool]:
        """检查 AttributeError 的范围"""
        traceback = error.traceback or ""
        file_matches = re.findall(r'File "([^"]+\.py)", line (\d+)', traceback)
        if len(file_matches) >= 2:
            error_file = file_matches[-1][0]
            error_basename = Path(error_file).name
            if error_basename != "main.py" and error_basename.endswith('.py'):
                return True

        if "module '" in error.error_message and "' has no attribute" in error.error_message:
            return False

        builtin_types = ["'str'", "'int'", "'float'", "'list'", "'dict'"]
        if any(t in error.error_message for t in builtin_types):
            return False

        class_match = re.search(r"'(\w+)' object has no attribute", error.error_message)
        if class_match:
            class_name = class_match.group(1)
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    return False
            return True

        return None

    def _check_symbol_scope(self, error: ErrorContext, code: str) -> bool:
        """检查符号是否在当前文件作用域内"""
        symbol = self.extract_symbol(error)
        if not symbol or symbol == "unknown":
            return False

        tree = ast.parse(code)
        local_symbols = set()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                local_symbols.add(node.name)
                if isinstance(node, ast.FunctionDef):
                    for arg in node.args.args:
                        local_symbols.add(arg.arg)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        local_symbols.add(target.id)

        if symbol in local_symbols:
            return False

        if error.error_type == "NameError":
            traceback = error.traceback or ""
            file_matches = re.findall(r'File "([^"]+\.py)", line (\d+)', traceback)
            if len(file_matches) >= 2:
                error_file = file_matches[-1][0]
                error_basename = Path(error_file).name
                if error_basename != "main.py" and error_basename.endswith('.py'):
                    return True

            for local_sym in local_symbols:
                dist = _levenshtein_distance(symbol, local_sym)
                max_len = max(len(symbol), len(local_sym))
                if max_len > 0 and dist / max_len < 0.3:
                    return False

            try:
                results = self.context_tools.search_symbol(symbol, fuzzy=False)
                if not results or (results and results[0]['confidence'] < 0.5):
                    return False
            except Exception:
                pass

        return True
