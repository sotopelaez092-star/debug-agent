#!/usr/bin/env python3
"""
简化版测试脚本 - 内嵌测试case
"""
import sys
from pathlib import Path
import time

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agent.react_agent import ReActAgent

# 内嵌测试案例
TEST_CASES = [
    {
        'id': 1,
        'name': 'NameError - 简单拼写错误',
        'buggy_code': 'def greet():\n    print(f"Hello, {nme}")\ngreet()',
        'error_message': "NameError: name 'nme' is not defined"
    },
    {
        'id': 2,
        'name': 'ZeroDivisionError - 空列表',
        'buggy_code': 'def avg(nums):\n    return sum(nums) / len(nums)\nprint(avg([]))',
        'error_message': 'ZeroDivisionError: division by zero'
    },
    {
        'id': 3,
        'name': 'TypeError - 字符串拼接',
        'buggy_code': 'result = "5" + 3\nprint(result)',
        'error_message': "TypeError: can only concatenate str (not 'int') to str"
    },
    {
        'id': 4,
        'name': 'IndexError - 列表越界',
        'buggy_code': 'nums = [1, 2, 3]\nprint(nums[5])',
        'error_message': 'IndexError: list index out of range'
    },
    {
        'id': 5,
        'name': 'KeyError - 字典键不存在',
        'buggy_code': 'user = {"name": "Tom"}\nprint(user["age"])',
        'error_message': "KeyError: 'age'"
    }
]

def test_case(agent, case):
    """测试单个案例"""
    print(f"\n{'='*60}")
    print(f"Case {case['id']}: {case['name']}")
    print(f"{'='*60}")
    
    start = time.time()
    try:
        result = agent.debug(
            buggy_code=case['buggy_code'],
            error_traceback=case['error_message'],
            project_path=None
        )
        elapsed = time.time() - start
        
        success = result['success']
        iterations = result['iterations']
        
        print(f"✅ 成功: {success}")
        print(f"🔄 迭代: {iterations}次")
        print(f"⏱️  耗时: {elapsed:.2f}秒")
        
        return {
            'id': case['id'],
            'success': success,
            'iterations': iterations,
            'time': elapsed
        }
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        return {
            'id': case['id'],
            'success': False,
            'iterations': 0,
            'time': 0,
            'error': str(e)
        }

def main():
    print("🚀 测试优化后的ReAct Agent")
    print(f"📝 测试案例数: {len(TEST_CASES)}")
    
    # 创建agent
    agent = ReActAgent()
    
    # 测试所有case
    results = []
    for case in TEST_CASES:
        result = test_case(agent, case)
        results.append(result)
    
    # 统计
    print("\n" + "="*60)
    print("📊 测试结果")
    print("="*60)
    
    success = sum(1 for r in results if r['success'])
    total = len(results)
    rate = success / total * 100
    
    avg_iter = sum(r['iterations'] for r in results) / total
    avg_time = sum(r['time'] for r in results) / total
    
    print(f"\n成功率: {rate:.1f}% ({success}/{total})")
    print(f"平均迭代: {avg_iter:.2f}次")
    print(f"平均耗时: {avg_time:.2f}秒")
    
    # 失败案例
    failed = [r for r in results if not r['success']]
    if failed:
        print(f"\n失败案例:")
        for r in failed:
            print(f"  - Case {r['id']}")

if __name__ == '__main__':
    main()
