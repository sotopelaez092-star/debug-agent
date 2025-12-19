"""DebugAgent - 主调试代理（新架构）"""
import ast
import re
import logging
from pathlib import Path
from typing import Optional

from src.models.error_context import ErrorContext
from src.models.investigation_report import InvestigationReport, RelevantLocation
from src.models.results import DebugResult, FixResult, ExecutionResult
from src.tools_new.context_tools import ContextTools
from src.strategies.registry import ErrorStrategyRegistry
from src.agent.investigator import CodebaseInvestigator
from src.agent.retry_strategy import SmartRetryStrategy
from src.utils.llm_client import LLMClient

# 导入核心工具（新架构）
from src.core import ErrorIdentifier, CodeFixer, LocalExecutor
from src.core import LoopDetector, LoopAction, FixValidator, ValidationLevel
from src.utils.progress_logger import get_progress_logger
from src.utils.structured_logger import get_structured_logger, DebugPhase, FixMethod

logger = logging.getLogger(__name__)
progress = get_progress_logger()  # 用户可见的进度日志
slog = get_structured_logger()  # 结构化日志


def _levenshtein_distance(s1: str, s2: str) -> int:
    """计算两个字符串的编辑距离（不需要外部库）"""
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
        """
        初始化调试代理

        Args:
            project_path: 项目根目录路径
            api_key: LLM API 密钥
            model: LLM 模型名称
            confidence_threshold: 快速路径置信度阈值 (0.0-1.0)，默认 0.7
        """
        self.project_path = Path(project_path).resolve()
        self.confidence_threshold = confidence_threshold
        logger.info(f"初始化 DebugAgent: project_path={self.project_path}, confidence_threshold={confidence_threshold}")

        # 初始化组件
        self.context_tools = ContextTools(str(self.project_path))
        self.error_identifier = ErrorIdentifier()
        self.code_fixer = CodeFixer(api_key=api_key, model=model)
        self.executor = LocalExecutor(project_path=str(self.project_path))

        # 初始化错误策略注册表
        self.error_registry = ErrorStrategyRegistry()
        self.error_registry.register_all_defaults(confidence_threshold)
        logger.info(f"已注册错误策略: {self.error_registry.list_all()}")

        # 初始化 LLM 客户端和调查员
        self.llm = LLMClient(api_key=api_key, model=model)
        self.investigator = CodebaseInvestigator(self.llm, self.context_tools)

        # 初始化智能重试策略
        self.retry_strategy = SmartRetryStrategy(max_same_approach=2)

        # 初始化循环检测器和修复验证器
        self.loop_detector = LoopDetector()
        self.fix_validator = FixValidator(project_path=str(self.project_path))

    def _similar_name(self, name1: str, name2: str, threshold: float = 0.8) -> bool:
        """判断两个名称是否相似（基于编辑距离）"""
        if name1 == name2:
            return True
        # 简单的相似度计算：允许1-2个字符的差异
        len_diff = abs(len(name1) - len(name2))
        if len_diff > 2:
            return False
        # 计算公共前缀/后缀
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

    async def debug(
        self,
        buggy_code: str,
        error_traceback: str,
        error_file: str = "",
        max_retries: int = 3  # 减少重试次数，避免卡太久
    ) -> DebugResult:
        """
        主调试入口 - 双路径调试流程

        Args:
            buggy_code: 包含错误的代码
            error_traceback: 错误堆栈跟踪
            error_file: 出错文件路径（相对于项目根目录）
            max_retries: 最大重试次数

        Returns:
            DebugResult

        Raises:
            ValueError: 参数验证失败
            RuntimeError: 调试过程中出现不可恢复的错误
        """
        # 参数验证
        if not buggy_code or not isinstance(buggy_code, str):
            raise ValueError(f"buggy_code 必须是非空字符串，得到: {type(buggy_code).__name__}")

        if not error_traceback or not isinstance(error_traceback, str):
            raise ValueError(f"error_traceback 必须是非空字符串，得到: {type(error_traceback).__name__}")

        if not isinstance(error_file, str):
            raise ValueError(f"error_file 必须是字符串，得到: {type(error_file).__name__}")

        if not isinstance(max_retries, int) or max_retries < 1:
            raise ValueError(f"max_retries 必须是正整数，得到: {max_retries}")

        logger.info("=" * 60)
        logger.info("开始调试流程")
        logger.info("=" * 60)

        # 开始结构化日志会话
        slog.start_session()

        try:
            # === Phase 1: 错误识别 ===
            slog.start_phase(DebugPhase.ERROR_PARSE)
            progress.step(1, 5, "识别错误类型", "📋")
            logger.info("[Step 1] 识别错误")
            error = self.error_identifier.identify(error_traceback)
            # 如果提供了 error_file，覆盖识别的文件
            if error_file:
                error.error_file = error_file
            logger.info(f"错误类型: {error.error_type}")
            logger.info(f"错误消息: {error.error_message}")
            progress.success(f"检测到: {error.error_type}")

            # 记录错误信息
            slog.set_error_info(error.error_type, error.error_message, error.error_file)
            slog.end_phase(success=True, error_type=error.error_type)

            # === Phase 2: 范围检测 ===
            slog.start_phase(DebugPhase.SCOPE_DETECT)
            progress.step(2, 5, "分析错误范围", "🔍")
            logger.info("[Step 2] 判断是否跨文件错误")
            is_cross_file = self._is_cross_file(error, buggy_code)
            logger.info(f"跨文件错误: {is_cross_file}")
            progress.success('跨文件错误（需要调查项目结构）' if is_cross_file else '单文件错误（快速修复）')
            slog.set_cross_file(is_cross_file)
            slog.end_phase(success=True, is_cross_file=is_cross_file)

            if not is_cross_file:
                # 单文件直接修复
                progress.step(3, 5, "快速修复模式", "⚡")
                logger.info("单文件错误，直接修复")
                slog.set_fix_method(FixMethod.LLM_CALL)
                result = await self._fix_single_file(buggy_code, error, max_retries=3)  # 单文件最多3次

                if result.success:
                    self.code_fixer.save_token_stats()
                    slog.end_session(success=True)
                    return result

                # 关键：单文件修复失败，回退到跨文件模式
                progress.warning("单文件修复失败，回退到跨文件调查模式...")
                logger.info("⚠️ 单文件修复失败，启动跨文件调查作为保底")
                is_cross_file = True  # 强制进入跨文件流程

            # === Phase 3: 调查阶段 ===
            slog.start_phase(DebugPhase.INVESTIGATION)
            progress.step(3, 5, "尝试快速路径（索引查找）", "⚡")
            logger.info("[Step 3] 尝试快速路径")
            report = self._try_fast_path(error)

            # 4. 快速路径失败，完整探索
            if not report or report.confidence < self.confidence_threshold:
                if report:
                    logger.info(f"快速路径置信度不足: {report.confidence:.2f} < {self.confidence_threshold}")
                    progress.warning(f"快速路径置信度不足 ({report.confidence:.0%})，启动完整调查...")
                else:
                    logger.info("快速路径未找到结果")
                    progress.warning("快速路径未找到结果，启动完整调查...")

                progress.step(4, 5, "LLM 完整调查（可能需要 30-60 秒）", "🤖")
                logger.info("[Step 4] 启动完整调查")
                report = await self.investigator.investigate(error)
                logger.info(f"调查完成，置信度: {report.confidence:.2f}")
                progress.success(f"调查完成（置信度: {report.confidence:.0%})")
                slog.set_fix_method(FixMethod.LLM_CALL)
            else:
                logger.info(f"快速路径成功，置信度: {report.confidence:.2f}")
                progress.success(f"快速路径成功（置信度: {report.confidence:.0%})")
                slog.set_fix_method(FixMethod.TRACEBACK_FAST)
            slog.end_phase(success=True, confidence=report.confidence)

            # === Phase 4: 修复阶段 ===
            slog.start_phase(DebugPhase.CODE_FIX)
            progress.step(5, 5, "生成并验证修复", "🔧")
            logger.info(f"[Step 5] 基于调查报告修复代码（最多 {max_retries} 次尝试）")

            current_error = error
            current_report = report
            accumulated_files = {}  # 累积所有修复的文件
            force_llm = False  # 当 PatternFixer 失败时强制使用 LLM

            for attempt in range(max_retries):
                slog.increment_attempt()

                # 循环检测：检查是否陷入重复失败模式
                loop_check = self.loop_detector.check_loop()
                if loop_check.action == LoopAction.ABORT:
                    logger.warning(f"循环检测触发终止: {loop_check.reason}")
                    progress.warning(f"检测到循环: {loop_check.reason}")
                    break
                elif loop_check.action == LoopAction.ESCALATE:
                    logger.info(f"循环检测建议升级: {loop_check.reason}")
                    force_llm = True  # 升级到 LLM 修复
                elif loop_check.action == LoopAction.SWITCH_STRATEGY:
                    logger.info(f"循环检测建议切换策略: {loop_check.reason}")
                    force_llm = True

                progress.progress(f"尝试 {attempt + 1}/{max_retries}: 生成修复代码...")
                logger.info(f"--- 尝试 {attempt + 1}/{max_retries}, force_llm={force_llm} ---")

                fix_result = await self._fix_with_report(buggy_code, current_error, current_report, accumulated_files, force_llm=force_llm)

                # 累积修复的文件
                if fix_result.related_files:
                    accumulated_files.update(fix_result.related_files)

                # 合并累积的修复到 fix_result，确保 Docker 使用所有已修复的文件
                if accumulated_files:
                    if fix_result.related_files is None:
                        fix_result.related_files = {}
                    for fname, fcontent in accumulated_files.items():
                        if fname not in fix_result.related_files:
                            fix_result.related_files[fname] = fcontent
                            logger.debug(f"合并累积修复: {fname}")

                # 6. 验证修复
                progress.progress(f"尝试 {attempt + 1}/{max_retries}: 本地验证中...")
                # 使用实际的错误文件作为执行入口
                # 如果是 main.py 或错误文件为空，使用 main.py；否则使用错误文件本身
                verify_file = error.error_file if error.error_file and error.error_file != "main.py" else "main.py"
                # 确保使用最终修复的文件作为入口
                if fix_result.target_file:
                    verify_file = fix_result.target_file
                logger.debug(f"验证入口文件: {verify_file}")
                exec_result = await self._verify_fix(fix_result, verify_file)

                if exec_result.success:
                    logger.info(f"✅ 修复成功！(第 {attempt + 1} 次尝试)")
                    # 记录成功尝试到循环检测器
                    self.loop_detector.record_attempt(
                        fixed_code=fix_result.fixed_code,
                        error_type=current_error.error_type,
                        error_message=current_error.error_message,
                        layer=3 if force_llm else 1,
                        success=True
                    )
                    # 记录成功尝试
                    approach = "pattern_fix" if fix_result.used_pattern_fixer else "llm_fix"
                    self.retry_strategy.record_attempt(
                        error_type=current_error.error_type,
                        approach=approach,
                        fix_content=fix_result.fixed_code,
                        success=True
                    )
                    self.code_fixer.save_token_stats()  # 保存 token 统计
                    slog.end_phase(success=True, attempt=attempt + 1)
                    slog.end_session(success=True)
                    # 合并所有修复的文件
                    all_files = accumulated_files.copy()
                    if fix_result.related_files:
                        all_files.update(fix_result.related_files)
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
                    logger.warning(f"❌ 验证失败:\n{exec_result.stderr}")

                    # 记录失败尝试到循环检测器
                    self.loop_detector.record_attempt(
                        fixed_code=fix_result.fixed_code,
                        error_type=current_error.error_type,
                        error_message=exec_result.stderr[:200] if exec_result.stderr else current_error.error_message,
                        layer=3 if force_llm else 1,
                        success=False
                    )

                    # 记录失败尝试到重试策略
                    approach = "pattern_fix" if fix_result.used_pattern_fixer else "llm_fix"
                    self.retry_strategy.record_attempt(
                        error_type=current_error.error_type,
                        approach=approach,
                        fix_content=fix_result.fixed_code,
                        success=False,
                        error_message=exec_result.stderr[:200] if exec_result.stderr else ""
                    )

                    # 关键：如果 PatternFixer 失败了，下次强制使用 LLM
                    if fix_result.used_pattern_fixer:
                        logger.info("PatternFixer 修复不完整，下次尝试使用 LLM")
                        force_llm = True

                    # 检查是否应该换策略
                    alternative = self.retry_strategy.suggest_alternative(current_error.error_type)
                    if alternative:
                        progress.warning(f"建议: {alternative}")
                        logger.info(f"重试策略建议: {alternative}")

                    # 检查是否是新错误（不同于当前错误）
                    if exec_result.stderr:
                        try:
                            new_error = self.error_identifier.identify(exec_result.stderr)
                            # 如果错误文件不同，说明是新错误，需要更新上下文
                            if new_error.error_file != current_error.error_file:
                                logger.info(f"检测到新错误: {new_error.error_file} (之前: {current_error.error_file})")
                                current_error = new_error
                                # 重置重试策略和循环检测器（新错误需要新策略）
                                self.retry_strategy.reset()
                                self.loop_detector.reset()
                                # 快速路径尝试获取新报告
                                new_report = self._try_fast_path(new_error)
                                if new_report:
                                    current_report = new_report
                                    logger.info(f"已更新调查报告 (置信度: {new_report.confidence:.0%})")
                        except Exception as e:
                            logger.debug(f"解析新错误失败: {e}")

            # 所有尝试均失败
            logger.error(f"修复失败（已尝试 {max_retries} 次）")
            self.code_fixer.save_token_stats()
            slog.end_phase(success=False, attempts=max_retries)
            slog.end_session(success=False)
            # 合并所有修复的文件
            all_files = accumulated_files.copy()
            if fix_result.related_files:
                all_files.update(fix_result.related_files)
            return DebugResult(
                success=False,
                original_error=error.dict(),
                fixed_code=fix_result.fixed_code,
                explanation=f"修复失败，已尝试 {max_retries} 次",
                attempts=max_retries,
                investigation_summary=current_report.summary,
                related_files=all_files
            )

        except ValueError as e:
            # 参数验证错误
            logger.error(f"参数验证失败: {e}")
            slog.end_session(success=False)
            raise

        except RuntimeError as e:
            # LLM 调用失败、修复生成失败等
            logger.error(f"调试过程中出现运行时错误: {e}", exc_info=True)
            slog.end_session(success=False)
            raise

        except Exception as e:
            # 未预期的错误
            logger.error(f"调试过程中出现未预期错误: {e}", exc_info=True)
            slog.end_session(success=False)
            raise RuntimeError(f"调试过程失败: {e}") from e

        finally:
            # 确保保存 token 统计
            try:
                self.code_fixer.save_token_stats()
            except Exception as e:
                logger.warning(f"保存 token 统计失败: {e}")

    def _is_cross_file(self, error: ErrorContext, code: str) -> bool:
        """
        判断是否跨文件错误

        Args:
            error: 错误上下文
            code: 当前文件代码

        Returns:
            True 如果是跨文件错误
        """
        try:
            # 特殊处理：动态导入 (importlib.import_module)
            if error.error_type in ["ImportError", "ModuleNotFoundError"]:
                # 检查是否是 importlib 动态导入（修复在当前文件的字符串字面量中）
                if 'importlib.import_module' in code or 'import_module(' in code:
                    module_match = re.search(r"No module named ['\"]?([\w.]+)['\"]?", error.error_message)
                    if module_match:
                        missing_module = module_match.group(1)
                        # 检查这个模块名是否作为字符串出现在代码中
                        if f'"{missing_module}"' in code or f"'{missing_module}'" in code:
                            logger.debug(f"动态导入模块 '{missing_module}' 在代码中以字符串形式存在，判断为单文件")
                            return False

            # 特殊处理：ImportError/ModuleNotFoundError 标准库拼写错误
            if error.error_type in ["ImportError", "ModuleNotFoundError"]:
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

                # 提取模块名
                module_match = re.search(r"No module named ['\"]?([\w.]+)['\"]?", error.error_message)
                if module_match:
                    full_module = module_match.group(1)  # 完整模块路径，如 'api.endpoints'
                    missing_module = full_module.split('.')[0]  # 取第一部分

                    # 如果是多级模块路径（如 api.endpoints），很可能是跨文件问题
                    if '.' in full_module:
                        logger.debug(f"多级模块路径 '{full_module}'，判断为跨文件")
                        return True

                    # 检查是否是标准库模块的拼写错误
                    for stdlib in STDLIB_MODULES:
                        dist = _levenshtein_distance(missing_module, stdlib)
                        max_len = max(len(missing_module), len(stdlib))
                        if max_len > 0 and dist / max_len < 0.4:  # 60%相似度
                            logger.debug(f"'{missing_module}' 可能是标准库 '{stdlib}' 的拼写错误，判断为单文件")
                            return False

                    # 检查是否在项目中存在相似模块
                    try:
                        results = self.context_tools.search_module(missing_module, fuzzy=True)
                        if results and results[0]['confidence'] > 0.7:
                            logger.debug(f"找到项目模块 '{results[0]['file']}'，判断为跨文件")
                            return True
                    except Exception:
                        pass

                    # 检查是否存在同名目录（可能是包）
                    try:
                        module_dir = self.project_path / missing_module
                        if module_dir.is_dir():
                            logger.debug(f"找到模块目录 '{missing_module}/'，判断为跨文件")
                            return True
                    except Exception:
                        pass

                    # 如果既不是标准库拼写错误，也找不到项目模块
                    # 保守起见，对于 ImportError 默认判断为跨文件（可能是缺少文件）
                    logger.debug(f"模块 '{missing_module}' 未找到，保守判断为跨文件")
                    return True

            # 特殊处理：AttributeError 通常是方法名拼写错误，不是跨文件问题
            if error.error_type == "AttributeError":
                # 首先检查 traceback - 如果错误发生在不同的文件中，那就是跨文件问题
                traceback = error.traceback or ""
                file_matches = re.findall(r'File "([^"]+\.py)", line (\d+)', traceback)
                if len(file_matches) >= 2:
                    # 最后一个是错误实际发生的位置
                    error_file = file_matches[-1][0]
                    # 检查是否是不同于 main 的文件
                    error_basename = Path(error_file).name
                    if error_basename != "main.py" and error_basename.endswith('.py'):
                        logger.debug(f"Traceback 显示错误在 {error_basename}，判断为跨文件")
                        return True

                # 检查是否是模块属性错误（module 'xxx' has no attribute）
                # 这通常是方法名拼写错误，如 os.path.jion -> os.path.join
                if "module '" in error.error_message and "' has no attribute" in error.error_message:
                    logger.debug(f"模块属性的 AttributeError，判断为单文件（方法名拼写错误）")
                    return False

                # 检查是否是类属性访问（可能涉及跨文件类定义）
                # 模式: 'ClassName' object has no attribute 'attr'
                if "'str'" in error.error_message or "'int'" in error.error_message or \
                   "'float'" in error.error_message or "'list'" in error.error_message or \
                   "'dict'" in error.error_message:
                    # 内置类型的方法错误，肯定是单文件拼写错误
                    logger.debug(f"内置类型的 AttributeError，判断为单文件")
                    return False

                # 对于自定义类，检查类是否在当前文件定义
                # 提取类名: 'ClassName' object has no attribute
                class_match = re.search(r"'(\w+)' object has no attribute", error.error_message)
                if class_match:
                    class_name = class_match.group(1)
                    # 检查类是否在当前文件定义
                    tree = ast.parse(code)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef) and node.name == class_name:
                            logger.debug(f"类 '{class_name}' 在当前文件定义，判断为单文件")
                            return False
                    logger.debug(f"类 '{class_name}' 不在当前文件，判断为跨文件")
                    return True

            # 提取错误中的符号
            symbol = self._extract_symbol(error)
            if not symbol or symbol == "unknown":
                return False

            # 使用 AST 提取当前文件的所有定义
            tree = ast.parse(code)
            local_symbols = set()

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    local_symbols.add(node.name)
                    # 添加函数参数
                    if isinstance(node, ast.FunctionDef):
                        for arg in node.args.args:
                            local_symbols.add(arg.arg)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            local_symbols.add(target.id)

            # 判断符号是否在本地定义
            if symbol in local_symbols:
                logger.debug(f"符号 '{symbol}' 在当前文件定义")
                return False

            # 对于 NameError，检查是否有相似的符号（可能是拼写错误）
            if error.error_type == "NameError":
                # 首先检查 traceback - 如果错误发生在不同的文件中，那就是跨文件问题
                traceback = error.traceback or ""
                file_matches = re.findall(r'File "([^"]+\.py)", line (\d+)', traceback)
                if len(file_matches) >= 2:
                    error_file = file_matches[-1][0]
                    error_basename = Path(error_file).name
                    if error_basename != "main.py" and error_basename.endswith('.py'):
                        logger.debug(f"Traceback 显示 NameError 在 {error_basename}，判断为跨文件")
                        return True

                # 1. 检查是否是拼写错误
                for local_sym in local_symbols:
                    dist = _levenshtein_distance(symbol, local_sym)
                    max_len = max(len(symbol), len(local_sym))
                    if max_len > 0 and dist / max_len < 0.3:  # 70%相似度
                        logger.debug(f"符号 '{symbol}' 可能是 '{local_sym}' 的拼写错误（单文件）")
                        return False

                # 2. 检查符号是否在项目中存在
                # 如果在整个项目中都不存在，很可能是逻辑错误（如 average 未定义），而非导入问题
                try:
                    results = self.context_tools.search_symbol(symbol, fuzzy=False)
                    if not results or (results and results[0]['confidence'] < 0.5):
                        logger.debug(f"符号 '{symbol}' 在项目中不存在，可能是单文件逻辑错误")
                        return False  # 判断为单文件（逻辑错误，非导入问题）
                except Exception as e:
                    logger.debug(f"搜索符号失败: {e}")

            logger.debug(f"符号 '{symbol}' 不在当前文件定义（跨文件）")
            return True

        except SyntaxError:
            logger.warning("代码解析失败，假定为单文件错误")
            return False

    def _extract_symbol(self, error: ErrorContext) -> str:
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

    def _try_fast_path(self, error: ErrorContext) -> Optional[InvestigationReport]:
        """
        尝试快速路径

        Args:
            error: 错误上下文

        Returns:
            InvestigationReport 如果置信度 > 0.9，否则 None
        """
        # 优化1: 直接从 traceback 提取文件路径（最快）
        traceback_report = self._try_traceback_fast_path(error)
        if traceback_report and traceback_report.confidence >= self.confidence_threshold:
            return traceback_report

        strategy = self.error_registry.get(error.error_type)
        if not strategy:
            logger.debug(f"未找到策略: {error.error_type}")
            return traceback_report  # 返回 traceback 解析结果（可能有低置信度）

        # 提取关键信息
        extracted = strategy.extract(error.error_message)
        if not extracted:
            logger.debug("策略提取失败")
            return None

        # 快速搜索
        result = strategy.fast_search(
            extracted,
            self.context_tools,
            error.error_file
        )

        if result and result.confidence > self.confidence_threshold:
            logger.info(f"快速路径成功: {result.suggestion}")
            # 转换为 InvestigationReport
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
        """
        从 traceback 直接提取文件路径的快速路径

        适用于 ImportError 等已包含文件路径的错误
        """
        traceback = error.traceback or ""

        # 模式1: "cannot import name 'X' from 'module' (/path/to/file.py)"
        # 注意：module 可能是 "pkg.helper" 格式
        # 重要：这类错误通常是导入语句中的拼写错误，应该修复导入语句所在的文件
        import_match = re.search(
            r"cannot import name ['\"](\w+)['\"] from ['\"]([\w.]+)['\"] \(([^)]+\.py)\)",
            traceback
        )
        if import_match:
            symbol = import_match.group(1)  # 尝试导入的符号（可能有拼写错误）
            module = import_match.group(2)
            module_file_path = import_match.group(3)

            # 转换模块文件路径为相对路径
            if module_file_path.startswith('/workspace/'):
                module_file_path = module_file_path[len('/workspace/'):]
            elif self.project_path and module_file_path.startswith(str(self.project_path)):
                module_file_path = str(Path(module_file_path).relative_to(self.project_path))

            # 获取导入语句所在的文件（是 traceback 的最后一个文件，即实际执行 import 的文件）
            # 例如：main.py → mod_b.py → mod_d.py，错误的 import 语句在 mod_b.py（最后一个文件）
            file_matches = re.findall(r'File "([^"]+\.py)", line (\d+)', traceback)
            importing_file = error.error_file or "main.py"
            importing_line = 1
            if file_matches:
                # 使用最后一个文件（实际执行导入的文件）
                importing_file = file_matches[-1][0]
                importing_line = int(file_matches[-1][1])
                # 转换为相对路径
                if importing_file.startswith('/workspace/'):
                    importing_file = importing_file[len('/workspace/'):]
                elif self.project_path:
                    try:
                        importing_file = str(Path(importing_file).relative_to(self.project_path))
                    except ValueError:
                        importing_file = Path(importing_file).name

            logger.info(f"Traceback 快速路径: 从 {module} 导入 {symbol} 失败")
            logger.info(f"  模块文件: {module_file_path}")
            logger.info(f"  导入语句所在文件: {importing_file}:{importing_line}")

            # 对于 "cannot import name" 错误，需要判断是导入语句有拼写错误还是定义有拼写错误
            # 读取模块文件内容来判断
            try:
                module_full_path = self.project_path / module_file_path
                if module_full_path.exists():
                    module_content = module_full_path.read_text(encoding='utf-8')
                    # 检查模块中是否已经存在要导入的符号
                    import ast
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
                            # 关键：也要检查从子模块导入的符号
                            # 例如: from .email import validate_email
                            elif isinstance(node, ast.ImportFrom):
                                for alias in node.names:
                                    # 使用别名（如果有），否则使用原名
                                    name = alias.asname if alias.asname else alias.name
                                    if name != '*':
                                        defined_names.add(name)

                        logger.debug(f"模块 {module} 中定义的符号: {defined_names}")

                        if symbol in defined_names:
                            # 符号存在于模块中，说明导入语句是正确的，可能其他地方有问题
                            fix_target = module_file_path
                            fix_reason = f"模块 {module} 中已存在 {symbol}，可能存在其他问题"
                        elif any(self._similar_name(symbol, name) for name in defined_names):
                            # 找到相似的名字，说明导入语句有拼写错误
                            similar = next(name for name in defined_names if self._similar_name(symbol, name))
                            fix_target = importing_file
                            fix_reason = f"模块 {module} 中存在 {similar}，导入语句中的 {symbol} 可能是拼写错误"
                            logger.info(f"检测到导入语句拼写错误: {symbol} -> {similar}")
                        else:
                            # 没有找到相似名字，可能是定义缺失
                            fix_target = module_file_path
                            fix_reason = f"模块 {module} 中缺少 {symbol} 的定义"
                    except:
                        fix_target = importing_file
                        fix_reason = "无法解析模块，默认修复导入语句"
                else:
                    fix_target = importing_file
                    fix_reason = "模块文件不存在，修复导入语句"
            except Exception as e:
                logger.warning(f"检查模块内容失败: {e}")
                fix_target = importing_file
                fix_reason = "检查失败，默认修复导入语句"

            return InvestigationReport(
                summary=f"ImportError: 无法从 {module} 导入 {symbol}，{fix_reason}",
                relevant_locations=[
                    # 首先返回要修复的文件
                    RelevantLocation(
                        file_path=fix_target,
                        line=importing_line if fix_target == importing_file else 1,
                        symbol=symbol,
                        reasoning=fix_reason
                    ),
                    # 然后返回另一个文件（用于提供上下文）
                    RelevantLocation(
                        file_path=module_file_path if fix_target == importing_file else importing_file,
                        line=1 if fix_target == importing_file else importing_line,
                        symbol=symbol,
                        reasoning=f"上下文文件"
                    )
                ],
                root_cause=fix_reason,
                suggested_fix=f"修复 {fix_target} 中的拼写错误",
                confidence=0.95
            )

        # 模式2: 从 traceback 中提取最后一个 File 路径（通常是错误发生的位置）
        file_matches = re.findall(r'File "([^"]+\.py)", line (\d+)', traceback)
        if file_matches and len(file_matches) > 1:
            # 取最后一个 (最接近错误发生的位置)
            last_file, last_line = file_matches[-1]

            # 转换为相对路径
            if last_file.startswith('/workspace/'):
                last_file = last_file[len('/workspace/'):]
            elif self.project_path:
                try:
                    last_file = str(Path(last_file).relative_to(self.project_path))
                except ValueError:
                    pass

            # 低置信度，作为备选
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
                confidence=0.7  # 较低置信度
            )

        return None

    async def _fix_single_file(
        self,
        code: str,
        error: ErrorContext,
        max_retries: int
    ) -> DebugResult:
        """
        单文件修复流程

        Args:
            code: 代码
            error: 错误上下文
            max_retries: 最大重试次数

        Returns:
            DebugResult
        """
        # 如果是 ImportError，尝试查找相关模块
        related_files = {}
        if error.error_type in ["ImportError", "ModuleNotFoundError"]:
            progress.progress("检测到导入错误，查找相关模块...")
            try:
                # 提取模块名
                match = re.search(r"No module named ['\"]?([\w.]+)['\"]?", error.error_message)
                if match:
                    module_name = match.group(1)
                    # 搜索模块文件
                    module_results = self.context_tools.search_module(module_name, fuzzy=True)
                    if module_results and module_results[0]['confidence'] > 0.7:
                        file_path = self.project_path / module_results[0]['file']
                        if file_path.exists():
                            related_files[module_results[0]['file']] = file_path.read_text(encoding='utf-8')
                            logger.info(f"找到相关模块: {module_results[0]['file']}")
                            progress.success(f"找到相关模块: {module_results[0]['file']} (置信度: {module_results[0]['confidence']:.0%})")
            except Exception as e:
                logger.warning(f"查找相关模块失败: {e}")

        # 追踪当前代码和错误（用于累积修复）
        current_code = code
        current_error = error
        force_llm = False  # 当 PatternFixer 失败时强制使用 LLM

        for attempt in range(max_retries):
            progress.progress(f"尝试 {attempt + 1}/{max_retries}: 生成修复代码...")
            logger.info(f"单文件修复尝试 {attempt + 1}/{max_retries}, force_llm={force_llm}")

            # 调用 CodeFixer（使用当前代码和错误，不是原始的）
            fix_result = await self.code_fixer.fix_code(
                buggy_code=current_code,
                error_message=current_error.error_message,
                error_type=current_error.error_type,
                force_llm=force_llm
            )

            # 验证修复
            progress.progress(f"尝试 {attempt + 1}/{max_retries}: 本地验证中...")
            # 直接执行修复后的代码
            exec_result = self.executor.execute(fix_result.fixed_code)

            if exec_result.success:
                logger.info(f"✅ 单文件修复成功！")
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
                logger.warning(f"验证失败:\n{exec_result.stderr}")
                progress.error("验证失败，重试...")

                # 关键：如果 PatternFixer 失败了，下次强制使用 LLM
                if fix_result.used_pattern_fixer:
                    logger.info("PatternFixer 修复不完整，下次尝试使用 LLM")
                    force_llm = True

                # 关键：更新当前代码为部分修复的版本
                current_code = fix_result.fixed_code

                # 关键：解析新错误，更新错误上下文
                if exec_result.stderr:
                    try:
                        new_error = self.error_identifier.identify(exec_result.stderr)
                        if new_error.error_type != current_error.error_type or \
                           new_error.error_message != current_error.error_message:
                            logger.info(f"检测到新错误: {new_error.error_type} (之前: {current_error.error_type})")
                            current_error = new_error
                    except Exception as e:
                        logger.debug(f"解析新错误失败: {e}")

        # 失败
        return DebugResult(
            success=False,
            original_error=error.dict(),
            fixed_code=fix_result.fixed_code,
            explanation=f"单文件修复失败，已尝试 {max_retries} 次",
            attempts=max_retries,
            related_files=related_files
        )

    async def _fix_with_report(
        self,
        code: str,
        error: ErrorContext,
        report: InvestigationReport,
        accumulated_files: dict = None,
        force_llm: bool = False
    ) -> FixResult:
        """
        基于调查报告修复代码

        Args:
            code: 原始代码
            error: 错误上下文
            report: 调查报告
            accumulated_files: 已累积的修复文件（可选，用于多文件修复）

        Returns:
            FixResult
        """
        # 辅助函数：将路径转换为相对于项目根目录的路径
        def normalize_path(file_path_str: str) -> str:
            """将路径标准化为相对路径（保留子目录结构）"""
            fp = Path(file_path_str)
            # 如果是绝对路径，尝试转换为相对路径
            if fp.is_absolute():
                try:
                    return str(fp.relative_to(self.project_path))
                except ValueError:
                    # 不在项目目录下，使用文件名
                    return fp.name
            # 已经是相对路径，直接返回
            return str(fp)

        # 辅助函数：加载子目录模块的 __init__.py 文件
        def load_init_files(rel_path: str):
            """加载子目录模块所需的所有 __init__.py 文件"""
            if '/' not in rel_path:
                return
            parts = rel_path.split('/')
            for i in range(1, len(parts)):
                init_rel_path = '/'.join(parts[:i]) + '/__init__.py'
                if init_rel_path not in related_files:
                    init_full_path = self.project_path / init_rel_path
                    if init_full_path.exists():
                        try:
                            init_content = init_full_path.read_text(encoding='utf-8')
                            related_files[init_rel_path] = init_content
                            logger.debug(f"加载 __init__.py: {init_rel_path}")
                            progress.progress(f"加载包初始化: {init_rel_path}", indent=2)
                        except Exception as e:
                            logger.debug(f"读取 __init__.py 失败 {init_rel_path}: {e}")

        # 读取相关文件（优先使用已累积的修复版本）
        related_files = dict(accumulated_files) if accumulated_files else {}
        for loc in report.relevant_locations:
            try:
                file_path = self.project_path / loc.file_path
                progress.progress(f"读取相关文件: {loc.file_path}", indent=2)
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    # 使用相对路径作为 key（保留子目录结构）
                    file_key = normalize_path(loc.file_path)
                    related_files[file_key] = content
                    # 如果是子目录文件，也加载 __init__.py
                    load_init_files(file_key)
                    logger.debug(f"读取相关文件: {loc.file_path} -> {file_key}")
                    progress.success(f"已读取: {loc.file_path} ({len(content)} 字符)", indent=2)
                else:
                    progress.warning(f"文件不存在: {file_path}", indent=2)

                    # 智能回退：对于 ImportError，尝试搜索相似的模块
                    if error.error_type in ["ImportError", "ModuleNotFoundError"]:
                        # 从错误消息中提取模块名
                        import re
                        match = re.search(r"No module named ['\"]?([\w.]+)['\"]?", error.error_message)
                        if match:
                            module_name = match.group(1)
                            logger.info(f"从错误消息中提取模块名: {module_name}")
                            progress.progress(f"尝试搜索模块: {module_name}", indent=2)

                            # 强制重新扫描项目（避免缓存问题）
                            logger.info("强制重新扫描项目以确保最新文件被索引")
                            self.context_tools._full_build()

                            matches = self.context_tools.search_module(module_name, fuzzy=True)
                            logger.info(f"搜索结果: {matches}")

                            if matches and matches[0]['confidence'] > 0.7:
                                found_file = matches[0]['file']
                                found_path = self.project_path / found_file
                                logger.info(f"检查文件: {found_path}, exists={found_path.exists()}")
                                if found_path.exists():
                                    content = found_path.read_text(encoding='utf-8')
                                    related_files[found_file] = content
                                    logger.info(f"找到相似模块: {found_file} (置信度: {matches[0]['confidence']})")
                                    progress.success(f"找到相似模块: {found_file} (置信度: {matches[0]['confidence']:.0%})", indent=2)
                            else:
                                logger.warning(f"未找到相似模块，搜索结果: {matches}")
                                progress.warning(f"未找到相似模块 '{module_name}'", indent=2)
            except Exception as e:
                logger.warning(f"读取文件失败 {loc.file_path}: {e}")
                progress.error(f"读取失败: {e}", indent=2)

        # 确保主文件的所有直接导入都被包含
        # 这对于跨文件错误很重要，因为 Docker 需要所有依赖文件
        def module_to_path(module_name: str) -> str:
            """将模块名转换为文件路径（支持子目录）

            Examples:
                'utils' -> 'utils.py'
                'services.user' -> 'services/user.py'
                'models.data.types' -> 'models/data/types.py'
            """
            return module_name.replace('.', '/') + '.py'

        def try_load_module(module_name: str, source_name: str):
            """尝试加载模块文件（支持多种路径格式）"""
            # 尝试作为文件: services/user.py
            module_file = module_to_path(module_name)
            module_path = self.project_path / module_file

            if module_path.exists() and module_file not in related_files:
                try:
                    content = module_path.read_text(encoding='utf-8')
                    related_files[module_file] = content
                    logger.info(f"从 {source_name} 添加导入模块: {module_file}")

                    # 如果是子目录模块，也检查 __init__.py
                    if '/' in module_file:
                        parts = module_file.split('/')
                        for i in range(1, len(parts)):
                            init_path = '/'.join(parts[:i]) + '/__init__.py'
                            init_full = self.project_path / init_path
                            if init_full.exists() and init_path not in related_files:
                                init_content = init_full.read_text(encoding='utf-8')
                                related_files[init_path] = init_content
                                logger.info(f"添加 __init__.py: {init_path}")
                    return True
                except Exception as e:
                    logger.debug(f"读取导入模块失败 {module_file}: {e}")

            # 尝试作为包目录: services/user/__init__.py
            package_init = module_name.replace('.', '/') + '/__init__.py'
            package_path = self.project_path / package_init
            if package_path.exists() and package_init not in related_files:
                try:
                    content = package_path.read_text(encoding='utf-8')
                    related_files[package_init] = content
                    logger.info(f"从 {source_name} 添加导入包: {package_init}")
                    return True
                except Exception as e:
                    logger.debug(f"读取导入包失败 {package_init}: {e}")

            return False

        def parse_and_load_imports(source_code, source_name="code"):
            """解析代码中的导入语句并加载相关模块"""
            try:
                tree = ast.parse(source_code)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        if isinstance(node, ast.ImportFrom) and node.module:
                            # from module import ... (e.g., from services.user import UserService)
                            try_load_module(node.module, source_name)
                        elif isinstance(node, ast.Import):
                            # import module (e.g., import services.user)
                            for alias in node.names:
                                try_load_module(alias.name, source_name)
            except Exception as e:
                logger.warning(f"解析 {source_name} 导入语句失败: {e}")

        # 解析主文件的导入
        parse_and_load_imports(code, "main code")

        # 解析所有已加载相关文件的导入（递归加载依赖）
        # 最多迭代3次，避免无限循环
        for iteration in range(3):
            files_before = set(related_files.keys())
            for fname, fcontent in list(related_files.items()):
                parse_and_load_imports(fcontent, fname)
            files_after = set(related_files.keys())
            if files_before == files_after:
                # 没有新文件加载，停止迭代
                break
            logger.debug(f"导入解析迭代 {iteration + 1}: 新增 {len(files_after - files_before)} 个文件")

        # 确定要修复的代码（如果 error_file 指向其他文件，需要加载该文件）
        actual_buggy_code = code
        original_main_file = None  # 原始传入的主文件名
        actual_error_file = ""  # 实际要修复的文件名（相对路径）

        # 优先使用 report 中的 relevant_locations（更准确）
        target_file_from_report = ""
        if report.relevant_locations:
            target_file_from_report = report.relevant_locations[0].file_path
            logger.info(f"Report 建议修复文件: {target_file_from_report}")

        print(f"\n[DEBUG] error.error_file = '{error.error_file}'")
        print(f"[DEBUG] target_file_from_report = '{target_file_from_report}'")

        # 确定目标错误文件
        # 如果 error.error_file 已经是具体的文件名（非 main.py 且非空），优先使用它
        # 否则使用 report 建议
        if error.error_file and error.error_file not in ["", "main.py", "unknown location"]:
            target_error_file = error.error_file
            logger.debug(f"使用 error.error_file: {error.error_file}")
        else:
            target_error_file = target_file_from_report or error.error_file
            logger.debug(f"使用 target_file_from_report: {target_file_from_report}")

        # 特殊处理：<frozen xxx> 路径表示 Python 内部模块，应该跳过
        if target_error_file and "<frozen" in target_error_file:
            target_error_file = ""
            logger.info("检测到 <frozen> 路径，跳过文件加载")

        if target_error_file and target_error_file != "" and target_error_file != "unknown location":
            # 保存完整路径用于从磁盘加载
            full_error_path = target_error_file
            # 使用相对路径作为 key（保留子目录结构）
            actual_error_file = normalize_path(target_error_file)
            logger.debug(f"目标文件路径: {full_error_path} -> key: {actual_error_file}")

            # 尝试从 related_files 中获取（可能已经加载过）
            if actual_error_file in related_files:
                actual_buggy_code = related_files[actual_error_file]
                # 移除，避免重复（稍后会添加修复后的版本）
                del related_files[actual_error_file]
                # 将原始 main code 加入 related_files
                original_main_file = "main.py"  # 假设原始代码是 main.py
                related_files[original_main_file] = code
                logger.info(f"实际修复文件: {actual_error_file}")
                logger.info(f"原始主文件 {original_main_file} 已加入 related_files")
            else:
                # 尝试加载该文件（使用完整路径）
                if Path(full_error_path).is_absolute():
                    load_path = Path(full_error_path)
                else:
                    load_path = self.project_path / full_error_path
                if load_path.exists():
                    actual_buggy_code = load_path.read_text(encoding='utf-8')
                    # 将原始 main code 加入 related_files
                    original_main_file = "main.py"
                    related_files[original_main_file] = code
                    logger.info(f"从磁盘加载实际错误文件: {actual_error_file}")
                    logger.info(f"原始主文件 {original_main_file} 已加入 related_files")
                else:
                    logger.warning(f"错误文件不存在: {load_path}，使用原始代码")

        # 特殊处理: "unknown location" 的 ImportError (通常是包的 __init__.py 问题)
        if error.error_file == "unknown location" and error.error_type == "ImportError":
            # 从错误消息中提取包名: "cannot import name 'X' from 'package'"
            import re
            pkg_match = re.search(r"cannot import name ['\"](\w+)['\"] from ['\"](\w+)['\"]", error.error_message)
            if pkg_match:
                symbol_name = pkg_match.group(1)
                package_name = pkg_match.group(2)
                init_path = self.project_path / package_name / "__init__.py"
                logger.info(f"检测到 unknown location, 尝试查找: {init_path}")
                if init_path.exists():
                    actual_error_file = f"{package_name}/__init__.py"
                    actual_buggy_code = init_path.read_text(encoding='utf-8')
                    original_main_file = "main.py"
                    related_files[original_main_file] = code
                    logger.info(f"找到包的 __init__.py: {actual_error_file}")

        # 构建上下文
        fix_context = {
            "investigation_summary": report.summary,
            "relevant_locations": [
                {
                    "file": loc.file_path,
                    "line": loc.line,
                    "symbol": loc.symbol,
                    "reasoning": loc.reasoning
                }
                for loc in report.relevant_locations
            ],
            "root_cause": report.root_cause,
            "suggested_fix": report.suggested_fix,
            "related_symbols": {
                loc.symbol: {
                    "type": "unknown",
                    "file": loc.file_path,
                    "line": loc.line,
                    "definition": loc.code_snippet
                }
                for loc in report.relevant_locations
            }
        }

        # 获取错误策略的额外上下文（用于 CircularImport 和 KeyError）
        strategy = self.error_registry.get(error.error_type)
        if strategy:
            try:
                extracted = strategy.extract(error.error_message)
                if hasattr(strategy, 'get_fix_context'):
                    extra_context = strategy.get_fix_context(
                        extracted, self.context_tools, actual_error_file or error.error_file
                    )
                    if extra_context:
                        fix_context["strategy_context"] = extra_context
                        logger.info(f"添加策略上下文: {list(extra_context.keys())}")
            except Exception as e:
                logger.debug(f"获取策略上下文失败: {e}")

        # 调用 CodeFixer
        if force_llm:
            logger.info("🔧 强制使用 LLM（PatternFixer 上次失败）")
        fix_result = await self.code_fixer.fix_code(
            buggy_code=actual_buggy_code,
            error_message=error.error_message,
            context=fix_context,
            error_type=error.error_type,
            force_llm=force_llm
        )

        # 添加 related_files 到结果
        # 重要：如果我们修复的是非主文件，需要将修复后的代码添加到 related_files
        print(f"\n[DEBUG] Before final assembly:")
        print(f"  actual_error_file = '{actual_error_file}'")
        print(f"  original_main_file = '{original_main_file}'")

        # 如果修复的是非主文件（actual_error_file 存在且非空，且与主文件不同）
        if actual_error_file and original_main_file:
            # 跨文件场景：我们修复的是 actual_error_file，不是原始 main 文件
            # 将修复后的代码添加到 related_files（使用相对路径作为 key）
            related_files[actual_error_file] = fix_result.fixed_code
            logger.info(f"将修复后的 {actual_error_file} 添加到 related_files")
            # fix_result.fixed_code 应该是原始 main code（用于执行）
            fix_result.fixed_code = code
            logger.info(f"恢复 fix_result.fixed_code 为原始主文件代码")
        elif actual_error_file:
            # 单文件场景：error_file 就是 main file，直接使用修复后的代码
            logger.info(f"单文件场景：直接使用修复后的代码作为主文件")

        fix_result.related_files = related_files
        # 设置目标文件用于验证 - 如果有实际错误文件，使用它；否则使用原始主文件
        if actual_error_file:
            fix_result.target_file = actual_error_file
        elif original_main_file:
            fix_result.target_file = original_main_file
        logger.debug(f"设置验证目标文件: {fix_result.target_file}")
        return fix_result

    async def _verify_fix(self, fix_result: FixResult, main_filename: str = "main.py") -> ExecutionResult:
        """
        验证修复结果

        Args:
            fix_result: 修复结果
            main_filename: 主文件名（要执行的入口文件）

        Returns:
            ExecutionResult
        """
        if fix_result.related_files:
            # 多文件修复 - 合并所有修复到 fixes 字典
            fixes = fix_result.related_files.copy()
            # 只有当 main_filename 不在 related_files 中时才添加 fixed_code
            # 这避免了覆盖已经修复好的目标文件
            if main_filename not in fixes:
                fixes[main_filename] = fix_result.fixed_code
            logger.debug(f"验证文件列表: {list(fixes.keys())}, 入口: {main_filename}")
            return self.executor.execute_with_fixes(
                main_file=main_filename,
                fixes=fixes,
                backup=True  # 失败时自动回滚
            )
        else:
            # 单文件执行
            return self.executor.execute(fix_result.fixed_code)

    async def debug_file(
        self,
        file_path: str,
        max_iterations: int = 10,
        auto_save: bool = True
    ) -> dict:
        """
        循环修复模式：自动运行 → 修复 → 再运行，直到没有错误

        Args:
            file_path: 要调试的文件路径
            max_iterations: 最大循环次数（防止无限循环）
            auto_save: 是否自动保存修复后的代码到文件

        Returns:
            {
                "success": bool,
                "iterations": int,
                "fixes": [{"error": str, "fix": str}, ...],
                "final_code": str,
                "message": str
            }
        """
        import subprocess
        import os
        import sys

        file_path = Path(file_path).resolve()
        if not file_path.exists():
            return {
                "success": False,
                "iterations": 0,
                "fixes": [],
                "final_code": "",
                "message": f"文件不存在: {file_path}"
            }

        # 计算相对于 project_path 的路径（用于 error_file 参数）
        try:
            relative_file_path = str(file_path.relative_to(self.project_path))
        except ValueError:
            # 文件不在 project_path 下，使用文件名
            relative_file_path = file_path.name

        # 读取原始代码
        original_code = file_path.read_text(encoding='utf-8')
        current_code = original_code
        fixes = []

        progress.info(f"🔄 开始循环修复: {relative_file_path}")
        progress.info(f"   项目路径: {self.project_path}")
        progress.info(f"   最大迭代次数: {max_iterations}")

        for iteration in range(max_iterations):
            progress.step(iteration + 1, max_iterations, f"第 {iteration + 1} 轮", "🔄")

            # 1. 运行代码，获取错误
            progress.progress("运行代码检查错误...")

            # 如果不自动保存，需要执行内存中的代码
            if not auto_save and iteration > 0:
                # 执行内存中的代码（写入临时文件）
                exec_result = self.executor.execute(current_code)
                if exec_result.success:
                    progress.success(f"✅ 代码运行成功！共修复 {len(fixes)} 个错误")
                    return {
                        "success": True,
                        "iterations": iteration + 1,
                        "fixes": fixes,
                        "final_code": current_code,
                        "message": f"成功！共修复 {len(fixes)} 个错误"
                    }
                stderr = exec_result.stderr
            else:
                # 运行文件（设置正确的 cwd 和 PYTHONPATH）
                try:
                    env = os.environ.copy()
                    env["PYTHONPATH"] = str(self.project_path)
                    result = subprocess.run(
                        [sys.executable, str(file_path)],
                        cwd=str(self.project_path),
                        capture_output=True,
                        text=True,
                        timeout=30,
                        env=env
                    )
                except subprocess.TimeoutExpired:
                    progress.error("执行超时 (30s)")
                    return {
                        "success": False,
                        "iterations": iteration + 1,
                        "fixes": fixes,
                        "final_code": current_code,
                        "message": "执行超时"
                    }

                # 检查是否有错误
                if result.returncode == 0:
                    progress.success(f"✅ 代码运行成功！共修复 {len(fixes)} 个错误")
                    return {
                        "success": True,
                        "iterations": iteration + 1,
                        "fixes": fixes,
                        "final_code": current_code,
                        "message": f"成功！共修复 {len(fixes)} 个错误"
                    }
                stderr = result.stderr

            if not stderr:
                progress.warning("代码返回非零但无错误信息")
                return {
                    "success": False,
                    "iterations": iteration + 1,
                    "fixes": fixes,
                    "final_code": current_code,
                    "message": "代码返回非零但无错误信息"
                }

            # 3. 提取错误类型
            error_preview = stderr.strip().split('\n')[-1][:100]
            progress.progress(f"发现错误: {error_preview}")

            # 4. 调用调试器修复
            debug_result = await self.debug(
                buggy_code=current_code,
                error_traceback=stderr,
                error_file=relative_file_path,  # 使用相对路径，保留子目录结构
                max_retries=3
            )

            if not debug_result.success:
                progress.error(f"❌ 修复失败: {debug_result.explanation}")
                return {
                    "success": False,
                    "iterations": iteration + 1,
                    "fixes": fixes,
                    "final_code": current_code,
                    "message": f"第 {iteration + 1} 轮修复失败: {debug_result.explanation}"
                }

            # 5. 记录修复
            fixes.append({
                "iteration": iteration + 1,
                "error": error_preview,
                "fix": debug_result.explanation
            })

            # 6. 更新代码
            current_code = debug_result.fixed_code

            # 7. 保存到文件（如果启用）
            if auto_save:
                file_path.write_text(current_code, encoding='utf-8')

                # 保存相关文件（跨文件修复的关键！）
                if hasattr(debug_result, 'related_files') and debug_result.related_files:
                    for rel_name, rel_content in debug_result.related_files.items():
                        # 使用 project_path 作为基础路径，而不是 file_path.parent
                        rel_path = self.project_path / rel_name
                        # 确保父目录存在
                        rel_path.parent.mkdir(parents=True, exist_ok=True)
                        if rel_path.exists() or rel_name.endswith('.py'):
                            rel_path.write_text(rel_content, encoding='utf-8')
                            progress.success(f"已保存相关文件: {rel_name}")

                progress.success(f"已保存修复 #{iteration + 1}: {debug_result.explanation[:50]}")
            else:
                progress.success(f"修复 #{iteration + 1}: {debug_result.explanation[:50]}")

        # 达到最大迭代次数
        progress.warning(f"⚠️ 达到最大迭代次数 ({max_iterations})，可能存在循环修复")
        return {
            "success": False,
            "iterations": max_iterations,
            "fixes": fixes,
            "final_code": current_code,
            "message": f"达到最大迭代次数 ({max_iterations})"
        }
