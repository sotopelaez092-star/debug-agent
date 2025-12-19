"""文件读取工具"""
from pathlib import Path
import logging
from .base import BaseTool
from src.models.tool_result import ToolResult, ErrorType

logger = logging.getLogger(__name__)


class ReadFileTool(BaseTool):
    """读取文件内容，可指定行范围"""

    def __init__(self, project_root: str = "."):
        if not project_root:
            raise ValueError("project_root 不能为空")
        self.project_root = Path(project_root)
        if not self.project_root.exists():
            logger.warning(f"项目根目录不存在: {project_root}")

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "读取指定文件的内容，可以指定起始和结束行号来读取部分内容。返回带行号的文件内容。"

    async def execute(self, path: str, start_line: int = 1, end_line: int = None) -> str:
        """执行文件读取

        Args:
            path: 文件路径（相对于项目根目录或绝对路径）
            start_line: 起始行号（从1开始）
            end_line: 结束行号（None 表示读到文件末尾）

        Returns:
            带行号的文件内容字符串

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 参数验证失败
            UnicodeDecodeError: 文件编码错误
        """
        # 参数验证
        if not path or not isinstance(path, str):
            raise ValueError(f"path 必须是非空字符串，得到: {type(path).__name__}")

        if start_line < 1:
            raise ValueError(f"start_line 必须 >= 1，得到: {start_line}")

        if end_line is not None and end_line < start_line:
            raise ValueError(f"end_line ({end_line}) 不能小于 start_line ({start_line})")

        # 标准化路径：去掉可能的重复前缀
        normalized_path = path
        project_name = self.project_root.name
        if path.startswith(f"{project_name}/"):
            # 去掉重复的项目目录前缀
            normalized_path = path[len(project_name) + 1:]
            logger.debug(f"去除重复前缀: {path} -> {normalized_path}")

        # 如果是相对路径，相对于项目根目录
        file_path = self.project_root / normalized_path if not Path(normalized_path).is_absolute() else Path(normalized_path)

        # 检查文件是否存在
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {path} (解析为: {file_path})")

        # 检查是否是文件
        if not file_path.is_file():
            raise ValueError(f"路径不是文件: {path}")

        # 读取文件
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError as e:
            logger.error(f"文件编码错误: {file_path}")
            raise UnicodeDecodeError(
                e.encoding, e.object, e.start, e.end,
                f"无法以 UTF-8 编码读取文件: {path}"
            )

        lines = content.split('\n')
        total_lines = len(lines)

        # 调整行号（从1开始）
        start_idx = max(0, start_line - 1)
        end_idx = total_lines if end_line is None else min(total_lines, end_line)

        if start_idx >= total_lines:
            logger.warning(f"起始行号 {start_line} 超出文件范围 (共 {total_lines} 行)")
            return f"文件共 {total_lines} 行，起始行号 {start_line} 超出范围"

        selected_lines = lines[start_idx:end_idx]

        # 返回带行号的内容
        result_lines = []
        for i, line in enumerate(selected_lines, start=start_line):
            result_lines.append(f"{i:4d}: {line}")

        logger.debug(f"成功读取 {file_path.name}，行范围: {start_line}-{end_idx}")
        return '\n'.join(result_lines)

    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径（相对于项目根目录或绝对路径）"
                },
                "start_line": {
                    "type": "integer",
                    "description": "起始行号（从1开始，默认1）",
                    "default": 1,
                    "minimum": 1
                },
                "end_line": {
                    "type": "integer",
                    "description": "结束行号（不指定则读取到文件末尾）",
                    "minimum": 1
                }
            },
            "required": ["path"]
        }
