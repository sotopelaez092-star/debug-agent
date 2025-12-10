"""
BaseHandler - 错误处理器基类

定义错误处理器的通用接口
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class BaseErrorHandler(ABC):
    """
    错误处理器基类

    所有具体的错误处理器都应继承此类，并实现以下方法：
    - collect_context(): 收集错误相关的上下文
    - suggest_fix(): 生成修复建议
    - get_search_query(): 生成 RAG 搜索查询
    """

    # 处理器支持的错误类型
    supported_errors: List[str] = []

    def __init__(self):
        """初始化处理器"""
        self.name = self.__class__.__name__
        logger.debug(f"初始化错误处理器: {self.name}")

    @abstractmethod
    def collect_context(
        self,
        error_info: Dict[str, Any],
        project_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        收集错误相关的上下文信息

        Args:
            error_info: 错误信息字典
            project_path: 项目路径

        Returns:
            上下文信息字典
        """
        pass

    @abstractmethod
    def suggest_fix(
        self,
        error_info: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成修复建议

        Args:
            error_info: 错误信息
            context: 上下文信息

        Returns:
            修复建议字典
        """
        pass

    @abstractmethod
    def get_search_query(self, error_info: Dict[str, Any]) -> str:
        """
        生成 RAG 搜索查询

        Args:
            error_info: 错误信息

        Returns:
            搜索查询字符串
        """
        pass

    def can_handle(self, error_type: str) -> bool:
        """
        检查是否可以处理该错误类型

        Args:
            error_type: 错误类型

        Returns:
            是否可以处理
        """
        return error_type in self.supported_errors

    def get_priority_hints(self, error_info: Dict[str, Any]) -> List[str]:
        """
        获取修复优先级提示

        Args:
            error_info: 错误信息

        Returns:
            提示列表
        """
        return []
