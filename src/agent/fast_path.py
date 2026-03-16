"""FastPath - 快速路径修复（不需要 LLM 的快速修复逻辑）"""
import ast
import re
import logging
from pathlib import Path
from typing import Optional

from src.models.error_context import ErrorContext
from src.models.investigation_report import InvestigationReport, RelevantLocation

logger = logging.getLogger(__name__)


class FastPath:
    """快速路径：通过索引查找和 traceback 解析快速定位问题"""

    def __init__(self, project_path: Path, context_tools, error_registry, confidence_threshold: float):
        self.project_path = project_path
        self.context_tools = context_tools
        self.error_registry = error_registry
        self.confidence_threshold = confidence_threshold

    def _similar_name(self, name1: str, name2: str, threshold: float = 0.8) -> bool:
        """判断两个名称是否相似"""
        if name1 == name2:
            return True
        len_diff = abs(len(name1) - len(name2))
        if len_diff > 2:
            return False
        min_len = min(len(name1), len(name2))
        common = 0
        for i in range(min_len):
            if name1[i] == name2[i]:
                common += 1
            else:
                break
        for i in range(1, min_len - common + 1):
            if name1[-i] == name2[-i]:
                common += 1
            else:
                break
        return common / max(len(name1), len(name2)) >= threshold

    def try_fast_path(self, error: ErrorContext) -> Optional[InvestigationReport]:
        """尝试快速路径"""
        # 优化1: 直接从 traceback 提取文件路径
        traceback_report = self._try_traceback_fast_path(error)
        if traceback_report and traceback_report.confidence >= self.confidence_threshold:
            return traceback_report

        strategy = self.error_registry.get(error.error_type)
        if not strategy:
            return traceback_report

        extracted = strategy.extract(error.error_message)
        if not extracted:
            return None

        result = strategy.fast_search(extracted, self.context_tools, error.error_file)

        if result and result.confidence > self.confidence_threshold:
            logger.info(f"快速路径成功: {result.suggestion}")
            return InvestigationReport(
                summary=f"快速路径: {result.suggestion}",
                relevant_locations=[
                    RelevantLocation(
                        file_path=result.file or error.error_file,
                        line=result.line or 0,
                        symbol=result.symbol,
                        reasoning=result.suggestion
                    )
                ],
                root_cause=result.suggestion,
                suggested_fix=result.suggestion,
                confidence=result.confidence
            )

        return None

    def _try_traceback_fast_path(self, error: ErrorContext) -> Optional[InvestigationReport]:
        """从 traceback 直接提取文件路径的快速路径"""
        traceback = error.traceback or ""

        # 模式1: "cannot import name 'X' from 'module' (/path/to/file.py)"
        import_match = re.search(
            r"cannot import name ['\"](\w+)['\"] from ['\"]([\w.]+)['\"] \(([^)]+\.py)\)",
            traceback
        )
        if import_match:
            return self._handle_import_traceback(import_match, error, traceback)

        # 模式2: 从 traceback 中提取最后一个 File 路径
        file_matches = re.findall(r'File "([^"]+\.py)", line (\d+)', traceback)
        if file_matches and len(file_matches) > 1:
            last_file, last_line = file_matches[-1]
            last_file = self._normalize_traceback_path(last_file)

            return InvestigationReport(
                summary=f"错误发生在 {last_file}:{last_line}",
                relevant_locations=[
                    RelevantLocation(
                        file_path=last_file,
                        line=int(last_line),
                        symbol="unknown",
                        reasoning="错误发生位置"
                    )
                ],
                root_cause=f"错误发生在 {last_file} 第 {last_line} 行",
                suggested_fix="检查并修复该位置的代码",
                confidence=0.7
            )

        return None

    def _handle_import_traceback(self, import_match, error, traceback) -> InvestigationReport:
        """处理 ImportError 的 traceback 快速路径"""
        symbol = import_match.group(1)
        module = import_match.group(2)
        module_file_path = self._normalize_traceback_path(import_match.group(3))

        # 获取导入语句所在的文件
        file_matches = re.findall(r'File "([^"]+\.py)", line (\d+)', traceback)
        importing_file = error.error_file or "main.py"
        importing_line = 1
        if file_matches:
            importing_file = self._normalize_traceback_path(file_matches[-1][0])
            importing_line = int(file_matches[-1][1])

        # 判断是导入语句拼写错误还是定义缺失
        fix_target, fix_reason = self._analyze_import_error(
            symbol, module, module_file_path, importing_file
        )

        return InvestigationReport(
            summary=f"ImportError: 无法从 {module} 导入 {symbol}，{fix_reason}",
            relevant_locations=[
                RelevantLocation(
                    file_path=fix_target,
                    line=importing_line if fix_target == importing_file else 1,
                    symbol=symbol,
                    reasoning=fix_reason
                ),
                RelevantLocation(
                    file_path=module_file_path if fix_target == importing_file else importing_file,
                    line=1 if fix_target == importing_file else importing_line,
                    symbol=symbol,
                    reasoning="上下文文件"
                )
            ],
            root_cause=fix_reason,
            suggested_fix=f"修复 {fix_target} 中的拼写错误",
            confidence=0.95
        )

    def _analyze_import_error(self, symbol, module, module_file_path, importing_file):
        """分析 ImportError 的具体原因"""
        try:
            module_full_path = self.project_path / module_file_path
            if module_full_path.exists():
                module_content = module_full_path.read_text(encoding='utf-8')
                try:
                    tree = ast.parse(module_content)
                    defined_names = set()
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            defined_names.add(node.name)
                        elif isinstance(node, ast.ClassDef):
                            defined_names.add(node.name)
                        elif isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name):
                                    defined_names.add(target.id)
                        elif isinstance(node, ast.ImportFrom):
                            for alias in node.names:
                                name = alias.asname if alias.asname else alias.name
                                if name != '*':
                                    defined_names.add(name)

                    if symbol in defined_names:
                        return module_file_path, f"模块 {module} 中已存在 {symbol}，可能存在其他问题"
                    elif any(self._similar_name(symbol, name) for name in defined_names):
                        similar = next(name for name in defined_names if self._similar_name(symbol, name))
                        return importing_file, f"模块 {module} 中存在 {similar}，导入语句中的 {symbol} 可能是拼写错误"
                    else:
                        return module_file_path, f"模块 {module} 中缺少 {symbol} 的定义"
                except Exception:
                    return importing_file, "无法解析模块，默认修复导入语句"
            else:
                return importing_file, "模块文件不存在，修复导入语句"
        except Exception:
            return importing_file, "检查失败，默认修复导入语句"

    def _normalize_traceback_path(self, file_path: str) -> str:
        """将 traceback 中的路径转换为相对路径"""
        if file_path.startswith('/workspace/'):
            return file_path[len('/workspace/'):]
        if self.project_path:
            try:
                return str(Path(file_path).relative_to(self.project_path))
            except ValueError:
                return Path(file_path).name
        return file_path
