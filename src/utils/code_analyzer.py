# src/utils/code_analyzer.py
"""
代码分析器
使用AST分析Python代码结构
"""
import ast
from typing import Dict, List, Set

class CodeAnalyzer:
    """Python代码分析器"""

    def __init__(self):
        self.variables: Set[str] = set()
        self.functions_called: Set[str] = set()
        self.has_none: bool = False
        self.has_try_except: bool = False
        self.attribute_accesses: List[Dict] = []

    def analyze(self, code: str) -> Dict:
        """
        分析代码

        Args:
            code: Python代码字符串

        Returns:
            分析结果
        """
        try:
            # 解析代码为AST
            tree = ast.parse(code)

            # 遍历AST
            self._visit_tree(tree)

            # 返回结果
            return {
                'variables': list(self.variables),
                'functions_called': list(self.functions_called),
                'has_none': self.has_none,
                'has_try_except': self.has_try_except,
                'attribute_accesses': self.attribute_accesses,
                'line_count': len(code.split('\n'))
            }

        except SyntaxError as e:
            return {
                'error': 'SyntaxError',
                'message':str(e)
            }

    def _visit_tree(self, tree):
        """遍历AST树，提取信息"""
        
        for node in ast.walk(tree):
            # 1. 检查变量赋值（x = ...)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.variables.add(target.id)
            
            # 2. 检查函数调用（print(...), len(...) 等）
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    self.functions_called.add(node.func.id)
            
            # 3. 检查None值
            if isinstance(node, ast.Constant):
                if node.value is None:
                    self.has_none = True
            
            # 4. 检查try-except
            if isinstance(node, ast.Try):
                self.has_try_except = True
            
            # 5. 检查属性访问（x.name）
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    self.attribute_accesses.append({
                        'object': node.value.id,
                        'attribute': node.attr
                    })

if __name__ == "__main__":
    # 测试1: 基础案例
    print("=" * 60)
    print("测试1: AttributeError案例")
    analyzer1 = CodeAnalyzer()  # 新建实例
    test_code1 = """x = None
print(x.name)"""
    result = analyzer1.analyze(test_code1)
    print(result)
    
    # 测试2: try-except
    print("\n" + "=" * 60)
    print("测试2: try-except案例")
    analyzer2 = CodeAnalyzer()  # 新建实例
    test_code2 = """try:
    num = int('abc')
except ValueError:
    num = 0"""
    result = analyzer2.analyze(test_code2)
    print(result)
    
    # 测试3: 多个函数调用
    print("\n" + "=" * 60)
    print("测试3: 多个函数调用")
    analyzer3 = CodeAnalyzer()  # 新建实例
    test_code3 = """data = [1, 2, 3]
length = len(data)
print(length)"""
    result = analyzer3.analyze(test_code3)
    print(result)