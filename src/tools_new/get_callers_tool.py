"""函数调用者查询工具"""
from typing import List, TYPE_CHECKING
from .base import BaseTool

if TYPE_CHECKING:
    from .context_tools import ContextTools


class GetCallersTool(BaseTool):
    """获取调用某个函数的所有位置"""

    def __init__(self, context_tools: "ContextTools"):
        self.context_tools = context_tools

    @property
    def name(self) -> str:
        return "get_callers"

    @property
    def description(self) -> str:
        return "获取调用指定函数的所有位置。返回调用者的文件路径、行号和函数名。"

    async def execute(self, name: str) -> List[dict]:
        """执行调用者查询"""
        return self.context_tools.get_callers(name)

    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "要查询的函数名"
                }
            },
            "required": ["name"]
        }
