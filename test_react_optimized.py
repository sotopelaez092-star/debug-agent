#!/usr/bin/env python3
"""
测试优化后的 ReActAgent
验证 LoopDetector, TokenManager 整合是否正常工作
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from src.agent.react_agent import ReActAgent

def test_simple_nameerror():
    """测试简单的 NameError 修复"""
    print("\n" + "=" * 60)
    print("测试 1: 简单 NameError (typo)")
    print("=" * 60)

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 请配置 DEEPSEEK_API_KEY")
        return False

    agent = ReActAgent(api_key=api_key, max_iterations=10)

    buggy_code = """
name = "Alice"
print(f"Hello, {naem}")
"""

    error_traceback = """
Traceback (most recent call last):
  File "main.py", line 2
NameError: name 'naem' is not defined
"""

    start = time.time()
    result = agent.debug(
        buggy_code=buggy_code,
        error_traceback=error_traceback
    )
    elapsed = time.time() - start

    print(f"\n结果:")
    print(f"  成功: {result.get('success')}")
    print(f"  迭代次数: {result.get('iterations')}")
    print(f"  耗时: {elapsed:.2f}s")

    if result.get('loop_detector_stats'):
        stats = result['loop_detector_stats']
        print(f"  循环检测统计: 检查次数={stats.get('total_checks', 0)}")

    if result.get('fixed_code'):
        print(f"\n修复后代码:")
        print("-" * 40)
        print(result['fixed_code'][:200])
        print("-" * 40)

    return result.get('success', False)


def test_typeerror():
    """测试 TypeError 修复"""
    print("\n" + "=" * 60)
    print("测试 2: TypeError (字符串拼接)")
    print("=" * 60)

    api_key = os.getenv("DEEPSEEK_API_KEY")
    agent = ReActAgent(api_key=api_key, max_iterations=10)

    buggy_code = """
age = 25
print("My age is " + age)
"""

    error_traceback = """
Traceback (most recent call last):
  File "main.py", line 2
TypeError: can only concatenate str (not "int") to str
"""

    start = time.time()
    result = agent.debug(
        buggy_code=buggy_code,
        error_traceback=error_traceback
    )
    elapsed = time.time() - start

    print(f"\n结果:")
    print(f"  成功: {result.get('success')}")
    print(f"  迭代次数: {result.get('iterations')}")
    print(f"  耗时: {elapsed:.2f}s")

    return result.get('success', False)


def test_indexerror():
    """测试 IndexError 修复"""
    print("\n" + "=" * 60)
    print("测试 3: IndexError (越界)")
    print("=" * 60)

    api_key = os.getenv("DEEPSEEK_API_KEY")
    agent = ReActAgent(api_key=api_key, max_iterations=10)

    buggy_code = """
nums = [1, 2, 3]
print(nums[3])
"""

    error_traceback = """
Traceback (most recent call last):
  File "main.py", line 2
IndexError: list index out of range
"""

    start = time.time()
    result = agent.debug(
        buggy_code=buggy_code,
        error_traceback=error_traceback
    )
    elapsed = time.time() - start

    print(f"\n结果:")
    print(f"  成功: {result.get('success')}")
    print(f"  迭代次数: {result.get('iterations')}")
    print(f"  耗时: {elapsed:.2f}s")

    return result.get('success', False)


def main():
    print("\n" + "=" * 60)
    print("🧪 ReActAgent 优化测试 (LoopDetector + TokenManager)")
    print("=" * 60)

    results = []

    # 测试 1: NameError
    try:
        results.append(("NameError", test_simple_nameerror()))
    except Exception as e:
        print(f"❌ 测试 1 失败: {e}")
        results.append(("NameError", False))

    # 测试 2: TypeError
    try:
        results.append(("TypeError", test_typeerror()))
    except Exception as e:
        print(f"❌ 测试 2 失败: {e}")
        results.append(("TypeError", False))

    # 测试 3: IndexError
    try:
        results.append(("IndexError", test_indexerror()))
    except Exception as e:
        print(f"❌ 测试 3 失败: {e}")
        results.append(("IndexError", False))

    # 汇总
    print("\n" + "=" * 60)
    print("📊 测试汇总")
    print("=" * 60)

    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    for name, ok in results:
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")

    print(f"\n🎯 通过率: {passed}/{total} ({100*passed/total:.0f}%)")
    print("=" * 60)


if __name__ == "__main__":
    main()
