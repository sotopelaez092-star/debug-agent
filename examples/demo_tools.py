"""
基础工具使用示例
演示错误解析器和代码分析器的功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import ErrorParser, CodeAnalyzer


def demo_error_parser():
    """演示错误解析器"""
    print("=" * 60)
    print("🔍 错误解析器示例")
    print("=" * 60)
    
    parser = ErrorParser()
    
    errors = [
        "AttributeError: 'NoneType' object has no attribute 'name'",
        "TypeError: can only concatenate str (not 'int') to str",
        "KeyError: 'age'",
        "IndexError: list index out of range"
    ]
    
    for error in errors:
        result = parser.parse(error)
        print(f"\n原始错误: {error}")
        print(f"错误类型: {result['error_type']}")
        if 'object_type' in result:
            print(f"  对象类型: {result['object_type']}")
        if 'attribute' in result:
            print(f"  属性名: {result['attribute']}")
        if 'key' in result:
            print(f"  键名: {result['key']}")


def demo_code_analyzer():
    """演示代码分析器"""
    print("\n\n" + "=" * 60)
    print("🔬 代码分析器示例")
    print("=" * 60)
   
    
    code_samples = [
        ("None访问", "x = None\nprint(x.name)"),
        ("try-except", "try:\n    num = int('abc')\nexcept ValueError:\n    num = 0"),
        ("列表操作", "data = [1, 2, 3]\nprint(len(data))")
    ]
    
    for name, code in code_samples:
        analyzer = CodeAnalyzer()
        result = analyzer.analyze(code)
        print(f"\n示例: {name}")
        print(f"代码:\n{code}")
        print(f"\n分析结果:")
        print(f"  变量: {result['variables']}")
        print(f"  函数调用: {result['functions_called']}")
        print(f"  包含None: {result['has_none']}")
        print(f"  包含异常处理: {result['has_try_except']}")


if __name__ == "__main__":
    demo_error_parser()
    demo_code_analyzer()
    print("\n\n✅ 演示完成！")