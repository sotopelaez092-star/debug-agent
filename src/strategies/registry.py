"""错误策略注册表"""
from typing import Dict, Optional
import logging

from .base import BaseErrorStrategy
from .name_error import NameErrorStrategy
from .import_error import ImportErrorStrategy
from .attribute_error import AttributeErrorStrategy
from .type_error import TypeErrorStrategy
from .key_error import KeyErrorStrategy
from .circular_import import CircularImportStrategy

logger = logging.getLogger(__name__)


class ErrorStrategyRegistry:
    """错误策略注册表"""

    def __init__(self):
        self._strategies: Dict[str, BaseErrorStrategy] = {}

    def register(self, strategy: BaseErrorStrategy):
        """注册错误策略"""
        self._strategies[strategy.error_type] = strategy
        logger.debug(f"注册错误策略: {strategy.error_type}")

        # ImportError 和 ModuleNotFoundError 共用策略
        if strategy.error_type == "ImportError":
            self._strategies["ModuleNotFoundError"] = strategy
            logger.debug("注册错误策略: ModuleNotFoundError (共享 ImportError 策略)")

    def get(self, error_type: str) -> Optional[BaseErrorStrategy]:
        """获取错误策略"""
        return self._strategies.get(error_type)

    def register_all_defaults(self, confidence_threshold: float = 0.7):
        """
        注册所有默认策略

        Args:
            confidence_threshold: 置信度阈值 (0.0-1.0)，默认 0.7
        """
        self.register(NameErrorStrategy(confidence_threshold))
        self.register(ImportErrorStrategy(max(confidence_threshold, 0.75)))  # ImportError 默认阈值稍高
        self.register(AttributeErrorStrategy(confidence_threshold))
        self.register(TypeErrorStrategy(confidence_threshold))
        self.register(KeyErrorStrategy(confidence_threshold))
        self.register(CircularImportStrategy(confidence_threshold))
        logger.info(f"已注册 {len(self._strategies)} 个错误策略 (阈值={confidence_threshold})")

    def list_all(self) -> list:
        """列出所有已注册的策略"""
        return list(self._strategies.keys())
