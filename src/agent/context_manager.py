"""
项目上下文管理器 - AI Debug Assistant的核心创新模块

自动扫描项目文件，构建符号表和依赖图，智能提取错误相关的上下文。
这是ChatGPT/Claude做不到的核心功能。
"""

import os
import ast
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union

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
INCLUDE_EXTENSIONS = {'.py'}  # 暂时只处理Python文件

# 文件大小限制（避免处理过大的文件）
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB


class ContextManager:
    """
    项目上下文管理器
    
    功能：
    1. 扫描项目所有Python文件
    2. 构建符号表（函数/类定义位置）
    3. 构建依赖图（import关系）
    4. 智能提取错误相关的上下文
    
    Attributes:
        project_path: 项目根目录路径
        file_contents: 文件内容缓存 {相对路径: 内容}
        symbol_table: 符号定义表 {符号名: 定义信息}
        import_graph: 导入依赖图 {文件: import信息}
    """
    
    def __init__(self, project_path: str):
        """
        初始化上下文管理器
        
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
        
        # 初始化数据结构
        self.file_contents: Dict[str, str] = {}  # {相对路径: 文件内容}
        self.symbol_table: Dict[str, Dict[str, Any]] = {}  # {符号名: 定义信息}
        self.import_graph: Dict[str, Dict[str, Any]] = {}  # {文件路径: import信息}
        
        # 扫描统计信息
        self.scan_stats = {
            'total_files': 0,
            'scanned_files': 0,
            'skipped_files': 0,
            'parse_errors': 0,
            'total_symbols': 0
        }
        
        # 记录扫描过程中的错误
        self.scan_errors: List[Dict[str, str]] = []
        
        logger.info(f"初始化ContextManager, 项目路径: {self.project_path}")
        
        # 自动执行扫描
        try:
            self._scan_project()
            self._build_symbol_table()
            self._build_import_graph()
        except Exception as e:
            logger.error(f"项目扫描失败: {e}", exc_info=True)
            # 不抛出异常，允许部分失败
            self.scan_errors.append({
                'error': 'scan_failed',
                'message': str(e)
            })
    
    def _is_ignored_dir(self, dir_name: str) -> bool:
        """
        检查目录是否应该被忽略
        
        Args:
            dir_name: 目录名
            
        Returns:
            True如果应该忽略
        """
        return dir_name in IGNORE_DIRS or dir_name.startswith('.')
    
    def _is_valid_python_file(self, file_path: str) -> bool:
        """
        检查是否是有效的Python文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            True如果是有效的Python文件
        """
        # 检查扩展名
        if not any(file_path.endswith(ext) for ext in INCLUDE_EXTENSIONS):
            return False
        
        # 检查文件大小
        try:
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                logger.warning(f"文件过大，跳过: {file_path} ({file_size} bytes)")
                return False
        except OSError:
            return False
        
        # 检查是否匹配忽略模式
        file_name = os.path.basename(file_path)
        for pattern in IGNORE_PATTERNS:
            if pattern.startswith('*') and file_name.endswith(pattern[1:]):
                return False
        
        return True

    def _scan_project(self) -> None:
        """
        扫描项目目录，收集所有相关文件
        
        递归遍历项目目录，读取所有.py文件的内容
        过滤掉venv、__pycache__等目录
        """
        logger.info(f"开始扫描项目目录: {self.project_path}")

        # 重置统计信息
        self.scan_stats = {
            'total_files': 0,
            'scanned_files': 0,
            'skipped_files': 0,
            'parse_errors': 0,
            'total_symbols': 0
        }

        try:
            # 使用os.walk遍历目录树
            for root, dirs, files in os.walk(self.project_path):
                # 计算相对路径
                rel_root = os.path.relpath(root, self.project_path)
                if rel_root == '.':
                    rel_root = ''

                # 过滤掉需要忽略的目录
                # dirs[:]是原地修改，这牙膏os.walk就不会进入这些目录
                dirs[:] = [d for d in dirs if not self._is_ignored_dir(d)]

                # 处理当前目录下的文件
                for file_name in files:
                    # 完整路径
                    file_path = os.path.join(root, file_name)

                    # 相对路径
                    relative_path = os.path.join(rel_root, file_name)

                    # 统一使用正斜杠（跨平台兼容）
                    relative_path = relative_path.replace('\\', '/')
                
                    self.scan_stats['total_files'] += 1

                    # 检查是否是有效的Python文件
                    if not self._is_valid_python_file(file_path):
                        self.scan_stats['skipped_files'] += 1
                        continue

                    # 读取文件内容
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    
                        # 存储文件内容
                        self.file_contents[relative_path] = content
                        self.scan_stats['scanned_files'] += 1
                        
                        logger.debug(f"成功扫描文件: {relative_path}")
                        
                    except UnicodeDecodeError:
                        # 尝试其他编码
                        try:
                            with open(file_path, 'r', encoding='latin-1') as f:
                                content = f.read()
                            self.file_contents[relative_path] = content
                            self.scan_stats['scanned_files'] += 1
                            logger.warning(f"使用latin-1编码读取: {relative_path}")
                        except Exception as e:
                            self.scan_stats['parse_errors'] += 1
                            self.scan_errors.append({
                                'file': relative_path,
                                'error': 'encoding_error',
                                'message': str(e)
                            })
                            logger.error(f"编码错误: {relative_path} - {e}")
                    
                    except PermissionError as e:
                        self.scan_stats['parse_errors'] += 1
                        self.scan_errors.append({
                            'file': relative_path,
                            'error': 'permission_denied',
                            'message': str(e)
                        })
                        logger.error(f"权限不足: {relative_path}")
                    
                    except Exception as e:
                        self.scan_stats['parse_errors'] += 1
                        self.scan_errors.append({
                            'file': relative_path,
                            'error': 'read_error',
                            'message': str(e)
                        })
                        logger.error(f"读取文件失败: {relative_path} - {e}", exc_info=True)
            
            # 扫描完成，记录统计
            logger.info(
                f"项目扫描完成: "
                f"总文件数={self.scan_stats['total_files']}, "
                f"成功扫描={self.scan_stats['scanned_files']}, "
                f"跳过={self.scan_stats['skipped_files']}, "
                f"错误={self.scan_stats['parse_errors']}"
            )
            
        except Exception as e:
            logger.error(f"项目扫描过程中发生错误: {e}", exc_info=True)
            raise RuntimeError(f"项目扫描失败: {e}")

    def get_scan_summary(self) -> Dict[str, Any]:
        """
        获取扫描结果摘要
        
        Returns:
            包含扫描统计和错误信息的字典
        """
        return {
            'project_path': self.project_path,
            'stats': self.scan_stats.copy(),
            'errors': self.scan_errors.copy(),
            'file_count': len(self.file_contents),
            'files': list(self.file_contents.keys())
        }
    def get_context_for_error(
        self,
        error_file: str,
        error_line: int,
        error_type: str,
        undefined_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        智能提取错误相关的上下文
        
        Args:
            error_file: 错误发生的文件路径（相对于项目根目录）
            error_line: 错误发生的行号
            error_type: 错误类型（NameError, ImportError, AttributeError等）
            undefined_name: 未定义的名称（对NameError很关键）
            
        Returns:
            Dict包含:
                - error_file_content: 错误文件的完整内容
                - related_symbols: 相关的符号定义
                - related_files: 相关文件的内容
                - import_suggestions: 建议的import语句
                
        Raises:
            ValueError: 如果error_file不在项目中
        """
        # 1. 输入验证
        if not error_file or not isinstance(error_file, str):
            raise ValueError("error_file必须是非空字符串")
        
        if error_line < 1:
            raise ValueError(f"error_line必须是正整数，当前值: {error_line}")
        
        if not error_type or not isinstance(error_type, str):
            raise ValueError("error_type必须是非空字符串")
        
        # 转换为绝对路径
        if error_file not in self.file_contents:
            raise ValueError(f"文件不在项目中: {error_file}")
        
        logger.info(f"开始提取上下文: {error_file}:{error_line}, 错误类型: {error_type}")
        
        # 2. 准备基础context
        all_files = self.file_contents.copy()
        if error_file in all_files:
            del all_files[error_file]

        context = {
            "error_file_content": self.file_contents[error_file],
            "related_symbols": {},
            "related_files": all_files,
            "import_suggestions": []
        }
        
        # 3. 根据error_type路由到不同处理函数
        try:
            if error_type == "NameError":
                self._handle_name_error(context, error_file, undefined_name)
                
            elif error_type in ["ImportError", "ModuleNotFoundError"]:
                self._handle_import_error(context, error_file, undefined_name)
                
            elif error_type == "AttributeError":
                self._handle_attribute_error(context, error_file, undefined_name)
                
            else:
                logger.warning(f"未知错误类型: {error_type}，返回基础信息")
        
        except Exception as e:
            logger.error(f"提取上下文失败: {e}", exc_info=True)
        
        # 4. 返回context
        logger.info(f"上下文提取完成，找到 {len(context['related_symbols'])} 个相关符号")
        return context


    def _handle_name_error(
        self,
        context: Dict[str, Any],
        error_file: str,  # ✅ 现在是相对路径
        undefined_name: Optional[str]
    ) -> None:
        """
        处理NameError：查找未定义的符号
        
        Args:
            context: 上下文字典（会被修改）
            error_file: 错误文件的相对路径
            undefined_name: 未定义的名称
        """
        logger.info("处理NameError...")
        
        if not undefined_name:
            logger.warning("NameError但未提供undefined_name，无法提取上下文")
            return
        
        # 在符号表中查找
        if undefined_name not in self.symbol_table:
            logger.warning(f"符号 '{undefined_name}' 未在项目中找到")
            return
        
        symbol_info = self.symbol_table[undefined_name]
        definition_file = symbol_info['file']  # ✅ 这已经是相对路径
        logger.info(f"找到符号 '{undefined_name}' 定义在: {definition_file}")
        
        # 提取定义
        definition_code = self._extract_definition(definition_file, undefined_name)
        
        if not definition_code:
            logger.warning(f"无法提取符号 '{undefined_name}' 的定义")
            return
        
        # 添加到相关符号
        context["related_symbols"][undefined_name] = {
            "file": definition_file,
            "definition": definition_code,
            "type": symbol_info['type']  # ✅ 直接使用符号表中的type
        }
        
        # 添加相关文件内容
        if definition_file not in context["related_files"]:
            context["related_files"][definition_file] = self.file_contents[definition_file]
        
        # 生成import建议
        import_suggestion = self._generate_import_suggestion(
            error_file,
            definition_file,
            undefined_name
        )
        
        if import_suggestion:
            context["import_suggestions"].append(import_suggestion)
        
        logger.info(f"NameError上下文提取完成: {undefined_name}")

    def _handle_import_error(
        self,
        context: Dict[str, Any],
        error_file: str,
        module_name: Optional[Union[str, Dict[str, str]]]
    ) -> None:
        """
        处理ImportError：查找依赖关系
        
        Args:
            context: 上下文字典（会被修改）
            error_file: 错误文件的绝对路径
            module_name: 
                - 字符串：模块名（如'utls'）
                - 字典：{'function': 'calcuate', 'module': 'utils'}
        """
        logger.info("处理ImportError...")
        
        if not module_name:
            logger.warning("ImportError但未提供module_name，无法提取上下文")
            return

        # ========== 情况1：函数导入错误（新增）==========
        if isinstance(module_name, dict):
            function_name = module_name['function']  # 'calcuate'
            module = module_name['module']           # 'utils'
            
            logger.info(f"函数导入错误: from {module} import {function_name}")
            
            # 找到模块文件
            module_file = None
            for file_path in self.file_contents.keys():
                file_module_name = os.path.splitext(os.path.basename(file_path))[0]
                if file_module_name == module:
                    module_file = file_path
                    break
            
            if not module_file:
                logger.warning(f"未找到模块文件: {module}.py")
                return
            
            logger.info(f"找到模块文件: {module_file}")
            
            # 收集该模块中的所有函数
            module_functions = []
            for symbol_name, symbol_info in self.symbol_table.items():
                if symbol_info['file'] == module_file and symbol_info['type'] == 'function':
                    module_functions.append(symbol_name)
            
            logger.info(f"模块 '{module}' 中的函数: {module_functions}")
            
            # 模糊匹配函数名
            from difflib import get_close_matches
            matches = get_close_matches(function_name, module_functions, n=1, cutoff=0.6)
            
            if matches:
                correct_function = matches[0]
                logger.info(f"🔧 函数名纠正: '{function_name}' → '{correct_function}'")
                
                # 添加模块文件
                context["related_files"][module_file] = self.file_contents[module_file]
                
                # 生成正确的import建议
                import_suggestion = f"from {module} import {correct_function}"
                context["import_suggestions"].append(import_suggestion)
                
                logger.info("ImportError上下文提取完成（函数名纠正）")
            else:
                logger.warning(f"在模块 '{module}' 中未找到匹配的函数: '{function_name}'")
            
            return
        
        # ========== 情况2：模块名错误（原有逻辑）==========
        # 收集所有可用模块名
        available_modules = []
        for file_path in self.file_contents.keys():
            if file_path.endswith('.py'):
                # ✅ 用不同的变量名，不要覆盖参数
                file_module_name = os.path.splitext(os.path.basename(file_path))[0]
                available_modules.append(file_module_name)
        
        logger.info(f"可用模块: {available_modules}")
        logger.info(f"尝试匹配: '{module_name}'")
        
        # 模糊匹配纠正拼写错误
        from difflib import get_close_matches
        matches = get_close_matches(
            module_name,    # ✅ 用module_name（参数）
            available_modules, 
            n=1,
            cutoff=0.6
        )
        
        if matches:
            corrected = matches[0]
            logger.info(f"🔧 模块名纠正: '{module_name}' → '{corrected}'")
            module_name = corrected  # ✅ 更新module_name（后面查找会用到）
        else:
            logger.warning(f"未找到匹配的模块: '{module_name}'")
        # ========== 模糊匹配结束 ==========
        
        # 查找项目中是否有这个模块（用纠正后的module_name）
        for file_path in self.file_contents.keys():
            # 检查文件名是否匹配模块名
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            
            if file_name == module_name:  # ✅ 现在module_name可能已经纠正过了
                logger.info(f"找到模块 '{module_name}' 对应文件: {file_path}")
                
                # 添加到相关文件
                context["related_files"][file_path] = self.file_contents[file_path]
                
                # 生成import建议
                import_suggestion = self._generate_import_suggestion(
                    error_file,
                    file_path,
                    None  # ImportError不需要具体符号名
                )
                
                if import_suggestion:
                    context["import_suggestions"].append(import_suggestion)
                
                break
        else:
            logger.warning(f"模块 '{module_name}' 未在项目中找到")
        
        logger.info("ImportError上下文提取完成")


    def _handle_attribute_error(
        self,
        context: Dict[str, Any],
        error_file: str,
        attribute_info: Optional[Union[str, Dict[str, str]]]
    ) -> None:
        """
        处理AttributeError：根据不同情况查找
        
        Args:
            attribute_info: 
                - 字符串：简单的属性名
                - 字典：{'type': 'object_attribute', 'class': 'User', 'attribute': 'age'}
                    或 {'type': 'module_attribute', 'module': 'utils', 'attribute': 'calculte'}
        """
        logger.info("处理AttributeError...")
        
        if not attribute_info:
            logger.warning("AttributeError但未提供attribute_info")
            return
        
        # 如果是字符串，按NameError处理
        if isinstance(attribute_info, str):
            self._handle_name_error(context, error_file, attribute_info)
            return
        
        # ========== 情况1&2：对象属性/方法错误 ==========
        if attribute_info.get('type') == 'object_attribute':
            class_name = attribute_info['class']
            attr_name = attribute_info['attribute']
            
            logger.info(f"对象属性错误: {class_name}.{attr_name}")
            
            # 在symbol_table中查找类定义
            if class_name in self.symbol_table:
                symbol_info = self.symbol_table[class_name]
                file_path = symbol_info['file']
                
                logger.info(f"找到类 '{class_name}' 在文件: {file_path}")
                
                # ✅ 新增：提取类的完整定义
                class_definition = self._extract_definition(file_path, class_name)
                
                # 添加类所在的文件
                context["related_files"][file_path] = self.file_contents[file_path]
                
                # 添加符号信息（包含完整定义）
                context["related_symbols"][class_name] = {
                    'name': class_name,
                    'type': symbol_info['type'],
                    'file': file_path,
                    'line': symbol_info['line'],
                    'definition': class_definition  # ✅ 新增
                }
                
                # 生成import建议
                import_suggestion = self._generate_import_suggestion(
                    error_file,
                    file_path,
                    class_name
                )
                if import_suggestion:
                    context["import_suggestions"].append(import_suggestion)
                
                logger.info(f"AttributeError上下文提取完成（对象属性）")
            else:
                logger.warning(f"未找到类定义: {class_name}")
            
            return
        
        # ========== 情况3：模块属性错误（函数名拼写） ==========
        if attribute_info.get('type') == 'module_attribute':
            module_name = attribute_info['module']
            attr_name = attribute_info['attribute']
            
            logger.info(f"模块属性错误: {module_name}.{attr_name}")
            
            # 找到模块文件
            module_file = None
            for file_path in self.file_contents.keys():
                file_module_name = os.path.splitext(os.path.basename(file_path))[0]
                if file_module_name == module_name:
                    module_file = file_path
                    break
            
            if not module_file:
                logger.warning(f"未找到模块文件: {module_name}.py")
                return
            
            logger.info(f"找到模块文件: {module_file}")
            
            # 收集该模块的所有函数
            module_functions = []
            for symbol_name, symbol_info in self.symbol_table.items():
                if symbol_info['file'] == module_file and symbol_info['type'] == 'function':
                    module_functions.append(symbol_name)
            
            logger.info(f"模块 '{module_name}' 中的函数: {module_functions}")
            
            # 模糊匹配函数名
            from difflib import get_close_matches
            matches = get_close_matches(attr_name, module_functions, n=1, cutoff=0.6)
            
            if matches:
                correct_function = matches[0]
                logger.info(f"🔧 函数名纠正: '{attr_name}' → '{correct_function}'")
            
            # 无论是否匹配成功，都添加模块文件
            context["related_files"][module_file] = self.file_contents[module_file]
            
            logger.info("AttributeError上下文提取完成（模块属性）")
            return


    def _extract_definition(
    self,
    file_path: str,  # ✅ 相对路径
    symbol_name: str
    ) -> str:
        """
        从文件中提取函数/类的完整定义
        
        Args:
            file_path: 文件的相对路径
            symbol_name: 符号名称（函数名或类名）
            
        Returns:
            完整的定义代码（包含docstring和函数体）
            如果提取失败返回空字符串
        """
        # ✅ 加调试
        if symbol_name == 'Calculator':
            print(f"🔍 DEBUG _extract_definition:")
            print(f"  file_path: {file_path}")
            print(f"  symbol_name: {symbol_name}")
            symbol_info = self.symbol_table.get(symbol_name)
            print(f"  symbol_info type: {type(symbol_info)}")
            print(f"  symbol_info: {symbol_info}")

            
        if file_path not in self.file_contents:
            logger.warning(f"文件不存在: {file_path}")
            return ""
        
        content = self.file_contents[file_path]
        
        # 从符号表获取行号信息
        if symbol_name in self.symbol_table:
            symbol_info = self.symbol_table[symbol_name]
            if symbol_info['file'] == file_path:
                # 直接使用符号表中的行号信息
                lines = content.split('\n')
                start_line = symbol_info['line'] - 1
                end_line = symbol_info['end_line']
                
                definition_lines = lines[start_line:end_line]
                return '\n'.join(definition_lines)
        
        logger.warning(f"在 {file_path} 中未找到符号: {symbol_name}")
        return ""


    def _generate_import_suggestion(
        self,
        from_file: str,  # ✅ 相对路径
        to_file: str,    # ✅ 相对路径
        symbol_name: Optional[str]
    ) -> str:
        """
        生成import建议
        
        Args:
            from_file: 错误文件的相对路径
            to_file: 定义文件的相对路径
            symbol_name: 要导入的符号名称（可选）
            
        Returns:
            import语句，例如 "from utils import calculate"
            如果生成失败返回空字符串
        """
        try:
            # 移除.py扩展名
            module_path = os.path.splitext(to_file)[0]
            
            # 转换路径分隔符为点号
            module_path = module_path.replace(os.sep, '.')
            
            # 处理相对导入
            if os.path.dirname(from_file) == os.path.dirname(to_file):
                # 同一目录，使用相对导入
                module_name = os.path.basename(module_path)
                if symbol_name:
                    return f"from {module_name} import {symbol_name}"
                else:
                    return f"import {module_name}"
            else:
                # 不同目录，使用绝对导入
                if symbol_name:
                    return f"from {module_path} import {symbol_name}"
                else:
                    return f"import {module_path}"
        
        except Exception as e:
            logger.error(f"生成import建议失败: {e}")
            return ""


    def _build_symbol_table(self) -> None:
        """
        构建符号表，提取所有函数和类的定义位置

        只提取顶层定义（不包括嵌套函数和类方法）
        """
        logger.info("开始构建符号表")

        # 遍历所有已扫描的文件
        for file_path, content in self.file_contents.items():
            try:
                # 解析Python代码的AST
                tree = ast.parse(content, filename=file_path)

                # 遍历AST的顶层节点
                for node in tree.body:
                    # 提取函数定义
                    if isinstance(node, ast.FunctionDef):
                        symbol_name = node.name
                        symbol_info = {
                            'type': 'function',
                            'file': file_path,
                            'line': node.lineno,
                            'end_line': node.end_lineno,
                            'col_offset': node.col_offset,
                        }

                        # 提取函数签名（参数列表）
                        args = []
                        for arg in node.args.args:
                            args.append(arg.arg)
                        symbol_info['args'] = args

                        # 处理重名情况
                        self._add_symbol(symbol_name, symbol_info)

                    # 提取类定义
                    elif isinstance(node, ast.ClassDef):
                        symbol_name = node.name
                        symbol_info = {
                        'type': 'class',
                        'file': file_path,
                        'line': node.lineno,
                        'end_line': node.end_lineno,
                        'col_offset': node.col_offset,
                        }

                        # 提取基类
                        bases = []
                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                bases.append(base.id)
                        symbol_info['bases'] = bases

                        # 处理重名情况
                        self._add_symbol(symbol_name, symbol_info)
            except SyntaxError as e:
                logger.error(f"语法错误，无法解析 {file_path}: {e}")
                self.scan_errors.append({
                    'file': file_path,
                    'error': 'syntax_error',
                    'message': str(e),
                    'line': e.lineno if hasattr(e, 'lineno') else None
                })
                self.scan_stats['parse_errors'] += 1

            except Exception as e:
                logger.error(f"解析文件失败 {file_path}: {e}", exc_info=True)
                self.scan_errors.append({
                    'file': file_path,
                    'error': 'parse_error',
                    'message': str(e),
                })
                self.scan_stats['parse_errors'] += 1

            # 更新统计信息
            total_symbols = sum(
                len(defs) if isinstance(defs, list) else 1
                for defs in self.symbol_table.values()
            )
            self.scan_stats['total_symbols'] = total_symbols

            logger.info(f"符号表构建完成，共找到 {total_symbols} 个符号")
    
    def _add_symbol(self, symbol_name: str, symbol_info: Dict[str, Any]) -> None:
        """
        添加符号到符号表，处理重名情况
        
        Args:
            symbol_name: 符号名称
            symbol_info: 符号信息
        """
        if symbol_name in self.symbol_table:
            # 处理重名：转换为列表或追加到列表
            existing = self.symbol_table[symbol_name]
            if isinstance(existing, list):
                existing.append(symbol_info)
            else:
                self.symbol_table[symbol_name] = [existing, symbol_info]
        else:
            # 第一次出现，直接存储
            self.symbol_table[symbol_name] = symbol_info

    def find_symbol(self, symbol_name: str) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """
        查找符号定义
        
        Args:
            symbol_name: 要查找的符号名称
            
        Returns:
            符号信息（字典或列表，如果有重名）
            如果未找到返回None
        """
        return self.symbol_table.get(symbol_name)

    def get_symbol_summary(self) -> Dict[str, Any]:
        """
        获取符号表摘要
        
        Returns:
            符号统计信息
        """
        # 统计各类型符号数量
        function_count = 0
        class_count = 0
        duplicate_count = 0
        
        for name, info in self.symbol_table.items():
            if isinstance(info, list):
                duplicate_count += 1
                for item in info:
                    if item['type'] == 'function':
                        function_count += 1
                    else:
                        class_count += 1
            else:
                if info['type'] == 'function':
                    function_count += 1
                else:
                    class_count += 1
        
        return {
            'total_symbols': len(self.symbol_table),
            'function_count': function_count,
            'class_count': class_count,
            'duplicate_names': duplicate_count,
            'symbols': list(self.symbol_table.keys())
        }

    def _build_import_graph(self) -> None:
        """
        构建import依赖图，分析每个文件导入了哪些模块
        """
        logger.info("开始构建import依赖图")

        # 遍历所有文件
        for file_path, content in self.file_contents.items():
            # 初始化该文件的import信息
            self.import_graph[file_path] = {
                'imports': [],
                'imported_by': []
            }

            try:
                # 解析AST
                tree = ast.parse(content, filename=file_path)

                # 遍历所有节点，查找import语句
                for node in ast.walk(tree):
                    # 处理 import xxx
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            import_info = {
                                'type': 'import',
                                'module': alias.name,
                                'alias': alias.asname,
                                'line': node.lineno
                            }
                            self.import_graph[file_path]['imports'].append(import_info)

                        # 处理 from xxx import yyy
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module if node.module else ''
                        level = node.level
                        
                        # 提取导入的名称
                        names = []
                        for alias in node.names:
                            names.append({
                                'name': alias.name,
                                'alias': alias.asname
                            })

                        import_info = {
                            'type': 'from',
                            'module': module,
                            'names': names,
                            'level': level,
                            'line': node.lineno
                        }
                        self.import_graph[file_path]['imports'].append(import_info)

            except SyntaxError as e:
                logger.error(f"解析import时语法错误 {file_path}: {e}")
            except Exception as e:
                logger.error(f"构建import图失败 {file_path}: {e}", exc_info=True)

        # 计算反向依赖
        self._calculate_reverse_imports()

        logger.info(f"Import依赖图构建完成")

    def _calculate_reverse_imports(self) -> None:
        """
        计算反向导入关系：每个模块被哪些文件导入
        """

        # 遍历所有import关系
        for file_path, import_data in self.import_graph.items():
            for import_info in import_data['imports']:
                # 尝试将import的模块名匹配到项目中的文件
                imported_file = self._resolve_import_to_file(import_info, file_path)
                if imported_file and imported_file in self.import_graph:
                    # 记录反向依赖
                    self.import_graph[imported_file]['imported_by'].append(file_path)

    def _resolve_import_to_file(self, import_info: Dict[str, Any], from_file: str) -> Optional[str]:
        """
        将import语句解析为项目中的实际文件路径
        
        Args:
            import_info: import信息
            from_file: 发起import的文件
            
        Returns:
            解析后的文件路径，如果不是项目内文件则返回None
        """
        module = import_info['module']
        
        # 处理相对导入
        if import_info.get('level', 0) > 0:
            # TODO: 处理相对导入 (. 或 ..)
            # 现在先跳过
            return None
        
        # 将模块路径转换为可能的文件路径
        # 例如: utils.calculator -> utils/calculator.py 或 utils/calculator/__init__.py
        possible_paths = []
        
        # 将点号替换为路径分隔符
        module_path = module.replace('.', '/')
        
        # 尝试.py文件
        possible_paths.append(f"{module_path}.py")
        
        # 尝试包的__init__.py
        possible_paths.append(f"{module_path}/__init__.py")
        
        # 检查这些路径是否存在于我们的文件中
        for path in possible_paths:
            if path in self.file_contents:
                return path
        
        return None

    def get_import_summary(self) -> Dict[str, Any]:
        """
        获取import依赖图的摘要信息
        
        Returns:
            import统计和依赖关系
        """
        summary = {
            'total_files': len(self.import_graph),
            'files_with_imports': 0,
            'total_imports': 0,
            'internal_imports': 0,  # 项目内部的import
            'external_imports': 0,  # 第三方库的import
            'import_details': {}
        }
        
        for file_path, import_data in self.import_graph.items():
            imports = import_data['imports']
            if imports:
                summary['files_with_imports'] += 1
                summary['total_imports'] += len(imports)
                
                # 统计每个文件的import
                summary['import_details'][file_path] = {
                    'import_count': len(imports),
                    'imported_by_count': len(import_data['imported_by']),
                    'imports': [f"{imp['module']}" for imp in imports],
                    'imported_by': import_data['imported_by']
                }
        
        return summary
