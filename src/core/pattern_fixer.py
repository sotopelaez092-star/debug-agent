"""PatternFixer - 基于模式的快速修复器（无需LLM）"""
import re
import logging
from typing import Optional, Tuple, List
from difflib import get_close_matches

logger = logging.getLogger(__name__)


class PatternFixer:
    """
    基于规则的快速修复器
    处理常见的简单错误，避免 LLM 调用
    """

    # 常见的方法名拼写错误
    COMMON_METHOD_TYPOS = {
        'appned': 'append',
        'apend': 'append',
        'lenght': 'length',
        'lentgh': 'length',
        'pirnt': 'print',
        'pritn': 'print',
        'retrun': 'return',
        'ture': 'True',
        'flase': 'False',
        'fasle': 'False',
        'slef': 'self',
        'sefl': 'self',
        'improt': 'import',
        'form': 'from',  # careful - context matters
        'opn': 'open',
        'oepn': 'open',
        'summ': 'sum',
        'lne': 'len',
        'maxx': 'max',
        'mni': 'min',
        'raneg': 'range',
        'prnit': 'print',
        'lst': 'list',
        'srt': 'str',
        'itn': 'int',
        'flt': 'float',
        'bol': 'bool',
        'dct': 'dict',
        'tpl': 'tuple',
        'st': 'set',
    }

    # 常见的属性拼写错误
    COMMON_ATTR_TYPOS = {
        'uper': 'upper',
        'loewr': 'lower',
        'lowr': 'lower',
        'striip': 'strip',
        'strp': 'strip',
        'spilt': 'split',
        'joiin': 'join',
        'repalce': 'replace',
        'startwith': 'startswith',
        'endwith': 'endswith',
        'isalpa': 'isalpha',
        'isnumric': 'isnumeric',
    }

    # 标准库模块拼写
    STDLIB_MODULES = {
        'maath': 'math', 'maths': 'math', 'matth': 'math',
        'ramdom': 'random', 'randm': 'random', 'randon': 'random',
        'jsn': 'json', 'jsom': 'json', 'jsonn': 'json',
        'oss': 'os', 'syss': 'sys',
        'tiem': 'time', 'timee': 'time',
        'collectons': 'collections', 'collecitons': 'collections', 'colections': 'collections',
        'itertols': 'itertools', 'itertool': 'itertools',
        'functols': 'functools', 'functool': 'functools',
        'pathlibb': 'pathlib', 'pathllib': 'pathlib',
        'rre': 're',
        'loging': 'logging', 'loggging': 'logging', 'loggin': 'logging',
        'datetme': 'datetime', 'dattime': 'datetime', 'datetim': 'datetime',
        'typng': 'typing', 'typping': 'typing',
        'subproces': 'subprocess', 'subproccess': 'subprocess',
        'heapqq': 'heapq', 'heapq': 'heapq',
        'bisectt': 'bisect',
        'copyy': 'copy',
        'operatorr': 'operator',
        'enumm': 'enum',
    }

    # 常见的键名拼写错误（用于 KeyError）
    COMMON_KEY_TYPOS = {
        'nme': 'name', 'namee': 'name', 'naem': 'name',
        'valeu': 'value', 'vlaue': 'value', 'vlue': 'value',
        'ky': 'key', 'kye': 'key',
        'tpye': 'type', 'tyep': 'type',
        'id': 'id', 'idd': 'id',
        'dat': 'data', 'dataa': 'data',
        'resutl': 'result', 'reuslt': 'result',
        'statsu': 'status', 'stauts': 'status',
        'mesage': 'message', 'messge': 'message',
    }

    def try_fix(self, code: str, error_type: str, error_message: str) -> Optional[Tuple[str, str]]:
        """
        尝试快速修复 - 扫描并修复所有已知的错误模式

        Args:
            code: 源代码
            error_type: 错误类型 (NameError, AttributeError, etc.)
            error_message: 错误消息

        Returns:
            (fixed_code, explanation) 如果能修复，否则 None
        """
        fixed_code = code
        all_explanations = []

        # 尝试所有修复方法，不只是当前错误类型
        # 这样可以一次修复多个不同类型的错误

        # 1. 尝试修复属性错误 (AttributeError)
        result = self._fix_attribute_error(fixed_code, error_message)
        if result:
            fixed_code, explanation = result
            all_explanations.append(explanation)

        # 2. 尝试修复导入错误 (ImportError/ModuleNotFoundError)
        result = self._fix_import_error(fixed_code, error_message)
        if result:
            fixed_code, explanation = result
            all_explanations.append(explanation)

        # 3. 尝试修复名称错误 (NameError) - 只在代码有变化时才尝试
        if error_type == "NameError":
            result = self._fix_name_error(fixed_code, error_message)
            if result:
                fixed_code, explanation = result
                all_explanations.append(explanation)

        # 4. 尝试修复键错误 (KeyError)
        if error_type == "KeyError":
            result = self._fix_key_error(fixed_code, error_message)
            if result:
                fixed_code, explanation = result
                all_explanations.append(explanation)

        # 如果有修复，返回合并的结果
        if all_explanations and fixed_code != code:
            return fixed_code, "; ".join(all_explanations)

        return None

    def _fix_name_error(self, code: str, error_message: str) -> Optional[Tuple[str, str]]:
        """修复 NameError"""
        # 提取未定义的名称
        match = re.search(r"name ['\"](\w+)['\"] is not defined", error_message)
        if not match:
            return None

        undefined_name = match.group(1)

        # 1. 检查是否是常见拼写错误
        if undefined_name in self.COMMON_METHOD_TYPOS:
            correct = self.COMMON_METHOD_TYPOS[undefined_name]
            fixed_code = re.sub(rf'\b{undefined_name}\b', correct, code)
            return fixed_code, f"修复拼写错误: {undefined_name} → {correct}"

        # 2. 从代码中找相似的已定义名称
        defined_names = self._extract_defined_names(code)
        similar = get_close_matches(undefined_name, defined_names, n=1, cutoff=0.8)
        if similar:
            correct = similar[0]
            fixed_code = re.sub(rf'\b{undefined_name}\b', correct, code)
            return fixed_code, f"修复变量名拼写: {undefined_name} → {correct}"

        return None

    def _fix_attribute_error(self, code: str, error_message: str) -> Optional[Tuple[str, str]]:
        """修复 AttributeError - 扫描并修复所有已知的属性拼写错误"""
        fixed_code = code
        fixes = []

        # 1. 先修复错误消息中提到的错误
        match = re.search(r"has no attribute ['\"](\w+)['\"]", error_message)
        if match:
            wrong_attr = match.group(1)

            # 检查 Python 建议
            suggest_match = re.search(r"Did you mean[:\s]+['\"](\w+)['\"]", error_message)
            if suggest_match:
                correct = suggest_match.group(1)
                if f'.{wrong_attr}' in fixed_code:
                    fixed_code = re.sub(rf'\.{wrong_attr}\b', f'.{correct}', fixed_code)
                    fixes.append(f"{wrong_attr} → {correct}")

            # 检查常见拼写错误
            elif wrong_attr in self.COMMON_ATTR_TYPOS:
                correct = self.COMMON_ATTR_TYPOS[wrong_attr]
                fixed_code = re.sub(rf'\.{wrong_attr}\b', f'.{correct}', fixed_code)
                fixes.append(f"{wrong_attr} → {correct}")

        # 2. 扫描并修复所有其他已知的属性拼写错误
        for wrong, correct in self.COMMON_ATTR_TYPOS.items():
            if f'.{wrong}' in fixed_code:
                fixed_code = re.sub(rf'\.{wrong}\b', f'.{correct}', fixed_code)
                if f"{wrong} → {correct}" not in fixes:
                    fixes.append(f"{wrong} → {correct}")

        # 3. 扫描常见的字符串方法拼写错误（扩展列表）
        extra_typos = {
            # 字符串方法
            'lowwer': 'lower', 'uppper': 'upper', 'tittle': 'title',
            'capitlize': 'capitalize', 'swapcse': 'swapcase',
            'cenetr': 'center', 'ljuust': 'ljust', 'rjuust': 'rjust',
            'zfil': 'zfill', 'counnt': 'count', 'findd': 'find',
            'inddex': 'index', 'isalnm': 'isalnum', 'isdigt': 'isdigit',
            'islowwer': 'islower', 'isuppr': 'isupper', 'isspce': 'isspace',
            'starswith': 'startswith', 'endswidth': 'endswith',
            'replacce': 'replace', 'splitt': 'split', 'rsplitt': 'rsplit',
            'splt': 'split', 'stip': 'strip', 'raed': 'read',
            'jion': 'join', 'formt': 'format', 'encod': 'encode',
            'decod': 'decode', 'expandtab': 'expandtabs',
            # 列表方法
            'srot': 'sort', 'revese': 'reverse', 'appnd': 'append',
            'exted': 'extend', 'insrt': 'insert', 'remov': 'remove',
            'popp': 'pop', 'cler': 'clear', 'cpy': 'copy',
            # 字典方法
            'kyes': 'keys', 'valuse': 'values', 'valeus': 'values',
            'itmes': 'items', 'upadte': 'update', 'gte': 'get',
            # 集合方法
            'ad': 'add', 'uion': 'union', 'intersecton': 'intersection',
            # random 模块方法
            'shuffe': 'shuffle', 'choce': 'choice', 'sampl': 'sample',
            'randint': 'randint', 'chioce': 'choice',
            # os.path 方法
            'jion': 'join', 'exsts': 'exists', 'exsits': 'exists',
            # 其他常见方法
            'most_comon': 'most_common', 'toatl': 'total',
            'apend': 'append', 'apendleft': 'appendleft', 'poplft': 'popleft',
            'heapfy': 'heapify', 'heappoop': 'heappop', 'heappsh': 'heappush',
            'nsmallst': 'nsmallest', 'bisect_lefft': 'bisect_left', 'insrt': 'insort',
            'deepcpy': 'deepcopy',
        }
        for wrong, correct in extra_typos.items():
            if f'.{wrong}' in fixed_code:
                fixed_code = re.sub(rf'\.{wrong}\b', f'.{correct}', fixed_code)
                if f"{wrong} → {correct}" not in fixes:
                    fixes.append(f"{wrong} → {correct}")

        if fixes and fixed_code != code:
            return fixed_code, f"修复属性名拼写: {', '.join(fixes)}"

        return None

    def _fix_import_error(self, code: str, error_message: str) -> Optional[Tuple[str, str]]:
        """修复 ImportError/ModuleNotFoundError - 扫描并修复所有已知的模块拼写错误"""
        fixed_code = code
        fixes = []

        # 1. 扫描并修复所有已知的标准库拼写错误
        for wrong, correct in self.STDLIB_MODULES.items():
            # 检查 import xxx
            if re.search(rf'\bimport\s+{wrong}\b', fixed_code):
                fixed_code = re.sub(rf'\bimport\s+{wrong}\b', f'import {correct}', fixed_code)
                fixed_code = re.sub(rf'\b{wrong}\.', f'{correct}.', fixed_code)  # 修复使用处
                if f"{wrong} → {correct}" not in fixes:
                    fixes.append(f"{wrong} → {correct}")
            # 检查 from xxx import
            if re.search(rf'\bfrom\s+{wrong}\b', fixed_code):
                fixed_code = re.sub(rf'\bfrom\s+{wrong}\b', f'from {correct}', fixed_code)
                if f"{wrong} → {correct}" not in fixes:
                    fixes.append(f"{wrong} → {correct}")

        # 2. 扩展的模块拼写错误列表
        extra_module_typos = {
            'jsn': 'json', 'jsom': 'json', 'jsonn': 'json',
            'maths': 'math', 'matth': 'math',
            'randon': 'random', 'randoom': 'random',
            'datetme': 'datetime', 'dattime': 'datetime',
            'typng': 'typing', 'typping': 'typing',
            'pathliib': 'pathlib', 'pathllib': 'pathlib',
            'loging': 'logging', 'loggin': 'logging',
            'itertools': 'itertools', 'itertool': 'itertools',
            'functool': 'functools', 'functoolss': 'functools',
            'subproces': 'subprocess', 'subproccess': 'subprocess',
        }
        for wrong, correct in extra_module_typos.items():
            if re.search(rf'\bimport\s+{wrong}\b', fixed_code):
                fixed_code = re.sub(rf'\bimport\s+{wrong}\b', f'import {correct}', fixed_code)
                fixed_code = re.sub(rf'\b{wrong}\.', f'{correct}.', fixed_code)
                if f"{wrong} → {correct}" not in fixes:
                    fixes.append(f"{wrong} → {correct}")
            if re.search(rf'\bfrom\s+{wrong}\b', fixed_code):
                fixed_code = re.sub(rf'\bfrom\s+{wrong}\b', f'from {correct}', fixed_code)
                if f"{wrong} → {correct}" not in fixes:
                    fixes.append(f"{wrong} → {correct}")

        if fixes and fixed_code != code:
            return fixed_code, f"修复模块名拼写: {', '.join(fixes)}"

        return None

    def _fix_key_error(self, code: str, error_message: str) -> Optional[Tuple[str, str]]:
        """修复 KeyError - 修复字典键名拼写错误"""
        fixed_code = code
        fixes = []

        # 提取错误的键名
        match = re.search(r"KeyError:\s*['\"](\w+)['\"]", error_message)
        if not match:
            return None

        wrong_key = match.group(1)

        # 1. 检查是否是常见的键名拼写错误
        if wrong_key in self.COMMON_KEY_TYPOS:
            correct = self.COMMON_KEY_TYPOS[wrong_key]
            # 修复字典访问: data['nme'] -> data['name']
            fixed_code = re.sub(rf"\[(['\"]){wrong_key}\1\]", f"['{correct}']", fixed_code)
            # 修复 .get() 调用
            fixed_code = re.sub(rf"\.get\s*\(\s*(['\"]){wrong_key}\1", f".get('{correct}'", fixed_code)
            if fixed_code != code:
                fixes.append(f"{wrong_key} → {correct}")

        # 2. 扫描代码中所有的键名，找相似的
        if not fixes:
            # 提取代码中定义的键名
            defined_keys = set()
            # 字典定义: {'key': value}
            defined_keys.update(re.findall(r"['\"](\w+)['\"]\s*:", code))
            # 字典访问: data['key']
            defined_keys.update(re.findall(r"\[['\"](\w+)['\"]\]", code))

            similar = get_close_matches(wrong_key, list(defined_keys), n=1, cutoff=0.8)
            if similar:
                correct = similar[0]
                fixed_code = re.sub(rf"\[(['\"]){wrong_key}\1\]", f"['{correct}']", fixed_code)
                fixed_code = re.sub(rf"\.get\s*\(\s*(['\"]){wrong_key}\1", f".get('{correct}'", fixed_code)
                if fixed_code != code:
                    fixes.append(f"{wrong_key} → {correct}")

        if fixes and fixed_code != code:
            return fixed_code, f"修复键名拼写: {', '.join(fixes)}"

        return None

    def _fix_type_error(self, code: str, error_message: str) -> Optional[Tuple[str, str]]:
        """修复简单的 TypeError"""
        # 缺少参数
        match = re.search(r"missing (\d+) required positional argument", error_message)
        if match:
            # 这种情况通常需要上下文，先跳过
            return None

        # 参数过多
        match = re.search(r"takes (\d+) positional arguments? but (\d+) (?:was|were) given", error_message)
        if match:
            # 这种情况也需要上下文
            return None

        return None

    def _extract_defined_names(self, code: str) -> List[str]:
        """从代码中提取已定义的名称"""
        names = set()

        # 函数定义
        names.update(re.findall(r'def\s+(\w+)\s*\(', code))

        # 类定义
        names.update(re.findall(r'class\s+(\w+)\s*[:\(]', code))

        # 变量赋值
        names.update(re.findall(r'^(\w+)\s*=', code, re.MULTILINE))

        # for 循环变量
        names.update(re.findall(r'for\s+(\w+)\s+in', code))

        # 函数参数
        for match in re.finditer(r'def\s+\w+\s*\(([^)]*)\)', code):
            params = match.group(1)
            names.update(re.findall(r'(\w+)\s*[,=)]', params))

        return list(names)
