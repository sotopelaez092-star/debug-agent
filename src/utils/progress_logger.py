"""进度日志系统 - 用户友好的实时进度显示"""
import logging
import sys
from typing import Optional

# 全局开关
_enabled = True


class ProgressLogger:
    """进度日志器 - 同时输出到控制台和日志文件"""

    def __init__(self, name: str = "debug_agent", level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # 避免重复添加 handler
        if self.logger.handlers:
            return

        # 1. 控制台 handler（用户可见，彩色输出）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # 简洁的格式：只显示消息
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)

        # 2. 文件 handler（详细日志，用于调试）
        # file_handler = logging.FileHandler('debug_agent.log', encoding='utf-8')
        # file_handler.setLevel(logging.DEBUG)
        # file_formatter = logging.Formatter(
        #     '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        # )
        # file_handler.setFormatter(file_formatter)

        self.logger.addHandler(console_handler)
        # self.logger.addHandler(file_handler)

    def step(self, step_num: int, total: int, message: str, icon: str = "📋"):
        """显示步骤进度"""
        if not _enabled:
            return
        self.logger.info(f"\n{icon} [{step_num}/{total}] {message}")

    def progress(self, message: str, indent: int = 1):
        """显示进度信息"""
        if not _enabled:
            return
        prefix = "   " * indent + "→ "
        self.logger.info(f"{prefix}{message}")

    def success(self, message: str, indent: int = 1):
        """显示成功信息"""
        if not _enabled:
            return
        prefix = "   " * indent + "✓ "
        self.logger.info(f"{prefix}{message}")

    def warning(self, message: str, indent: int = 1):
        """显示警告信息"""
        if not _enabled:
            return
        prefix = "   " * indent + "⚠ "
        self.logger.warning(f"{prefix}{message}")

    def error(self, message: str, indent: int = 1):
        """显示错误信息"""
        if not _enabled:
            return
        prefix = "   " * indent + "✗ "
        self.logger.error(f"{prefix}{message}")

    def info(self, message: str, indent: int = 0):
        """显示普通信息"""
        if not _enabled:
            return
        prefix = "   " * indent
        self.logger.info(f"{prefix}{message}")

    def debug(self, message: str):
        """显示调试信息（不会显示在控制台）"""
        if not _enabled:
            return
        self.logger.debug(message)


# 全局单例
_progress_logger: Optional[ProgressLogger] = None


def get_progress_logger() -> ProgressLogger:
    """获取全局进度日志器"""
    global _progress_logger
    if _progress_logger is None:
        _progress_logger = ProgressLogger()
    return _progress_logger
