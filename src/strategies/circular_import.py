"""循环导入处理策略 - 增强版，支持具体修复建议"""
import re
import ast
from typing import Optional, List, Dict, Set
from pathlib import Path
from .base import BaseErrorStrategy
from src.models.results import SearchResult


class CircularImportStrategy(BaseErrorStrategy):
    """CircularImport 策略：检测循环导入并提供具体修复建议"""

    # 解决方案模板
    SOLUTION_TEMPLATES = {
        'type_checking': {
            'description': '使用 TYPE_CHECKING 延迟类型导入',
            'priority': 1,  # 最优先
            'template': '''from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from {module} import {symbol}'''
        },
        'late_import': {
            'description': '在函数内部延迟导入',
            'priority': 2,
            'template': '''def {function}(...):
    from {module} import {symbol}  # 延迟导入
    ...'''
        },
        'string_annotation': {
            'description': '使用字符串类型注解',
            'priority': 3,
            'template': '''def __init__(self, factory: "{symbol}", ...):  # 字符串注解
    ...'''
        }
    }

    def __init__(self, confidence_threshold: float = 0.9):
        # 循环导入检测需要高置信度，避免误报
        super().__init__(confidence_threshold)

    @property
    def error_type(self) -> str:
        return "CircularImport"

    def extract(self, error_message: str) -> dict:
        """提取循环导入相关信息"""
        result = {}

        # ImportError: cannot import name 'X' from partially initialized module 'Y'
        if "partially initialized module" in error_message.lower():
            match = re.search(r"cannot import name '(\w+)' from partially initialized module '([\w.]+)'", error_message)
            if match:
                result["symbol"] = match.group(1)
                result["module"] = match.group(2)
                result["circular"] = True
                return result

            match = re.search(r"from partially initialized module '([\w.]+)'", error_message)
            if match:
                result["module"] = match.group(1)
                result["circular"] = True
                return result

        # 一般的循环导入错误
        if "circular import" in error_message.lower():
            result["circular"] = True
            return result

        # cannot import name (可能是循环导入)
        if "cannot import name" in error_message:
            match = re.search(r"cannot import name '(\w+)'", error_message)
            if match:
                result["symbol"] = match.group(1)
                result["possible_circular"] = True

            # 尝试提取模块名
            match = re.search(r"from '([\w.]+)'", error_message)
            if match:
                result["module"] = match.group(1)

        return result

    def fast_search(self, extracted: dict, tools, error_file: str = "") -> Optional[SearchResult]:
        """检测循环导入并提供具体修复建议"""
        if not extracted.get("circular") and not extracted.get("possible_circular"):
            return None

        # 检测循环导入
        cycles = tools.detect_circular_imports()

        if cycles:
            # 分析循环并生成具体修复建议
            fix_suggestions = self._analyze_cycles_and_suggest_fixes(
                cycles, extracted, tools, error_file
            )

            suggestion = "检测到循环导入:\n"
            for i, cycle in enumerate(cycles[:3], 1):
                cycle_path = " → ".join(cycle)
                suggestion += f"  循环 {i}: {cycle_path}\n"

            if len(cycles) > 3:
                suggestion += f"  ... 以及其他 {len(cycles) - 3} 个循环\n"

            suggestion += "\n" + fix_suggestions

            return SearchResult(
                symbol=extracted.get("symbol", "circular_import"),
                file=error_file,
                confidence=0.95,
                suggestion=suggestion
            )

        # 如果没有检测到循环但可能存在
        if extracted.get("possible_circular"):
            # 尝试提供基于符号的建议
            symbol = extracted.get("symbol", "")
            module = extracted.get("module", "")

            if symbol and module:
                suggestion = self._generate_type_checking_suggestion(module, symbol)
            else:
                suggestion = "可能存在循环导入，建议:\n"
                suggestion += "1. 使用 TYPE_CHECKING 延迟类型导入\n"
                suggestion += "2. 将导入移到函数内部\n"
                suggestion += "3. 重构代码以消除循环依赖"

            return SearchResult(
                symbol=symbol or "possible_circular_import",
                file=error_file,
                confidence=0.6,
                suggestion=suggestion
            )

        return None

    def _analyze_cycles_and_suggest_fixes(
        self, cycles: List[List[str]], extracted: dict,
        tools, error_file: str
    ) -> str:
        """分析循环导入并生成具体修复建议"""
        symbol = extracted.get("symbol", "")
        module = extracted.get("module", "")

        suggestions = []

        # 如果有明确的符号和模块，分析导入用途
        if symbol and error_file:
            usage_type = self._analyze_import_usage(error_file, symbol, tools)

            if usage_type == "type_hint_only":
                suggestions.append("【推荐方案】使用 TYPE_CHECKING:\n")
                suggestions.append(self._generate_type_checking_suggestion(module, symbol))
            elif usage_type == "runtime":
                suggestions.append("【推荐方案】延迟导入（函数内部）:\n")
                suggestions.append(f"  将 'from {module} import {symbol}' 移到使用它的函数内部")
            else:
                # 默认建议
                suggestions.append("【修复建议】:\n")
                suggestions.append(self._generate_type_checking_suggestion(module, symbol))
        else:
            # 通用建议
            suggestions.append("【修复建议】:\n")
            suggestions.append("方案 1: 使用 TYPE_CHECKING (推荐用于类型注解)\n")
            suggestions.append("  from typing import TYPE_CHECKING\n")
            suggestions.append("  if TYPE_CHECKING:\n")
            suggestions.append("      from module import Class\n\n")
            suggestions.append("方案 2: 延迟导入 (用于运行时需要)\n")
            suggestions.append("  def function():\n")
            suggestions.append("      from module import Class  # 移到函数内\n")

        return "".join(suggestions)

    def _analyze_import_usage(self, file_path: str, symbol: str, tools) -> str:
        """分析符号在文件中的使用方式"""
        try:
            # 读取文件
            full_path = tools.project_path / file_path
            if not full_path.exists():
                return "unknown"

            content = full_path.read_text(encoding='utf-8')
            tree = ast.parse(content)

            has_type_hint = False
            has_runtime_use = False

            for node in ast.walk(tree):
                # 检查类型注解
                if isinstance(node, ast.AnnAssign) and node.annotation:
                    if self._contains_name(node.annotation, symbol):
                        has_type_hint = True

                # 检查函数参数和返回类型注解
                if isinstance(node, ast.FunctionDef):
                    for arg in node.args.args:
                        if arg.annotation and self._contains_name(arg.annotation, symbol):
                            has_type_hint = True
                    if node.returns and self._contains_name(node.returns, symbol):
                        has_type_hint = True

                # 检查运行时调用
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == symbol:
                        has_runtime_use = True
                    elif isinstance(node.func, ast.Attribute) and node.func.attr == symbol:
                        has_runtime_use = True

                # 检查 isinstance
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == "isinstance":
                        if len(node.args) >= 2 and self._contains_name(node.args[1], symbol):
                            has_runtime_use = True

            if has_type_hint and not has_runtime_use:
                return "type_hint_only"
            elif has_runtime_use:
                return "runtime"
            else:
                return "unknown"

        except Exception:
            return "unknown"

    def _contains_name(self, node, name: str) -> bool:
        """检查 AST 节点是否包含指定名称"""
        if isinstance(node, ast.Name):
            return node.id == name
        elif isinstance(node, ast.Subscript):
            return self._contains_name(node.value, name) or self._contains_name(node.slice, name)
        elif isinstance(node, ast.Attribute):
            return node.attr == name
        elif isinstance(node, ast.Tuple):
            return any(self._contains_name(elt, name) for elt in node.elts)
        return False

    def _generate_type_checking_suggestion(self, module: str, symbol: str) -> str:
        """生成 TYPE_CHECKING 方案的代码示例"""
        return f'''  from typing import TYPE_CHECKING
  if TYPE_CHECKING:
      from {module} import {symbol}

  # 然后在类型注解中使用字符串形式:
  def __init__(self, param: "{symbol}"):
      ...
'''

    def get_fix_context(self, extracted: dict, tools, error_file: str = "") -> dict:
        """获取循环导入的修复上下文，包含具体的修复代码"""
        symbol = extracted.get("symbol", "")
        module = extracted.get("module", "")

        if not symbol or not module:
            return {}

        context = {
            "circular_import": True,
            "symbol": symbol,
            "module": module,
            "error_file": error_file,
        }

        # 分析导入用途
        if error_file:
            usage_type = self._analyze_import_usage(error_file, symbol, tools)
            context["usage_type"] = usage_type

            if usage_type == "type_hint_only":
                # 生成 TYPE_CHECKING 修复代码
                context["fix_strategy"] = "TYPE_CHECKING"
                context["fix_instructions"] = [
                    f"1. 移除顶层的 'from {module} import {symbol}' 导入",
                    f"2. 添加 'from typing import TYPE_CHECKING'",
                    f"3. 在 'if TYPE_CHECKING:' 块中添加 'from {module} import {symbol}'",
                    f"4. 将所有 '{symbol}' 类型注解改为字符串形式 '\"{symbol}\"'"
                ]
                context["fix_code_template"] = f'''from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from {module} import {symbol}

# 使用字符串注解:
def __init__(self, factory: "{symbol}", ...):
    ...'''
            else:
                # 延迟导入方案
                context["fix_strategy"] = "late_import"
                context["fix_instructions"] = [
                    f"1. 移除顶层的 'from {module} import {symbol}' 导入",
                    f"2. 在需要使用 {symbol} 的函数内部添加导入语句"
                ]
                context["fix_code_template"] = f'''def some_method(self):
    from {module} import {symbol}  # 延迟导入
    return {symbol}(...)'''

        return context
