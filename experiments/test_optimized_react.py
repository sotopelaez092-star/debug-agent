#!/usr/bin/env python3
"""
测试优化后的ReAct Agent
"""
import sys
import json
from pathlib import Path
import time

# 添加项目根目录到path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agent.react_agent import ReActAgent

def load_test_cases():
    """加载测试案例"""
    test_file = project_root / "data" / "test_cases" / "week6_test_set.json"
    with open(test_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def evaluate_case(agent, case):
    """评估单个案例"""
    print(f"\n{'='*60}")
    print(f"测试案例 {case['id']}: {case['name']}")
    print(f"{'='*60}")
    
    # 构建错误代码
    if 'project_files' in case:
        # 多文件项目
        main_file = case.get('main_file', 'main.py')
        buggy_code = case['project_files'][main_file]
        
        # 创建临时项目目录
        import tempfile
        import os
        
        temp_dir = tempfile.mkdtemp()
        for filename, content in case['project_files'].items():
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        project_path = temp_dir
    else:
        # 单文件
        buggy_code = case['buggy_code']
        project_path = None
    
    # 执行debug
    start_time = time.time()
    try:
        result = agent.debug(
            buggy_code=buggy_code,
            error_traceback=case['error_message'],
            project_path=project_path
        )
        elapsed = time.time() - start_time
        
        print(f"\n结果:")
        print(f"  成功: {result['success']}")
        print(f"  迭代: {result['iterations']}")
        print(f"  耗时: {elapsed:.2f}秒")
        
        return {
            'case_id': case['id'],
            'name': case['name'],
            'success': result['success'],
            'iterations': result['iterations'],
            'time': elapsed,
            'error': result.get('error', None)
        }
    
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        return {
            'case_id': case['id'],
            'name': case['name'],
            'success': False,
            'iterations': 0,
            'time': 0,
            'error': str(e)
        }
    
    finally:
        # 清理临时目录
        if project_path:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    print("🚀 开始测试优化后的ReAct Agent")
    print("="*60)
    
    # 1. 加载测试案例
    test_cases = load_test_cases()
    print(f"�� 加载了 {len(test_cases)} 个测试案例")
    
    # 2. 创建agent
    agent = ReActAgent()
    
    # 3. 评估所有案例
    results = []
    for case in test_cases:
        result = evaluate_case(agent, case)
        results.append(result)
    
    # 4. 统计结果
    print("\n" + "="*60)
    print("📊 评估结果汇总")
    print("="*60)
    
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    success_rate = success_count / total_count * 100
    
    avg_iterations = sum(r['iterations'] for r in results) / total_count
    avg_time = sum(r['time'] for r in results) / total_count
    
    print(f"\n总体指标:")
    print(f"  成功率: {success_rate:.2f}% ({success_count}/{total_count})")
    print(f"  平均迭代: {avg_iterations:.2f}次")
    print(f"  平均耗时: {avg_time:.2f}秒")
    
    # 5. 失败案例
    failed = [r for r in results if not r['success']]
    if failed:
        print(f"\n失败案例 ({len(failed)}个):")
        for r in failed:
            print(f"  - Case {r['case_id']}: {r['name']}")
            if r['error']:
                print(f"    原因: {r['error']}")
    
    # 6. 保存结果
    output_file = project_root / "experiments" / "optimized_react_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total': total_count,
                'success': success_count,
                'success_rate': success_rate,
                'avg_iterations': avg_iterations,
                'avg_time': avg_time
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 结果已保存到: {output_file}")

if __name__ == '__main__':
    main()
