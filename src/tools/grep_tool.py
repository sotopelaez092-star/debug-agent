"""代码搜索工具（grep）"""
import re
import subprocess
from pathlib import Path
from typing import List
import logging
from .base import BaseTool

logger = logging.getLogger(__name__)


class GrepTool(BaseTool):
    """在代码库中搜索关键词或正则表达式"""

    def __init__(self, project_root: str = "."):
        if not project_root:
            raise ValueError("project_root 不能为空")
        self.project_root = Path(project_root)
        if not self.project_root.exists():
            logger.warning(f"项目根目录不存在: {project_root}")

    @property
    def name(self) -> str:
        return "grep"

    @property
    def description(self) -> str:
        return "在代码库中搜索关键词或正则表达式。返回包含匹配内容的文件路径、行号和匹配行。"

    async def execute(self, pattern: str, path: str = ".", use_regex: bool = False) -> List[dict]:
        """执行 grep 搜索

        Args:
            pattern: 要搜索的关键词或正则表达式
            path: 搜索路径（相对于项目根目录）
            use_regex: 是否将 pattern 视为正则表达式

        Returns:
            匹配结果列表，每个结果包含 file, line, content

        Raises:
            ValueError: 参数验证失败
            TimeoutError: 搜索超时
        """
        # 参数验证
        if not pattern or not isinstance(pattern, str):
            raise ValueError(f"pattern 必须是非空字符串，得到: {type(pattern).__name__}")

        if not isinstance(path, str):
            raise ValueError(f"path 必须是字符串，得到: {type(path).__name__}")

        # 构建搜索路径
        if path == ".":
            search_path = self.project_root
        else:
            search_path = self.project_root / path
            if not search_path.exists():
                logger.warning(f"搜索路径不存在: {search_path}")
                return []

        # 尝试使用系统的 ripgrep (rg)
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
                logger.debug(f"ripgrep 搜索成功: {pattern}")
                return self._parse_rg_output(result.stdout)
            elif result.returncode == 1:
                # ripgrep 返回 1 表示没有匹配
                logger.debug(f"ripgrep 未找到匹配: {pattern}")
                return []

        except FileNotFoundError:
            logger.debug("ripgrep 未安装，使用 Python 实现")
        except subprocess.TimeoutExpired:
            logger.warning(f"ripgrep 搜索超时: {pattern}")
            raise TimeoutError(f"搜索超时 (>10s): {pattern}")
        except Exception as e:
            logger.warning(f"ripgrep 执行失败: {e}，使用 Python 实现")

        # 回退到 Python 实现
        return self._python_grep(pattern, search_path, use_regex)

    def _parse_rg_output(self, output: str) -> List[dict]:
        """解析 ripgrep JSON 输出

        Args:
            output: ripgrep 的 JSON 输出

        Returns:
            解析后的匹配结果列表
        """
        import json
        results = []

        if not output or not output.strip():
            return results

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
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug(f"解析 ripgrep 输出行失败: {e}")
                continue
            except Exception as e:
                logger.warning(f"处理 ripgrep 输出时出错: {e}")
                continue

        return results

    def _python_grep(self, pattern: str, search_path: Path, use_regex: bool) -> List[dict]:
        """Python 实现的 grep

        Args:
            pattern: 搜索模式
            search_path: 搜索路径
            use_regex: 是否使用正则表达式

        Returns:
            匹配结果列表
        """
        results = []

        # 编译正则表达式（带错误处理）
        regex_pattern = None
        if use_regex:
            try:
                regex_pattern = re.compile(pattern)
                logger.debug(f"使用正则表达式: {pattern}")
            except re.error as e:
                # 无效的正则表达式，回退到字面量搜索
                logger.warning(f"正则表达式无效 '{pattern}': {e}，回退到字面量搜索")
                use_regex = False
                # 转义特殊字符用于字面量搜索
                pattern = re.escape(pattern)

        IGNORE_PATTERNS = [
            'venv', 'env', '.venv', '__pycache__', '.pytest_cache',
            '.git', 'node_modules', 'dist', 'build', '.debug_agent_cache'
        ]

        try:
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
                                logger.debug(f"达到结果上限 (50)，停止搜索")
                                return results

                except UnicodeDecodeError:
                    logger.debug(f"跳过非 UTF-8 文件: {py_file}")
                    continue
                except Exception as e:
                    logger.debug(f"读取文件失败 {py_file}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Python grep 搜索失败: {e}", exc_info=True)
            # 返回已找到的结果

        logger.debug(f"Python grep 找到 {len(results)} 个匹配")
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
