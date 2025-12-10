#!/usr/bin/env python3
"""
AI Debug Assistant 实际 Bug 修复测试集
测试项目能否真正修复各类 Python 错误
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from src.agent.debug_agent import DebugAgent

# 测试用例定义
TEST_CASES = [
    {
        "name": "NameError - 变量拼写错误",
        "buggy_code": """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        totla += num  # 拼写错误: totla -> total
    return total

result = calculate_sum([1, 2, 3, 4, 5])
print(result)
""",
        "error_traceback": """
Traceback (most recent call last):
  File "main.py", line 4, in calculate_sum
    totla += num
NameError: name 'totla' is not defined
""",
        "expected_fix": "total",  # 期望修复后包含这个
    },
    {
        "name": "NameError - 未定义变量",
        "buggy_code": """
def greet(name):
    message = f"Hello, {username}!"  # 应该用 name 而不是 username
    return message

print(greet("Alice"))
""",
        "error_traceback": """
Traceback (most recent call last):
  File "main.py", line 2, in greet
    message = f"Hello, {username}!"
NameError: name 'username' is not defined
""",
        "expected_fix": "name",
    },
    {
        "name": "TypeError - 字符串和整数相加",
        "buggy_code": """
def format_price(price):
    return "Price: $" + price  # 类型错误

print(format_price(99))
""",
        "error_traceback": """
Traceback (most recent call last):
  File "main.py", line 2, in format_price
    return "Price: $" + price
TypeError: can only concatenate str (not "int") to str
""",
        "expected_fix": "str(price)",
    },
    {
        "name": "IndexError - 列表越界",
        "buggy_code": """
def get_last_item(items):
    return items[len(items)]  # 应该是 len(items) - 1

numbers = [1, 2, 3]
print(get_last_item(numbers))
""",
        "error_traceback": """
Traceback (most recent call last):
  File "main.py", line 2, in get_last_item
    return items[len(items)]
IndexError: list index out of range
""",
        "expected_fix": "-1",
    },
    {
        "name": "KeyError - 字典键不存在",
        "buggy_code": """
def get_user_email(user):
    return user['emial']  # 拼写错误: emial -> email

user = {'name': 'Alice', 'email': 'alice@example.com'}
print(get_user_email(user))
""",
        "error_traceback": """
Traceback (most recent call last):
  File "main.py", line 2, in get_user_email
    return user['emial']
KeyError: 'emial'
""",
        "expected_fix": "email",
    },
    {
        "name": "AttributeError - 方法名拼写错误",
        "buggy_code": """
def process_text(text):
    return text.uper()  # 拼写错误: uper -> upper

result = process_text("hello")
print(result)
""",
        "error_traceback": """
Traceback (most recent call last):
  File "main.py", line 2, in process_text
    return text.uper()
AttributeError: 'str' object has no attribute 'uper'
""",
        "expected_fix": "upper",
    },
    {
        "name": "SyntaxError - 缺少冒号",
        "buggy_code": """
def is_positive(n)  # 缺少冒号
    return n > 0

print(is_positive(5))
""",
        "error_traceback": """
  File "main.py", line 1
    def is_positive(n)
                      ^
SyntaxError: expected ':'
""",
        "expected_fix": "def is_positive(n):",
    },
    {
        "name": "ZeroDivisionError - 除零错误",
        "buggy_code": """
def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)  # 空列表时会除零

print(calculate_average([]))
""",
        "error_traceback": """
Traceback (most recent call last):
  File "main.py", line 3, in calculate_average
    return total / len(numbers)
ZeroDivisionError: division by zero
""",
        "expected_fix": "if",  # 期望有条件判断
    },
]


def run_test(agent, test_case, index):
    """运行单个测试用例"""
    print(f"\n{'='*60}")
    print(f"测试 {index}: {test_case['name']}")
    print('='*60)

    print(f"\n📝 错误代码:")
    print(test_case['buggy_code'][:200] + "..." if len(test_case['buggy_code']) > 200 else test_case['buggy_code'])

    print(f"\n❌ 错误信息:")
    print(test_case['error_traceback'].strip()[:150])

    try:
        result = agent.debug(
            buggy_code=test_case['buggy_code'],
            error_traceback=test_case['error_traceback'],
            error_file="main.py",
            max_retries=2
        )

        success = result.get('success', False)
        final_code = result.get('final_code', '')

        # 检查是否包含预期修复
        contains_fix = test_case['expected_fix'].lower() in final_code.lower()

        print(f"\n🔧 修复结果: {'成功' if success else '失败'}")

        if final_code:
            print(f"\n✅ 修复后代码:")
            print(final_code[:300] + "..." if len(final_code) > 300 else final_code)

        # 获取解释
        if result.get('attempts'):
            explanation = result['attempts'][0].get('explanation', '')
            if explanation:
                print(f"\n💡 修复解释:")
                print(explanation[:200] + "..." if len(explanation) > 200 else explanation)

        return {
            'name': test_case['name'],
            'success': success,
            'contains_expected_fix': contains_fix,
            'final_code': final_code
        }

    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        return {
            'name': test_case['name'],
            'success': False,
            'contains_expected_fix': False,
            'error': str(e)
        }


def main():
    print("\n" + "🐛 AI Debug Assistant 实际 Bug 修复测试 ".center(60, "="))

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 错误: 请先配置 DEEPSEEK_API_KEY")
        print("运行: echo 'DEEPSEEK_API_KEY=你的key' > .env")
        return

    print(f"\n✅ API Key 已配置")
    print(f"📊 测试用例数: {len(TEST_CASES)}")

    # 初始化 Agent
    agent = DebugAgent(
        api_key=api_key,
        project_path=str(Path(__file__).parent)
    )

    # 运行测试
    results = []
    for i, test_case in enumerate(TEST_CASES, 1):
        result = run_test(agent, test_case, i)
        results.append(result)

    # 汇总结果
    print("\n" + "="*60)
    print(" 测试结果汇总 ".center(60, "="))
    print("="*60)

    success_count = sum(1 for r in results if r['success'])
    fix_count = sum(1 for r in results if r['contains_expected_fix'])

    print(f"\n{'测试用例':<30} {'修复成功':<10} {'符合预期':<10}")
    print("-"*50)

    for r in results:
        status = "✅" if r['success'] else "❌"
        expected = "✅" if r['contains_expected_fix'] else "⚠️"
        print(f"{r['name']:<30} {status:<10} {expected:<10}")

    print("-"*50)
    print(f"\n📈 总体结果:")
    print(f"   修复成功率: {success_count}/{len(results)} ({100*success_count/len(results):.1f}%)")
    print(f"   符合预期率: {fix_count}/{len(results)} ({100*fix_count/len(results):.1f}%)")

    if success_count == len(results):
        print("\n🎉 完美！所有测试用例都修复成功！")
    elif success_count >= len(results) * 0.7:
        print("\n👍 不错！大部分测试用例修复成功")
    else:
        print("\n🔧 还有改进空间，继续优化吧")


if __name__ == "__main__":
    main()
