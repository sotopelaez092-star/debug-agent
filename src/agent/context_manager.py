"""
项目上下文管理器 - AI Debug Assistant的核心创新模块

优化版本：懒加载，按需扫描 import 链上的文件
"""

import os
import ast
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from difflib import get_close_matches

logger = logging.getLogger(__name__)


# 需要忽略的目录
IGNORE_DIRS = {
    'venv', 'env', '.venv',  # 虚拟环境
    '__pycache__', '.pytest_cache', '.mypy_cache',  # 缓存目录
    '.git', '.svn', '.hg',  # 版本控制
    'node_modules',  # 前端依赖
    'dist', 'build', '.egg-info',  # 构建产物
    '.idea', '.vscode',  # IDE配置
    '.tox', '.coverage',  # 测试相关
}

# 需要忽略的文件模式
IGNORE_PATTERNS = {
    '*.pyc', '*.pyo', '*.pyd',  # Python字节码
    '.DS_Store', 'Thumbs.db',  # 系统文件
    '*.so', '*.dylib', '*.dll',  # 二进制文件
}

# 只处理的文件扩展名
INCLUDE_EXTENSIONS = {'.py'}

# 文件大小限制（避免处理过大的文件）
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB


class ContextManager:
    """
    项目上下文管理器（优化版 - 懒加载）

    功能：
    1. 懒加载：不在初始化时扫描所有文件
    2. 按需扫描：只扫描 import 链上的相关文件
    3. 缓存机制：已扫描的文件和符号会被缓存
    4. 智能提取：根据错误类型提取相关上下文

    Attributes:
        project_path: 项目根目录路径
        _file_cache: 文件内容缓存 {相对路径: 内容}
        _symbol_cache: 符号定义缓存 {符号名: 定义信息}
        _import_cache: 导入关系缓存 {文件: import信息}
    """

    def __init__(self, project_path: str):
        """
        初始化上下文管理器（懒加载，不立即扫描）

        Args:
            project_path: 项目根目录的路径

        Raises:
            ValueError: 如果project_path无效
            FileNotFoundError: 如果路径不存在
        """
        # 输入验证
        if not project_path or not isinstance(project_path, str):
            raise ValueError("project_path必须是非空字符串")

        # 转换为绝对路径并验证存在性
        self.project_path = os.path.abspath(project_path)
        if not os.path.exists(self.project_path):
            raise FileNotFoundError(f"项目路径不存在: {self.project_path}")

        if not os.path.isdir(self.project_path):
            raise ValueError(f"project_path必须是目录: {self.project_path}")

        # 懒加载缓存
        self._file_cache: Dict[str, str] = {}  # {相对路径: 文件内容}
        self._symbol_cache: Dict[str, Dict[str, Any]] = {}  # {符号名: 定义信息}
        self._import_cache: Dict[str, List[Dict]] = {}  # {文件路径: import列表}
        self._all_files: Optional[List[str]] = None  # 所有Python文件列表（懒加载）

        # 扫描统计信息
        self.scan_stats = {
            'files_discovered': 0,
            'files_loaded': 0,
            'symbols_found': 0,
            'cache_hits': 0,
        }

        logger.info(f"ContextManager初始化完成（懒加载模式）: {self.project_path}")

    def _discover_all_files(self) -> List[str]:
        """
        发现项目中所有的Python文件（只获取路径，不读取内容）

        Returns:
            Python文件相对路径列表
        """
        if self._all_files is not None:
            return self._all_files

        self._all_files = []

        for root, dirs, files in os.walk(self.project_path):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if not self._is_ignored_dir(d)]

            rel_root = os.path.relpath(root, self.project_path)
            if rel_root == '.':
                rel_root = ''

            for file_name in files:
                if file_name.endswith('.py'):
                    rel_path = os.path.join(rel_root, file_name).replace('\\', '/')
                    if rel_path.startswith('./'):
                        rel_path = rel_path[2:]
                    self._all_files.append(rel_path)

        self.scan_stats['files_discovered'] = len(self._all_files)
        logger.info(f"发现 {len(self._all_files)} 个Python文件")
        return self._all_files

    def _is_ignored_dir(self, dir_name: str) -> bool:
        """检查目录是否应该被忽略"""
        return dir_name in IGNORE_DIRS or dir_name.startswith('.')

    def _load_file(self, rel_path: str) -> Optional[str]:
        """
        懒加载单个文件内容

        Args:
            rel_path: 文件相对路径

        Returns:
            文件内容，如果加载失败返回None
        """
        # 检查缓存
        if rel_path in self._file_cache:
            self.scan_stats['cache_hits'] += 1
            return self._file_cache[rel_path]

        # 加载文件
        full_path = os.path.join(self.project_path, rel_path)

        if not os.path.exists(full_path):
            logger.warning(f"文件不存在: {rel_path}")
            return None

        # 检查文件大小
        try:
            if os.path.getsize(full_path) > MAX_FILE_SIZE:
                logger.warning(f"文件过大，跳过: {rel_path}")
                return None
        except OSError:
            return None

        # 读取文件
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self._file_cache[rel_path] = content
            self.scan_stats['files_loaded'] += 1
            logger.debug(f"加载文件: {rel_path}")
            return content
        except UnicodeDecodeError:
            try:
                with open(full_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                self._file_cache[rel_path] = content
                self.scan_stats['files_loaded'] += 1
                return content
            except Exception as e:
                logger.error(f"读取文件失败: {rel_path} - {e}")
                return None
        except Exception as e:
            logger.error(f"读取文件失败: {rel_path} - {e}")
            return None

    def _parse_file_symbols(self, rel_path: str) -> Dict[str, Dict]:
        """
        解析单个文件的符号定义

        Args:
            rel_path: 文件相对路径

        Returns:
            {符号名: 符号信息} 字典
        """
        content = self._load_file(rel_path)
        if not content:
            return {}

        symbols = {}

        try:
            tree = ast.parse(content, filename=rel_path)

            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    symbols[node.name] = {
                        'type': 'function',
                        'file': rel_path,
                        'line': node.lineno,
                        'end_line': node.end_lineno,
                        'args': [arg.arg for arg in node.args.args],
                    }
                elif isinstance(node, ast.ClassDef):
                    # 提取类的方法
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods.append(item.name)

                    symbols[node.name] = {
                        'type': 'class',
                        'file': rel_path,
                        'line': node.lineno,
                        'end_line': node.end_lineno,
                        'methods': methods,
                        'bases': [base.id for base in node.bases if isinstance(base, ast.Name)],
                    }
        except SyntaxError as e:
            logger.warning(f"语法错误，无法解析: {rel_path} - {e}")
        except Exception as e:
            logger.error(f"解析文件失败: {rel_path} - {e}")

        return symbols

    def _parse_file_imports(self, rel_path: str) -> List[Dict]:
        """
        解析单个文件的import语句

        Args:
            rel_path: 文件相对路径

        Returns:
            import信息列表
        """
        if rel_path in self._import_cache:
            return self._import_cache[rel_path]

        content = self._load_file(rel_path)
        if not content:
            return []

        imports = []

        try:
            tree = ast.parse(content, filename=rel_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            'type': 'import',
                            'module': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno,
                        })
                elif isinstance(node, ast.ImportFrom):
                    module = node.module if node.module else ''
                    for alias in node.names:
                        imports.append({
                            'type': 'from',
                            'module': module,
                            'name': alias.name,
                            'alias': alias.asname,
                            'level': node.level,
                            'line': node.lineno,
                        })
        except Exception as e:
            logger.warning(f"解析import失败: {rel_path} - {e}")

        self._import_cache[rel_path] = imports
        return imports

    def _find_related_files(self, entry_file: str, max_depth: int = 3) -> Set[str]:
        """
        从入口文件开始，找出import链上的相关文件

        Args:
            entry_file: 入口文件相对路径
            max_depth: 最大递归深度

        Returns:
            相关文件路径集合
        """
        all_files = self._discover_all_files()
        visited = set()
        to_visit = [(entry_file, 0)]

        while to_visit:
            current_file, depth = to_visit.pop(0)

            if current_file in visited or depth > max_depth:
                continue

            visited.add(current_file)

            # 解析这个文件的import
            imports = self._parse_file_imports(current_file)

            for imp in imports:
                # 尝试将import映射到项目文件
                module = imp.get('module', '')

                # 转换模块名到可能的文件路径
                possible_paths = self._module_to_paths(module, current_file)

                for path in possible_paths:
                    if path in all_files and path not in visited:
                        to_visit.append((path, depth + 1))

        return visited

    def _module_to_paths(self, module: str, from_file: str) -> List[str]:
        """
        将模块名转换为可能的文件路径

        Args:
            module: 模块名（如 'utils' 或 'src.utils'）
            from_file: 发起import的文件

        Returns:
            可能的文件路径列表
        """
        if not module:
            return []

        paths = []

        # 1. 直接转换：utils -> utils.py
        simple_path = module.replace('.', '/') + '.py'
        paths.append(simple_path)

        # 2. 包形式：utils -> utils/__init__.py
        package_path = module.replace('.', '/') + '/__init__.py'
        paths.append(package_path)

        # 3. 相对于当前文件目录
        from_dir = os.path.dirname(from_file)
        if from_dir:
            rel_simple = os.path.join(from_dir, module.split('.')[-1] + '.py')
            paths.append(rel_simple.replace('\\', '/'))

        return paths

    def _find_symbol_globally(self, symbol_name: str) -> Optional[Dict]:
        """
        在整个项目中查找符号定义

        Args:
            symbol_name: 符号名称

        Returns:
            符号信息，未找到返回None
        """
        # 先检查缓存
        if symbol_name in self._symbol_cache:
            return self._symbol_cache[symbol_name]

        # 扫描所有文件查找
        all_files = self._discover_all_files()

        for file_path in all_files:
            symbols = self._parse_file_symbols(file_path)

            # 缓存这个文件的所有符号
            for name, info in symbols.items():
                if name not in self._symbol_cache:
                    self._symbol_cache[name] = info

            if symbol_name in symbols:
                self.scan_stats['symbols_found'] += 1
                return symbols[symbol_name]

        return None

    def _extract_definition(self, file_path: str, symbol_name: str) -> str:
        """
        从文件中提取符号的完整定义代码

        Args:
            file_path: 文件相对路径
            symbol_name: 符号名称

        Returns:
            定义代码，失败返回空字符串
        """
        content = self._load_file(file_path)
        if not content:
            return ""

        # 从符号缓存获取行号
        symbol_info = self._symbol_cache.get(symbol_name)
        if not symbol_info or symbol_info['file'] != file_path:
            # 重新解析这个文件
            symbols = self._parse_file_symbols(file_path)
            symbol_info = symbols.get(symbol_name)

        if not symbol_info:
            return ""

        lines = content.split('\n')
        start_line = symbol_info['line'] - 1
        end_line = symbol_info.get('end_line', start_line + 1)

        return '\n'.join(lines[start_line:end_line])

    def _generate_import_suggestion(
        self,
        from_file: str,
        to_file: str,
        symbol_name: Optional[str]
    ) -> str:
        """
        生成import建议

        Args:
            from_file: 错误文件
            to_file: 定义文件
            symbol_name: 要导入的符号名

        Returns:
            import语句
        """
        # 移除.py扩展名，转换为模块路径
        module_path = os.path.splitext(to_file)[0].replace('/', '.').replace('\\', '.')

        # 如果是同目录，使用简单的模块名
        if os.path.dirname(from_file) == os.path.dirname(to_file):
            module_name = os.path.splitext(os.path.basename(to_file))[0]
            if symbol_name:
                return f"from {module_name} import {symbol_name}"
            else:
                return f"import {module_name}"
        else:
            if symbol_name:
                return f"from {module_path} import {symbol_name}"
            else:
                return f"import {module_path}"

    def get_context_for_error(
        self,
        error_file: str,
        error_line: int,
        error_type: str,
        undefined_name: Optional[Union[str, Dict]] = None
    ) -> Dict[str, Any]:
        """
        智能提取错误相关的上下文（优化版）

        Args:
            error_file: 错误发生的文件路径
            error_line: 错误发生的行号
            error_type: 错误类型
            undefined_name: 未定义的名称

        Returns:
            上下文字典
        """
        logger.info(f"提取上下文: {error_file}:{error_line}, 类型: {error_type}")

        # 验证错误文件存在
        if not self._load_file(error_file):
            raise ValueError(f"文件不在项目中或无法读取: {error_file}")

        # 基础上下文
        context = {
            "error_file_content": self._file_cache[error_file],
            "related_symbols": {},
            "related_files": {},
            "import_suggestions": [],
        }

        # 找出import链上的相关文件
        related_files = self._find_related_files(error_file)
        for file_path in related_files:
            if file_path != error_file:
                content = self._load_file(file_path)
                if content:
                    context["related_files"][file_path] = content

        # 根据错误类型处理
        try:
            if error_type == "NameError":
                self._handle_name_error(context, error_file, undefined_name)
            elif error_type in ["ImportError", "ModuleNotFoundError"]:
                self._handle_import_error(context, error_file, undefined_name)
            elif error_type == "AttributeError":
                self._handle_attribute_error(context, error_file, undefined_name)
            else:
                logger.info(f"未特殊处理的错误类型: {error_type}")
        except Exception as e:
            logger.error(f"处理错误上下文失败: {e}", exc_info=True)

        logger.info(f"上下文提取完成: {len(context['related_symbols'])} 个符号, "
                   f"{len(context['related_files'])} 个相关文件")
        return context

    def _handle_name_error(
        self,
        context: Dict[str, Any],
        error_file: str,
        undefined_name: Optional[str]
    ) -> None:
        """处理NameError：查找未定义的符号"""
        if not undefined_name or not isinstance(undefined_name, str):
            return

        logger.info(f"查找未定义符号: {undefined_name}")

        # 全局搜索符号
        symbol_info = self._find_symbol_globally(undefined_name)

        if symbol_info:
            definition_file = symbol_info['file']
            definition_code = self._extract_definition(definition_file, undefined_name)

            context["related_symbols"][undefined_name] = {
                "file": definition_file,
                "definition": definition_code,
                "type": symbol_info['type'],
                "line": symbol_info['line'],
            }

            # 添加相关文件
            if definition_file not in context["related_files"]:
                content = self._load_file(definition_file)
                if content:
                    context["related_files"][definition_file] = content

            # 生成import建议
            suggestion = self._generate_import_suggestion(
                error_file, definition_file, undefined_name
            )
            if suggestion:
                context["import_suggestions"].append(suggestion)

            logger.info(f"找到符号 '{undefined_name}' 在 {definition_file}")
        else:
            logger.warning(f"未找到符号: {undefined_name}")

    def _handle_import_error(
        self,
        context: Dict[str, Any],
        error_file: str,
        module_info: Optional[Union[str, Dict]]
    ) -> None:
        """处理ImportError：查找模块或函数"""
        if not module_info:
            return

        all_files = self._discover_all_files()

        # 情况1：函数导入错误 {'function': 'xxx', 'module': 'yyy'}
        if isinstance(module_info, dict):
            function_name = module_info.get('function', '')
            module_name = module_info.get('module', '')

            logger.info(f"处理函数导入错误: from {module_name} import {function_name}")

            # 找到模块文件
            module_file = None
            for file_path in all_files:
                file_module = os.path.splitext(os.path.basename(file_path))[0]
                if file_module == module_name:
                    module_file = file_path
                    break

            if module_file:
                # 获取模块中的所有函数
                symbols = self._parse_file_symbols(module_file)
                module_functions = [name for name, info in symbols.items()
                                   if info['type'] == 'function']

                # 模糊匹配
                matches = get_close_matches(function_name, module_functions, n=1, cutoff=0.6)
                if matches:
                    correct_name = matches[0]
                    context["import_suggestions"].append(
                        f"from {module_name} import {correct_name}"
                    )
                    logger.info(f"函数名纠正: '{function_name}' -> '{correct_name}'")

                # 添加模块文件
                content = self._load_file(module_file)
                if content:
                    context["related_files"][module_file] = content
            return

        # 情况2：模块名错误
        module_name = module_info
        logger.info(f"处理模块导入错误: {module_name}")

        # 收集所有可用模块名
        available_modules = []
        for file_path in all_files:
            mod_name = os.path.splitext(os.path.basename(file_path))[0]
            available_modules.append((mod_name, file_path))

        # 模糊匹配
        module_names = [m[0] for m in available_modules]
        matches = get_close_matches(module_name, module_names, n=1, cutoff=0.6)

        if matches:
            correct_module = matches[0]
            # 找到对应文件
            for mod_name, file_path in available_modules:
                if mod_name == correct_module:
                    content = self._load_file(file_path)
                    if content:
                        context["related_files"][file_path] = content
                    context["import_suggestions"].append(f"import {correct_module}")
                    logger.info(f"模块名纠正: '{module_name}' -> '{correct_module}'")
                    break

    def _handle_attribute_error(
        self,
        context: Dict[str, Any],
        error_file: str,
        attr_info: Optional[Union[str, Dict]]
    ) -> None:
        """处理AttributeError：查找类或模块属性"""
        if not attr_info:
            return

        # 字符串形式：按NameError处理
        if isinstance(attr_info, str):
            self._handle_name_error(context, error_file, attr_info)
            return

        # 对象属性错误: {'type': 'object_attribute', 'class': 'User', 'attribute': 'age'}
        if attr_info.get('type') == 'object_attribute':
            class_name = attr_info.get('class', '')
            attr_name = attr_info.get('attribute', '')

            logger.info(f"处理对象属性错误: {class_name}.{attr_name}")

            # 查找类定义
            symbol_info = self._find_symbol_globally(class_name)

            if symbol_info and symbol_info['type'] == 'class':
                file_path = symbol_info['file']
                definition_code = self._extract_definition(file_path, class_name)

                context["related_symbols"][class_name] = {
                    "file": file_path,
                    "definition": definition_code,
                    "type": "class",
                    "line": symbol_info['line'],
                    "methods": symbol_info.get('methods', []),
                }

                # 添加文件
                content = self._load_file(file_path)
                if content:
                    context["related_files"][file_path] = content

                # 生成import建议
                suggestion = self._generate_import_suggestion(error_file, file_path, class_name)
                if suggestion:
                    context["import_suggestions"].append(suggestion)
            return

        # 模块属性错误: {'type': 'module_attribute', 'module': 'utils', 'attribute': 'calc'}
        if attr_info.get('type') == 'module_attribute':
            module_name = attr_info.get('module', '')
            attr_name = attr_info.get('attribute', '')

            logger.info(f"处理模块属性错误: {module_name}.{attr_name}")

            # 找到模块文件
            all_files = self._discover_all_files()
            for file_path in all_files:
                if os.path.splitext(os.path.basename(file_path))[0] == module_name:
                    symbols = self._parse_file_symbols(file_path)

                    # 模糊匹配属性名
                    symbol_names = list(symbols.keys())
                    matches = get_close_matches(attr_name, symbol_names, n=1, cutoff=0.6)

                    if matches:
                        logger.info(f"属性名纠正: '{attr_name}' -> '{matches[0]}'")

                    # 添加模块文件
                    content = self._load_file(file_path)
                    if content:
                        context["related_files"][file_path] = content
                    break

    # === 兼容性方法（保持旧API可用）===

    @property
    def file_contents(self) -> Dict[str, str]:
        """兼容旧API：返回已缓存的文件内容"""
        return self._file_cache

    @property
    def symbol_table(self) -> Dict[str, Dict]:
        """兼容旧API：返回已缓存的符号表"""
        return self._symbol_cache

    def get_scan_summary(self) -> Dict[str, Any]:
        """获取扫描统计信息"""
        return {
            'project_path': self.project_path,
            'stats': self.scan_stats.copy(),
            'cached_files': len(self._file_cache),
            'cached_symbols': len(self._symbol_cache),
        }

    def find_symbol(self, symbol_name: str) -> Optional[Dict]:
        """查找符号定义"""
        return self._find_symbol_globally(symbol_name)
