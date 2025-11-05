# src/utils/error_parser.py
"""
错误解析器
解析Python错误消息，提取结构化信息
"""
from typing import Dict, Optional
import re

class ErrorParser:
    """Python错误消息解析器"""

    def __init__(self):
        pass

    def _parse_attribute_error(self, message: str) -> Dict:
        """
        解析AttributeError，提取对象类型和属性名
        例如：'NoneType' object has no attribute 'name'
        """
        details = {}

        # 提取对象类型
        match = re.search(r"'(\w+)'\s+object", message)
        if match:
            details['object_type'] = match.group(1)

        # 提取属性名
        match = re.search(r"attribute\s+'(\w+)'", message)
        if match:
            details['attribute'] = match.group(1)

        return details

    def _parse_type_error(self, message: str) -> Dict:
        """
        解析TypeError，提取类型信息
        例如: can only concatenate str (not 'int') to str
        """
        details = {}
        
        # 提取类型信息
        match = re.search(r"not\s+'(\w+)'", message)
        if match:
            details['wrong_type'] = match.group(1)
        
        return details

    def _parse_key_error(self, message: str) -> Dict:
        """
        解析KeyError，提取键名
        例如: 'age'
        """
        details = {}
        
        # 提取键名
        match = re.search(r"'([^']+)'", message)
        if match:
            details['key'] = match.group(1)
        
        return details

    def parse(self, error_message: str) -> Dict:
        """
        解析错误消息

        Args:
            error_message: Python错误消息字符串

        Returns:
            解析后的结构话信息

        Raises:
            ValueError: 当error_message为空时
        """
        # 1. 输入验证
        if not error_message or not isinstance(error_message, str):
            raise ValueError("error_message必须是非空字符串")

        # 2. 初始化结果
        result = {
            'error_type': 'Unknown',
            'message': error_message,
            'raw': error_message
        }

        # 3. 提取错误类型（冒号前面的部分）
        if ':' in error_message:
            parts = error_message.split(":", 1)
            result['error_type'] = parts[0].strip()
            result['message'] = parts[1].strip()

        # 4. 根据错误类型提取详细信息
        error_type = result['error_type']
        
        if error_type == 'AttributeError':
            details = self._parse_attribute_error(result['message'])
            result.update(details)
        elif error_type == 'TypeError':
            details = self._parse_type_error(result['message'])
            result.update(details)
        elif error_type == 'KeyError':
            details = self._parse_key_error(result['message'])
            result.update(details)
        # 其他错误类型暂时不做特殊处理
        
        return result

if __name__ == "__main__":
    # 测试
    parser = ErrorParser()

    test_errors = [
        "AttributeError: 'NoneType' object has no attribute 'name'",
        "TypeError: can only concatenate str (not 'int') to str",
        "KeyError: 'age'"
    ]

    for error in test_errors:
        result = parser.parse(error)
        print(f'\n输入：{error}')
        print(f'输出：{result}')