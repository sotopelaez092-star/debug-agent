#!/usr/bin/env python3
"""
Route vs ReAct 模式对比批量测试

功能：
1. 对比两种模式的修复成功率
2. 使用 Docker 或 subprocess 验证代码能否运行
3. 验证输出是否符合预期（不只是能运行）
4. 统计性能指标：时间、迭代次数、LLM调用次数

使用方法：
    python batch_compare_test.py [--mode route|react|both] [--cases N]
"""

import os
import sys
import time
import subprocess
import tempfile
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

# 检查 Docker 是否可用
DOCKER_AVAILABLE = False
try:
    result = subprocess.run(['docker', 'info'], capture_output=True, timeout=5)
    DOCKER_AVAILABLE = result.returncode == 0
except:
    pass


# ============ 测试用例定义 ============
# 每个用例包含：id, 类别, 错误代码, 错误信息, 期望输出（用于验证）
TEST_CASES = [
    # ===== NameError (10个) =====
    {
        "id": "NE01",
        "cat": "NameError",
        "code": 'print(helllo)',
        "error": "NameError: name 'helllo' is not defined",
        "expect": "hello",  # 应该打印 hello
        "description": "变量名拼写错误"
    },
    {
        "id": "NE02",
        "cat": "NameError",
        "code": 'name = "Alice"\nprint(f"Hello, {naem}")',
        "error": "NameError: name 'naem' is not defined",
        "expect": "Alice",
        "description": "f-string 中变量名拼写错误"
    },
    {
        "id": "NE03",
        "cat": "NameError",
        "code": 'total = 0\nfor i in range(5):\n    totla += i\nprint(total)',
        "error": "NameError: name 'totla' is not defined",
        "expect": "10",
        "description": "循环中变量名拼写错误"
    },
    {
        "id": "NE04",
        "cat": "NameError",
        "code": 'x = 5\nprint(X)',
        "error": "NameError: name 'X' is not defined",
        "expect": "5",
        "description": "大小写错误"
    },
    {
        "id": "NE05",
        "cat": "NameError",
        "code": 'value = 10\nresult = vlaue * 2\nprint(result)',
        "error": "NameError: name 'vlaue' is not defined",
        "expect": "20",
        "description": "计算中变量名拼写错误"
    },

    # ===== TypeError (5个) =====
    {
        "id": "TE01",
        "cat": "TypeError",
        "code": 'print("Price: $" + 100)',
        "error": 'TypeError: can only concatenate str (not "int") to str',
        "expect": "100",
        "description": "字符串与整数拼接"
    },
    {
        "id": "TE02",
        "cat": "TypeError",
        "code": 'x = "5"\nprint(x + 3)',
        "error": 'TypeError: can only concatenate str (not "int") to str',
        "expect": "8",
        "description": "字符串数字与整数相加"
    },
    {
        "id": "TE03",
        "cat": "TypeError",
        "code": 'age = 25\nprint("Age: " + age)',
        "error": 'TypeError: can only concatenate str (not "int") to str',
        "expect": "25",
        "description": "打印时类型不匹配"
    },

    # ===== AttributeError (4个) =====
    {
        "id": "AE01",
        "cat": "AttributeError",
        "code": 'print("hello".uper())',
        "error": "AttributeError: 'str' object has no attribute 'uper'",
        "expect": "HELLO",
        "description": "方法名拼写错误 upper->uper"
    },
    {
        "id": "AE02",
        "cat": "AttributeError",
        "code": 'nums = [3, 1, 2]\nnums.srot()\nprint(nums)',
        "error": "AttributeError: 'list' object has no attribute 'srot'",
        "expect": "[1, 2, 3]",
        "description": "方法名拼写错误 sort->srot"
    },
    {
        "id": "AE03",
        "cat": "AttributeError",
        "code": 's = "hello"\nprint(s.repalce("l", "x"))',
        "error": "AttributeError: 'str' object has no attribute 'repalce'",
        "expect": "hexxo",
        "description": "方法名拼写错误 replace->repalce"
    },
    {
        "id": "AE04",
        "cat": "AttributeError",
        "code": 'lst = [1, 2, 3]\nlst.apend(4)\nprint(lst)',
        "error": "AttributeError: 'list' object has no attribute 'apend'",
        "expect": "[1, 2, 3, 4]",
        "description": "方法名拼写错误 append->apend"
    },

    # ===== IndexError (3个) =====
    {
        "id": "IE01",
        "cat": "IndexError",
        "code": 'print([1, 2, 3][3])',
        "error": "IndexError: list index out of range",
        "expect": "3",
        "description": "列表索引越界"
    },
    {
        "id": "IE02",
        "cat": "IndexError",
        "code": 's = "abc"\nprint(s[3])',
        "error": "IndexError: string index out of range",
        "expect": "c",
        "description": "字符串索引越界"
    },
    {
        "id": "IE03",
        "cat": "IndexError",
        "code": 'def last(lst):\n    return lst[len(lst)]\nprint(last([1, 2, 3]))',
        "error": "IndexError: list index out of range",
        "expect": "3",
        "description": "获取最后元素时索引错误"
    },

    # ===== KeyError (2个) =====
    {
        "id": "KE01",
        "cat": "KeyError",
        "code": 'user = {"name": "Tom", "email": "t@t.com"}\nprint(user["emial"])',
        "error": "KeyError: 'emial'",
        "expect": "t@t.com",
        "description": "字典键名拼写错误"
    },
    {
        "id": "KE02",
        "cat": "KeyError",
        "code": 'config = {"host": "localhost", "port": 8080}\nprint(config["prot"])',
        "error": "KeyError: 'prot'",
        "expect": "8080",
        "description": "字典键名拼写错误"
    },

    # ===== RecursionError (1个) =====
    {
        "id": "RE01",
        "cat": "RecursionError",
        "code": 'def factorial(n):\n    return n * factorial(n - 1)\nprint(factorial(5))',
        "error": "RecursionError: maximum recursion depth exceeded",
        "expect": "120",
        "description": "递归缺少终止条件"
    },
]


def run_code_subprocess(code: str, timeout: int = 5) -> Dict:
    """使用 subprocess 执行代码"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        tmp = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'exit_code': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'stdout': '', 'stderr': 'Timeout', 'exit_code': -1}
    except Exception as e:
        return {'success': False, 'stdout': '', 'stderr': str(e), 'exit_code': -1}
    finally:
        os.unlink(tmp)


def run_code_docker(code: str, timeout: int = 10) -> Dict:
    """使用 Docker 执行代码"""
    try:
        from src.agent.tools.docker_executor import DockerExecutor
        executor = DockerExecutor(timeout=timeout)
        return executor.execute(code)
    except Exception as e:
        # Fallback to subprocess
        return run_code_subprocess(code, timeout)


def run_code(code: str, timeout: int = 5) -> Dict:
    """执行代码（自动选择 Docker 或 subprocess）"""
    if DOCKER_AVAILABLE:
        return run_code_docker(code, timeout)
    else:
        return run_code_subprocess(code, timeout)


def test_route_mode(api_key: str, test_case: Dict) -> Dict:
    """使用 Route 模式测试"""
    from src.agent.debug_agent import DebugAgent

    start_time = time.time()

    try:
        agent = DebugAgent(api_key=api_key)

        traceback = f"""Traceback (most recent call last):
  File "main.py", line 1
{test_case['error']}"""

        result = agent.debug(
            buggy_code=test_case['code'],
            error_traceback=traceback,
            max_retries=1
        )

        elapsed = time.time() - start_time

        fixed_code = result.get('final_code', '')
        ai_success = result.get('success', False)
        attempts = result.get('total_attempts', 0)

        # 验证执行
        if ai_success and fixed_code:
            run_result = run_code(fixed_code)
            runs = run_result['success']
            output = run_result['stdout']

            # 检查输出是否符合预期
            expect = test_case.get('expect', '')
            if expect:
                correct = expect in output
            else:
                correct = runs  # 没有期望值时，能运行就算对
        else:
            runs, correct, output = False, False, ''

        return {
            'mode': 'Route',
            'ai_success': ai_success,
            'runs': runs,
            'correct': correct,
            'output': output,
            'time': elapsed,
            'attempts': attempts,
            'fixed_code': fixed_code,
            'loop_stats': result.get('loop_detector_stats', {})
        }

    except Exception as e:
        elapsed = time.time() - start_time
        return {
            'mode': 'Route',
            'ai_success': False,
            'runs': False,
            'correct': False,
            'output': '',
            'time': elapsed,
            'attempts': 0,
            'error': str(e)
        }


def test_react_mode(api_key: str, test_case: Dict) -> Dict:
    """使用 ReAct 模式测试"""
    from src.agent.react_agent import ReActAgent

    start_time = time.time()

    try:
        agent = ReActAgent(api_key=api_key, max_iterations=10)

        traceback = f"""Traceback (most recent call last):
  File "main.py", line 1
{test_case['error']}"""

        result = agent.debug(
            buggy_code=test_case['code'],
            error_traceback=traceback
        )

        elapsed = time.time() - start_time

        fixed_code = result.get('fixed_code', '')
        ai_success = result.get('success', False)
        iterations = result.get('iterations', 0)

        # 验证执行
        if ai_success and fixed_code:
            run_result = run_code(fixed_code)
            runs = run_result['success']
            output = run_result['stdout']

            # 检查输出是否符合预期
            expect = test_case.get('expect', '')
            if expect:
                correct = expect in output
            else:
                correct = runs
        else:
            runs, correct, output = False, False, ''

        return {
            'mode': 'ReAct',
            'ai_success': ai_success,
            'runs': runs,
            'correct': correct,
            'output': output,
            'time': elapsed,
            'iterations': iterations,
            'fixed_code': fixed_code,
            'loop_stats': result.get('loop_detector_stats', {})
        }

    except Exception as e:
        elapsed = time.time() - start_time
        return {
            'mode': 'ReAct',
            'ai_success': False,
            'runs': False,
            'correct': False,
            'output': '',
            'time': elapsed,
            'iterations': 0,
            'error': str(e)
        }


def print_comparison_table(route_results: List[Dict], react_results: List[Dict], test_cases: List[Dict]):
    """打印对比表格"""
    print("\n" + "=" * 100)
    print("📊 详细对比结果")
    print("=" * 100)

    print(f"\n{'ID':<6} {'类别':<15} {'Route':<20} {'ReAct':<20} {'结果对比':<15}")
    print("-" * 100)

    for i, tc in enumerate(test_cases):
        route = route_results[i] if i < len(route_results) else {}
        react = react_results[i] if i < len(react_results) else {}

        route_status = "✅" if route.get('correct') else ("⚠️" if route.get('runs') else "❌")
        react_status = "✅" if react.get('correct') else ("⚠️" if react.get('runs') else "❌")

        route_info = f"{route_status} {route.get('time', 0):.1f}s"
        react_info = f"{react_status} {react.get('time', 0):.1f}s/{react.get('iterations', 0)}it"

        # 对比结果
        if route.get('correct') and react.get('correct'):
            comparison = "两者都对"
        elif route.get('correct'):
            comparison = "Route 胜"
        elif react.get('correct'):
            comparison = "ReAct 胜"
        else:
            comparison = "两者都错"

        print(f"{tc['id']:<6} {tc['cat']:<15} {route_info:<20} {react_info:<20} {comparison:<15}")


def print_summary(route_results: List[Dict], react_results: List[Dict]):
    """打印汇总统计"""
    print("\n" + "=" * 80)
    print("📈 性能汇总")
    print("=" * 80)

    n = len(route_results)

    # Route 统计
    route_correct = sum(1 for r in route_results if r.get('correct'))
    route_runs = sum(1 for r in route_results if r.get('runs'))
    route_time = sum(r.get('time', 0) for r in route_results)

    # ReAct 统计
    react_correct = sum(1 for r in react_results if r.get('correct'))
    react_runs = sum(1 for r in react_results if r.get('runs'))
    react_time = sum(r.get('time', 0) for r in react_results)
    react_iterations = sum(r.get('iterations', 0) for r in react_results)

    print(f"\n{'指标':<20} {'Route 模式':<20} {'ReAct 模式':<20} {'对比':<15}")
    print("-" * 80)

    # 正确率
    route_rate = 100 * route_correct / n if n > 0 else 0
    react_rate = 100 * react_correct / n if n > 0 else 0
    winner = "Route" if route_rate > react_rate else ("ReAct" if react_rate > route_rate else "平手")
    print(f"{'正确率':<20} {route_correct}/{n} ({route_rate:.1f}%){'':>5} {react_correct}/{n} ({react_rate:.1f}%){'':>5} {winner}")

    # 运行率
    route_run_rate = 100 * route_runs / n if n > 0 else 0
    react_run_rate = 100 * react_runs / n if n > 0 else 0
    winner = "Route" if route_run_rate > react_run_rate else ("ReAct" if react_run_rate > route_run_rate else "平手")
    print(f"{'代码可运行率':<20} {route_runs}/{n} ({route_run_rate:.1f}%){'':>5} {react_runs}/{n} ({react_run_rate:.1f}%){'':>5} {winner}")

    # 时间
    route_avg_time = route_time / n if n > 0 else 0
    react_avg_time = react_time / n if n > 0 else 0
    winner = "Route" if route_avg_time < react_avg_time else ("ReAct" if react_avg_time < route_avg_time else "平手")
    print(f"{'平均耗时':<20} {route_avg_time:.1f}s{'':>13} {react_avg_time:.1f}s{'':>13} {winner}")

    # 总时间
    print(f"{'总耗时':<20} {route_time:.1f}s{'':>13} {react_time:.1f}s{'':>13}")

    # ReAct 特有指标
    react_avg_iter = react_iterations / n if n > 0 else 0
    print(f"{'平均迭代次数':<20} N/A{'':>17} {react_avg_iter:.1f}{'':>17}")

    # 按类别统计
    print("\n" + "=" * 80)
    print("📊 按错误类别统计")
    print("=" * 80)

    categories = ['NameError', 'TypeError', 'AttributeError', 'IndexError', 'KeyError', 'RecursionError']

    print(f"\n{'类别':<20} {'Route 正确率':<20} {'ReAct 正确率':<20}")
    print("-" * 60)

    for cat in categories:
        cat_indices = [i for i, tc in enumerate(TEST_CASES[:n]) if tc['cat'] == cat]
        if not cat_indices:
            continue

        route_cat_correct = sum(1 for i in cat_indices if route_results[i].get('correct'))
        react_cat_correct = sum(1 for i in cat_indices if react_results[i].get('correct'))

        total = len(cat_indices)
        route_pct = 100 * route_cat_correct / total
        react_pct = 100 * react_cat_correct / total

        print(f"{cat:<20} {route_cat_correct}/{total} ({route_pct:.0f}%){'':>10} {react_cat_correct}/{total} ({react_pct:.0f}%)")


def main():
    parser = argparse.ArgumentParser(description='Route vs ReAct 模式对比测试')
    parser.add_argument('--mode', choices=['route', 'react', 'both'], default='both',
                        help='测试模式: route, react, 或 both (默认)')
    parser.add_argument('--cases', type=int, default=None,
                        help='测试用例数量 (默认全部)')
    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("🧪 Route vs ReAct 模式对比批量测试")
    print("=" * 80)

    # 检查 API Key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 请配置 DEEPSEEK_API_KEY")
        return

    # 检查执行环境
    print(f"\n执行环境:")
    print(f"  Docker 可用: {'是' if DOCKER_AVAILABLE else '否 (使用 subprocess)'}")
    print(f"  测试模式: {args.mode}")

    # 确定测试用例
    test_cases = TEST_CASES[:args.cases] if args.cases else TEST_CASES
    print(f"  测试用例数: {len(test_cases)}")

    route_results = []
    react_results = []

    # ===== Route 模式测试 =====
    if args.mode in ['route', 'both']:
        print("\n" + "=" * 80)
        print("🔄 Route 模式测试")
        print("=" * 80)

        for i, tc in enumerate(test_cases, 1):
            print(f"\n[{i:02d}/{len(test_cases)}] {tc['id']}: {tc['cat']} - {tc['description']}")

            result = test_route_mode(api_key, tc)
            route_results.append(result)

            status = "✅" if result['correct'] else ("⚠️ 能运行但输出不对" if result['runs'] else "❌")
            print(f"  结果: {status}")
            print(f"  耗时: {result['time']:.1f}s, 尝试次数: {result.get('attempts', 0)}")
            if result.get('output'):
                print(f"  输出: {result['output'][:50]}...")
            if result.get('error'):
                print(f"  错误: {result['error'][:50]}...")

    # ===== ReAct 模式测试 =====
    if args.mode in ['react', 'both']:
        print("\n" + "=" * 80)
        print("🤖 ReAct 模式测试")
        print("=" * 80)

        for i, tc in enumerate(test_cases, 1):
            print(f"\n[{i:02d}/{len(test_cases)}] {tc['id']}: {tc['cat']} - {tc['description']}")

            result = test_react_mode(api_key, tc)
            react_results.append(result)

            status = "✅" if result['correct'] else ("⚠️ 能运行但输出不对" if result['runs'] else "❌")
            print(f"  结果: {status}")
            print(f"  耗时: {result['time']:.1f}s, 迭代: {result.get('iterations', 0)}")
            if result.get('output'):
                print(f"  输出: {result['output'][:50]}...")
            if result.get('error'):
                print(f"  错误: {result['error'][:50]}...")

    # ===== 汇总对比 =====
    if args.mode == 'both' and route_results and react_results:
        print_comparison_table(route_results, react_results, test_cases)
        print_summary(route_results, react_results)
    elif route_results:
        n = len(route_results)
        correct = sum(1 for r in route_results if r['correct'])
        print(f"\n🎯 Route 模式最终成功率: {correct}/{n} ({100*correct/n:.1f}%)")
    elif react_results:
        n = len(react_results)
        correct = sum(1 for r in react_results if r['correct'])
        print(f"\n🎯 ReAct 模式最终成功率: {correct}/{n} ({100*correct/n:.1f}%)")

    # 保存结果
    results_data = {
        'test_cases': len(test_cases),
        'docker_available': DOCKER_AVAILABLE,
        'route_results': route_results,
        'react_results': react_results
    }

    with open('compare_results.json', 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n💾 详细结果已保存到: compare_results.json")
    print("=" * 80)


if __name__ == "__main__":
    main()
