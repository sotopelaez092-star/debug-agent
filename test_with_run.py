#!/usr/bin/env python3
"""AI Debug Assistant 完整测试 - 包含运行验证"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from src.agent.debug_agent import DebugAgent

TEST_CASES = [
    {
        "name": "NameError - 拼写错误",
        "buggy_code": """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        totla += num
    return total
print(calculate_sum([1, 2, 3, 4, 5]))
""",
        "error_traceback": """
Traceback (most recent call last):
  File "main.py", line 4, in calculate_sum
    totla += num
NameError: name 'totla' is not defined
""",
        "expected_output": "15",
    },
    {
        "name": "TypeError - 类型转换",
        "buggy_code": """
def format_price(price):
    return "Price: $" + price
print(format_price(99))
""",
        "error_traceback": """
Traceback (most recent call last):
  File "main.py", line 2, in format_price
    return "Price: $" + price
TypeError: can only concatenate str (not "int") to str
""",
        "expected_output": "Price: $99",
    },
    {
        "name": "AttributeError - 方法名",
        "buggy_code": """
text = "hello world"
print(text.uper())
""",
        "error_traceback": """
Traceback (most recent call last):
  File "main.py", line 2, in <module>
    print(text.uper())
AttributeError: 'str' object has no attribute 'uper'
""",
        "expected_output": "HELLO WORLD",
    },
    {
        "name": "IndexError - 列表越界",
        "buggy_code": """
numbers = [1, 2, 3]
print(numbers[3])
""",
        "error_traceback": """
Traceback (most recent call last):
  File "main.py", line 2, in <module>
    print(numbers[3])
IndexError: list index out of range
""",
        "expected_output": "3",
    },
    {
        "name": "递归终止条件",
        "buggy_code": """
def factorial(n):
    return n * factorial(n - 1)
print(factorial(5))
""",
        "error_traceback": """
Traceback (most recent call last):
  File "main.py", line 2, in factorial
    return n * factorial(n - 1)
RecursionError: maximum recursion depth exceeded
""",
        "expected_output": "120",
    },
    {
        "name": "ZeroDivisionError",
        "buggy_code": """
def safe_divide(a, b):
    return a / b
print(safe_divide(10, 0))
""",
        "error_traceback": """
Traceback (most recent call last):
  File "main.py", line 2, in safe_divide
    return a / b
ZeroDivisionError: division by zero
""",
        "expected_output": None,
    },
]


def run_code(code: str, timeout: int = 5) -> dict:
    """在子进程中运行代码"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        temp_file = f.name

    try:
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'stdout': '', 'stderr': 'Timeout', 'returncode': -1}
    except Exception as e:
        return {'success': False, 'stdout': '', 'stderr': str(e), 'returncode': -1}
    finally:
        os.unlink(temp_file)


def run_test(agent, test_case, index):
    print(f"\n{'='*60}")
    print(f"测试 {index}: {test_case['name']}")
    print('='*60)

    # 1. 验证原始代码确实有错
    print("\n[Step 1] 验证原始代码有错误...")
    original_result = run_code(test_case['buggy_code'])
    if original_result['success']:
        print(f"  ⚠️ 原始代码居然能运行: {original_result['stdout']}")
    else:
        print(f"  ✅ 确认有错误")

    # 2. 调用 AI 修复
    print("\n[Step 2] 调用 AI 修复...")
    try:
        result = agent.debug(
            buggy_code=test_case['buggy_code'],
            error_traceback=test_case['error_traceback'],
            error_file="main.py",
            max_retries=2
        )

        if not result.get('success') or not result.get('final_code'):
            print("  ❌ AI 修复失败")
            return {'name': test_case['name'], 'ai_fix': False, 'runs': False, 'correct': False}

        final_code = result['final_code']
        print(f"  ✅ AI 返回修复代码")

    except Exception as e:
        print(f"  ❌ AI 异常: {e}")
        return {'name': test_case['name'], 'ai_fix': False, 'runs': False, 'correct': False}

    # 3. 执行修复后的代码
    print("\n[Step 3] 执行修复后代码...")
    fixed_result = run_code(final_code)

    if not fixed_result['success']:
        print(f"  ❌ 修复后代码仍有错误: {fixed_result['stderr'][:80]}")
        return {'name': test_case['name'], 'ai_fix': True, 'runs': False, 'correct': False}

    print(f"  ✅ 代码运行成功，输出: {fixed_result['stdout']}")

    # 4. 验证输出是否正确
    print("\n[Step 4] 验证输出...")
    expected = test_case['expected_output']
    actual = fixed_result['stdout']

    if expected is None:
        correct = True
        print(f"  ✅ 输出正确 (任意非崩溃输出)")
    elif expected in actual:
        correct = True
        print(f"  ✅ 输出正确 (期望: {expected}, 实际: {actual})")
    else:
        correct = False
        print(f"  ❌ 输出不符预期 (期望: {expected}, 实际: {actual})")

    return {
        'name': test_case['name'],
        'ai_fix': True,
        'runs': True,
        'correct': correct,
        'output': actual
    }


def main():
    print("\n" + "="*60)
    print("🧪 AI Debug Assistant 完整验证测试")
    print("   (修复 + 运行 + 输出验证)")
    print("="*60)

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 请先配置 DEEPSEEK_API_KEY")
        return

    print(f"\n✅ API Key 已配置")

    agent = DebugAgent(api_key=api_key, project_path=str(Path(__file__).parent))

    results = []
    for i, tc in enumerate(TEST_CASES, 1):
        results.append(run_test(agent, tc, i))

    # 汇总
    print("\n" + "="*60)
    print("📊 完整测试结果")
    print("="*60)

    total = len(results)
    ai_fix = sum(1 for r in results if r['ai_fix'])
    runs = sum(1 for r in results if r['runs'])
    correct = sum(1 for r in results if r['correct'])

    print(f"\n{'测试用例':<25} {'AI修复':<8} {'能运行':<8} {'输出正确':<8}")
    print("-"*55)
    for r in results:
        f1 = "✅" if r['ai_fix'] else "❌"
        f2 = "✅" if r['runs'] else "❌"
        f3 = "✅" if r['correct'] else "❌"
        print(f"{r['name']:<25} {f1:<8} {f2:<8} {f3:<8}")

    print("-"*55)
    print(f"{'汇总':<25} {ai_fix}/{total:<6} {runs}/{total:<6} {correct}/{total:<6}")

    print(f"\n📈 最终成功率: {correct}/{total} ({100*correct/total:.0f}%)")


if __name__ == "__main__":
    main()
