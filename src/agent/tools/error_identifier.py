"""
ErrorIdentifier - 错误识别器
从traceback中提取错误信息
"""

import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ErrorIdentifier:
    """
    错误识别器

    功能：
    1. 从traceback中提取错误类型
    2. 提取文件名和行号
    3. 提取错误描述
    """

    # 支持的错误类型
    SUPPORTED_ERRIR_TYPES = [
        "AttributeError",
        "TypeError", 
        "NameError",
        "IndexError",
        "KeyError"
    ]

    def __init__(self):
        """初始化ErrorIdentifier"""
        logger.info("ErrorIdentifier初始化完成")

    def identify(self, traceback: str) -> Dict[str, any]:
        """
        识别错误信息

        Args:
            traceback: 包含错误信息的traceback字符串
            
        Returns:
            {
                "error_type": "AttributeError",
                "error_message": "具体错误描述",
                "file": "main.py",
                "line": 10,
                "full_traceback": "完整traceback"
            }

        Raises:
            ValueError: 当traceback为空时
        """
        # 1. 输入验证
        if not traceback or not isinstance(traceback, str):
            raise ValueError("traceback必须是非空字符串")
        
        # 去除首尾空白
        traceback = traceback.strip()

        if len(traceback) == 0:
            raise ValueError("traceback不能为空")
        
        logger.info("开始识别错误信息")
        logger.debug(f"traceback长度: {len(traceback)}")

        # 2. 提取错误类型
        error_type_pattern = r'(\w+Error):\s*(.+)$'

        error_type = None
        error_message =None
        # 从最后一行开始找（错误类型通常在最后）
        lines = traceback.split('\n')
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            
            match = re.search(error_type_pattern, line)
            if match:
                error_type = match.group(1)
                error_message = match.group(2)
                logger.debug(f"找到错误类型: {error_type}")
                break

        # 如果没有找到错误类型，返回未知
        if not error_type:
            logger.warning("未找到错误类型")
            return {
                "error_type" : "UnknownError",
                "error_message" : "无法解析错误信息",
                "file": None,
                "line": None,
                "full_traceback": traceback
            }

        # 3. 提取文件名和行号
        file_pattern = r'File\s+"([^"]+)",\s+line\s+(\d+)'

        file_name = None
        line_number = None

        # 从所有行中找文件信息（通常在倒数第二行或更前面）
        for line in lines:
            match = re.search(file_pattern, line)
            if match:
                file_name = match.group(1)
                line_number = int(match.group(2))
                logger.debug(f"找到文件名: {file_name}, 行号: {line_number}")
        
        if not file_name:
            logger.warning("未找到文件名和行号")
        
        # 4. 返回结果
        logger.info(
            f"识别完成 - 类型: {error_type}, "
            f"文件: {file_name}, "
            f"行号: {line_number}"
        )

        return {
            "error_type": error_type,
            "error_message": error_message,
            "file": file_name,
            "line": line_number,
            "full_traceback": traceback
        }



if __name__ == "__main__":
    identifier = ErrorIdentifier()

    # 测试案例1: AttributeError
    test_traceback_1 = """
Traceback (most recent call last):
  File "main.py", line 10, in <module>
    print(user.name)
AttributeError: 'NoneType' object has no attribute 'name'
"""
    
    result = identifier.identify(test_traceback_1)
    print("测试1结果:", result)
    
    # 测试案例2: NameError
    test_traceback_2 = """
Traceback (most recent call last):
  File "test.py", line 5, in greet
    print(f"Hello, {nane}")
NameError: name 'nane' is not defined
"""
    
    result = identifier.identify(test_traceback_2)
    print("测试2结果:", result)
    
