"""函数调用者查询工具"""
from typing import List, TYPE_CHECKING
import logging
from .base import BaseTool

if TYPE_CHECKING:
    from .context_tools import ContextTools

logger = logging.getLogger(__name__)


class GetCallersTool(BaseTool):
    """获取调用某个函数的所有位置"""

    def __init__(self, context_tools: "ContextTools"):
        if not context_tools:
            raise ValueError("context_tools 不能为空")
        self.context_tools = context_tools

    @property
    def name(self) -> str:
        return "get_callers"

    @property
    def description(self) -> str:
        return "获取调用指定函数的所有位置。返回调用者的文件路径、行号和函数名。"

    async def execute(self, name: str) -> List[dict]:
        """执行调用者查询

        Args:
            name: 要查询的函数名

        Returns:
            调用者列表

        Raises:
            ValueError: 参数验证失败
        """
        # 参数验证
        if not name or not isinstance(name, str):
            raise ValueError(f"name 必须是非空字符串，得到: {type(name).__name__}")

        try:
            results = self.context_tools.get_callers(name)
            logger.debug(f"查询函数 '{name}' 的调用者，找到 {len(results)} 个位置")
            return results
        except Exception as e:
            logger.error(f"查询调用者失败 '{name}': {e}", exc_info=True)
            raise

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
