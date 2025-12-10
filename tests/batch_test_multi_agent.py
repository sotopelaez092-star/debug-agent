"""
Multi-Agent系统批量测试脚本

读取week6_test_set.json的30个测试案例
用Multi-Agent系统运行
收集统计数据
"""

import sys
import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agent.multi_agent import debug_code

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_test_cases(file_path: str) -> list:
    """加载测试案例"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'test_cases' in data:
        return data['test_cases']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"不支持的JSON格式: {type(data)}")


def run_single_test(
    case: dict, 
    case_num: int, 
    total: int,
    session_id: str = None
) -> dict:
    """运行单个测试案例"""
    print(f"\n📝 测试案例 {case_num}/{total}: {case['id']}")
    print("=" * 60)
    
    print(f"名称: {case.get('name', 'N/A')}")
    print(f"难度: {case.get('difficulty', 'N/A')}")
    print(f"类别: {case.get('category', 'N/A')}")
    
    error_file = case['error_file']
    buggy_code = case['project_files'][error_file]
    
    error_traceback = f"""Traceback (most recent call last):
  File "{error_file}", line 1, in <module>
{case['error_message']}"""
    
    # ✅ 构建LangSmith标签
    run_name = f"Test_{case['id']:02d}_{case.get('name', 'Unknown')}"
    
    tags = [
        "batch_test",
        f"case_{case['id']}",
        case.get('category', 'unknown'),
        case.get('difficulty', 'unknown'),
        case.get('error_type', 'unknown')
    ]
    
    if session_id:
        tags.append(f"session:{session_id}")
    
    metadata = {
        "case_id": case['id'],
        "case_name": case.get('name'),
        "category": case.get('category'),
        "difficulty": case.get('difficulty'),
        "error_type": case.get('error_type')
    }
    
    start_time = time.time()
    
    try:
        result = debug_code(
            buggy_code=buggy_code,
            error_traceback=error_traceback,
            project_path=None,
            run_name=run_name,
            tags=tags,
            metadata=metadata
        )
        
        elapsed = time.time() - start_time
        
        # ✅ 正确的成功判断：只看Docker执行结果
        test_result = result.get('test_result', {})
        docker_success = test_result.get('success', False) if test_result else False

        # 真正的成功 = Docker执行成功
        success = docker_success

        # 获取错误信息（用于记录）
        error_msg = result.get('error_message', '')
        if not success and test_result:
            # 如果失败，优先记录Docker的stderr
            docker_stderr = test_result.get('stderr', '')
            if docker_stderr:
                error_msg = docker_stderr
        
        return {
            'case_id': case['id'],
            'case_name': case.get('name', f"Case {case['id']}"),
            'success': success,
            'attempts': result.get('attempts', 1),
            'elapsed_time': round(elapsed, 2),
            'fixed_code': result.get('fixed_code', ''),
            'explanation': result.get('explanation', ''),
            'error': error_msg if not success else None,
            
            # ✅ 新增：调试信息
            'docker_success': docker_success,
            'is_finished': result.get('is_finished', False),
            'docker_stdout': test_result.get('stdout', '') if test_result else '',
            'docker_stderr': test_result.get('stderr', '') if test_result else ''
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 测试失败: {str(e)}")
        logger.error(f"测试案例 {case['id']} 失败", exc_info=True)
        
        return {
            'case_id': case['id'],
            'case_name': case.get('name', f"Case {case['id']}"),
            'success': False,
            'attempts': 0,
            'elapsed_time': round(elapsed, 2),
            'fixed_code': '',
            'explanation': '',
            'error': str(e),
            'has_docker_error': False
        }


def calculate_statistics(results: list) -> dict:
    """计算统计数据"""
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful
    
    success_rate = (successful / total * 100) if total > 0 else 0
    
    times = [r['elapsed_time'] for r in results]
    avg_time = sum(times) / len(times) if times else 0
    min_time = min(times) if times else 0
    max_time = max(times) if times else 0
    
    attempts = [r['attempts'] for r in results if r['success']]
    avg_attempts = sum(attempts) / len(attempts) if attempts else 0
    
    first_try_success = sum(1 for r in results if r['success'] and r['attempts'] == 1)
    first_try_rate = (first_try_success / total * 100) if total > 0 else 0
    
    docker_errors = sum(1 for r in results if r.get('has_docker_error', False))
    
    stats = {
        'total_cases': total,
        'successful': successful,
        'failed': failed,
        'success_rate': round(success_rate, 2),
        'first_try_success': first_try_success,
        'first_try_rate': round(first_try_rate, 2),
        'avg_time': round(avg_time, 2),
        'min_time': round(min_time, 2),
        'max_time': round(max_time, 2),
        'avg_attempts': round(avg_attempts, 2),
        'docker_errors': docker_errors
    }
    
    return stats


def print_summary(stats: dict, results: list):
    """打印测试总结"""
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    
    print(f"\n总体统计:")
    print(f"  总案例数: {stats['total_cases']}")
    print(f"  成功: {stats['successful']} ✅")
    print(f"  失败: {stats['failed']} ❌")
    print(f"  成功率: {stats['success_rate']}%")
    print(f"  首次成功: {stats['first_try_success']} ({stats['first_try_rate']}%)")
    
    if stats.get('docker_errors', 0) > 0:
        print(f"  Docker执行错误: {stats['docker_errors']} ⚠️")
    
    print(f"\n性能统计:")
    print(f"  平均耗时: {stats['avg_time']}秒")
    print(f"  最快: {stats['min_time']}秒")
    print(f"  最慢: {stats['max_time']}秒")
    print(f"  平均尝试次数: {stats['avg_attempts']}")
    
    if stats['failed'] > 0:
        print(f"\n❌ 失败案例详情:")
        for r in results:
            if not r['success']:
                error_msg = r.get('error', '未知错误')
                error_short = error_msg[:100] + '...' if len(error_msg) > 100 else error_msg
                print(f"  - 案例 {r['case_id']} ({r['case_name']})")
                print(f"    错误: {error_short}")
                if r.get('has_docker_error'):
                    print(f"    类型: Docker执行错误 ⚠️")


def save_results(results: list, stats: dict, output_file: str):
    """保存结果到JSON文件"""
    output = {
        'timestamp': datetime.now().isoformat(),
        'statistics': stats,
        'results': results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 结果已保存到: {output_file}")


def main():
    """主函数"""
    print("🚀 Multi-Agent批量测试启动")
    print("="*60)
    
    session_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📊 Session ID: {session_id}")
    print(f"🏷️  LangSmith Tags: batch_test, session:{session_id}")
    print("="*60)
    
    test_file = "data/test_cases/week6_test_set.json"
    print(f"📂 加载测试案例: {test_file}")
    
    try:
        test_cases = load_test_cases(test_file)
        print(f"✅ 成功加载 {len(test_cases)} 个测试案例")
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return
    
    results = []
    total = len(test_cases)
    
    start_time = time.time()
    
    for i, case in enumerate(test_cases, 1):
        result = run_single_test(case, i, total, session_id=session_id)
        results.append(result)
        
        if i % 10 == 0:
            output_file = "data/evaluation/multi_agent_batch_results_partial.json"
            stats = calculate_statistics(results)
            stats['session_id'] = session_id
            save_results(results, stats, output_file)
    
    total_time = time.time() - start_time
    
    stats = calculate_statistics(results)
    stats['total_time'] = round(total_time, 2)
    stats['session_id'] = session_id
    
    print_summary(stats, results)
    
    print(f"\n⏱️  总测试时间: {total_time:.2f}秒")
    print(f"📊 Session ID: {session_id}")
    
    output_file = "data/evaluation/multi_agent_batch_results.json"
    save_results(results, stats, output_file)
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60)


if __name__ == "__main__":
    main()