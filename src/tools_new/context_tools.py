"""ContextTools - 预建索引层，支持增量更新和缓存"""
import pickle
import hashlib
import ast
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

try:
    from Levenshtein import distance as levenshtein
except ImportError:
    # 简单的 Levenshtein 距离实现作为后备
    def levenshtein(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

from src.models.results import SymbolMatch

logger = logging.getLogger(__name__)


class ContextTools:
    """预建索引层 - 支持增量更新和缓存"""

    IGNORE_PATTERNS = [
        '/venv/', '/env/', '/.venv/', '/__pycache__/', '/.pytest_cache/',
        '/.git/', '/.svn/', '/node_modules/', '/dist/', '/build/',
        '/.idea/', '/.vscode/'
        # 注意：移除了 '/tests/'，因为测试项目可能包含 tests 目录
    ]

    def __init__(self, project_path: str, cache_dir: str = ".debug_agent_cache"):
        self.project_path = Path(project_path).resolve()
        # 缓存目录放在项目路径下
        self.cache_dir = self.project_path / cache_dir
        self.cache_dir.mkdir(exist_ok=True)

        # 索引
        self.symbol_table: Dict[str, List[SymbolMatch]] = {}
        self.import_graph: Dict[str, List[str]] = {}
        self.class_table: Dict[str, Dict] = {}
        self.function_signatures: Dict[str, str] = {}
        self.dict_keys: Set[str] = set()
        self.call_graph: Dict[str, List[Dict]] = {}
        # 新增：函数返回字典键追踪（用于 KeyError 分析）
        self.function_return_keys: Dict[str, Dict] = {}

        # 文件哈希记录（用于增量更新）
        self.file_hashes: Dict[str, str] = {}

        logger.info(f"初始化 ContextTools，项目路径: {self.project_path}")
        self._load_or_build_indexes()

    # ========== 索引构建 ==========

    def _load_or_build_indexes(self):
        """加载或构建索引"""
        cache_file = self.cache_dir / "indexes.pkl"

        if cache_file.exists():
            try:
                cached = pickle.load(cache_file.open('rb'))
                current_hash = self._get_project_hash()

                if cached.get('project_hash') == current_hash:
                    logger.info("从缓存加载索引")
                    self._load_from_cache(cached)
                    return
                else:
                    logger.info("项目已更新，执行增量更新")
                    self._incremental_update(cached)
                    return
            except Exception as e:
                logger.warning(f"加载缓存失败: {e}，重新构建索引")

        logger.info("首次构建索引")
        self._full_build()
        self._save_cache()

    def _get_project_hash(self) -> str:
        """计算项目哈希值（用于快速变更检测）"""
        mtimes = []
        for py_file in self.project_path.rglob("*.py"):
            if self._should_ignore(py_file):
                continue
            try:
                mtimes.append(f"{py_file}:{py_file.stat().st_mtime}")
            except:
                continue
        return hashlib.md5("\n".join(sorted(mtimes)).encode()).hexdigest()

    def _get_file_hashes(self) -> Dict[str, str]:
        """获取所有文件的哈希值字典（用于增量更新）"""
        hashes = {}
        for py_file in self.project_path.rglob("*.py"):
            if self._should_ignore(py_file):
                continue
            try:
                relative_path = str(py_file.relative_to(self.project_path))
                mtime = py_file.stat().st_mtime
                hashes[relative_path] = hashlib.md5(f"{mtime}".encode()).hexdigest()
            except:
                continue
        return hashes

    def _should_ignore(self, path: Path) -> bool:
        """判断是否应该忽略路径"""
        path_str = str(path)
        return any(p in path_str for p in self.IGNORE_PATTERNS)

    def _full_build(self):
        """完整构建索引"""
        logger.info("开始完整索引构建")
        for py_file in self.project_path.rglob("*.py"):
            if self._should_ignore(py_file):
                continue
            self._index_single_file(py_file)

        # 更新文件哈希
        self.file_hashes = self._get_file_hashes()
        logger.info(f"索引构建完成，符号数: {sum(len(v) for v in self.symbol_table.values())}")

    def _incremental_update(self, cached: dict):
        """增量更新索引 - 只重建有变更的文件"""
        self._load_from_cache(cached)

        old_hashes = self.file_hashes
        new_hashes = self._get_file_hashes()

        # 找出变更的文件
        changed_files = []
        deleted_files = []

        # 检查新增和修改的文件
        for file_path, new_hash in new_hashes.items():
            if file_path not in old_hashes or old_hashes[file_path] != new_hash:
                changed_files.append(file_path)

        # 检查删除的文件
        for file_path in old_hashes:
            if file_path not in new_hashes:
                deleted_files.append(file_path)

        if not changed_files and not deleted_files:
            logger.info("项目无变更，使用缓存")
            return

        logger.info(f"增量更新: {len(changed_files)} 个文件变更, {len(deleted_files)} 个文件删除")

        # 清理删除文件的索引
        for file_path in deleted_files:
            self._remove_file_symbols(file_path)

        # 重建变更文件的索引
        for file_path in changed_files:
            # 先清理旧索引
            self._remove_file_symbols(file_path)
            # 重新索引
            full_path = self.project_path / file_path
            if full_path.exists():
                self._index_single_file(full_path)

        # 更新文件哈希
        self.file_hashes = new_hashes
        self._save_cache()

        logger.info(f"增量更新完成，符号数: {sum(len(v) for v in self.symbol_table.values())}")

    def _remove_file_symbols(self, relative_path: str):
        """清理指定文件的所有索引数据"""
        # 清理 symbol_table
        for symbol_name in list(self.symbol_table.keys()):
            self.symbol_table[symbol_name] = [
                match for match in self.symbol_table[symbol_name]
                if match.file != relative_path
            ]
            if not self.symbol_table[symbol_name]:
                del self.symbol_table[symbol_name]

        # 清理 import_graph
        if relative_path in self.import_graph:
            del self.import_graph[relative_path]

        # 清理 class_table
        for class_name in list(self.class_table.keys()):
            if self.class_table[class_name].get('file') == relative_path:
                del self.class_table[class_name]

        # 清理 function_signatures
        for sig_key in list(self.function_signatures.keys()):
            if sig_key.startswith(f"{relative_path}:"):
                del self.function_signatures[sig_key]

        # 清理 call_graph
        if relative_path in self.call_graph:
            del self.call_graph[relative_path]

        logger.debug(f"已清理文件索引: {relative_path}")

    def _index_single_file(self, file_path: Path):
        """索引单个文件"""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content, filename=str(file_path))

            relative_path = str(file_path.relative_to(self.project_path))

            for node in ast.walk(tree):
                # 函数定义
                if isinstance(node, ast.FunctionDef):
                    self._add_symbol(node.name, relative_path, node.lineno, "function")
                    self._extract_signature(node, relative_path)
                    self._extract_calls(node, relative_path)
                    # 新增：提取函数返回的字典结构
                    self._extract_return_dict_structure(node, relative_path)

                # 类定义
                elif isinstance(node, ast.ClassDef):
                    self._add_symbol(node.name, relative_path, node.lineno, "class")
                    self._extract_class_info(node, relative_path)

                # 导入
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    self._extract_import(node, relative_path)

                # 字典 key
                elif isinstance(node, ast.Dict):
                    for key in node.keys:
                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                            self.dict_keys.add(key.value)

        except SyntaxError as e:
            logger.debug(f"跳过语法错误文件: {file_path} - {e}")
        except Exception as e:
            logger.debug(f"索引文件失败: {file_path} - {e}")

    def _extract_return_dict_structure(self, func_node: ast.FunctionDef, file_path: str):
        """提取函数返回的字典结构（用于 KeyError 分析）"""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
                structure = self._parse_dict_ast(node.value)
                if structure and structure.get('keys'):
                    func_key = f"{file_path}:{func_node.name}"
                    self.function_return_keys[func_key] = {
                        'function': func_node.name,
                        'file': file_path,
                        'line': func_node.lineno,
                        'structure': structure
                    }
                break  # 只取第一个 return 语句

    def _parse_dict_ast(self, dict_node: ast.Dict, depth: int = 0) -> Optional[Dict]:
        """递归解析字典 AST 结构"""
        if depth > 3:  # 防止过深递归
            return None

        result = {'keys': [], 'nested': {}}

        for key, value in zip(dict_node.keys, dict_node.values):
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                key_str = key.value
                result['keys'].append(key_str)
                # 递归解析嵌套字典
                if isinstance(value, ast.Dict):
                    nested = self._parse_dict_ast(value, depth + 1)
                    if nested:
                        result['nested'][key_str] = nested

        return result if result['keys'] else None

    def _add_symbol(self, name: str, file: str, line: int, symbol_type: str):
        """添加符号到索引"""
        if name not in self.symbol_table:
            self.symbol_table[name] = []
        self.symbol_table[name].append(SymbolMatch(
            name=name,
            file=file,
            line=line,
            symbol_type=symbol_type,
            confidence=1.0
        ))

    def _extract_signature(self, node: ast.FunctionDef, file_path: str):
        """提取函数签名（同时索引函数参数）"""
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
            # 将函数参数也添加到符号表（标记为 parameter 类型）
            self._add_symbol(arg.arg, file_path, node.lineno, "parameter")
        signature = f"def {node.name}({', '.join(args)})"
        self.function_signatures[node.name] = signature

    def _extract_class_info(self, node: ast.ClassDef, file_path: str):
        """提取类信息"""
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)

        self.class_table[node.name] = {
            'file': file_path,
            'line': node.lineno,
            'methods': methods
        }

    def _extract_import(self, node, file_path: str):
        """提取导入信息"""
        if file_path not in self.import_graph:
            self.import_graph[file_path] = []

        if isinstance(node, ast.Import):
            for alias in node.names:
                self.import_graph[file_path].append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                self.import_graph[file_path].append(node.module)

    def _extract_calls(self, node: ast.FunctionDef, file_path: str):
        """提取函数调用关系"""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    func_name = child.func.id
                    if func_name not in self.call_graph:
                        self.call_graph[func_name] = []
                    self.call_graph[func_name].append({
                        'file': file_path,
                        'line': child.lineno,
                        'caller': node.name
                    })

    # ========== 查询方法 ==========

    def search_symbol(
        self,
        name: str,
        fuzzy: bool = True,
        error_file: str = ""
    ) -> List[SymbolMatch]:
        """搜索符号，支持模糊匹配"""
        # 精确匹配
        if name in self.symbol_table:
            matches = self.symbol_table[name].copy()
            for m in matches:
                m.confidence = 1.0
            logger.info(f"精确匹配到符号 '{name}': {len(matches)} 个位置")
            return sorted(matches, key=lambda x: x.confidence, reverse=True)

        if not fuzzy:
            return []

        # 模糊匹配
        logger.info(f"开始模糊匹配符号 '{name}'")
        matches = []
        for symbol_name, locations in self.symbol_table.items():
            dist = levenshtein(name.lower(), symbol_name.lower())
            max_len = max(len(name), len(symbol_name))
            similarity = 1 - (dist / max_len)

            # 降低阈值到 0.6，允许编辑距离 ≤ 2 的拼写错误通过
            if similarity > 0.6:  # 阈值
                for loc in locations:
                    match = SymbolMatch(
                        name=symbol_name,
                        file=loc.file,
                        line=loc.line,
                        symbol_type=loc.symbol_type,
                        confidence=self._calculate_confidence(
                            name, symbol_name, loc, error_file
                        )
                    )
                    matches.append(match)

        matches = sorted(matches, key=lambda x: x.confidence, reverse=True)
        logger.info(f"模糊匹配到 {len(matches)} 个候选")
        return matches

    def _calculate_confidence(
        self,
        query: str,
        match: str,
        loc: SymbolMatch,
        error_file: str
    ) -> float:
        """多因子加权置信度"""
        score = 0.0

        # 1. 编辑距离 (0.5) - 提高权重，因为这是最重要的指标
        max_len = max(len(query), len(match))
        edit_dist = levenshtein(query, match)
        edit_sim = 1 - (edit_dist / max_len)

        # 对于非常接近的匹配（编辑距离 ≤ 2），给予额外奖励
        if edit_dist <= 2:
            edit_sim = max(edit_sim, 0.85)  # 保证至少 0.85 的相似度

        score += edit_sim * 0.5

        # 2. 唯一性 (0.2) - 降低权重
        all_matches = self.symbol_table.get(match, [])
        uniqueness = 1.0 if len(all_matches) == 1 else 1.0 / len(all_matches)
        score += uniqueness * 0.2

        # 3. 可达性 (0.2)
        reachable = 1.0 if self._is_importable(error_file, loc.file) else 0.3
        score += reachable * 0.2

        # 4. 类型匹配 (0.1)
        # parameter 也应该算高分，因为 NameError 经常是参数名拼写错误
        type_score = 1.0 if loc.symbol_type in ("function", "class", "parameter") else 0.5
        score += type_score * 0.1

        return round(score, 2)

    def _is_importable(self, from_file: str, to_file: str) -> bool:
        """检查是否可导入"""
        if not from_file:
            return True
        # 简化实现：同一项目内都认为可导入
        return True

    def search_module(self, module: str, fuzzy: bool = True) -> List[dict]:
        """搜索模块路径 - 增强版，支持路径结构匹配和包搜索"""
        results = []
        module_parts = module.split('.')  # ['api', 'endpoints', 'users'] 或 ['api', 'endpoints']
        target_name = module_parts[-1]    # 'users' 或 'endpoints'

        # 1. 搜索 .py 文件
        for py_file in self.project_path.rglob("*.py"):
            if self._should_ignore(py_file):
                continue

            rel_path = py_file.relative_to(self.project_path)
            # 转换为模块路径: api/v2/endpoints/users.py -> api.v2.endpoints.users
            actual_module_path = str(rel_path.with_suffix('')).replace('/', '.')
            actual_parts = actual_module_path.split('.')

            # 检查文件匹配
            self._check_module_match(
                module_parts, target_name, actual_module_path, actual_parts,
                str(rel_path), fuzzy, results
            )

        # 2. 搜索包（带 __init__.py 的目录）- 对于缺少中间包层级的情况很重要
        for init_file in self.project_path.rglob("__init__.py"):
            if self._should_ignore(init_file):
                continue

            # 包路径是 __init__.py 的父目录
            pkg_dir = init_file.parent
            rel_path = pkg_dir.relative_to(self.project_path)
            # 转换为模块路径: api/v2/endpoints -> api.v2.endpoints
            actual_module_path = str(rel_path).replace('/', '.')
            if actual_module_path == '.':
                continue  # 跳过根目录
            actual_parts = actual_module_path.split('.')

            # 检查包匹配
            self._check_module_match(
                module_parts, target_name, actual_module_path, actual_parts,
                str(rel_path), fuzzy, results, is_package=True
            )

        # 去重并排序
        seen = set()
        unique_results = []
        for r in sorted(results, key=lambda x: x['confidence'], reverse=True):
            key = r['module']
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        return unique_results

    def _check_module_match(
        self, query_parts: List[str], target_name: str,
        actual_module_path: str, actual_parts: List[str],
        file_path: str, fuzzy: bool, results: List[dict],
        is_package: bool = False
    ):
        """检查模块是否匹配查询"""
        query_module = '.'.join(query_parts)

        # 1. 完全精确匹配
        if actual_module_path == query_module:
            results.append({
                'module': query_module,
                'file': file_path,
                'confidence': 1.0
            })
            return

        # 2. 目标名精确匹配 + 路径结构分析（处理缺少中间包的情况）
        if actual_parts[-1] == target_name:
            # 计算路径相似度
            path_similarity = self._calculate_path_similarity(query_parts, actual_parts)
            if path_similarity > 0.5:
                # 分析路径差异，生成修复建议
                diff_analysis = self._analyze_path_diff(query_parts, actual_parts)
                results.append({
                    'module': actual_module_path,
                    'file': file_path,
                    'confidence': round(path_similarity, 2),
                    'suggestion': diff_analysis.get('suggestion', ''),
                    'refactor_type': diff_analysis.get('type', 'unknown'),
                    'is_package': is_package
                })
                return

        # 3. 模糊名称匹配
        if fuzzy:
            dist = levenshtein(target_name, actual_parts[-1])
            max_len = max(len(target_name), len(actual_parts[-1]))
            similarity = 1 - (dist / max_len)

            # 对于编辑距离 ≤ 2 的匹配，给予额外奖励
            if dist <= 2:
                similarity = max(similarity, 0.85)

            # 降低阈值到 0.6，与 search_symbol 一致
            if similarity > 0.6:
                results.append({
                    'module': actual_module_path,
                    'file': file_path,
                    'confidence': round(similarity * 0.8, 2),  # 降权因为名称不完全匹配
                    'is_package': is_package
                })

    def _calculate_path_similarity(self, query_parts: List[str], actual_parts: List[str]) -> float:
        """计算路径结构相似度

        例如: ['api', 'endpoints', 'users'] vs ['api', 'v2', 'endpoints', 'users']
        共同子序列: api, endpoints, users = 3/3 = 1.0 (查询部分全部匹配)
        """
        # 找最长公共子序列 (LCS)
        common = 0
        j = 0
        for part in query_parts:
            for k in range(j, len(actual_parts)):
                if part == actual_parts[k]:
                    common += 1
                    j = k + 1
                    break

        # 共同部分占查询路径的比例
        query_match_ratio = common / len(query_parts) if query_parts else 0

        # 如果查询的所有部分都在实际路径中找到，给高分
        if common == len(query_parts):
            # 额外考虑路径长度差异（越接近越好）
            length_penalty = 1 - (abs(len(actual_parts) - len(query_parts)) * 0.1)
            return min(0.95, query_match_ratio * max(0.7, length_penalty))

        return query_match_ratio * 0.8

    def _analyze_path_diff(self, old_path: List[str], new_path: List[str]) -> dict:
        """分析路径差异类型，生成修复建议"""
        # Case 1: 添加前缀 (utils -> shared.utils)
        if len(new_path) > len(old_path):
            # 检查旧路径是否是新路径的后缀
            if new_path[-len(old_path):] == old_path:
                prefix = new_path[:-len(old_path)]
                return {
                    'type': 'prefix_added',
                    'suggestion': f"模块被移动到 {'.'.join(prefix)} 包下，正确导入: from {'.'.join(new_path)} import ..."
                }

        # Case 2: 添加中间层 (api.endpoints -> api.v2.endpoints)
        # 找共同前缀
        common_prefix = []
        for i, (o, n) in enumerate(zip(old_path, new_path)):
            if o == n:
                common_prefix.append(o)
            else:
                break

        if common_prefix:
            # 找出缺少的中间部分
            old_remaining = old_path[len(common_prefix):]
            new_remaining = new_path[len(common_prefix):]

            # 检查旧路径剩余部分是否在新路径剩余部分中
            missing_parts = []
            j = 0
            for part in old_remaining:
                found = False
                for k in range(j, len(new_remaining)):
                    if part == new_remaining[k]:
                        # 记录跳过的部分（这些是缺少的中间层）
                        missing_parts.extend(new_remaining[j:k])
                        j = k + 1
                        found = True
                        break
                if not found:
                    break

            if missing_parts:
                return {
                    'type': 'intermediate_missing',
                    'missing': missing_parts,
                    'suggestion': f"缺少中间包层级 '{'.'.join(missing_parts)}'，正确导入: from {'.'.join(new_path)} import ..."
                }

        return {
            'type': 'path_changed',
            'suggestion': f"模块路径已变更为: {'.'.join(new_path)}"
        }

    def get_callers(self, func_name: str) -> List[dict]:
        """获取函数调用者"""
        return self.call_graph.get(func_name, [])

    def get_class_methods(self, class_name: str) -> List[str]:
        """获取类的方法列表"""
        return self.class_table.get(class_name, {}).get('methods', [])

    def get_function_signature(self, func_name: str) -> Optional[str]:
        """获取函数签名"""
        return self.function_signatures.get(func_name)

    def search_dict_keys(self, query: str = "", fuzzy: bool = True) -> List[str]:
        """搜索字典 key"""
        if not query:
            return list(self.dict_keys)

        if query in self.dict_keys:
            return [query]

        if not fuzzy:
            return []

        # 模糊匹配
        matches = []
        for key in self.dict_keys:
            dist = levenshtein(query, key)
            max_len = max(len(query), len(key))
            similarity = 1 - (dist / max_len)
            if similarity > 0.7:
                matches.append(key)

        return matches

    def search_dict_key_origin(self, missing_key: str) -> List[Dict]:
        """搜索字典键的来源，支持嵌套结构追踪

        用于处理如 config["log_level"] → config["logging"]["level"] 的情况
        """
        results = []

        for func_key, info in self.function_return_keys.items():
            structure = info.get('structure', {})
            func_name = info.get('function', '')
            file_path = info.get('file', '')

            # 1. 顶层键精确匹配
            if missing_key in structure.get('keys', []):
                results.append({
                    'function': func_name,
                    'file': file_path,
                    'key': missing_key,
                    'access_path': f'["{missing_key}"]',
                    'confidence': 1.0,
                    'type': 'exact'
                })
                continue

            # 2. 嵌套键搜索 - 检查是否在某个嵌套结构中
            nested_results = self._search_nested_key(
                structure, missing_key, func_name, file_path
            )
            results.extend(nested_results)

            # 3. 模糊匹配顶层键
            for key in structure.get('keys', []):
                dist = levenshtein(missing_key.lower(), key.lower())
                if dist <= 2 and dist > 0:  # 编辑距离 ≤ 2 且不完全相同
                    similarity = 1 - (dist / max(len(missing_key), len(key)))
                    results.append({
                        'function': func_name,
                        'file': file_path,
                        'key': key,
                        'access_path': f'["{key}"]',
                        'confidence': round(similarity, 2),
                        'type': 'fuzzy',
                        'suggestion': f"'{missing_key}' 可能是 '{key}' 的拼写错误"
                    })

        # 按置信度排序
        return sorted(results, key=lambda x: x['confidence'], reverse=True)

    def _search_nested_key(
        self, structure: Dict, missing_key: str,
        func_name: str, file_path: str, prefix: str = ""
    ) -> List[Dict]:
        """在嵌套字典结构中搜索键"""
        results = []

        for parent_key, nested in structure.get('nested', {}).items():
            current_prefix = f'{prefix}["{parent_key}"]' if prefix else f'["{parent_key}"]'

            # 检查嵌套键是否匹配
            if missing_key in nested.get('keys', []):
                results.append({
                    'function': func_name,
                    'file': file_path,
                    'key': f'{parent_key}.{missing_key}',
                    'access_path': f'{current_prefix}["{missing_key}"]',
                    'confidence': 0.95,
                    'type': 'nested',
                    'suggestion': f"键 '{missing_key}' 在嵌套结构中: dict{current_prefix}['{missing_key}']"
                })

            # 检查父键是否与 missing_key 相关（如 log_level → logging.level）
            # 将 missing_key 按 _ 分割，检查是否匹配父键+嵌套键
            parts = missing_key.split('_')
            if len(parts) >= 2:
                potential_parent = parts[0]
                potential_child = '_'.join(parts[1:])

                if parent_key.lower() == potential_parent.lower() or \
                   parent_key.lower().startswith(potential_parent.lower()):
                    # 检查嵌套键
                    for nested_key in nested.get('keys', []):
                        if nested_key.lower() == potential_child.lower():
                            results.append({
                                'function': func_name,
                                'file': file_path,
                                'key': f'{parent_key}.{nested_key}',
                                'access_path': f'{current_prefix}["{nested_key}"]',
                                'confidence': 0.9,
                                'type': 'restructured',
                                'suggestion': f"'{missing_key}' 已重构为嵌套结构: dict{current_prefix}['{nested_key}']"
                            })

            # 递归搜索更深层嵌套
            deeper_results = self._search_nested_key(
                nested, missing_key, func_name, file_path, current_prefix
            )
            results.extend(deeper_results)

        return results

    def detect_circular_imports(self) -> List[List[str]]:
        """检测循环导入"""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]):
            if node in rec_stack:
                # 找到环
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.import_graph.get(node, []):
                # 查找对应的文件
                for file in self.import_graph.keys():
                    if neighbor in file or file.endswith(f"{neighbor}.py"):
                        dfs(file, path.copy())

            rec_stack.remove(node)

        for file in self.import_graph.keys():
            if file not in visited:
                dfs(file, [])

        return cycles

    # ========== 缓存 ==========

    def _save_cache(self):
        """保存缓存"""
        cache_file = self.cache_dir / "indexes.pkl"
        data = {
            'project_hash': self._get_project_hash(),
            'file_hashes': self.file_hashes,
            'symbol_table': self.symbol_table,
            'import_graph': self.import_graph,
            'class_table': self.class_table,
            'function_signatures': self.function_signatures,
            'dict_keys': self.dict_keys,
            'call_graph': self.call_graph,
            'function_return_keys': self.function_return_keys,  # 新增
        }
        try:
            pickle.dump(data, cache_file.open('wb'))
            logger.info(f"缓存已保存到 {cache_file}")
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")

    def _load_from_cache(self, cached: dict):
        """从缓存加载"""
        self.file_hashes = cached.get('file_hashes', {})
        self.symbol_table = cached.get('symbol_table', {})
        self.import_graph = cached.get('import_graph', {})
        self.class_table = cached.get('class_table', {})
        self.function_signatures = cached.get('function_signatures', {})
        self.dict_keys = cached.get('dict_keys', set())
        self.call_graph = cached.get('call_graph', {})
        self.function_return_keys = cached.get('function_return_keys', {})  # 新增
        logger.info("缓存加载完成")
