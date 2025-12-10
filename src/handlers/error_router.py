"""
ErrorRouter - 错误路由器

根据错误类型路由到专门的处理器
"""

import logging
from typing import Dict, List, Optional, Any, Type

from .base_handler import BaseErrorHandler
from .import_error_handler import ImportErrorHandler
from .name_error_handler import NameErrorHandler
from .type_error_handler import TypeErrorHandler

logger = logging.getLogger(__name__)


class GenericErrorHandler(BaseErrorHandler):
    """通用错误处理器，用于处理未知错误类型"""

    supported_errors = ['*']

    def collect_context(
        self,
        error_info: Dict[str, Any],
        project_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """收集通用上下文"""
        return {
            'error_type': 'generic',
            'error_message': error_info.get('error_message', ''),
            'file': error_info.get('file'),
            'line': error_info.get('line'),
        }

    def suggest_fix(
        self,
        error_info: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成通用修复建议"""
        return {
            'primary_fix': None,
            'suggestions': [{
                'type': 'general',
                'description': f"发生 {error_info.get('error_type', '未知')} 错误",
                'hint': "查看错误信息和堆栈跟踪定位问题",
                'confidence': 'low',
            }],
            'confidence': 'low',
        }

    def get_search_query(self, error_info: Dict[str, Any]) -> str:
        """生成搜索查询"""
        error_type = error_info.get('error_type', 'Error')
        error_message = error_info.get('error_message', '')[:100]
        return f"Python {error_type} {error_message}"


class ErrorRouter:
    """
    错误路由器

    功能：
    1. 根据错误类型选择合适的处理器
    2. 管理处理器注册
    3. 提供统一的错误处理接口

    Attributes:
        handlers: 已注册的处理器 {错误类型: 处理器实例}
        default_handler: 默认处理器
    """

    def __init__(self):
        """初始化路由器"""
        self.handlers: Dict[str, BaseErrorHandler] = {}
        self.default_handler = GenericErrorHandler()

        # 注册默认处理器
        self._register_default_handlers()

        logger.info(f"ErrorRouter 初始化完成，已注册 {len(self.handlers)} 个处理器")

    def _register_default_handlers(self):
        """注册默认的错误处理器"""
        handlers = [
            ImportErrorHandler(),
            NameErrorHandler(),
            TypeErrorHandler(),
        ]

        for handler in handlers:
            for error_type in handler.supported_errors:
                self.register(error_type, handler)

    def register(self, error_type: str, handler: BaseErrorHandler):
        """
        注册错误处理器

        Args:
            error_type: 错误类型
            handler: 处理器实例
        """
        self.handlers[error_type] = handler
        logger.debug(f"注册处理器: {error_type} -> {handler.name}")

    def get_handler(self, error_type: str) -> BaseErrorHandler:
        """
        获取错误处理器

        Args:
            error_type: 错误类型

        Returns:
            对应的处理器，如果没有则返回默认处理器
        """
        handler = self.handlers.get(error_type, self.default_handler)
        logger.debug(f"路由 {error_type} -> {handler.name}")
        return handler

    def route(
        self,
        error_info: Dict[str, Any],
        project_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        路由错误到合适的处理器并执行处理

        Args:
            error_info: 错误信息字典，包含：
                - error_type: 错误类型
                - error_message: 错误信息
                - file: 错误文件
                - line: 错误行号
            project_path: 项目路径

        Returns:
            处理结果字典，包含：
                - handler: 使用的处理器名称
                - context: 收集的上下文
                - fix_suggestions: 修复建议
                - search_query: RAG 搜索查询
                - priority_hints: 优先级提示
        """
        error_type = error_info.get('error_type', 'UnknownError')

        # 获取处理器
        handler = self.get_handler(error_type)

        # 执行处理
        try:
            # 收集上下文
            context = handler.collect_context(error_info, project_path)

            # 生成修复建议
            fix_suggestions = handler.suggest_fix(error_info, context)

            # 生成搜索查询
            search_query = handler.get_search_query(error_info)

            # 获取优先级提示
            priority_hints = handler.get_priority_hints(error_info)

            result = {
                'handler': handler.name,
                'context': context,
                'fix_suggestions': fix_suggestions,
                'search_query': search_query,
                'priority_hints': priority_hints,
                'success': True,
            }

            logger.info(f"错误路由完成: {error_type} -> {handler.name}")
            return result

        except Exception as e:
            logger.error(f"错误处理失败: {e}", exc_info=True)
            return {
                'handler': handler.name,
                'context': {},
                'fix_suggestions': {'suggestions': [], 'confidence': 'low'},
                'search_query': f"Python {error_type}",
                'priority_hints': [],
                'success': False,
                'error': str(e),
            }

    def get_supported_errors(self) -> List[str]:
        """获取支持的错误类型列表"""
        return list(self.handlers.keys())

    def get_handler_info(self) -> Dict[str, str]:
        """获取所有处理器信息"""
        return {
            error_type: handler.name
            for error_type, handler in self.handlers.items()
        }
