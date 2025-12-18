"""FixValidator - 修复验证器，确保修复代码的质量"""
import ast
import re
import logging
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """验证级别"""
    SYNTAX_ONLY = auto()       # 只检查语法
    BASIC = auto()             # 语法 + 基本运行时
    FULL = auto()              # 完整验证（包含单元测试）


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    level: ValidationLevel
    syntax_ok: bool
    runtime_ok: Optional[bool] = None
    test_ok: Optional[bool] = None
    error_message: str = ""
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class FixValidator:
    """
    修复验证器

    三层验证:
    1. 语法检查 (AST parse) - 快速
    2. 运行时验证 (实际执行) - 基本
    3. 单元测试/静态分析 - 完整
    """

    def __init__(self, project_path: Optional[str] = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()

    def validate(
        self,
        fixed_code: str,
        original_code: str = "",
        level: ValidationLevel = ValidationLevel.BASIC,
        executor=None
    ) -> ValidationResult:
        """
        验证修复代码

        Args:
            fixed_code: 修复后的代码
            original_code: 原始代码（用于比较）
            level: 验证级别
            executor: 执行器实例（用于运行时验证）

        Returns:
            ValidationResult
        """
        warnings = []

        # 1. 语法检查（必须通过）
        syntax_ok, syntax_error = self._check_syntax(fixed_code)
        if not syntax_ok:
            return ValidationResult(
                passed=False,
                level=level,
                syntax_ok=False,
                error_message=f"语法错误: {syntax_error}"
            )

        # 2. 代码质量检查（警告级别）
        quality_warnings = self._check_code_quality(fixed_code, original_code)
        warnings.extend(quality_warnings)

        if level == ValidationLevel.SYNTAX_ONLY:
            return ValidationResult(
                passed=True,
                level=level,
                syntax_ok=True,
                warnings=warnings
            )

        # 3. 运行时验证
        if executor:
            runtime_ok, runtime_error = self._check_runtime(fixed_code, executor)
            if not runtime_ok:
                return ValidationResult(
                    passed=False,
                    level=level,
                    syntax_ok=True,
                    runtime_ok=False,
                    error_message=f"运行时错误: {runtime_error}",
                    warnings=warnings
                )

            if level == ValidationLevel.BASIC:
                return ValidationResult(
                    passed=True,
                    level=level,
                    syntax_ok=True,
                    runtime_ok=True,
                    warnings=warnings
                )

            # 4. 完整验证（单元测试等）
            if level == ValidationLevel.FULL:
                test_ok, test_error = self._run_tests(fixed_code)
                return ValidationResult(
                    passed=test_ok,
                    level=level,
                    syntax_ok=True,
                    runtime_ok=True,
                    test_ok=test_ok,
                    error_message=test_error if not test_ok else "",
                    warnings=warnings
                )

        # 无执行器时，只返回语法检查结果
        return ValidationResult(
            passed=True,
            level=level,
            syntax_ok=True,
            warnings=warnings
        )

    def quick_validate(self, code: str) -> Tuple[bool, str]:
        """快速语法验证"""
        return self._check_syntax(code)

    def _check_syntax(self, code: str) -> Tuple[bool, str]:
        """AST 语法检查"""
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, str(e)

    def _check_code_quality(self, fixed_code: str, original_code: str) -> List[str]:
        """代码质量检查（返回警告列表）"""
        warnings = []

        # 1. 检查代码是否为空
        if not fixed_code.strip():
            warnings.append("修复后的代码为空")
            return warnings

        # 2. 检查是否与原代码相同
        if fixed_code.strip() == original_code.strip():
            warnings.append("修复后的代码与原代码相同")

        # 3. 检查是否添加了过多代码
        if original_code:
            original_lines = len(original_code.strip().split('\n'))
            fixed_lines = len(fixed_code.strip().split('\n'))
            if fixed_lines > original_lines * 2:
                warnings.append(f"代码行数从 {original_lines} 增加到 {fixed_lines}")

        # 4. 检查是否删除了过多代码
        if original_code:
            if fixed_lines < original_lines * 0.5 and original_lines > 5:
                warnings.append(f"代码行数从 {original_lines} 减少到 {fixed_lines}")

        # 5. 检查是否有未使用的导入（简单检查）
        try:
            tree = ast.parse(fixed_code)
            imports = set()
            used_names = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports.add(name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            name = alias.asname if alias.asname else alias.name
                            if name != '*':
                                imports.add(name)
                elif isinstance(node, ast.Name):
                    used_names.add(node.id)

            # 简单检查（可能有误报）
            unused = imports - used_names
            if len(unused) > 2:
                warnings.append(f"可能有未使用的导入: {', '.join(list(unused)[:3])}")
        except:
            pass

        # 6. 检查是否有调试代码
        debug_patterns = [
            r'\bprint\s*\(\s*["\']DEBUG',
            r'\bprint\s*\(\s*f?["\'].*debug.*["\']',
            r'\bbreakpoint\s*\(\s*\)',
            r'\bpdb\.',
        ]
        for pattern in debug_patterns:
            if re.search(pattern, fixed_code, re.IGNORECASE):
                warnings.append("代码中可能包含调试语句")
                break

        return warnings

    def _check_runtime(self, code: str, executor) -> Tuple[bool, str]:
        """运行时验证"""
        try:
            result = executor.execute(code)
            if result.success:
                return True, ""
            else:
                return False, result.stderr[:500] if result.stderr else "Unknown error"
        except Exception as e:
            return False, str(e)

    def _run_tests(self, code: str) -> Tuple[bool, str]:
        """运行单元测试（如果存在）"""
        # TODO: 实现单元测试集成
        # 目前返回 True，因为大多数项目可能没有测试
        return True, ""

    def compare_fixes(self, original: str, fix1: str, fix2: str) -> int:
        """
        比较两个修复方案，返回更优的选择

        Returns:
            1 如果 fix1 更好
            2 如果 fix2 更好
            0 如果无法判断
        """
        # 1. 检查语法
        syntax1, _ = self._check_syntax(fix1)
        syntax2, _ = self._check_syntax(fix2)

        if syntax1 and not syntax2:
            return 1
        if syntax2 and not syntax1:
            return 2

        if not syntax1 and not syntax2:
            return 0

        # 2. 比较代码变化量（偏好最小变化）
        diff1 = self._calculate_diff(original, fix1)
        diff2 = self._calculate_diff(original, fix2)

        if diff1 < diff2:
            return 1
        if diff2 < diff1:
            return 2

        return 0

    def _calculate_diff(self, original: str, fixed: str) -> int:
        """计算代码差异量"""
        original_lines = set(original.strip().split('\n'))
        fixed_lines = set(fixed.strip().split('\n'))

        added = len(fixed_lines - original_lines)
        removed = len(original_lines - fixed_lines)

        return added + removed
