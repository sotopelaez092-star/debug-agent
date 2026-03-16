"""工具基类定义"""
from abc import ABC, abstractmethod
from typing import Any, Dict
import logging

from src.models.tool_result import ToolResult, ErrorType

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """工具基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """执行工具（子类实现具体逻辑）"""
        pass

    async def safe_execute(self, **kwargs) -> ToolResult:
        """安全执行工具（包含参数验证和错误处理）

        这是一个包装方法，会：
        1. 验证参数
        2. 调用 execute()
        3. 捕获异常并返回结构化结果
        """
        # 参数验证
        validation_error = self.validate_parameters(kwargs)
        if validation_error:
            logger.warning(f"[{self.name}] 参数验证失败: {validation_error}")
            return ToolResult.error_result(
                error=f"参数验证失败: {validation_error}",
                error_type=ErrorType.VALIDATION
            )

        # 执行工具
        try:
            result = await self.execute(**kwargs)
            # 如果工具已经返回 ToolResult，直接使用
            if isinstance(result, ToolResult):
                return result
            # 否则包装为成功结果
            return ToolResult.success_result(result)

        except FileNotFoundError as e:
            error_msg = f"文件不存在: {str(e)}"
            logger.error(f"[{self.name}] {error_msg}")
            return ToolResult.error_result(error_msg, ErrorType.NOT_FOUND)

        except PermissionError as e:
            error_msg = f"权限不足: {str(e)}"
            logger.error(f"[{self.name}] {error_msg}")
            return ToolResult.error_result(error_msg, ErrorType.PERMISSION)

        except TimeoutError as e:
            error_msg = f"操作超时: {str(e)}"
            logger.error(f"[{self.name}] {error_msg}")
            return ToolResult.error_result(error_msg, ErrorType.TIMEOUT)

        except ValueError as e:
            error_msg = f"参数错误: {str(e)}"
            logger.warning(f"[{self.name}] {error_msg}")
            return ToolResult.error_result(error_msg, ErrorType.VALIDATION)

        except Exception as e:
            error_msg = f"执行失败: {type(e).__name__}: {str(e)}"
            logger.error(f"[{self.name}] {error_msg}", exc_info=True)
            return ToolResult.error_result(error_msg, ErrorType.INTERNAL)

    def validate_parameters(self, params: dict) -> str | None:
        """验证参数（可选实现）

        Returns:
            错误消息（如果验证失败），None（如果验证通过）
        """
        schema = self.get_parameters_schema()
        required_params = schema.get("required", [])

        # 检查必需参数
        for param_name in required_params:
            if param_name not in params:
                return f"缺少必需参数: {param_name}"

        # 检查参数类型（基础检查）
        properties = schema.get("properties", {})
        for param_name, param_value in params.items():
            if param_name in properties:
                expected_type = properties[param_name].get("type")
                if expected_type and not self._check_type(param_value, expected_type):
                    return f"参数 {param_name} 类型错误: 期望 {expected_type}, 得到 {type(param_value).__name__}"

        return None

    @staticmethod
    def _check_type(value: Any, expected_type: str) -> bool:
        """检查值是否符合预期类型"""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type is None:
            return True  # 未知类型，跳过检查
        return isinstance(value, expected_python_type)

    def to_schema(self) -> dict:
        """转换为 LLM tool schema (OpenAI function calling 格式)"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema()
            }
        }

    @abstractmethod
    def get_parameters_schema(self) -> dict:
        """获取参数 schema"""
        pass
