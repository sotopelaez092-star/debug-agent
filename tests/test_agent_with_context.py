"""测试Agent集成多文件Docker"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent.debug_agent import DebugAgent


def test_cross_file_nameerror():
    """测试跨文件NameError修复"""
    
    print("=" * 60)
    print("测试: 跨文件NameError（真实import）")
    print("=" * 60)
    
    # 模拟项目目录结构
    project_path = "/tmp/test_project"
    
    # 创建临时项目
    os.makedirs(project_path, exist_ok=True)
    
    # 写入utils.py
    with open(os.path.join(project_path, "utils.py"), 'w') as f:
        f.write("def calculate(a, b):\n    return a + b\n")
    
    # 错误的main.py（没有import）
    buggy_code = """
result = calculate(10, 20)
print(f"Result: {result}")
"""
    
    # 错误信息
    error_traceback = """
Traceback (most recent call last):
  File "main.py", line 2, in <module>
    result = calculate(10, 20)
NameError: name 'calculate' is not defined
"""
    
    # 创建Agent
    agent = DebugAgent(project_path=project_path)
    
    # 执行debug
    result = agent.debug(
        buggy_code=buggy_code,
        error_traceback=error_traceback,
        max_retries=2
    )
    
    # 检查结果
    print(f"\n成功: {result['success']}")
    print(f"尝试次数: {result['attempts']}")
    print(f"\n修复后的代码:")
    print(result['fixed_code'])
    print(f"\n执行结果:")
    print(result['final_execution'])
    
    # 验证
    assert result['success'], "应该修复成功"
    assert 'from utils import calculate' in result['fixed_code'], "应该有import语句"
    assert result['final_execution']['success'], "执行应该成功"
    assert 'Result: 30' in result['final_execution']['stdout'], "应该输出正确结果"
    
    print("\n✅ 测试通过！真正使用了import！")
    
    # 清理
    import shutil
    shutil.rmtree(project_path)


if __name__ == '__main__':
    test_cross_file_nameerror()
    print("=" * 60)
    print("🎉 集成测试通过！")
    print("=" * 60)