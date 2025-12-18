"""文件读取工具"""
from pathlib import Path
from .base import BaseTool


class ReadFileTool(BaseTool):
    """读取文件内容，可指定行范围"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "读取指定文件的内容，可以指定起始和结束行号来读取部分内容。返回带行号的文件内容。"

    async def execute(self, path: str, start_line: int = 1, end_line: int = None) -> str:
        """执行文件读取"""
        try:
            # 标准化路径：去掉可能的重复前缀
            normalized_path = path
            project_name = self.project_root.name
            if path.startswith(f"{project_name}/"):
                # 去掉重复的项目目录前缀
                normalized_path = path[len(project_name) + 1:]

            # 如果是相对路径，相对于项目根目录
            file_path = self.project_root / normalized_path if not Path(normalized_path).is_absolute() else Path(normalized_path)

            if not file_path.exists():
                return f"错误: 文件不存在 - {path}"

            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # 调整行号（从1开始）
            start_idx = max(0, start_line - 1)
            end_idx = len(lines) if end_line is None else min(len(lines), end_line)

            selected_lines = lines[start_idx:end_idx]

            # 返回带行号的内容
            result_lines = []
            for i, line in enumerate(selected_lines, start=start_line):
                result_lines.append(f"{i:4d}: {line}")

            return '\n'.join(result_lines)

        except UnicodeDecodeError:
            return f"错误: 无法读取文件（编码错误） - {path}"
        except Exception as e:
            return f"错误: 读取文件失败 - {str(e)}"

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
                    "default": 1
                },
                "end_line": {
                    "type": "integer",
                    "description": "结束行号（不指定则读取到文件末尾）"
                }
            },
            "required": ["path"]
        }
