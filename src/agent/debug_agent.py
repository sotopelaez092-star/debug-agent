"""DebugAgent - 主调试代理"""
import ast
import re
import logging
from pathlib import Path
from typing import Optional

from src.models.error_context import ErrorContext
from src.models.investigation_report import InvestigationReport, RelevantLocation
from src.models.results import DebugResult, FixResult, ExecutionResult
from src.tools.context_tools import ContextTools
from src.strategies.registry import ErrorStrategyRegistry
from src.agent.investigator import CodebaseInvestigator
from src.agent.retry_strategy import SmartRetryStrategy
from src.agent.scope_analyzer import ScopeAnalyzer
from src.agent.fast_path import FastPath
from src.utils.llm_client import LLMClient

from src.core import ErrorIdentifier, CodeFixer, LocalExecutor
from src.core import LoopDetector, LoopAction, FixValidator, ValidationLevel
from src.utils.progress_logger import get_progress_logger
from src.utils.structured_logger import get_structured_logger, DebugPhase, FixMethod

logger = logging.getLogger(__name__)
progress = get_progress_logger()
slog = get_structured_logger()


class DebugAgent:
    """
    主调试代理 - 双路径设计

    Fast Path: 快速路径（置信度 > 0.7）
    Full Investigation: 完整探索（CodebaseInvestigator）
    """

    def __init__(
        self,
        project_path: str,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        confidence_threshold: float = 0.7
    ):
        self.project_path = Path(project_path).resolve()
        self.confidence_threshold = confidence_threshold

        # 核心组件
        self.context_tools = ContextTools(str(self.project_path))
        self.error_identifier = ErrorIdentifier()
        self.code_fixer = CodeFixer(api_key=api_key, model=model)
        self.executor = LocalExecutor(project_path=str(self.project_path))

        # 错误策略
        self.error_registry = ErrorStrategyRegistry()
        self.error_registry.register_all_defaults(confidence_threshold)

        # LLM 客户端和调查员
        self.llm = LLMClient(api_key=api_key, model=model)
        self.investigator = CodebaseInvestigator(self.llm, self.context_tools)

        # 重试和循环检测
        self.retry_strategy = SmartRetryStrategy(max_same_approach=2)
        self.loop_detector = LoopDetector()
        self.fix_validator = FixValidator(project_path=str(self.project_path))

        # 拆分出的分析器
        self.scope_analyzer = ScopeAnalyzer(self.project_path, self.context_tools)
        self.fast_path = FastPath(
            self.project_path, self.context_tools,
            self.error_registry, confidence_threshold
        )

    async def debug(
        self,
        buggy_code: str,
        error_traceback: str,
        error_file: str = "",
        max_retries: int = 3
    ) -> DebugResult:
        """主调试入口 - 双路径调试流程"""
        if not buggy_code or not isinstance(buggy_code, str):
            raise ValueError(f"buggy_code 必须是非空字符串，得到: {type(buggy_code).__name__}")
        if not error_traceback or not isinstance(error_traceback, str):
            raise ValueError(f"error_traceback 必须是非空字符串，得到: {type(error_traceback).__name__}")

        slog.start_session()

        try:
            # Phase 1: 错误识别
            slog.start_phase(DebugPhase.ERROR_PARSE)
            progress.step(1, 5, "识别错误类型", "📋")
            error = self.error_identifier.identify(error_traceback)
            if error_file:
                error.error_file = error_file
            progress.success(f"检测到: {error.error_type}")
            slog.set_error_info(error.error_type, error.error_message, error.error_file)
            slog.end_phase(success=True, error_type=error.error_type)

            # Phase 2: 范围检测
            slog.start_phase(DebugPhase.SCOPE_DETECT)
            progress.step(2, 5, "分析错误范围", "🔍")
            is_cross_file = self.scope_analyzer.is_cross_file(error, buggy_code)
            progress.success('跨文件错误（需要调查项目结构）' if is_cross_file else '单文件错误（快速修复）')
            slog.set_cross_file(is_cross_file)
            slog.end_phase(success=True, is_cross_file=is_cross_file)

            if not is_cross_file:
                progress.step(3, 5, "快速修复模式", "⚡")
                slog.set_fix_method(FixMethod.LLM_CALL)
                result = await self._fix_single_file(buggy_code, error, max_retries=3)
                if result.success:
                    self.code_fixer.save_token_stats()
                    slog.end_session(success=True)
                    return result
                progress.warning("单文件修复失败，回退到跨文件调查模式...")
                is_cross_file = True

            # Phase 3: 调查阶段
            slog.start_phase(DebugPhase.INVESTIGATION)
            progress.step(3, 5, "尝试快速路径（索引查找）", "⚡")
            report = self.fast_path.try_fast_path(error)

            if not report or report.confidence < self.confidence_threshold:
                progress.step(4, 5, "LLM 完整调查（可能需要 30-60 秒）", "🤖")
                report = await self.investigator.investigate(error)
                progress.success(f"调查完成（置信度: {report.confidence:.0%})")
                slog.set_fix_method(FixMethod.LLM_CALL)
            else:
                progress.success(f"快速路径成功（置信度: {report.confidence:.0%})")
                slog.set_fix_method(FixMethod.TRACEBACK_FAST)
            slog.end_phase(success=True, confidence=report.confidence)

            # Phase 4: 修复阶段
            slog.start_phase(DebugPhase.CODE_FIX)
            progress.step(5, 5, "生成并验证修复", "🔧")

            result = await self._retry_fix_loop(buggy_code, error, report, max_retries)

            self.code_fixer.save_token_stats()
            slog.end_phase(success=result.success, attempts=result.attempts)
            slog.end_session(success=result.success)
            return result

        except (ValueError, RuntimeError):
            slog.end_session(success=False)
            raise
        except Exception as e:
            slog.end_session(success=False)
            raise RuntimeError(f"调试过程失败: {e}") from e
        finally:
            try:
                self.code_fixer.save_token_stats()
            except Exception:
                pass

    async def _retry_fix_loop(
        self, code: str, error: ErrorContext,
        report: InvestigationReport, max_retries: int
    ) -> DebugResult:
        """带重试和循环检测的修复循环"""
        current_error = error
        current_report = report
        accumulated_files = {}
        force_llm = False

        for attempt in range(max_retries):
            slog.increment_attempt()

            # 循环检测
            loop_check = self.loop_detector.check_loop()
            if loop_check.action == LoopAction.ABORT:
                progress.warning(f"检测到循环: {loop_check.reason}")
                break
            elif loop_check.action in [LoopAction.ESCALATE, LoopAction.SWITCH_STRATEGY]:
                force_llm = True

            progress.progress(f"尝试 {attempt + 1}/{max_retries}: 生成修复代码...")

            fix_result = await self._fix_with_report(
                code, current_error, current_report, accumulated_files, force_llm=force_llm
            )

            if fix_result.related_files:
                accumulated_files.update(fix_result.related_files)

            # 验证修复
            progress.progress(f"尝试 {attempt + 1}/{max_retries}: 本地验证中...")
            verify_file = current_error.error_file if current_error.error_file and current_error.error_file != "main.py" else "main.py"
            if fix_result.target_file:
                verify_file = fix_result.target_file
            exec_result = await self._verify_fix(fix_result, verify_file)

            if exec_result.success:
                self._record_attempt(fix_result, current_error, force_llm, success=True)
                all_files = {**accumulated_files, **(fix_result.related_files or {})}
                return DebugResult(
                    success=True,
                    original_error=error.dict(),
                    fixed_code=fix_result.fixed_code,
                    explanation=fix_result.explanation,
                    attempts=attempt + 1,
                    investigation_summary=current_report.summary,
                    related_files=all_files
                )
            else:
                self._record_attempt(fix_result, current_error, force_llm, success=False,
                                     stderr=exec_result.stderr)

                if fix_result.used_pattern_fixer:
                    force_llm = True

                # 检查是否是新错误
                if exec_result.stderr:
                    current_error, current_report = self._check_new_error(
                        exec_result.stderr, current_error, current_report
                    )

        # 所有尝试均失败
        all_files = {**accumulated_files, **(fix_result.related_files or {})}
        return DebugResult(
            success=False,
            original_error=error.dict(),
            fixed_code=fix_result.fixed_code,
            explanation=f"修复失败，已尝试 {max_retries} 次",
            attempts=max_retries,
            investigation_summary=current_report.summary,
            related_files=all_files
        )

    def _record_attempt(self, fix_result, error, force_llm, success, stderr=""):
        """记录修复尝试结果"""
        self.loop_detector.record_attempt(
            fixed_code=fix_result.fixed_code,
            error_type=error.error_type,
            error_message=stderr[:200] if stderr else error.error_message,
            layer=3 if force_llm else 1,
            success=success
        )
        approach = "pattern_fix" if fix_result.used_pattern_fixer else "llm_fix"
        self.retry_strategy.record_attempt(
            error_type=error.error_type,
            approach=approach,
            fix_content=fix_result.fixed_code,
            success=success,
            error_message=stderr[:200] if stderr else ""
        )

    def _check_new_error(self, stderr, current_error, current_report):
        """检查验证失败后是否出现了新错误"""
        try:
            new_error = self.error_identifier.identify(stderr)
            if new_error.error_file != current_error.error_file:
                self.retry_strategy.reset()
                self.loop_detector.reset()
                new_report = self.fast_path.try_fast_path(new_error)
                if new_report:
                    return new_error, new_report
                return new_error, current_report
        except Exception:
            pass
        return current_error, current_report

    async def _fix_single_file(self, code: str, error: ErrorContext, max_retries: int) -> DebugResult:
        """单文件修复流程"""
        related_files = {}
        if error.error_type in ["ImportError", "ModuleNotFoundError"]:
            progress.progress("检测到导入错误，查找相关模块...")
            try:
                match = re.search(r"No module named ['\"]?([\w.]+)['\"]?", error.error_message)
                if match:
                    module_name = match.group(1)
                    module_results = self.context_tools.search_module(module_name, fuzzy=True)
                    if module_results and module_results[0]['confidence'] > 0.7:
                        file_path = self.project_path / module_results[0]['file']
                        if file_path.exists():
                            related_files[module_results[0]['file']] = file_path.read_text(encoding='utf-8')
            except Exception:
                pass

        current_code = code
        current_error = error
        force_llm = False

        for attempt in range(max_retries):
            progress.progress(f"尝试 {attempt + 1}/{max_retries}: 生成修复代码...")

            fix_result = await self.code_fixer.fix_code(
                buggy_code=current_code,
                error_message=current_error.error_message,
                error_type=current_error.error_type,
                force_llm=force_llm
            )

            progress.progress(f"尝试 {attempt + 1}/{max_retries}: 本地验证中...")
            exec_result = self.executor.execute(fix_result.fixed_code)

            if exec_result.success:
                progress.success("验证成功！")
                return DebugResult(
                    success=True,
                    original_error=error.dict(),
                    fixed_code=fix_result.fixed_code,
                    explanation=fix_result.explanation,
                    attempts=attempt + 1,
                    related_files=related_files
                )
            else:
                if fix_result.used_pattern_fixer:
                    force_llm = True
                current_code = fix_result.fixed_code
                if exec_result.stderr:
                    try:
                        new_error = self.error_identifier.identify(exec_result.stderr)
                        if new_error.error_type != current_error.error_type or \
                           new_error.error_message != current_error.error_message:
                            current_error = new_error
                    except Exception:
                        pass

        return DebugResult(
            success=False,
            original_error=error.dict(),
            fixed_code=fix_result.fixed_code,
            explanation=f"单文件修复失败，已尝试 {max_retries} 次",
            attempts=max_retries,
            related_files=related_files
        )

    async def _fix_with_report(
        self, code: str, error: ErrorContext,
        report: InvestigationReport, accumulated_files: dict = None,
        force_llm: bool = False
    ) -> FixResult:
        """基于调查报告修复代码"""
        related_files = dict(accumulated_files) if accumulated_files else {}

        # 加载相关文件
        for loc in report.relevant_locations:
            try:
                file_path = self.project_path / loc.file_path
                if file_path.exists():
                    file_key = self._normalize_path(loc.file_path)
                    related_files[file_key] = file_path.read_text(encoding='utf-8')
                    self._load_init_files(file_key, related_files)
                elif error.error_type in ["ImportError", "ModuleNotFoundError"]:
                    self._search_similar_module(error, related_files)
            except Exception as e:
                logger.warning(f"读取文件失败 {loc.file_path}: {e}")

        # 递归加载导入依赖
        self._load_import_dependencies(code, related_files)

        # 确定要修复的文件
        actual_buggy_code, actual_error_file, original_main_file = \
            self._resolve_target_file(code, error, report, related_files)

        # 构建上下文
        fix_context = self._build_fix_context(report, error, actual_error_file)

        # 调用 CodeFixer
        fix_result = await self.code_fixer.fix_code(
            buggy_code=actual_buggy_code,
            error_message=error.error_message,
            context=fix_context,
            error_type=error.error_type,
            force_llm=force_llm
        )

        # 组装结果
        if actual_error_file and original_main_file:
            related_files[actual_error_file] = fix_result.fixed_code
            fix_result.fixed_code = code
        fix_result.related_files = related_files
        if actual_error_file:
            fix_result.target_file = actual_error_file
        elif original_main_file:
            fix_result.target_file = original_main_file

        return fix_result

    async def _verify_fix(self, fix_result: FixResult, main_filename: str = "main.py") -> ExecutionResult:
        """验证修复结果"""
        if fix_result.related_files:
            fixes = fix_result.related_files.copy()
            if main_filename not in fixes:
                fixes[main_filename] = fix_result.fixed_code
            return self.executor.execute_with_fixes(
                main_file=main_filename, fixes=fixes, backup=True
            )
        else:
            return self.executor.execute(fix_result.fixed_code)

    # === 辅助方法 ===

    def _normalize_path(self, file_path_str: str) -> str:
        """将路径标准化为相对路径"""
        fp = Path(file_path_str)
        if fp.is_absolute():
            try:
                return str(fp.relative_to(self.project_path))
            except ValueError:
                return fp.name
        return str(fp)

    def _load_init_files(self, rel_path: str, related_files: dict):
        """加载子目录模块的 __init__.py 文件"""
        if '/' not in rel_path:
            return
        parts = rel_path.split('/')
        for i in range(1, len(parts)):
            init_rel_path = '/'.join(parts[:i]) + '/__init__.py'
            if init_rel_path not in related_files:
                init_full_path = self.project_path / init_rel_path
                if init_full_path.exists():
                    try:
                        related_files[init_rel_path] = init_full_path.read_text(encoding='utf-8')
                    except Exception:
                        pass

    def _load_import_dependencies(self, code: str, related_files: dict):
        """递归加载导入依赖"""
        def parse_and_load(source_code, source_name="code"):
            try:
                tree = ast.parse(source_code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        self._try_load_module(node.module, related_files)
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            self._try_load_module(alias.name, related_files)
            except Exception:
                pass

        parse_and_load(code, "main code")
        for iteration in range(3):
            files_before = set(related_files.keys())
            for fname, fcontent in list(related_files.items()):
                parse_and_load(fcontent, fname)
            if set(related_files.keys()) == files_before:
                break

    def _try_load_module(self, module_name: str, related_files: dict):
        """尝试加载模块文件"""
        module_file = module_name.replace('.', '/') + '.py'
        module_path = self.project_path / module_file
        if module_path.exists() and module_file not in related_files:
            try:
                related_files[module_file] = module_path.read_text(encoding='utf-8')
                self._load_init_files(module_file, related_files)
            except Exception:
                pass
            return

        package_init = module_name.replace('.', '/') + '/__init__.py'
        package_path = self.project_path / package_init
        if package_path.exists() and package_init not in related_files:
            try:
                related_files[package_init] = package_path.read_text(encoding='utf-8')
            except Exception:
                pass

    def _search_similar_module(self, error, related_files):
        """搜索相似模块"""
        try:
            match = re.search(r"No module named ['\"]?([\w.]+)['\"]?", error.error_message)
            if match:
                module_name = match.group(1)
                self.context_tools._full_build()
                matches = self.context_tools.search_module(module_name, fuzzy=True)
                if matches and matches[0]['confidence'] > 0.7:
                    found_file = matches[0]['file']
                    found_path = self.project_path / found_file
                    if found_path.exists():
                        related_files[found_file] = found_path.read_text(encoding='utf-8')
        except Exception:
            pass

    def _resolve_target_file(self, code, error, report, related_files):
        """确定实际要修复的文件"""
        actual_buggy_code = code
        original_main_file = None
        actual_error_file = ""

        target_file_from_report = ""
        if report.relevant_locations:
            target_file_from_report = report.relevant_locations[0].file_path

        if error.error_file and error.error_file not in ["", "main.py", "unknown location"]:
            target_error_file = error.error_file
        else:
            target_error_file = target_file_from_report or error.error_file

        if target_error_file and "<frozen" in target_error_file:
            target_error_file = ""

        if target_error_file and target_error_file not in ["", "unknown location"]:
            actual_error_file = self._normalize_path(target_error_file)

            if actual_error_file in related_files:
                actual_buggy_code = related_files[actual_error_file]
                del related_files[actual_error_file]
                original_main_file = "main.py"
                related_files[original_main_file] = code
            else:
                load_path = Path(target_error_file) if Path(target_error_file).is_absolute() \
                    else self.project_path / target_error_file
                if load_path.exists():
                    actual_buggy_code = load_path.read_text(encoding='utf-8')
                    original_main_file = "main.py"
                    related_files[original_main_file] = code

        # 特殊处理: unknown location 的 ImportError
        if error.error_file == "unknown location" and error.error_type == "ImportError":
            pkg_match = re.search(r"cannot import name ['\"](\w+)['\"] from ['\"](\w+)['\"]", error.error_message)
            if pkg_match:
                package_name = pkg_match.group(2)
                init_path = self.project_path / package_name / "__init__.py"
                if init_path.exists():
                    actual_error_file = f"{package_name}/__init__.py"
                    actual_buggy_code = init_path.read_text(encoding='utf-8')
                    original_main_file = "main.py"
                    related_files[original_main_file] = code

        return actual_buggy_code, actual_error_file, original_main_file

    def _build_fix_context(self, report, error, actual_error_file):
        """构建修复上下文"""
        fix_context = {
            "investigation_summary": report.summary,
            "relevant_locations": [
                {"file": loc.file_path, "line": loc.line,
                 "symbol": loc.symbol, "reasoning": loc.reasoning}
                for loc in report.relevant_locations
            ],
            "root_cause": report.root_cause,
            "suggested_fix": report.suggested_fix,
            "related_symbols": {
                loc.symbol: {
                    "type": "unknown", "file": loc.file_path,
                    "line": loc.line, "definition": loc.code_snippet
                }
                for loc in report.relevant_locations
            }
        }

        strategy = self.error_registry.get(error.error_type)
        if strategy:
            try:
                extracted = strategy.extract(error.error_message)
                if hasattr(strategy, 'get_fix_context'):
                    extra_context = strategy.get_fix_context(
                        extracted, self.context_tools,
                        actual_error_file or error.error_file
                    )
                    if extra_context:
                        fix_context["strategy_context"] = extra_context
            except Exception:
                pass

        return fix_context
