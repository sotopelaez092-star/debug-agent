"""
TypeErrorHandler - 类型错误处理器

专门处理 TypeError
"""

import re
import logging
from typing import Dict, List, Optional, Any

from .base_handler import BaseErrorHandler

logger = logging.getLogger(__name__)


class TypeErrorHandler(BaseErrorHandler):
    """
    类型错误处理器

    处理:
    - TypeError: unsupported operand type(s)
    - TypeError: xxx() takes x positional arguments but y were given
    - TypeError: 'xxx' object is not callable
    - TypeError: 'xxx' object is not subscriptable
    - TypeError: cannot unpack non-iterable xxx object
    """

    supported_errors = ['TypeError']

    def collect_context(
        self,
        error_info: Dict[str, Any],
        project_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """收集类型错误的上下文"""
        context = {
            'error_type': 'type',
            'subtype': None,
            'involved_types': [],
            'operation': None,
            'expected': None,
            'actual': None,
        }

        error_message = error_info.get('error_message', '')

        # 解析不同类型的 TypeError

        # 1. 操作符类型错误
        match = re.search(
            r"unsupported operand type\(s\) for (.+): '(\w+)' and '(\w+)'",
            error_message
        )
        if match:
            context['subtype'] = 'operand'
            context['operation'] = match.group(1)
            context['involved_types'] = [match.group(2), match.group(3)]
            logger.info(f"操作符类型错误: {context['operation']} on {context['involved_types']}")
            return context

        # 2. 参数数量错误
        match = re.search(
            r"(\w+)\(\) takes (\d+) positional arguments? but (\d+) (?:was|were) given",
            error_message
        )
        if match:
            context['subtype'] = 'argument_count'
            context['operation'] = match.group(1)
            context['expected'] = int(match.group(2))
            context['actual'] = int(match.group(3))
            logger.info(f"参数数量错误: {context['operation']} expected {context['expected']}, got {context['actual']}")
            return context

        # 3. 对象不可调用
        match = re.search(r"'(\w+)' object is not callable", error_message)
        if match:
            context['subtype'] = 'not_callable'
            context['involved_types'] = [match.group(1)]
            logger.info(f"不可调用错误: {context['involved_types'][0]}")
            return context

        # 4. 对象不可下标访问
        match = re.search(r"'(\w+)' object is not subscriptable", error_message)
        if match:
            context['subtype'] = 'not_subscriptable'
            context['involved_types'] = [match.group(1)]
            logger.info(f"不可下标访问: {context['involved_types'][0]}")
            return context

        # 5. 不可迭代
        match = re.search(r"cannot unpack non-iterable (\w+) object", error_message)
        if match:
            context['subtype'] = 'not_iterable'
            context['involved_types'] = [match.group(1)]
            logger.info(f"不可迭代: {context['involved_types'][0]}")
            return context

        # 6. 缺少必需参数
        match = re.search(
            r"(\w+)\(\) missing (\d+) required positional arguments?: (.+)",
            error_message
        )
        if match:
            context['subtype'] = 'missing_arguments'
            context['operation'] = match.group(1)
            context['expected'] = match.group(3)
            logger.info(f"缺少参数: {context['operation']} missing {context['expected']}")
            return context

        # 默认
        context['subtype'] = 'unknown'
        return context

    def suggest_fix(
        self,
        error_info: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成类型错误的修复建议"""
        suggestions = []
        primary_fix = None

        subtype = context.get('subtype')
        involved_types = context.get('involved_types', [])
        operation = context.get('operation')

        if subtype == 'operand':
            # 操作符类型不匹配
            suggestions.append({
                'type': 'type_conversion',
                'description': f"操作符 '{operation}' 不支持 {' 和 '.join(involved_types)} 类型",
                'hint': "需要进行类型转换，例如 str() 或 int()",
                'confidence': 'high',
            })

            # 提供具体的转换建议
            if 'str' in involved_types and 'int' in involved_types:
                if '+' in str(operation):
                    primary_fix = "如果是字符串拼接，使用 str(数字)；如果是数学运算，使用 int(字符串)"

        elif subtype == 'argument_count':
            expected = context.get('expected', '?')
            actual = context.get('actual', '?')
            suggestions.append({
                'type': 'argument_mismatch',
                'description': f"函数 '{operation}' 期望 {expected} 个参数，但收到 {actual} 个",
                'hint': "检查函数调用的参数数量",
                'confidence': 'high',
            })
            primary_fix = f"检查 {operation}() 的参数数量，应该是 {expected} 个"

        elif subtype == 'missing_arguments':
            expected = context.get('expected', '')
            suggestions.append({
                'type': 'missing_arguments',
                'description': f"函数 '{operation}' 缺少必需参数: {expected}",
                'hint': "添加缺少的参数",
                'confidence': 'high',
            })
            primary_fix = f"为 {operation}() 添加参数: {expected}"

        elif subtype == 'not_callable':
            type_name = involved_types[0] if involved_types else 'object'
            suggestions.append({
                'type': 'not_callable',
                'description': f"'{type_name}' 类型的对象不能作为函数调用",
                'hint': "检查是否误用了变量名，或者移除多余的括号",
                'confidence': 'high',
            })
            primary_fix = f"'{type_name}' 不是函数，不能使用 () 调用"

        elif subtype == 'not_subscriptable':
            type_name = involved_types[0] if involved_types else 'object'
            suggestions.append({
                'type': 'not_subscriptable',
                'description': f"'{type_name}' 类型的对象不支持下标访问 []",
                'hint': "检查对象类型，可能需要先转换为列表或字典",
                'confidence': 'high',
            })

        elif subtype == 'not_iterable':
            type_name = involved_types[0] if involved_types else 'object'
            suggestions.append({
                'type': 'not_iterable',
                'description': f"'{type_name}' 类型的对象不可迭代",
                'hint': "检查变量是否是预期的可迭代类型（如列表、元组）",
                'confidence': 'high',
            })

        else:
            suggestions.append({
                'type': 'general',
                'description': "类型错误",
                'hint': "检查变量类型是否符合预期",
                'confidence': 'low',
            })

        return {
            'primary_fix': primary_fix,
            'suggestions': suggestions,
            'confidence': 'high' if primary_fix else 'medium',
        }

    def get_search_query(self, error_info: Dict[str, Any]) -> str:
        """生成 RAG 搜索查询"""
        error_message = error_info.get('error_message', '')

        # 简化错误消息用于搜索
        # 移除具体的类型名和数字
        simplified = re.sub(r"'[\w.]+'", "'type'", error_message)
        simplified = re.sub(r"\d+", "N", simplified)

        return f"Python TypeError {simplified[:100]}"

    def get_priority_hints(self, error_info: Dict[str, Any]) -> List[str]:
        """获取优先级提示"""
        hints = []
        error_message = error_info.get('error_message', '')

        if 'NoneType' in error_message:
            hints.append("变量可能是 None，检查是否正确赋值或函数是否返回了值")

        if 'str' in error_message and 'int' in error_message:
            hints.append("字符串和数字不能直接运算，需要类型转换")

        return hints
