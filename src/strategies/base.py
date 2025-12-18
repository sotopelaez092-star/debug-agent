"""错误处理策略基类"""
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.tools_new.context_tools import ContextTools
    from src.models.results import SearchResult


class BaseErrorStrategy(ABC):
    """错误处理策略基类"""

    def __init__(self, confidence_threshold: float = 0.7):
        """
        初始化策略

        Args:
            confidence_threshold: 置信度阈值 (0.0-1.0)，默认 0.7
        """
        self.confidence_threshold = confidence_threshold

    @property
    @abstractmethod
    def error_type(self) -> str:
        """错误类型名称"""
        pass

    @abstractmethod
    def extract(self, error_message: str) -> dict:
        """
        从错误信息提取关键字段

        Args:
            error_message: 错误消息

        Returns:
            提取的关键信息字典
        """
        pass

    @abstractmethod
    def fast_search(
        self,
        extracted: dict,
        tools: "ContextTools",
        error_file: str = ""
    ) -> Optional["SearchResult"]:
        """
        快速路径搜索

        Args:
            extracted: 提取的关键信息
            tools: ContextTools 实例
            error_file: 出错文件路径

        Returns:
            SearchResult 如果找到高置信度结果，否则 None
        """
        pass
