"""测试多文件Docker执行"""
import sys
import os

# 添加src到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from agent.tools.docker_executor import DockerExecutor

def test_simple_import():
    """测试简单的跨文件import"""

    print("=" * 60)
    print("测试1: 简单的跨文件import")
    print("=" * 60)

    # 主代码
    main_code = """
from utils import add

result = add(10, 20)
print(f"Result: {result}")
"""
    # 相关文件
    related_files = {
        'utils.py': 'def add(a, b):\n    return a + b'
    }
    
    # 执行
    executor = DockerExecutor()
    result = executor.execute_with_context(
        main_code=main_code,
        related_files=related_files
    )

    # 检查结果
    print(f"成功: {result['success']}")
    print(f"退出码: {result['exit_code']}")
    print(f"输出: {result['stdout']}")
    print(f"错误: {result['stderr']}")
    
    # 验证
    assert result['success'], "执行应该成功"
    assert 'Result: 30' in result['stdout'], "输出应该包含Result: 30"
    
    print("✅ 测试通过！")
    print()


def test_subdirectory_import():
    """测试子目录import"""
    
    print("=" * 60)
    print("测试2: 子目录import")
    print("=" * 60)

    # 主代码
    main_code = """
from utils import add
from src.helpers import multiply

result1 = add(10, 20)
result2 = multiply(5, 6)
print(f"Add: {result1}")
print(f"Multiply: {result2}")
"""

    # 相关文件（包含子目录）
    related_files = {
        'utils.py': 'def add(a, b):\n    return a + b',
        'src/helpers.py': 'def multiply(a, b):\n    return a * b'
    }
    
    # 执行
    executor = DockerExecutor()
    result = executor.execute_with_context(
        main_code=main_code,
        related_files=related_files
    )

    # 检查结果
    print(f"成功: {result['success']}")
    print(f"退出码: {result['exit_code']}")
    print(f"输出: {result['stdout']}")
    print(f"错误: {result['stderr']}")
    
    # 验证
    assert result['success'], "执行应该成功"
    assert 'Add: 30' in result['stdout'], "应该有add的结果"
    assert 'Multiply: 30' in result['stdout'], "应该有multiply的结果"
    
    print("✅ 测试通过！")
    print()


def test_empty_related_files():
    """测试空related_files（单文件场景）"""
    
    print("=" * 60)
    print("测试3: 空related_files")
    print("=" * 60)
    
    # 只有main.py，没有其他文件
    main_code = """
def square(x):
    return x * x

result = square(5)
print(f"Square: {result}")
"""
    
    related_files = {}  # ← 空字典
    
    # 执行
    executor = DockerExecutor()
    result = executor.execute_with_context(
        main_code=main_code,
        related_files=related_files
    )
    
    # 检查结果
    print(f"成功: {result['success']}")
    print(f"输出: {result['stdout']}")
    
    # 验证
    assert result['success'], "单文件执行应该成功"
    assert 'Square: 25' in result['stdout'], "应该输出Square: 25"
    
    print("✅ 测试通过！")
    print()


def test_code_with_error():
    """测试代码执行失败的情况"""
    
    print("=" * 60)
    print("测试4: 代码有错误")
    print("=" * 60)
    
    # 故意写错的代码
    main_code = """
from utils import add

result = add(10)  # ← 缺少参数！
print(result)
"""
    
    related_files = {
        'utils.py': 'def add(a, b):\n    return a + b'
    }
    
    # 执行
    executor = DockerExecutor()
    result = executor.execute_with_context(
        main_code=main_code,
        related_files=related_files
    )
    
    # 检查结果
    print(f"成功: {result['success']}")
    print(f"退出码: {result['exit_code']}")
    print(f"错误: {result['stderr']}")
    
    # 验证
    assert not result['success'], "执行应该失败"
    assert 'TypeError' in result['stderr'], "应该有TypeError错误"
    
    print("✅ 测试通过！")
    print()


def test_nested_subdirectory():
    """测试多层嵌套目录"""
    
    print("=" * 60)
    print("测试5: 嵌套子目录")
    print("=" * 60)
    
    # 主代码
    main_code = """
from src.utils.math import multiply
from src.data.models import User

result = multiply(3, 4)
user = User("Tom")
print(f"Result: {result}")
print(f"User: {user.name}")
"""
    
    # 多层嵌套
    related_files = {
        'src/utils/math.py': 'def multiply(a, b):\n    return a * b',
        'src/data/models.py': '''
class User:
    def __init__(self, name):
        self.name = name
'''
    }
    
    # 执行
    executor = DockerExecutor()
    result = executor.execute_with_context(
        main_code=main_code,
        related_files=related_files
    )
    
    # 检查结果
    print(f"成功: {result['success']}")
    print(f"输出: {result['stdout']}")
    
    # 验证
    assert result['success'], "嵌套目录应该工作"
    assert 'Result: 12' in result['stdout']
    assert 'User: Tom' in result['stdout']
    
    print("✅ 测试通过！")
    print()



if __name__ == '__main__':
    test_simple_import()
    test_subdirectory_import()
    test_empty_related_files()      # ← 新增
    test_code_with_error()          # ← 新增
    test_nested_subdirectory()      # ← 新增
    print("=" * 60)
    print("🎉 所有测试通过！")
    print("=" * 60)



