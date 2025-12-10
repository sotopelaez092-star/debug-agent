"""
ImportErrorHandler - 导入错误处理器

专门处理 ImportError 和 ModuleNotFoundError
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any
from difflib import get_close_matches

from .base_handler import BaseErrorHandler

logger = logging.getLogger(__name__)


class ImportErrorHandler(BaseErrorHandler):
    """
    导入错误处理器

    处理:
    - ImportError: cannot import name 'xxx' from 'yyy'
    - ModuleNotFoundError: No module named 'xxx'
    """

    supported_errors = ['ImportError', 'ModuleNotFoundError']

    # 常见的拼写错误修正
    COMMON_TYPOS = {
        'requets': 'requests',
        'numppy': 'numpy',
        'padas': 'pandas',
        'sklear': 'sklearn',
        'matplotib': 'matplotlib',
        'tensoflow': 'tensorflow',
        'pytoch': 'pytorch',
    }

    def collect_context(
        self,
        error_info: Dict[str, Any],
        project_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """收集导入错误的上下文"""
        context = {
            'error_type': 'import',
            'module_name': None,
            'function_name': None,
            'is_local_module': False,
            'similar_modules': [],
            'is_installed': None,
            'install_command': None,
        }

        error_message = error_info.get('error_message', '')

        # 解析错误消息
        # 情况1: cannot import name 'xxx' from 'yyy'
        match = re.search(r"cannot import name '(\w+)' from '(\w+)'", error_message)
        if match:
            context['function_name'] = match.group(1)
            context['module_name'] = match.group(2)
            logger.info(f"解析到函数导入错误: from {context['module_name']} import {context['function_name']}")

        # 情况2: No module named 'xxx'
        if not context['module_name']:
            match = re.search(r"No module named '([\w.]+)'", error_message)
            if match:
                context['module_name'] = match.group(1)
                logger.info(f"解析到模块导入错误: {context['module_name']}")

        # 检查是否是本地模块
        if project_path and context['module_name']:
            context['is_local_module'] = self._check_local_module(
                project_path, context['module_name']
            )

        # 查找相似模块
        if context['module_name']:
            context['similar_modules'] = self._find_similar_modules(
                context['module_name'], project_path
            )

            # 检查是否已安装（非本地模块）
            if not context['is_local_module']:
                context['is_installed'] = self._check_installed(context['module_name'])
                context['install_command'] = f"pip install {context['module_name']}"

        return context

    def suggest_fix(
        self,
        error_info: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成导入错误的修复建议"""
        suggestions = []
        primary_fix = None

        module_name = context.get('module_name', '')
        function_name = context.get('function_name', '')
        is_local = context.get('is_local_module', False)
        similar = context.get('similar_modules', [])
        is_installed = context.get('is_installed')

        # 情况1: 本地模块，可能是拼写错误
        if is_local and similar:
            correct_module = similar[0]
            primary_fix = f"将 '{module_name}' 改为 '{correct_module}'"
            suggestions.append({
                'type': 'typo_fix',
                'description': f"模块名拼写错误",
                'fix': f"import {correct_module}" if not function_name else f"from {correct_module} import {function_name}",
            })

        # 情况2: 函数名拼写错误
        elif function_name and similar:
            suggestions.append({
                'type': 'function_typo',
                'description': f"函数名可能拼写错误",
                'similar_names': similar,
            })

        # 情况3: 第三方包未安装
        elif not is_local and not is_installed:
            primary_fix = f"安装缺失的包: {context.get('install_command', '')}"
            suggestions.append({
                'type': 'missing_package',
                'description': f"包 '{module_name}' 未安装",
                'fix': context.get('install_command', ''),
            })

            # 检查常见拼写错误
            if module_name in self.COMMON_TYPOS:
                correct = self.COMMON_TYPOS[module_name]
                suggestions.append({
                    'type': 'typo_fix',
                    'description': f"可能是拼写错误",
                    'fix': f"import {correct}",
                })

        # 情况4: 包已安装但导入路径错误
        elif not is_local and is_installed:
            suggestions.append({
                'type': 'import_path',
                'description': f"包已安装，但导入路径可能不正确",
                'hint': "检查包的正确导入方式",
            })

        return {
            'primary_fix': primary_fix,
            'suggestions': suggestions,
            'confidence': 'high' if primary_fix else 'medium',
        }

    def get_search_query(self, error_info: Dict[str, Any]) -> str:
        """生成 RAG 搜索查询"""
        error_message = error_info.get('error_message', '')
        error_type = error_info.get('error_type', 'ImportError')

        # 提取关键信息
        module_match = re.search(r"'([\w.]+)'", error_message)
        module_name = module_match.group(1) if module_match else ''

        return f"Python {error_type} {module_name} solution"

    def _check_local_module(self, project_path: str, module_name: str) -> bool:
        """检查是否是本地模块"""
        # 转换模块名为文件路径
        module_path = module_name.replace('.', os.sep)

        possible_paths = [
            os.path.join(project_path, f"{module_path}.py"),
            os.path.join(project_path, module_path, "__init__.py"),
            os.path.join(project_path, "src", f"{module_path}.py"),
            os.path.join(project_path, "src", module_path, "__init__.py"),
        ]

        return any(os.path.exists(p) for p in possible_paths)

    def _find_similar_modules(
        self,
        module_name: str,
        project_path: Optional[str]
    ) -> List[str]:
        """查找相似的模块名"""
        candidates = []

        # 从项目中收集模块名
        if project_path:
            for root, dirs, files in os.walk(project_path):
                # 跳过特殊目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'venv', '__pycache__'}]

                for file in files:
                    if file.endswith('.py') and not file.startswith('_'):
                        candidates.append(file[:-3])  # 移除 .py

        # 添加常见的第三方包名
        common_packages = [
            'requests', 'numpy', 'pandas', 'matplotlib', 'sklearn',
            'tensorflow', 'torch', 'django', 'flask', 'fastapi',
            'pytest', 'json', 'os', 'sys', 'datetime', 'logging',
        ]
        candidates.extend(common_packages)

        # 模糊匹配
        matches = get_close_matches(module_name, candidates, n=3, cutoff=0.6)
        return matches

    def _check_installed(self, package_name: str) -> bool:
        """检查包是否已安装"""
        try:
            import importlib
            importlib.import_module(package_name.split('.')[0])
            return True
        except ImportError:
            return False
