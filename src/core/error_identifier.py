"""ErrorIdentifier - 错误识别器（新架构）"""
import re
import logging
from typing import Optional

from src.models.error_context import ErrorContext

logger = logging.getLogger(__name__)


class ErrorIdentifier:
    """从 traceback 中识别错误信息"""

    # 常见错误类型
    ERROR_TYPES = [
        "NameError",
        "ImportError",
        "ModuleNotFoundError",
        "AttributeError",
        "TypeError",
        "KeyError",
        "ValueError",
        "IndexError",
        "FileNotFoundError",
        "ZeroDivisionError",
        "SyntaxError"
    ]

    def identify(self, traceback: str) -> ErrorContext:
        """
        从 traceback 中识别错误

        Args:
            traceback: 完整的 Python traceback 字符串

        Returns:
            ErrorContext 对象

        Raises:
            ValueError: 如果输入为空或无法解析
        """
        if not traceback or not isinstance(traceback, str):
            raise ValueError("traceback 必须是非空字符串")

        traceback = traceback.strip()
        if not traceback:
            raise ValueError("traceback 不能为空")

        # 提取错误类型和消息
        error_type, error_message = self._extract_error_type_and_message(traceback)

        # 提取文件和行号
        error_file, error_line = self._extract_file_and_line(traceback)

        logger.info(f"识别错误: {error_type} - {error_message}")

        return ErrorContext(
            error_type=error_type,
            error_message=error_message,
            error_file=error_file,
            error_line=error_line,
            traceback=traceback
        )

    def _extract_error_type_and_message(self, traceback: str) -> tuple[str, str]:
        """
        提取错误类型和消息

        从 traceback 的最后一行提取，格式通常是：
        ErrorType: error message
        """
        lines = traceback.strip().split('\n')

        # 从最后一行开始查找
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue

            # 匹配错误类型: 错误消息
            # 例如: NameError: name 'x' is not defined
            match = re.match(r'^(\w+(?:Error|Exception)):\s*(.+)$', line)
            if match:
                error_type = match.group(1)
                error_message = match.group(2).strip()
                return error_type, error_message

            # 有些错误没有消息，只有类型
            # 例如: KeyboardInterrupt
            for err_type in self.ERROR_TYPES:
                if line == err_type:
                    return err_type, ""

        # 未找到错误类型
        logger.warning("无法从 traceback 中提取错误类型，使用 UnknownError")
        return "UnknownError", traceback.split('\n')[-1] if traceback else ""

    def _extract_file_and_line(self, traceback: str) -> tuple[str, int]:
        """
        提取文件路径和行号

        从 traceback 中查找，格式通常是：
        File "path/to/file.py", line 10, in function_name

        注意：返回最后一个匹配（实际错误发生位置），而非第一个

        特殊处理：对于 "cannot import name 'X' from 'module' (path)"，
        返回被导入的模块路径而不是导入语句所在的文件
        """
        lines = traceback.split('\n')

        last_file = ""
        last_line = 0

        for line in lines:
            # 匹配文件和行号
            # File "main.py", line 10
            match = re.search(r'File\s+"([^"]+)",\s+line\s+(\d+)', line)
            if match:
                last_file = match.group(1)
                last_line = int(match.group(2))

        # 特殊处理：ImportError: cannot import name 'X' from 'module' (/path/to/module.py)
        # 这种情况下，实际错误在被导入的模块中，而不是执行import的文件
        import_error_match = re.search(
            r"cannot import name ['\"](\w+)['\"] from ['\"](\w+)['\"] \(([^)]+)\)",
            traceback
        )
        if import_error_match:
            target_module_path = import_error_match.group(3)
            logger.debug(f"ImportError 特殊处理: 实际错误在 {target_module_path}")
            return target_module_path, 1  # 行号设为1，因为需要搜索整个文件

        # 返回最后一个匹配（实际错误发生的位置）
        return last_file, last_line

    def is_cross_file_error(self, error_context: ErrorContext) -> bool:
        """
        快速判断是否可能是跨文件错误

        Args:
            error_context: 错误上下文

        Returns:
            True 如果可能是跨文件错误
        """
        # NameError, ImportError, AttributeError 通常是跨文件错误
        cross_file_types = {
            "NameError",
            "ImportError",
            "ModuleNotFoundError",
            "AttributeError"
        }

        return error_context.error_type in cross_file_types
