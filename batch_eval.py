#!/usr/bin/env python3
"""
AI Debug Assistant 批量评估框架
对比测试 Route 模式 vs ReAct 模式
"""

import os
import sys
import json
import time
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

# ============================================================
# 测试用例定义（可扩展）
# ============================================================

TEST_CASES = [
    # NameError 类
    {
        "id": "NE001",
        "category": "NameError",
        "difficulty": "easy",
        "buggy_code": "def greet(name):\n    print(f'Hello, {nane}')\ngreet('World')",
        "error": "NameError: name 'nane' is not defined",
        "expected_output": "Hello, World",
    },
    {
        "id": "NE002",
        "category": "NameError",
        "difficulty": "easy",
        "buggy_code": "total = 0\nfor i in range(5):\n    totla += i\nprint(total)",
        "error": "NameError: name 'totla' is not defined",
        "expected_output": "10",
    },
    {
        "id": "NE003",
        "category": "NameError",
        "difficulty": "medium",
        "buggy_code": "def calc(x):\n    result = x * multiplier\n    return result\nmultiplier = 10\nprint(calc(5))",
        "error": "NameError: name 'multiplier' is not defined",
        "expected_output": "50",
    },

    # TypeError 类
    {
        "id": "TE001",
        "category": "TypeError",
        "difficulty": "easy",
        "buggy_code": "price = 100\nprint('Price: $' + price)",
        "error": "TypeError: can only concatenate str (not \"int\") to str",
        "expected_output": "Price: $100",
    },
    {
        "id": "TE002",
        "category": "TypeError",
        "difficulty": "medium",
        "buggy_code": "def add(a, b):\n    return a + b\nprint(add('hello', 5))",
        "error": "TypeError: can only concatenate str (not \"int\") to str",
        "expected_output": "hello5",
    },
    {
        "id": "TE003",
        "category": "TypeError",
        "difficulty": "medium",
        "buggy_code": "nums = [1, 2, 3]\nprint(sum(nums) / len)",
        "error": "TypeError: unsupported operand type(s) for /: 'int' and 'builtin_function_or_method'",
        "expected_output": "2.0",
    },

    # AttributeError 类
    {
        "id": "AE001",
        "category": "AttributeError",
        "difficulty": "easy",
        "buggy_code": "text = 'hello'\nprint(text.uper())",
        "error": "AttributeError: 'str' object has no attribute 'uper'",
        "expected_output": "HELLO",
    },
    {
        "id": "AE002",
        "category": "AttributeError",
        "difficulty": "easy",
        "buggy_code": "items = [3, 1, 2]\nitems.srot()\nprint(items)",
        "error": "AttributeError: 'list' object has no attribute 'srot'",
        "expected_output": "[1, 2, 3]",
    },

    # IndexError 类
    {
        "id": "IE001",
        "category": "IndexError",
        "difficulty": "easy",
        "buggy_code": "nums = [1, 2, 3]\nprint(nums[3])",
        "error": "IndexError: list index out of range",
        "expected_output": "3",
    },
    {
        "id": "IE002",
        "category": "IndexError",
        "difficulty": "medium",
        "buggy_code": "def get_last(lst):\n    return lst[len(lst)]\nprint(get_last([1,2,3]))",
        "error": "IndexError: list index out of range",
        "expected_output": "3",
    },

    # KeyError 类
    {
        "id": "KE001",
        "category": "KeyError",
        "difficulty": "easy",
        "buggy_code": "user = {'name': 'Alice', 'email': 'a@b.com'}\nprint(user['emial'])",
        "error": "KeyError: 'emial'",
        "expected_output": "a@b.com",
    },

    # RecursionError 类
    {
        "id": "RE001",
        "category": "RecursionError",
        "difficulty": "hard",
        "buggy_code": "def factorial(n):\n    return n * factorial(n-1)\nprint(factorial(5))",
        "error": "RecursionError: maximum recursion depth exceeded",
        "expected_output": "120",
    },

    # ZeroDivisionError 类
    {
        "id": "ZE001",
        "category": "ZeroDivisionError",
        "difficulty": "medium",
        "buggy_code": "def avg(nums):\n    return sum(nums) / len(nums)\nprint(avg([]))",
        "error": "ZeroDivisionError: division by zero",
        "expected_output": None,  # 任何合理处理都可以
    },

    # 逻辑错误类（较难）
    {
        "id": "LE001",
        "category": "LogicError",
        "difficulty": "hard",
        "buggy_code": "def is_even(n):\n    return n % 2 == 1\nprint(is_even(4))",
        "error": "AssertionError: is_even(4) should return True but got False",
        "expected_output": "True",
    },
    {
        "id": "LE002",
        "category": "LogicError",
        "difficulty": "hard",
        "buggy_code": "def reverse_list(lst):\n    return lst.reverse()\nresult = reverse_list([1,2,3])\nprint(result)",
        "error": "Output is None instead of [3, 2, 1]",
        "expected_output": "[3, 2, 1]",
    },
]


# ============================================================
# 评估结果数据类
# ============================================================

@dataclass
class TestResult:
    case_id: str
    category: str
    difficulty: str
    mode: str  # 'route' or 'react'
    ai_fix_success: bool
    code_runs: bool
    output_correct: bool
    response_time: float  # 秒
    error_message: str = ""
    final_code: str = ""
    actual_output: str = ""


# ============================================================
# 代码执行器
# ============================================================

def run_code(code: str, timeout: int = 5) -> Dict[str, Any]:
    """在子进程中安全执行代码"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
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
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'stdout': '', 'stderr': 'Timeout'}
    except Exception as e:
        return {'success': False, 'stdout': '', 'stderr': str(e)}
    finally:
        os.unlink(temp_file)


# ============================================================
# Route 模式测试器
# ============================================================

def test_route_mode(agent, case: Dict) -> TestResult:
    """Route 模式：直接调用 DebugAgent"""
    start_time = time.time()

    try:
        result = agent.debug(
            buggy_code=case['buggy_code'],
            error_traceback=f"Traceback:\n  File \"main.py\", line 1\n{case['error']}",
            error_file="main.py",
            max_retries=2
        )

        response_time = time.time() - start_time
        ai_fix_success = result.get('success', False)
        final_code = result.get('final_code', '')

        # 执行修复后的代码
        if ai_fix_success and final_code:
            run_result = run_code(final_code)
            code_runs = run_result['success']
            actual_output = run_result['stdout']

            # 检查输出
            expected = case.get('expected_output')
            if expected is None:
                output_correct = code_runs  # 只要能运行就算对
            else:
                output_correct = expected in actual_output
        else:
            code_runs = False
            output_correct = False
            actual_output = ""

        return TestResult(
            case_id=case['id'],
            category=case['category'],
            difficulty=case['difficulty'],
            mode='route',
            ai_fix_success=ai_fix_success,
            code_runs=code_runs,
            output_correct=output_correct,
            response_time=response_time,
            final_code=final_code,
            actual_output=actual_output
        )

    except Exception as e:
        return TestResult(
            case_id=case['id'],
            category=case['category'],
            difficulty=case['difficulty'],
            mode='route',
            ai_fix_success=False,
            code_runs=False,
            output_correct=False,
            response_time=time.time() - start_time,
            error_message=str(e)
        )


# ============================================================
# ReAct 模式测试器（多轮思考）
# ============================================================

def test_react_mode(agent, case: Dict) -> TestResult:
    """
    ReAct 模式：多轮 Thought -> Action -> Observation

    这里简化实现：让 LLM 先分析问题，再生成修复
    """
    from src.agent.tools.code_fixer import CodeFixer

    start_time = time.time()

    try:
        fixer = CodeFixer(api_key=os.getenv("DEEPSEEK_API_KEY"))

        # Step 1: Thought - 分析问题
        analysis_prompt = f"""
分析以下 Python 代码错误：

代码：
```python
{case['buggy_code']}
```

错误：{case['error']}

请用以下格式回答：
Thought: [分析错误原因]
Action: [需要做什么修复]
"""

        # Step 2: Action - 生成修复
        fix_result = fixer.fix_code(
            buggy_code=case['buggy_code'],
            error_traceback=case['error'],
            context=None,
            solutions=[]
        )

        response_time = time.time() - start_time
        ai_fix_success = fix_result.get('success', False)
        final_code = fix_result.get('fixed_code', '')

        # 执行验证
        if ai_fix_success and final_code:
            run_result = run_code(final_code)
            code_runs = run_result['success']
            actual_output = run_result['stdout']

            expected = case.get('expected_output')
            if expected is None:
                output_correct = code_runs
            else:
                output_correct = expected in actual_output
        else:
            code_runs = False
            output_correct = False
            actual_output = ""

        return TestResult(
            case_id=case['id'],
            category=case['category'],
            difficulty=case['difficulty'],
            mode='react',
            ai_fix_success=ai_fix_success,
            code_runs=code_runs,
            output_correct=output_correct,
            response_time=response_time,
            final_code=final_code,
            actual_output=actual_output
        )

    except Exception as e:
        return TestResult(
            case_id=case['id'],
            category=case['category'],
            difficulty=case['difficulty'],
            mode='react',
            ai_fix_success=False,
            code_runs=False,
            output_correct=False,
            response_time=time.time() - start_time,
            error_message=str(e)
        )


# ============================================================
# 批量评估
# ============================================================

def run_batch_evaluation(
    test_cases: List[Dict],
    modes: List[str] = ['route', 'react'],
    output_file: str = 'evaluation_results.json'
):
    """运行批量评估"""

    print("\n" + "="*70)
    print("🧪 AI Debug Assistant 批量评估")
    print("="*70)

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 请配置 DEEPSEEK_API_KEY")
        return

    # 初始化 Agent
    from src.agent.debug_agent import DebugAgent
    agent = DebugAgent(api_key=api_key, project_path=str(Path(__file__).parent))

    all_results = []

    for mode in modes:
        print(f"\n{'='*70}")
        print(f"📊 测试模式: {mode.upper()}")
        print('='*70)

        mode_results = []

        for i, case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] {case['id']}: {case['category']} ({case['difficulty']})")

            if mode == 'route':
                result = test_route_mode(agent, case)
            else:
                result = test_react_mode(agent, case)

            # 显示结果
            status = "✅" if result.output_correct else ("⚠️" if result.code_runs else "❌")
            print(f"  {status} AI修复={result.ai_fix_success}, 能运行={result.code_runs}, "
                  f"输出正确={result.output_correct}, 耗时={result.response_time:.2f}s")

            mode_results.append(result)
            all_results.append(result)

        # 模式统计
        print_mode_stats(mode, mode_results)

    # 对比统计
    if len(modes) > 1:
        print_comparison(all_results, modes)

    # 保存结果
    save_results(all_results, output_file)

    return all_results


def print_mode_stats(mode: str, results: List[TestResult]):
    """打印单个模式的统计"""
    total = len(results)
    ai_fix = sum(1 for r in results if r.ai_fix_success)
    runs = sum(1 for r in results if r.code_runs)
    correct = sum(1 for r in results if r.output_correct)
    avg_time = sum(r.response_time for r in results) / total

    print(f"\n📈 {mode.upper()} 模式统计:")
    print(f"  - AI 修复成功: {ai_fix}/{total} ({100*ai_fix/total:.1f}%)")
    print(f"  - 代码能运行: {runs}/{total} ({100*runs/total:.1f}%)")
    print(f"  - 输出正确:   {correct}/{total} ({100*correct/total:.1f}%)")
    print(f"  - 平均耗时:   {avg_time:.2f}s")

    # 按类别统计
    categories = set(r.category for r in results)
    print(f"\n  按错误类别:")
    for cat in sorted(categories):
        cat_results = [r for r in results if r.category == cat]
        cat_correct = sum(1 for r in cat_results if r.output_correct)
        print(f"    {cat}: {cat_correct}/{len(cat_results)}")

    # 按难度统计
    print(f"\n  按难度:")
    for diff in ['easy', 'medium', 'hard']:
        diff_results = [r for r in results if r.difficulty == diff]
        if diff_results:
            diff_correct = sum(1 for r in diff_results if r.output_correct)
            print(f"    {diff}: {diff_correct}/{len(diff_results)}")


def print_comparison(all_results: List[TestResult], modes: List[str]):
    """打印模式对比"""
    print(f"\n{'='*70}")
    print("📊 模式对比")
    print('='*70)

    print(f"\n{'指标':<20}", end="")
    for mode in modes:
        print(f"{mode.upper():<15}", end="")
    print()
    print("-"*50)

    for metric_name, metric_key in [
        ("AI修复成功率", "ai_fix_success"),
        ("代码运行率", "code_runs"),
        ("输出正确率", "output_correct"),
    ]:
        print(f"{metric_name:<20}", end="")
        for mode in modes:
            mode_results = [r for r in all_results if r.mode == mode]
            rate = sum(1 for r in mode_results if getattr(r, metric_key)) / len(mode_results)
            print(f"{rate*100:.1f}%{'':<10}", end="")
        print()

    # 平均响应时间
    print(f"{'平均响应时间':<20}", end="")
    for mode in modes:
        mode_results = [r for r in all_results if r.mode == mode]
        avg_time = sum(r.response_time for r in mode_results) / len(mode_results)
        print(f"{avg_time:.2f}s{'':<10}", end="")
    print()


def save_results(results: List[TestResult], output_file: str):
    """保存结果到 JSON"""
    data = {
        'timestamp': datetime.now().isoformat(),
        'total_cases': len(results),
        'results': [asdict(r) for r in results],
        'summary': {
            'route': {},
            'react': {}
        }
    }

    for mode in ['route', 'react']:
        mode_results = [r for r in results if r.mode == mode]
        if mode_results:
            total = len(mode_results)
            data['summary'][mode] = {
                'total': total,
                'ai_fix_rate': sum(1 for r in mode_results if r.ai_fix_success) / total,
                'run_rate': sum(1 for r in mode_results if r.code_runs) / total,
                'correct_rate': sum(1 for r in mode_results if r.output_correct) / total,
                'avg_time': sum(r.response_time for r in mode_results) / total,
            }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n💾 结果已保存到: {output_file}")


# ============================================================
# 主函数
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='AI Debug Assistant 批量评估')
    parser.add_argument('--mode', choices=['route', 'react', 'both'], default='both',
                        help='测试模式')
    parser.add_argument('--output', default='evaluation_results.json',
                        help='输出文件')
    parser.add_argument('--limit', type=int, default=None,
                        help='限制测试用例数量')

    args = parser.parse_args()

    modes = ['route', 'react'] if args.mode == 'both' else [args.mode]
    cases = TEST_CASES[:args.limit] if args.limit else TEST_CASES

    print(f"测试用例数: {len(cases)}")
    print(f"测试模式: {modes}")

    run_batch_evaluation(cases, modes, args.output)


if __name__ == "__main__":
    main()
