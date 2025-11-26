"""测试批量评估中的ContextManager"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tempfile
import shutil
from src.agent.debug_agent import DebugAgent
from dotenv import load_dotenv

load_dotenv()


def test_context_manager_in_batch():
    """测试ContextManager在批量评估中是否work"""
    
    # 创建临时项目
    project_path = tempfile.mkdtemp(prefix="test_context_")
    
    try:
        # 写入utils.py
        utils_file = os.path.join(project_path, 'utils.py')
        with open(utils_file, 'w') as f:
            f.write("""def calculate(a, b):
    return a + b
""")
        
        # 写入main.py（有错误）
        main_file = os.path.join(project_path, 'main.py')
        with open(main_file, 'w') as f:
            f.write("""result = calculate(10, 20)
print(f'Result: {result}')
""")
        
        print("=" * 60)
        print("测试：跨文件NameError")
        print("=" * 60)
        
        # 创建Agent
        api_key = os.getenv('DEEPSEEK_API_KEY')
        agent = DebugAgent(project_path=project_path, api_key=api_key)
        
        # 准备错误信息
        buggy_code = """result = calculate(10, 20)
print(f'Result: {result}')
"""
        
        error_traceback = """Traceback (most recent call last):
  File "main.py", line 1, in <module>
    result = calculate(10, 20)
NameError: name 'calculate' is not defined
"""
        
        # 执行debug
        result = agent.debug(
            buggy_code=buggy_code,
            error_traceback=error_traceback,
            error_file='main.py',
            max_retries=1
        )
        
        print("\n结果：")
        print(f"成功: {result['success']}")
        print(f"尝试次数: {result['total_attempts']}")
        
        if result['success']:
            print("\n修复代码:")
            print(result['final_code'])
            
            # 检查是否使用了import
            if 'from utils import' in result['final_code'] or 'import utils' in result['final_code']:
                print("\n✅ 使用了import！ContextManager工作了！")
            else:
                print("\n⚠️ 没有使用import，是直接定义函数")
        
    finally:
        shutil.rmtree(project_path)


if __name__ == '__main__':
    test_context_manager_in_batch()