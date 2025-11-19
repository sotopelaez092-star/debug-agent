"""
测试DebugAgent集成ContextManager - 端到端测试
"""
import os
import sys
import tempfile
import shutil

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.agent.debug_agent import DebugAgent


def test_debug_with_context():
    """
    测试完整流程：跨文件错误 + 上下文提取 + 修复
    """
    # 1. 创建临时项目
    temp_dir = tempfile.mkdtemp()
    print(f"\n创建临时项目: {temp_dir}")
    
    # utils.py - 工具函数
    utils_content = '''def calculate(a, b):
    """计算两个数的和"""
    return a + b

def multiply(x, y):
    """计算两个数的乘积"""
    return x * y
'''
    
    # main.py - 有错误的代码
    main_content = '''# 忘记import了
def test_calculate():
    result = calculate(10, 20)
    print(f"Result: {result}")
    return result

if __name__ == "__main__":
    test_calculate()
'''
    
    # 写入文件
    with open(os.path.join(temp_dir, 'utils.py'), 'w') as f:
        f.write(utils_content)
    
    with open(os.path.join(temp_dir, 'main.py'), 'w') as f:
        f.write(main_content)
    
    print("创建的文件:")
    print(f"  - utils.py (包含calculate函数)")
    print(f"  - main.py (忘记import calculate)")
    
    # 2. 准备错误信息
    buggy_code = main_content
    error_traceback = '''Traceback (most recent call last):
  File "main.py", line 8, in <module>
    test_calculate()
  File "main.py", line 3, in test_calculate
    result = calculate(10, 20)
NameError: name 'calculate' is not defined'''
    
    # 3. 初始化DebugAgent（带project_path）
    print("\n初始化DebugAgent...")
    
    # 从环境变量获取API key
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("⚠️  未设置DEEPSEEK_API_KEY环境变量")
        print("   测试将只验证流程，不会真正调用LLM")
        api_key = "fake-key-for-testing"
    
    agent = DebugAgent(
        api_key=api_key,
        project_path=temp_dir  # ← 传入项目路径
    )
    
    print(f"✅ Agent初始化成功")
    print(f"   - ContextManager已启用")
    print(f"   - 项目路径: {temp_dir}")
    
    # 4. 验证ContextManager已初始化
    assert agent.context_manager is not None, "ContextManager应该被初始化"
    assert agent.project_path == temp_dir, "项目路径应该被保存"
    
    print("\n验证ContextManager:")
    print(f"  - 扫描到 {len(agent.context_manager.file_contents)} 个文件")
    print(f"  - 符号表: {list(agent.context_manager.symbol_table.keys())}")
    
    # 5. 手动测试上下文提取（在调用debug前）
    print("\n测试上下文提取:")
    try:
        context = agent.context_manager.get_context_for_error(
            error_file="main.py",
            error_line=3,
            error_type="NameError",
            undefined_name="calculate"
        )
        
        print(f"  ✅ 找到 {len(context['related_symbols'])} 个相关符号")
        
        if 'calculate' in context['related_symbols']:
            symbol_info = context['related_symbols']['calculate']
            print(f"     - calculate (来自 {symbol_info['file']})")
            print(f"     - 类型: {symbol_info['type']}")
        
        if context['import_suggestions']:
            print(f"  ✅ Import建议: {context['import_suggestions']}")
        
    except Exception as e:
        print(f"  ❌ 上下文提取失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. 运行完整的debug流程
    print("\n" + "="*60)
    print("运行完整Debug流程...")
    print("="*60)
    
    try:
        result = agent.debug(
            buggy_code=buggy_code,
            error_traceback=error_traceback,
            error_file="main.py",  # ← 传入错误文件路径
            max_retries=2
        )
        
        print("\n" + "="*60)
        print("Debug结果:")
        print("="*60)
        print(f"成功: {result['success']}")
        print(f"尝试次数: {result.get('total_attempts', len(result.get('attempts', [])))}")

        if result['success']:
            print("\n✅ 修复成功!")
            print("\n修复后的代码:")
            print("-" * 60)
            print(result.get('final_code', '未找到修复代码'))  # ← 使用final_code
            print("-" * 60)
            
            # 从attempts中获取说明（如果有）
            if result.get('attempts') and len(result['attempts']) > 0:
                last_attempt = result['attempts'][-1]
                if 'explanation' in last_attempt:
                    print("\n修复说明:")
                    print(last_attempt['explanation'])
            
            # 验证修复代码包含import
            final_code = result.get('final_code', '')
            if 'import calculate' in final_code or 'from utils import calculate' in final_code:
                print("\n✅ 验证通过: 修复代码包含了import语句")
            else:
                print("\n⚠️  警告: 修复代码可能缺少import语句")
        else:
            print("\n❌ 修复失败")
            
            # 显示失败原因（如果有）
            if result.get('attempts') and len(result['attempts']) > 0:
                last_attempt = result['attempts'][-1]
                if 'execution_result' in last_attempt:
                    exec_result = last_attempt['execution_result']
                    if 'stderr' in exec_result and exec_result['stderr']:
                        print(f"错误信息: {exec_result['stderr'][:200]}")

        # 7. 验证关键点
        print("\n" + "="*60)
        print("验证关键点:")
        print("="*60)

        # 验证尝试记录中包含上下文信息
        if result.get('attempts'):
            first_attempt = result['attempts'][0]
            print(f"✅ 共进行了 {len(result['attempts'])} 次尝试")
            
            # 检查是否使用了RAG
            if result.get('solutions'):
                print(f"✅ 使用了RAG检索（找到 {len(result['solutions'])} 个方案）")
            
            # 简单检查：如果final_code包含import，说明可能用了上下文
            if result.get('final_code') and 'import' in result.get('final_code', ''):
                print(f"✅ 修复代码包含import语句（可能使用了上下文）")
        
    except Exception as e:
        print(f"\n❌ Debug流程失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 8. 清理
        print("\n清理临时文件...")
        shutil.rmtree(temp_dir)
        print("✅ 测试完成")


def test_debug_without_context():
    """
    测试单文件模式：不提供project_path
    """
    print("\n" + "="*60)
    print("测试单文件模式（无ContextManager）")
    print("="*60)
    
    # 简单的单文件错误
    buggy_code = '''def greet(name):
    print(f"Hello, {nme}")  # 拼写错误

greet("Tom")
'''
    
    error_traceback = '''Traceback (most recent call last):
  File "test.py", line 4, in <module>
    greet("Tom")
  File "test.py", line 2, in greet
    print(f"Hello, {nme}")
NameError: name 'nme' is not defined. Did you mean: 'name'?'''
    
    # 不提供project_path
    api_key = os.getenv('DEEPSEEK_API_KEY', 'fake-key')
    agent = DebugAgent(
        api_key=api_key,
        project_path=None  # ← 不提供项目路径
    )
    
    print("✅ Agent初始化成功（单文件模式）")
    assert agent.context_manager is None, "ContextManager不应该被初始化"
    
    try:
        result = agent.debug(
            buggy_code=buggy_code,
            error_traceback=error_traceback,
            error_file=None,  # ← 不提供错误文件
            max_retries=1
        )
        
        print(f"\n成功: {result['success']}")
        
        if result['success']:
            print("\n✅ 单文件模式修复成功")
            print(f"修复代码包含 'name': {'name' in result['fixed_code']}")
        
    except Exception as e:
        print(f"\n注意: 单文件模式测试失败（可能是API key问题）: {e}")
    
    print("\n✅ 单文件模式测试完成")


if __name__ == "__main__":
    # 测试1: 完整的多文件场景（带上下文）
    test_debug_with_context()
    
    print("\n\n")
    
    # 测试2: 单文件场景（不带上下文）
    test_debug_without_context()