"""
测试错误解析器
"""
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.error_parser import ErrorParser


def test_attribute_error():
    """测试AttributeError解析"""
    parser = ErrorParser()
    result = parser.parse("AttributeError: 'NoneType' object has no attribute 'name'")
    
    assert result['error_type'] == 'AttributeError'
    assert result['object_type'] == 'NoneType'
    assert result['attribute'] == 'name'
    print("✅ AttributeError测试通过")


def test_type_error():
    """测试TypeError解析"""
    parser = ErrorParser()
    result = parser.parse("TypeError: can only concatenate str (not 'int') to str")
    
    assert result['error_type'] == 'TypeError'
    assert result['wrong_type'] == 'int'
    print("✅ TypeError测试通过")


def test_key_error():
    """测试KeyError解析"""
    parser = ErrorParser()
    result = parser.parse("KeyError: 'age'")
    
    assert result['error_type'] == 'KeyError'
    assert result['key'] == 'age'
    print("✅ KeyError测试通过")


if __name__ == "__main__":
    test_attribute_error()
    test_type_error()
    test_key_error()
    print("\n🎉 所有测试通过！")