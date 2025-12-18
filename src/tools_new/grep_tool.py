"""代码搜索工具（grep）"""
import re
import subprocess
from pathlib import Path
from typing import List
from .base import BaseTool


class GrepTool(BaseTool):
    """在代码库中搜索关键词或正则表达式"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)

    @property
    def name(self) -> str:
        return "grep"

    @property
    def description(self) -> str:
        return "在代码库中搜索关键词或正则表达式。返回包含匹配内容的文件路径、行号和匹配行。"

    async def execute(self, pattern: str, path: str = ".", use_regex: bool = False) -> List[dict]:
        """执行 grep 搜索"""
        search_path = self.project_root / path if path != "." else self.project_root

        # 尝试使用系统的 grep 或 ripgrep (rg)
        try:
            # 优先使用 ripgrep
            cmd = ["rg", "--json", "-n", pattern, str(search_path)]
            if not use_regex:
                cmd.insert(1, "-F")  # 固定字符串模式

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return self._parse_rg_output(result.stdout)

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # 回退到 Python 实现
        return self._python_grep(pattern, search_path, use_regex)

    def _parse_rg_output(self, output: str) -> List[dict]:
        """解析 ripgrep JSON 输出"""
        import json
        results = []
        for line in output.strip().split('\n'):
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get('type') == 'match':
                    match_data = data['data']
                    results.append({
                        'file': match_data['path']['text'],
                        'line': match_data['line_number'],
                        'content': match_data['lines']['text'].strip()
                    })
            except:
                continue
        return results

    def _python_grep(self, pattern: str, search_path: Path, use_regex: bool) -> List[dict]:
        """Python 实现的 grep"""
        results = []

        # 编译正则表达式（带错误处理）
        if use_regex:
            try:
                regex_pattern = re.compile(pattern)
            except re.error as e:
                # 无效的正则表达式，回退到字面量搜索
                use_regex = False
                regex_pattern = None
                # 转义特殊字符用于字面量搜索
                pattern = re.escape(pattern)
        else:
            regex_pattern = None

        IGNORE_PATTERNS = [
            'venv', 'env', '.venv', '__pycache__', '.pytest_cache',
            '.git', 'node_modules', 'dist', 'build'
        ]

        for py_file in search_path.rglob("*.py"):
            # 跳过忽略的目录
            if any(p in str(py_file) for p in IGNORE_PATTERNS):
                continue

            try:
                content = py_file.read_text(encoding='utf-8')
                for line_num, line in enumerate(content.split('\n'), 1):
                    match = False
                    if use_regex and regex_pattern:
                        match = regex_pattern.search(line)
                    else:
                        match = pattern in line

                    if match:
                        results.append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'line': line_num,
                            'content': line.strip()
                        })

                        # 限制结果数量
                        if len(results) >= 50:
                            return results

            except:
                continue

        return results

    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "要搜索的关键词或正则表达式"
                },
                "path": {
                    "type": "string",
                    "description": "搜索路径（相对于项目根目录，默认为整个项目）",
                    "default": "."
                },
                "use_regex": {
                    "type": "boolean",
                    "description": "是否将 pattern 视为正则表达式（默认 false）",
                    "default": False
                }
            },
            "required": ["pattern"]
        }
