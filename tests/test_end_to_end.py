"""
Week 5 Day 6 - 端到端系统测试
测试不同类型的跨文件错误
"""
import os
import sys
import tempfile
import shutil
import time
from unittest.mock import Mock, patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.agent.debug_agent import DebugAgent


class TestCase:
    """测试用例"""
    def __init__(
        self,
        name: str,
        files: dict,  # {文件名: 内容}
        buggy_code: str,
        error_traceback: str,
        error_file: str,
        expected_fix: str = None
    ):
        self.name = name
        self.files = files
        self.buggy_code = buggy_code
        self.error_traceback = error_traceback
        self.error_file = error_file
        self.expected_fix = expected_fix


# 测试案例1: NameError - 函数未定义（基础）
CASE_1_FUNCTION_UNDEFINED = TestCase(
    name="Case 1: NameError - 函数未定义",
    files={
        "utils.py": '''def calculate(a, b):
    """计算两个数的和"""
    return a + b
''',
        "main.py": '''def test():
    result = calculate(10, 20)
    return result
'''
    },
    buggy_code='''def test():
    result = calculate(10, 20)
    return result
''',
    error_traceback='''Traceback (most recent call last):
  File "main.py", line 2, in <module>
    result = calculate(10, 20)
NameError: name 'calculate' is not defined''',
    error_file="main.py",
    expected_fix="import calculate"
)


# 测试案例2: NameError - 类未定义
CASE_2_CLASS_UNDEFINED = TestCase(
    name="Case 2: NameError - 类未定义",
    files={
        "models.py": '''class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def greet(self):
        return f"Hello, {self.name}"
''',
        "main.py": '''def create_user():
    user = User("Tom", 25)
    return user
'''
    },
    buggy_code='''def create_user():
    user = User("Tom", 25)
    return user
''',
    error_traceback='''Traceback (most recent call last):
  File "main.py", line 2, in <module>
    user = User("Tom", 25)
NameError: name 'User' is not defined''',
    error_file="main.py",
    expected_fix="import User"
)


# 测试案例3: NameError - 多个函数未定义
CASE_3_MULTIPLE_UNDEFINED = TestCase(
    name="Case 3: NameError - 多个函数未定义",
    files={
        "utils.py": '''def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
''',
        "main.py": '''def calculate():
    x = add(5, 3)
    y = multiply(x, 2)
    return y
'''
    },
    buggy_code='''def calculate():
    x = add(5, 3)
    y = multiply(x, 2)
    return y
''',
    error_traceback='''Traceback (most recent call last):
  File "main.py", line 2, in <module>
    x = add(5, 3)
NameError: name 'add' is not defined''',
    error_file="main.py",
    expected_fix="import add, multiply"
)


# 测试案例4: ImportError - 模块名错误
CASE_4_IMPORT_ERROR = TestCase(
    name="Case 4: ImportError - 模块名错误",
    files={
        "helpers.py": '''def process_data(data):
    return data.upper()
''',
        "main.py": '''from helper import process_data

def main():
    result = process_data("hello")
    return result
'''
    },
    buggy_code='''from helper import process_data

def main():
    result = process_data("hello")
    return result
''',
    error_traceback='''Traceback (most recent call last):
  File "main.py", line 1, in <module>
    from helper import process_data
ModuleNotFoundError: No module named 'helper'. Did you mean: 'helpers'?''',
    error_file="main.py",
    expected_fix="helpers"
)


# 测试案例5: 单文件错误（对照组）
CASE_5_SINGLE_FILE = TestCase(
    name="Case 5: 单文件拼写错误（对照组）",
    files={
        "main.py": '''def greet(name):
    print(f"Hello, {nme}")

greet("Tom")
'''
    },
    buggy_code='''def greet(name):
    print(f"Hello, {nme}")

greet("Tom")
''',
    error_traceback='''Traceback (most recent call last):
  File "main.py", line 4, in <module>
    greet("Tom")
  File "main.py", line 2, in greet
    print(f"Hello, {nme}")
NameError: name 'nme' is not defined. Did you mean: 'name'?''',
    error_file="main.py",
    expected_fix="name"
)


# 所有测试案例
ALL_TEST_CASES = [
    CASE_1_FUNCTION_UNDEFINED,
    CASE_2_CLASS_UNDEFINED,
    CASE_3_MULTIPLE_UNDEFINED,
    CASE_4_IMPORT_ERROR,
    CASE_5_SINGLE_FILE,
]


def run_test_case(test_case: TestCase, api_key: str) -> dict:
    """
    运行单个测试案例
    
    Returns:
        {
            'success': bool,
            'time': float,
            'attempts': int,
            'context_found': bool,
            'error': str
        }
    """
    # 创建临时项目
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 写入文件
        for filename, content in test_case.files.items():
            with open(os.path.join(temp_dir, filename), 'w') as f:
                f.write(content)
        
        # ✅ 在这里Mock，而不是在装饰器
        with patch('src.agent.tools.docker_executor.docker') as mock_docker_lib:
            # Mock docker.from_env()
            mock_client = Mock()
            mock_container = Mock()
            
            # 设置容器的wait返回值
            mock_container.wait.return_value = {'StatusCode': 0}
            
            # 设置容器的logs返回值
            mock_container.logs.return_value = b'Test passed\n'
            
            # 设置client的containers.run返回容器
            mock_client.containers.run.return_value = mock_container
            
            # 设置docker.from_env返回client
            mock_docker_lib.from_env.return_value = mock_client
            
            # 初始化Agent（这时DockerExecutor会被正确Mock）
            agent = DebugAgent(
                api_key=api_key,
                project_path=temp_dir
            )
            
            # 运行debug
            start_time = time.time()
            result = agent.debug(
                buggy_code=test_case.buggy_code,
                error_traceback=test_case.error_traceback,
                error_file=test_case.error_file,
                max_retries=2
            )
            end_time = time.time()
        
        # 检查是否找到了上下文
        context_found = False
        if agent.context_manager:
            context_found = len(agent.context_manager.symbol_table) > 0
        
        return {
            'success': result['success'],
            'time': end_time - start_time,
            'attempts': result.get('total_attempts', len(result.get('attempts', []))),
            'context_found': context_found,
            'fixed_code': result.get('final_code', ''),
            'error': None
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'time': 0,
            'attempts': 0,
            'context_found': False,
            'fixed_code': '',
            'error': str(e) + '\n' + traceback.format_exc()
        }
    
    finally:
        # 清理
        shutil.rmtree(temp_dir)


def main():
    """运行所有测试并生成报告"""
    print("\n" + "="*80)
    print("Week 5 Day 6 - 端到端系统测试")
    print("="*80)
    
    # 获取API key
    api_key = os.getenv('DEEPSEEK_API_KEY', 'fake-key-for-testing')
    if api_key == 'fake-key-for-testing':
        print("⚠️  使用fake API key，测试将只验证流程")
    else:
        print("✅ 使用真实API key")
    
    # 运行所有测试
    results = []
    
    for i, test_case in enumerate(ALL_TEST_CASES, 1):
        print(f"\n{'='*80}")
        print(f"测试 {i}/{len(ALL_TEST_CASES)}: {test_case.name}")
        print(f"{'='*80}")
        
        result = run_test_case(test_case, api_key=api_key)
        
        # 显示结果
        print(f"结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
        print(f"耗时: {result['time']:.2f}秒")
        print(f"尝试次数: {result['attempts']}")
        print(f"找到上下文: {'✅' if result['context_found'] else '❌'}")
        
        if result['error']:
            print(f"错误: {result['error']}")
        
        results.append({
            'name': test_case.name,
            **result
        })
    
    # 生成总结报告
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    total = len(results)
    success_count = sum(1 for r in results if r['success'])
    success_rate = success_count / total * 100 if total > 0 else 0
    
    avg_time = sum(r['time'] for r in results) / total if total > 0 else 0
    avg_attempts = sum(r['attempts'] for r in results if r['attempts'] > 0) / total if total > 0 else 0
    
    context_found_count = sum(1 for r in results if r['context_found'])
    
    print(f"\n总测试数: {total}")
    print(f"成功: {success_count} ({success_rate:.1f}%)")
    print(f"失败: {total - success_count}")
    print(f"平均耗时: {avg_time:.2f}秒")
    print(f"平均尝试次数: {avg_attempts:.1f}")
    print(f"找到上下文: {context_found_count}/{total}")
    
    # 详细结果表格
    print("\n详细结果:")
    print("-" * 80)
    print(f"{'案例':<40} {'成功':<8} {'耗时':<10} {'尝试':<8} {'上下文'}")
    print("-" * 80)
    
    for r in results:
        status = "✅" if r['success'] else "❌"
        context = "✅" if r['context_found'] else "❌"
        print(f"{r['name']:<40} {status:<8} {r['time']:>6.2f}秒  {r['attempts']:<8} {context}")
    
    print("-" * 80)
    
    # 保存结果到文件
    output_file = "docs/week5_end_to_end_test_results.md"
    os.makedirs("docs", exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write("# Week 5 端到端测试结果\n\n")
        f.write(f"**测试时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 总结\n\n")
        f.write(f"- 总测试数: {total}\n")
        f.write(f"- 成功率: {success_rate:.1f}% ({success_count}/{total})\n")
        f.write(f"- 平均耗时: {avg_time:.2f}秒\n")
        f.write(f"- 平均尝试次数: {avg_attempts:.1f}\n\n")
        f.write(f"## 详细结果\n\n")
        f.write("| 案例 | 成功 | 耗时 | 尝试次数 | 找到上下文 |\n")
        f.write("|------|------|------|----------|------------|\n")
        
        for r in results:
            status = "✅" if r['success'] else "❌"
            context = "✅" if r['context_found'] else "❌"
            f.write(f"| {r['name']} | {status} | {r['time']:.2f}s | {r['attempts']} | {context} |\n")
    
    print(f"\n✅ 测试结果已保存到: {output_file}")


if __name__ == "__main__":
    main()