"""
ReAct Agent 批量测试脚本
测试所有30个案例，统计结果
"""

import sys
import os
import json
import shutil
import tempfile
import time
import logging
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.react_agent import ReActAgent

# 配置日志（减少输出）
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_project_files(temp_dir: str, project_files: Dict[str, str]) -> None:
    """创建项目文件"""
    for file_path, content in project_files.items():
        full_path = os.path.join(temp_dir, file_path)
        # 创建子目录（如果需要）
        dir_name = os.path.dirname(full_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)


def run_single_test(agent: ReActAgent, case: Dict[str, Any]) -> Dict[str, Any]:
    """运行单个测试案例"""
    case_id = case['id']
    case_name = case['name']
    project_files = case['project_files']
    error_file = case['error_file']
    error_message = case['error_message']
    
    # 创建临时项目目录
    temp_dir = tempfile.mkdtemp(prefix=f"test_case_{case_id}_")
    
    try:
        # 创建项目文件
        create_project_files(temp_dir, project_files)
        
        # 获取错误代码
        buggy_code = project_files[error_file]
        
        # 构建traceback
        error_traceback = f"""
Traceback (most recent call last):
  File "{error_file}", line 1, in <module>
    ...
{error_message}
"""
        
        # 判断是否需要项目路径（跨文件场景）
        is_cross_file = len(project_files) > 1
        project_path = temp_dir if is_cross_file else None
        
        # 运行Agent
        start_time = time.time()
        result = agent.debug(
            buggy_code=buggy_code,
            error_traceback=error_traceback,
            project_path=project_path
        )
        elapsed_time = time.time() - start_time
        
        return {
            'case_id': case_id,
            'case_name': case_name,
            'category': case['category'],
            'error_type': case['error_type'],
            'success': result.get('success', False),
            'iterations': result.get('iterations', 0),
            'time': round(elapsed_time, 2),
            'fixed_code': result.get('fixed_code', ''),
            'error': result.get('error', '')
        }
        
    except Exception as e:
        return {
            'case_id': case_id,
            'case_name': case_name,
            'category': case['category'],
            'error_type': case['error_type'],
            'success': False,
            'iterations': 0,
            'time': 0,
            'fixed_code': '',
            'error': str(e)
        }
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)


def print_results_table(results: List[Dict[str, Any]]) -> None:
    """打印结果表格"""
    print("\n" + "=" * 80)
    print("详细结果")
    print("=" * 80)
    print(f"{'ID':<4} {'名称':<30} {'类别':<8} {'成功':<6} {'迭代':<6} {'耗时':<8}")
    print("-" * 80)
    
    for r in results:
        status = "✅" if r['success'] else "❌"
        name = r['case_name'][:28] + ".." if len(r['case_name']) > 30 else r['case_name']
        print(f"{r['case_id']:<4} {name:<30} {r['category']:<8} {status:<6} {r['iterations']:<6} {r['time']:<8}s")


def print_summary(results: List[Dict[str, Any]]) -> None:
    """打印统计摘要"""
    total = len(results)
    success = sum(1 for r in results if r['success'])
    failed = total - success
    
    avg_iterations = sum(r['iterations'] for r in results) / total if total > 0 else 0
    avg_time = sum(r['time'] for r in results) / total if total > 0 else 0
    
    # 按类别统计
    categories = {}
    for r in results:
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'total': 0, 'success': 0}
        categories[cat]['total'] += 1
        if r['success']:
            categories[cat]['success'] += 1
    
    # 按错误类型统计
    error_types = {}
    for r in results:
        et = r['error_type']
        if et not in error_types:
            error_types[et] = {'total': 0, 'success': 0}
        error_types[et]['total'] += 1
        if r['success']:
            error_types[et]['success'] += 1
    
    print("\n" + "=" * 80)
    print("📊 统计摘要")
    print("=" * 80)
    
    print(f"\n总体结果:")
    print(f"  总案例数: {total}")
    print(f"  成功: {success} ({success/total*100:.1f}%)")
    print(f"  失败: {failed} ({failed/total*100:.1f}%)")
    print(f"  平均迭代次数: {avg_iterations:.1f}")
    print(f"  平均耗时: {avg_time:.1f}s")
    
    print(f"\n按类别统计:")
    for cat, stats in sorted(categories.items()):
        rate = stats['success'] / stats['total'] * 100
        print(f"  {cat}: {stats['success']}/{stats['total']} ({rate:.1f}%)")
    
    print(f"\n按错误类型统计:")
    for et, stats in sorted(error_types.items()):
        rate = stats['success'] / stats['total'] * 100
        print(f"  {et}: {stats['success']}/{stats['total']} ({rate:.1f}%)")
    
    # 打印失败案例
    failed_cases = [r for r in results if not r['success']]
    if failed_cases:
        print(f"\n❌ 失败案例:")
        for r in failed_cases:
            print(f"  - 案例{r['case_id']}: {r['case_name']}")
            if r['error']:
                print(f"    错误: {r['error'][:100]}")


def main():
    print("🚀 ReAct Agent 批量测试")
    print("=" * 80)
    
    # 加载测试案例
    test_file = Path(__file__).parent.parent / "data" / "test_cases" / "week6_test_set.json"
    print(f"加载测试案例: {test_file}")
    
    with open(test_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    test_cases = data['test_cases']
    print(f"共 {len(test_cases)} 个案例")
    
    # 创建Agent（复用同一个实例）
    agent = ReActAgent()
    
    # 运行所有测试
    results = []
    for i, case in enumerate(test_cases):
        print(f"\n[{i+1}/{len(test_cases)}] 案例{case['id']}: {case['name']}")
        result = run_single_test(agent, case)
        results.append(result)
        
        status = "✅" if result['success'] else "❌"
        print(f"  {status} 迭代: {result['iterations']}, 耗时: {result['time']}s")
    
    # 打印详细结果
    print_results_table(results)
    
    # 打印统计摘要
    print_summary(results)
    
    # 保存结果到文件
    output_file = Path(__file__).parent.parent / "data" / "evaluation" / "react_batch_results.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'agent': 'ReActAgent',
            'total_cases': len(results),
            'success_count': sum(1 for r in results if r['success']),
            'results': results
        }, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {output_file}")


if __name__ == "__main__":
    main()