"""调查完成工具"""
from pydantic import ValidationError
import logging
from .base import BaseTool
from src.models.investigation_report import InvestigationReport

logger = logging.getLogger(__name__)


class CompleteInvestigationTool(BaseTool):
    """提交调查报告，标记调查完成"""

    @property
    def name(self) -> str:
        return "complete_investigation"

    @property
    def description(self) -> str:
        return """提交最终调查报告。调查完成时必须调用此工具。

报告必须包含以下字段：
- summary: 调查总结（至少10个字符）
- relevant_locations: 相关代码位置列表（至少1个位置）
- root_cause: 根本原因分析
- suggested_fix: 建议的修复方案
- confidence: 置信度（0-1之间的浮点数）
- exploration_trace: 探索轨迹（可选）

每个 relevant_location 需要包含：
- file_path: 文件路径
- line: 行号
- symbol: 符号名称
- reasoning: 选择此位置的原因
- code_snippet: 代码片段（可选）"""

    async def execute(self, report: dict) -> dict:
        """执行调查完成

        Args:
            report: 调查报告字典

        Returns:
            执行结果字典

        Raises:
            ValueError: 参数验证失败
        """
        # 参数验证
        if not report or not isinstance(report, dict):
            raise ValueError(f"report 必须是非空字典，得到: {type(report).__name__}")

        try:
            # 使用 Pydantic 验证报告格式
            validated = InvestigationReport(**report)
            logger.info(
                f"调查完成，置信度: {validated.confidence:.2f}，"
                f"相关位置数: {len(validated.relevant_locations)}"
            )
            return {
                "success": True,
                "report": validated
            }
        except ValidationError as e:
            # 返回详细的验证错误
            errors = []
            for error in e.errors():
                field = " -> ".join(str(x) for x in error['loc'])
                msg = error['msg']
                errors.append(f"{field}: {msg}")

            error_msg = "报告格式错误:\n" + "\n".join(errors)
            logger.warning(f"调查报告验证失败: {error_msg}")

            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            logger.error(f"处理调查报告时出错: {e}", exc_info=True)
            raise

    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "report": {
                    "type": "object",
                    "description": "调查报告对象",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "调查总结（至少10个字符）"
                        },
                        "relevant_locations": {
                            "type": "array",
                            "description": "相关代码位置列表",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "file_path": {"type": "string"},
                                    "line": {"type": "integer"},
                                    "symbol": {"type": "string"},
                                    "reasoning": {"type": "string"},
                                    "code_snippet": {"type": "string"}
                                },
                                "required": ["file_path", "line", "symbol", "reasoning"]
                            }
                        },
                        "root_cause": {
                            "type": "string",
                            "description": "根本原因分析"
                        },
                        "suggested_fix": {
                            "type": "string",
                            "description": "建议的修复方案"
                        },
                        "confidence": {
                            "type": "number",
                            "description": "置信度（0-1）",
                            "minimum": 0,
                            "maximum": 1
                        },
                        "exploration_trace": {
                            "type": "array",
                            "description": "探索轨迹（可选）",
                            "items": {"type": "string"}
                        }
                    },
                    "required": [
                        "summary",
                        "relevant_locations",
                        "root_cause",
                        "suggested_fix",
                        "confidence"
                    ]
                }
            },
            "required": ["report"]
        }
