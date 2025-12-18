"""调查阶段切换工具"""
from .base import BaseTool


class SetPhaseTool(BaseTool):
    """切换调查阶段"""

    @property
    def name(self) -> str:
        return "set_investigation_phase"

    @property
    def description(self) -> str:
        return """切换调查阶段。
- EXPLORE: 继续探索代码库，搜索更多相关文件和符号
- ANALYZE: 已收集足够信息，开始分析根本原因

只有在确认信息完整时才切换到 ANALYZE 阶段。"""

    async def execute(self, phase: str, reason: str) -> dict:
        """执行阶段切换"""
        if phase not in ("EXPLORE", "ANALYZE"):
            return {
                "success": False,
                "error": "阶段必须是 EXPLORE 或 ANALYZE"
            }

        return {
            "success": True,
            "phase": phase,
            "reason": reason
        }

    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "phase": {
                    "type": "string",
                    "enum": ["EXPLORE", "ANALYZE"],
                    "description": "目标阶段"
                },
                "reason": {
                    "type": "string",
                    "description": "切换阶段的原因"
                }
            },
            "required": ["phase", "reason"]
        }
