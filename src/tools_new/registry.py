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

if TYPE_CHECKING:
    from .context_tools import ContextTools

logger = logging.getLogger(__name__)


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool
        logger.debug(f"注册工具: {tool.name}")

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)

    def get_all_schemas(self) -> List[dict]:
        """获取所有工具的 schema（用于 LLM function calling）"""
        return [tool.to_schema() for tool in self._tools.values()]

    def register_all_defaults(self, context_tools: "ContextTools", project_root: str = "."):
        """注册所有默认工具"""
        self.register(SearchSymbolTool(context_tools))
        self.register(ReadFileTool(project_root))
        self.register(GrepTool(project_root))
        self.register(GetCallersTool(context_tools))
        self.register(SetPhaseTool())
        self.register(CompleteInvestigationTool())

        logger.info(f"已注册 {len(self._tools)} 个工具")

    def list_all(self) -> List[str]:
        """列出所有已注册的工具"""
        return list(self._tools.keys())
