"""LocalExecutor - 本地代码执行器（替代 Docker）"""
import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional

from src.models.results import ExecutionResult

logger = logging.getLogger(__name__)


class LocalExecutor:
    """
    本地代码执行器

    直接在用户环境运行代码，不使用 Docker：
    - 环境一致（和开发环境一样）
    - 没有路径映射问题
    - 速度更快
    - 依赖自动可用
    """

    def __init__(self, project_path: Optional[str] = None, timeout: int = 30):
        """
        初始化执行器

        Args:
            project_path: 项目根目录（用于设置工作目录和 PYTHONPATH）
            timeout: 执行超时时间（秒）
        """
        self.project_path = Path(project_path).resolve() if project_path else Path.cwd()
        self.timeout = timeout
        logger.info(f"LocalExecutor 初始化: project_path={self.project_path}, timeout={timeout}s")

    def _resolve_path(self, file_path: str) -> Path:
        """
        智能解析文件路径

        处理以下情况:
        1. 绝对路径 -> 直接使用
        2. 相对路径 -> 相对于 project_path
        3. 已包含 project_path 前缀的路径 -> 避免路径重复

        Args:
            file_path: 文件路径（可以是相对或绝对路径）

        Returns:
            解析后的绝对路径
        """
        fp = Path(file_path)

        # 1. 已经是绝对路径
        if fp.is_absolute():
            return fp

        # 2. 检查是否已包含 project_path 的部分（避免路径重复）
        # 例如: project_path=/a/b/c, file_path=b/c/file.py -> 可能导致 /a/b/c/b/c/file.py
        try:
            project_parts = self.project_path.parts
            file_parts = fp.parts
            # 检查文件路径是否以 project_path 的某部分开始
            for i in range(len(project_parts)):
                if project_parts[i:] == file_parts[:len(project_parts) - i]:
                    # 发现重叠，使用绝对路径
                    resolved = self.project_path.parent.joinpath(*project_parts[i:], *file_parts[len(project_parts) - i:])
                    if resolved.exists():
                        logger.debug(f"路径重叠检测: {file_path} -> {resolved}")
                        return resolved
        except Exception:
            pass

        # 3. 标准相对路径解析
        return self.project_path / fp

    def execute(self, code: str, filename: str = "main.py") -> ExecutionResult:
        """
        执行代码字符串

        Args:
            code: 要执行的代码
            filename: 保存的文件名

        Returns:
            ExecutionResult
        """
        # 写入临时文件
        temp_file = self.project_path / f".debug_temp_{filename}"
        try:
            temp_file.write_text(code, encoding='utf-8')
            result = self.execute_file(str(temp_file))
            return result
        finally:
            # 清理临时文件
            if temp_file.exists():
                temp_file.unlink()

    def execute_file(self, file_path: str) -> ExecutionResult:
        """
        直接执行文件

        Args:
            file_path: 文件路径（相对或绝对）

        Returns:
            ExecutionResult
        """
        resolved_path = self._resolve_path(file_path)
        if not resolved_path.exists():
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"文件不存在: {file_path} (resolved: {resolved_path})",
                exit_code=-1
            )

        # 确定工作目录：如果文件在子目录，使用文件的父目录或 project_path
        # 关键：对于子目录中的文件（如 app/main.py），需要正确设置 cwd 和 PYTHONPATH
        if resolved_path.parent != self.project_path and self.project_path in resolved_path.parents:
            # 文件在 project_path 的子目录中，使用 project_path 作为 cwd
            work_dir = self.project_path
        else:
            # 使用文件所在目录
            work_dir = resolved_path.parent

        # 设置环境变量，确保跨文件 import 正常
        env = os.environ.copy()
        # PYTHONPATH 包含 project_path 和文件所在目录（如果不同）
        python_paths = [str(self.project_path)]
        if work_dir != self.project_path:
            python_paths.append(str(work_dir))
        env["PYTHONPATH"] = os.pathsep.join(python_paths)

        logger.debug(f"执行文件: {resolved_path}, cwd={work_dir}, PYTHONPATH={env['PYTHONPATH']}")

        try:
            result = subprocess.run(
                [sys.executable, str(resolved_path)],
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env
            )

            success = result.returncode == 0

            # 检查 stderr 中是否有错误（有些程序 returncode=0 但有警告）
            stderr_lower = result.stderr.lower()
            has_error = any(err in stderr_lower for err in ['error', 'traceback', 'exception'])

            if success and has_error:
                # returncode=0 但有错误信息，可能是被捕获的异常
                logger.warning(f"returncode=0 但 stderr 有错误信息")
                success = False

            logger.info(f"执行完成: success={success}, returncode={result.returncode}")
            if not success:
                logger.debug(f"stderr: {result.stderr[:500]}")

            return ExecutionResult(
                success=success,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode
            )

        except subprocess.TimeoutExpired:
            logger.warning(f"执行超时 ({self.timeout}s)")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"执行超时 ({self.timeout}s)",
                exit_code=-1
            )
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1
            )

    def execute_with_fixes(
        self,
        main_file: str,
        fixes: dict[str, str],
        backup: bool = True
    ) -> ExecutionResult:
        """
        应用修复并执行

        Args:
            main_file: 主文件路径（相对于 project_path 或绝对路径）
            fixes: 修复内容 {文件路径: 修复后的代码}
            backup: 是否备份原文件

        Returns:
            ExecutionResult
        """
        backups = {}
        resolved_paths = {}  # 保存解析后的路径，用于回滚

        try:
            # 1. 备份并写入修复
            for file_path, fixed_code in fixes.items():
                # 使用智能路径解析
                full_path = self._resolve_path(file_path)
                resolved_paths[file_path] = full_path

                if backup and full_path.exists():
                    backups[file_path] = full_path.read_text(encoding='utf-8')

                # 确保目录存在
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(fixed_code, encoding='utf-8')
                logger.info(f"已写入修复: {file_path} -> {full_path}")

            # 2. 执行主文件（execute_file 内部会使用 _resolve_path）
            result = self.execute_file(main_file)

            # 3. 如果失败且有备份，回滚
            if not result.success and backup and backups:
                logger.info("执行失败，回滚修改...")
                for file_path, original_code in backups.items():
                    full_path = resolved_paths.get(file_path) or self._resolve_path(file_path)
                    full_path.write_text(original_code, encoding='utf-8')
                    logger.info(f"已回滚: {file_path}")

            return result

        except Exception as e:
            logger.error(f"执行修复失败: {e}")
            # 回滚
            if backup and backups:
                for file_path, original_code in backups.items():
                    try:
                        full_path = resolved_paths.get(file_path) or self._resolve_path(file_path)
                        full_path.write_text(original_code, encoding='utf-8')
                    except:
                        pass

            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1
            )
