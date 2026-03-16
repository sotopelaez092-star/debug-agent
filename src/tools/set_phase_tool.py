"""调查阶段切换工具"""
import logging
from .base import BaseTool

logger = logging.getLogger(__name__)


class SetPhaseTool(BaseTool):
    """切换调查阶段"""

    VALID_PHASES = ("EXPLORE", "ANALYZE")

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
        """执行阶段切换

        Args:
            phase: 目标阶段 (EXPLORE 或 ANALYZE)
            reason: 切换阶段的原因

        Returns:
            执行结果字典

        Raises:
            ValueError: 参数验证失败
        """
        # 参数验证
        if not phase or not isinstance(phase, str):
            raise ValueError(f"phase 必须是非空字符串，得到: {type(phase).__name__}")

        if not reason or not isinstance(reason, str):
            raise ValueError(f"reason 必须是非空字符串，得到: {type(reason).__name__}")

        if phase not in self.VALID_PHASES:
            raise ValueError(
                f"无效的阶段 '{phase}'，必须是 {' 或 '.join(self.VALID_PHASES)}"
            )

        if len(reason) < 10:
            raise ValueError(f"reason 太短（{len(reason)} 字符），至少需要 10 个字符")

        logger.info(f"切换调查阶段: {phase}，原因: {reason[:50]}...")
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
                    "enum": list(self.VALID_PHASES),
                    "description": "目标阶段"
                },
                "reason": {
                    "type": "string",
                    "description": "切换阶段的原因（至少10个字符）",
                    "minLength": 10
                }
            },
            "required": ["phase", "reason"]
        }
