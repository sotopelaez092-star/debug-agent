# tests/test_multi_agent.py
"""
测试Multi-Agent系统
"""
import sys
import os
import logging

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 现在可以导入了
from src.agent.multi_agent import debug_code

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 测试案例1：简单拼写错误
def test_simple_error():
    buggy_code = """
def greet(name):
    print(f"Hello, {nme}")  # 拼写错误

greet("Tom")
"""
    
    error_traceback = """
Traceback (most recent call last):
  File "test.py", line 4, in <module>
    greet("Tom")
  File "test.py", line 2, in greet
    print(f"Hello, {nme}")
NameError: name 'nme' is not defined
"""
    
    result = debug_code(
        buggy_code=buggy_code,
        error_traceback=error_traceback,
        project_path=None  # 单文件，不需要项目路径
    )
    
    print("\n" + "=" * 60)
    print("测试结果：")
    print("=" * 60)
    print(f"成功: {result['test_result']['success']}")
    print(f"尝试次数: {result['attempts']}")
    print(f"修复后的代码:\n{result['fixed_code']}")


if __name__ == "__main__":
    test_simple_error()