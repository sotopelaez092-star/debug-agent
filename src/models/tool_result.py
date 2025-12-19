"""工具执行结果的统一数据结构"""
from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum


class ErrorType(Enum):
    """错误类型枚举"""
    VALIDATION = "validation"  # 参数验证错误
    NOT_FOUND = "not_found"  # 资源不找到
    PERMISSION = "permission"  # 权限错误
    TIMEOUT = "timeout"  # 超时
    PARSE_ERROR = "parse_error"  # 解析错误
    NETWORK = "network"  # 网络错误
    INTERNAL = "internal"  # 内部错误
    UNKNOWN = "unknown"  # 未知错误


@dataclass
class ToolResult:
    """工具执行结果

    Attributes:
        success: 是否成功执行
        data: 返回的数据（成功时）
        error: 错误消息（失败时）
        error_type: 错误类型（失败时）
        metadata: 额外的元数据（如耗时、重试次数等）
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    metadata: Optional[dict] = None

    @classmethod
    def success_result(cls, data: Any, metadata: Optional[dict] = None) -> "ToolResult":
        """创建成功结果"""
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def error_result(
        cls,
        error: str,
        error_type: ErrorType = ErrorType.UNKNOWN,
        metadata: Optional[dict] = None
    ) -> "ToolResult":
        """创建错误结果"""
        return cls(
            success=False,
            error=error,
            error_type=error_type,
            metadata=metadata
        )

    def to_string(self) -> str:
        """转换为字符串（用于 LLM 可读的格式）"""
        if self.success:
            return str(self.data) if self.data is not None else "操作成功完成"
        else:
            error_prefix = f"[{self.error_type.value.upper()}]" if self.error_type else "[ERROR]"
            return f"{error_prefix} {self.error}"
