"""符号搜索工具"""
from typing import List, TYPE_CHECKING
import logging
from .base import BaseTool

if TYPE_CHECKING:
    from .context_tools import ContextTools
    from src.models.results import SymbolMatch

logger = logging.getLogger(__name__)


class SearchSymbolTool(BaseTool):
    """在代码库中搜索函数/类/变量定义，支持模糊匹配"""

    def __init__(self, context_tools: "ContextTools"):
        if not context_tools:
            raise ValueError("context_tools 不能为空")
        self.context_tools = context_tools

    @property
    def name(self) -> str:
        return "search_symbol"

    @property
    def description(self) -> str:
        return "在代码库中搜索函数/类/变量定义，支持模糊匹配。返回符号的定义位置、文件路径和置信度。"

    async def execute(self, name: str, fuzzy: bool = True) -> List["SymbolMatch"]:
        """执行符号搜索

        Args:
            name: 要搜索的符号名（函数名、类名或变量名）
            fuzzy: 是否启用模糊匹配

        Returns:
            符号匹配结果列表

        Raises:
            ValueError: 参数验证失败
        """
        # 参数验证
        if not name or not isinstance(name, str):
            raise ValueError(f"name 必须是非空字符串，得到: {type(name).__name__}")

        if not isinstance(fuzzy, bool):
            raise ValueError(f"fuzzy 必须是布尔值，得到: {type(fuzzy).__name__}")

        try:
            results = self.context_tools.search_symbol(name, fuzzy)
            logger.debug(f"符号搜索 '{name}' 找到 {len(results)} 个结果")
            return results
        except Exception as e:
            logger.error(f"符号搜索失败 '{name}': {e}", exc_info=True)
            raise

    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "要搜索的符号名（函数名、类名或变量名）"
                },
                "fuzzy": {
                    "type": "boolean",
                    "description": "是否启用模糊匹配（默认 true）",
                    "default": True
                }
            },
            "required": ["name"]
        }
