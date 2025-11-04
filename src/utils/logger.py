# src/utils/logger.py
"""
日志系统配置
使用 loguru 实现结构化日志
"""

import sys
from pathlib import Path
from datetime import datetime
from loguru import logger
from .config import get_settings


def setup_logger():
    """
    配置日志系统

    功能：
    - 控制台输出（彩色）
    - 文件输出（按日期分割）
    - 错误单独记录
    - 性能日志
    """
    settings = get_settings()

    # 创建日志目录
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 移除默认 handler
    logger.remove()

    # ===== 控制台输出 =====
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level=settings.log_level,
        colorize=True,
    )

    # ===== 通用日志文件 =====
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",  # ✅ 不要 f-string
        rotation="00:00",                       # 每天生成新文件
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        encoding="utf-8",
    )

    # ===== 错误日志（单独文件）=====
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="90 days",  # 错误日志保留更久
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        level="ERROR",
        encoding="utf-8",
    )

    logger.info(f"日志系统初始化完成 | 日志目录: {log_dir}")
    return logger


# 创建全局 logger 实例
app_logger = setup_logger()


def get_logger(name: str = None):
    """
    获取 logger 实例
    
    Args:
        name: 模块名称
    
    Returns:
        logger 实例
    """
    if name:
        return logger.bind(module=name)
    return logger


# 性能日志函数
def log_performance(operation: str, duration: float, **kwargs):
    """记录性能日志"""
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.bind(performance=operation).info(
        f"耗时: {duration:.3f}s | {extra_info}"
    )


# 装饰器：自动记录函数执行
def log_function(func):
    """装饰器：记录函数调用"""
    from functools import wraps
    import time

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        logger.debug(f"开始执行: {func_name}")

        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"完成执行: {func_name} | 耗时: {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"执行失败: {func_name} | 耗时: {duration:.3f}s | 错误: {e}")
            raise

    return wrapper


if __name__ == "__main__":
    # 测试日志系统
    logger.debug("这是DEBUG日志")
    logger.info("这是INFO日志")
    logger.warning("这是WARNING日志")
    logger.error("这是ERROR日志")

    # 测试性能日志
    log_performance("test_operation", 1.234, param1="value1", param2=100)

    # 测试装饰器
    @log_function
    def test_func():
        import time
        time.sleep(0.5)
        return "完成"

    test_func()

    print("\n✅ 日志系统测试完成！请检查 logs/ 目录")
