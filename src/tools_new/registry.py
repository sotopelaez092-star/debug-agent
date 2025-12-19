"""工具注册表"""
from typing import Dict, List, Optional, TYPE_CHECKING
import logging

from .base import BaseTool
from .search_symbol_tool import SearchSymbolTool
from .read_file_tool import ReadFileTool
from .grep_tool import GrepTool
from .get_callers_tool import GetCallersTool
from .set_phase_tool import SetPhaseTool
from .complete_investigation_tool import CompleteInvestigationTool
from src.models.tool_result import ToolResult, ErrorType

if TYPE_CHECKING:
    from .context_tools import ContextTools

logger = logging.getLogger(__name__)


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """注册工具

        Args:
            tool: 要注册的工具实例

        Raises:
            ValueError: 如果工具名称为空或已存在
        """
        if not tool or not tool.name:
            raise ValueError("工具名称不能为空")

        if tool.name in self._tools:
            logger.warning(f"工具 {tool.name} 已存在，将被覆盖")

        self._tools[tool.name] = tool
        logger.debug(f"注册工具: {tool.name}")

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具

        Args:
            name: 工具名称

        Returns:
            工具实例，如果不存在返回 None
        """
        if not name:
            logger.warning("尝试获取空名称的工具")
            return None

        tool = self._tools.get(name)
        if tool is None:
            logger.warning(f"工具不存在: {name}，可能是 LLM 幻觉")

        return tool

    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """安全执行工具（处理 LLM 幻觉）

        Args:
            name: 工具名称
            **kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        # 检查工具是否存在（处理 LLM 幻觉）
        if not name:
            return ToolResult.error_result(
                error="工具名称为空",
                error_type=ErrorType.VALIDATION
            )

        tool = self.get(name)
        if tool is None:
            available_tools = ", ".join(self.list_all())
            error_msg = (
                f"工具 '{name}' 不存在。"
                f"可用工具: {available_tools}"
            )
            logger.warning(f"[LLM 幻觉] {error_msg}")
            return ToolResult.error_result(
                error=error_msg,
                error_type=ErrorType.NOT_FOUND
            )

        # 执行工具
        return await tool.safe_execute(**kwargs)

    def get_all_schemas(self) -> List[dict]:
        """获取所有工具的 schema（用于 LLM function calling）"""
        return [tool.to_schema() for tool in self._tools.values()]

    def register_all_defaults(self, context_tools: "ContextTools", project_root: str = "."):
        """注册所有默认工具

        Args:
            context_tools: 上下文工具实例
            project_root: 项目根目录路径
        """
        try:
            self.register(SearchSymbolTool(context_tools))
            self.register(ReadFileTool(project_root))
            self.register(GrepTool(project_root))
            self.register(GetCallersTool(context_tools))
            self.register(SetPhaseTool())
            self.register(CompleteInvestigationTool())

            logger.info(f"已注册 {len(self._tools)} 个工具")
        except Exception as e:
            logger.error(f"注册默认工具失败: {e}", exc_info=True)
            raise

    def list_all(self) -> List[str]:
        """列出所有已注册的工具"""
        return list(self._tools.keys())
