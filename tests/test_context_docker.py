"""测试Docker多文件执行（不依赖RAG）"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent.context_manager import ContextManager
from src.agent.tools.docker_executor import DockerExecutor


def test_context_manager_with_docker():
    """测试ContextManager + Docker集成"""
    
    print("=" * 60)
    print("测试: ContextManager + Docker多文件执行")
    print("=" * 60)
    
    # 1. 创建临时项目
    project_path = "/tmp/test_project"
    os.makedirs(project_path, exist_ok=True)
    
    # 写入utils.py
    with open(os.path.join(project_path, "utils.py"), 'w') as f:
        f.write("def calculate(a, b):\n    return a + b\n")
    
    # 写入错误的main.py
    with open(os.path.join(project_path, "main.py"), 'w') as f:
        f.write("""
result = calculate(10, 20)
print(f"Result: {result}")
""")
    
    print("\n步骤1: 使用ContextManager分析项目")
    # 2. 使用ContextManager
    context_manager = ContextManager(project_path)
    context = context_manager.get_context_for_error(
        error_file="main.py",
        error_line=2,
        error_type="NameError",
        undefined_name="calculate"
    )
    
    print(f"找到 {len(context.get('related_files', {}))} 个相关文件")
    print(f"Import建议: {context.get('import_suggestions', [])}")
    
    # 3. 生成修复代码（手动，不用LLM）
    fixed_code = """from utils import calculate

result = calculate(10, 20)
print(f"Result: {result}")
"""
    
    print("\n步骤2: 在Docker中执行修复代码")
    # 4. 在Docker中执行
    executor = DockerExecutor()
    result = executor.execute_with_context(
        main_code=fixed_code,
        related_files=context['related_files'],
        main_filename="main.py"
    )
    
    # 5. 检查结果
    print(f"\n执行成功: {result['success']}")
    print(f"输出: {result['stdout']}")
    print(f"错误: {result['stderr']}")
    
    # 验证
    assert result['success'], "应该执行成功"
    assert 'Result: 30' in result['stdout'], "应该输出正确结果"
    
    print("\n✅ 测试通过！")
    print("✅ ContextManager找到了相关文件")
    print("✅ Docker成功执行了多文件代码")
    print("✅ 真正使用了import（不是复制代码）")
    
    # 清理
    import shutil
    shutil.rmtree(project_path)


if __name__ == '__main__':
    test_context_manager_with_docker()
    print("=" * 60)
    print("🎉 集成测试通过！")
    print("=" * 60)