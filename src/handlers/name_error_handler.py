"""
NameErrorHandler - 名称错误处理器

专门处理 NameError
"""

import re
import logging
from typing import Dict, List, Optional, Any
from difflib import get_close_matches

from .base_handler import BaseErrorHandler

logger = logging.getLogger(__name__)


class NameErrorHandler(BaseErrorHandler):
    """
    名称错误处理器

    处理:
    - NameError: name 'xxx' is not defined
    """

    supported_errors = ['NameError']

    # Python 内置函数和常量
    BUILTINS = {
        'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict',
        'set', 'tuple', 'bool', 'None', 'True', 'False', 'type', 'isinstance',
        'hasattr', 'getattr', 'setattr', 'open', 'input', 'sum', 'max', 'min',
        'abs', 'round', 'sorted', 'reversed', 'enumerate', 'zip', 'map', 'filter',
        'any', 'all', 'ord', 'chr', 'hex', 'bin', 'oct', 'format', 'repr',
        'id', 'hash', 'callable', 'dir', 'vars', 'globals', 'locals', 'eval', 'exec',
        'compile', 'super', 'property', 'classmethod', 'staticmethod',
        'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError',
        'AttributeError', 'ImportError', 'RuntimeError', 'StopIteration',
    }

    def collect_context(
        self,
        error_info: Dict[str, Any],
        project_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """收集名称错误的上下文"""
        context = {
            'error_type': 'name',
            'undefined_name': None,
            'is_builtin_typo': False,
            'similar_builtins': [],
            'possible_sources': [],
            'needs_import': False,
        }

        error_message = error_info.get('error_message', '')

        # 解析未定义的名称
        match = re.search(r"name '(\w+)' is not defined", error_message)
        if match:
            context['undefined_name'] = match.group(1)
            logger.info(f"解析到未定义名称: {context['undefined_name']}")

            undefined_name = context['undefined_name']

            # 检查是否是内置函数的拼写错误
            similar_builtins = get_close_matches(
                undefined_name, self.BUILTINS, n=2, cutoff=0.7
            )
            if similar_builtins:
                context['is_builtin_typo'] = True
                context['similar_builtins'] = similar_builtins

            # 分析可能的来源
            context['possible_sources'] = self._analyze_possible_sources(
                undefined_name, error_info
            )

        return context

    def suggest_fix(
        self,
        error_info: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成名称错误的修复建议"""
        suggestions = []
        primary_fix = None

        undefined_name = context.get('undefined_name', '')
        is_builtin_typo = context.get('is_builtin_typo', False)
        similar_builtins = context.get('similar_builtins', [])
        possible_sources = context.get('possible_sources', [])

        # 情况1: 内置函数拼写错误
        if is_builtin_typo and similar_builtins:
            correct_name = similar_builtins[0]
            primary_fix = f"将 '{undefined_name}' 改为 '{correct_name}'"
            suggestions.append({
                'type': 'typo_fix',
                'description': f"可能是内置函数的拼写错误",
                'fix': f"使用 {correct_name} 替代 {undefined_name}",
                'confidence': 'high',
            })

        # 情况2: 需要导入
        elif 'import' in possible_sources:
            suggestions.append({
                'type': 'missing_import',
                'description': f"'{undefined_name}' 可能需要导入",
                'hint': f"检查是否需要添加 import 语句",
                'confidence': 'medium',
            })

        # 情况3: 变量未定义
        elif 'variable' in possible_sources:
            suggestions.append({
                'type': 'undefined_variable',
                'description': f"变量 '{undefined_name}' 在使用前未定义",
                'hint': "检查变量名拼写，或在使用前定义该变量",
                'confidence': 'medium',
            })

        # 情况4: 作用域问题
        if 'scope' in possible_sources:
            suggestions.append({
                'type': 'scope_issue',
                'description': f"'{undefined_name}' 可能是作用域问题",
                'hint': "检查变量是否在正确的作用域内定义",
                'confidence': 'low',
            })

        # 通用建议
        if not suggestions:
            suggestions.append({
                'type': 'general',
                'description': f"名称 '{undefined_name}' 未定义",
                'hint': "检查拼写、导入语句或变量定义",
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

        # 提取未定义的名称
        match = re.search(r"name '(\w+)' is not defined", error_message)
        name = match.group(1) if match else 'variable'

        return f"Python NameError {name} is not defined solution"

    def _analyze_possible_sources(
        self,
        undefined_name: str,
        error_info: Dict[str, Any]
    ) -> List[str]:
        """分析未定义名称的可能来源"""
        sources = []

        # 检查是否像是导入的模块/函数
        if undefined_name[0].isupper():
            # 首字母大写，可能是类或常量
            sources.append('import')
            sources.append('class')

        # 检查是否像是变量
        if undefined_name.islower() or '_' in undefined_name:
            sources.append('variable')

        # 检查是否可能是作用域问题
        # 这需要更多上下文，暂时总是添加
        sources.append('scope')

        # 检查常见的需要导入的名称
        common_imports = {
            'json', 'os', 'sys', 'datetime', 'time', 're', 'math',
            'random', 'collections', 'itertools', 'functools',
            'typing', 'pathlib', 'logging', 'unittest', 'pytest',
            'np', 'pd', 'plt', 'tf', 'torch',
        }

        if undefined_name.lower() in common_imports:
            sources.insert(0, 'import')  # 优先考虑导入

        return sources

    def get_priority_hints(self, error_info: Dict[str, Any]) -> List[str]:
        """获取优先级提示"""
        hints = []

        error_message = error_info.get('error_message', '')
        match = re.search(r"name '(\w+)' is not defined", error_message)

        if match:
            name = match.group(1)

            # 检查常见模式
            if name in ['np', 'pd', 'plt']:
                hints.append(f"'{name}' 是常见的库别名，检查 import 语句")

            if name.startswith('self.'):
                hints.append("检查是否在类方法中正确使用 self")

        return hints
