"""符号搜索工具"""
from typing import List, TYPE_CHECKING
from .base import BaseTool

if TYPE_CHECKING:
    from .context_tools import ContextTools
    from src.models.results import SymbolMatch


class SearchSymbolTool(BaseTool):
    """在代码库中搜索函数/类/变量定义，支持模糊匹配"""

    def __init__(self, context_tools: "ContextTools"):
        self.context_tools = context_tools

    @property
    def name(self) -> str:
        return "search_symbol"

    @property
    def description(self) -> str:
        return "在代码库中搜索函数/类/变量定义，支持模糊匹配。返回符号的定义位置、文件路径和置信度。"

    async def execute(self, name: str, fuzzy: bool = True) -> List["SymbolMatch"]:
        """执行符号搜索"""
        return self.context_tools.search_symbol(name, fuzzy)

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
