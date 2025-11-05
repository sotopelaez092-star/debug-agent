# tests/test_code_analyzer.py
"""
测试代码分析器
"""
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.code_analyzer import CodeAnalyzer

def test_detect_none():
    """测试检测None"""
    analyzer = CodeAnalyzer()
    result = analyzer.analyze("x = None")

    assert result['has_none']
    assert 'x' in result['variables']
    print("✅ 检测None测试通过")

def test_detect_try_except():
    """测试检测try-except"""
    analyzer = CodeAnalyzer()
    code = """try:
    x = 1
except:
    x = 0"""
    result = analyzer.analyze(code)
    
    assert result['has_try_except'] == True
    print("✅ 检测try-except测试通过")


def test_detect_function_calls():
    """测试检测函数调用"""
    analyzer = CodeAnalyzer()
    result = analyzer.analyze("print(len([1, 2, 3]))")
    
    assert 'print' in result['functions_called']
    assert 'len' in result['functions_called']
    print("✅ 检测函数调用测试通过")

def test_detect_attribute_access():
    """测试检测属性访问"""
    analyzer = CodeAnalyzer()
    result = analyzer.analyze("x.name")
    
    assert len(result['attribute_accesses']) > 0
    assert result['attribute_accesses'][0]['object'] == 'x'
    assert result['attribute_accesses'][0]['attribute'] == 'name'
    print("✅ 检测属性访问测试通过")


if __name__ == "__main__":
    test_detect_none()
    test_detect_try_except()
    test_detect_function_calls()
    test_detect_attribute_access()
    print("\n🎉 所有测试通过！")
