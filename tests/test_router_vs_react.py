#!/usr/bin/env python3
"""
Router vs ReAct 批量对比测试（基于成功的test_router_vs_react.py改进）
- 34个案例（30构造 + 4真实）× 2 Agent × 3次 = 204次测试
- 并行执行（4线程）
- 支持checkpoint恢复
"""

import sys
import os
import json
import time
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.debug_agent import DebugAgent as RouterAgent
from src.agent.react_agent import ReActAgent
from dotenv import load_dotenv

load_dotenv()

# ============== 配置 ==============
NUM_RUNS = 3
MAX_WORKERS = 4
OUTPUT_DIR = "data/evaluation/batch_comparison"
CHECKPOINT_FILE = f"{OUTPUT_DIR}/checkpoint.json"

# API Key
api_key = os.getenv('DEEPSEEK_API_KEY')
if not api_key:
    print("❌ Error: DEEPSEEK_API_KEY not set")
    sys.exit(1)


# ============== 测试集加载 ==============

def load_all_test_cases() -> List[Dict]:
    """加载所有测试案例（构造 + 真实bug）"""
    all_cases = []
    
    # 1. 加载构造案例
    print("📂 Loading constructed test cases...")
    with open('data/test_cases/week6_test_set.json', 'r', encoding='utf-8') as f:
        constructed = json.load(f)['test_cases']
    
    for case in constructed:
        all_cases.append({
            'id': f"constructed_{case['id']}",
            'name': case['name'],
            'source': 'constructed',
            'error_type': case['error_type'],
            'category': case['category'],
            'project_files': case['project_files'],
            'error_file': case['error_file'],
            'error_message': case['error_message']
        })
    
    print(f"   ✅ Loaded {len(constructed)} constructed cases")
    
    # 2. 加载真实bug
    print("📂 Loading BugsinPy test cases...")
    with open('data/BugsInPy-master/test_cases_info.json', 'r', encoding='utf-8') as f:
        real_bugs = json.load(f)
    
    for case in real_bugs:
        all_cases.append({
            'id': case['id'],
            'name': f"Real: {case['id']}",
            'source': 'bugsinpy',
            'project_path': case['project_path'],
            'error_file': case['error_file'],
            'undefined_name': case['undefined_name'],
            'expected_import': case['expected_import']
        })
    
    print(f"   ✅ Loaded {len(real_bugs)} BugsinPy cases")
    print(f"   📊 Total: {len(all_cases)} cases\n")
    
    return all_cases


def prepare_test_input(case: Dict) -> tuple:
    """准备测试输入（统一两种格式）"""
    
    if case['source'] == 'constructed':
        # 构造案例：直接从project_files获取
        buggy_code = list(case['project_files'].values())[0]
        error_traceback = f"""Traceback (most recent call last):
  File "{case['error_file']}", line 1, in <module>
{case['error_message']}
"""
        return buggy_code, error_traceback, None
    
    else:
        # 真实bug：从BugsinPy加载
        base_path = "data/BugsInPy-master"
        project_path = os.path.join(base_path, case['project_path'])
        error_file = case['error_file']
        buggy_file_path = os.path.join(project_path, error_file)
        
        with open(buggy_file_path, 'r') as f:
            buggy_code = f.read()
        
        error_traceback = f"""Traceback (most recent call last):
  File "{error_file}", line 10, in <module>
    some_function()
NameError: name '{case['undefined_name']}' is not defined
"""
        return buggy_code, error_traceback, project_path


# ============== Checkpoint管理 ==============

def load_checkpoint() -> Dict:
    """加载checkpoint"""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {"completed": [], "results": {}}


def save_checkpoint(checkpoint: Dict):
    """保存checkpoint"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


# ============== 单次测试函数（保留原有逻辑）==============

def test_with_router_single(case: Dict, run_num: int) -> Dict[str, Any]:
    """用Router Agent测试单个案例（单次运行）"""
    
    case_id = case['id']
    test_id = f"{case_id}_router_run{run_num}"
    
    print(f"  🔷 {test_id}...", end=" ", flush=True)
    
    start_time = time.time()
    
    try:
        # 准备输入
        buggy_code, error_traceback, project_path = prepare_test_input(case)
        
        # 创建Router Agent
        agent = RouterAgent(
            api_key=api_key,
            project_path=project_path
        )
        
        # 禁用日志输出
        import logging
        logging.getLogger('src.agent').setLevel(logging.WARNING)
        logging.getLogger('src.agent.tools').setLevel(logging.WARNING)
        
        # 执行debug
        result = agent.debug(
            buggy_code=buggy_code,
            error_traceback=error_traceback,
            max_retries=2
        )
        
        elapsed = time.time() - start_time
        success = result.get('success', False)
        
        print(f"{'✅' if success else '❌'} {elapsed:.1f}s")
        
        # 详细记录
        return {
            'test_id': test_id,
            'case_id': case_id,
            'agent': 'router',
            'run_num': run_num,
            'source': case['source'],
            'success': success,
            'time': elapsed,
            'attempts': len(result.get('all_attempts', [])),
            'fixed_code': result.get('fixed_code', ''),
            'all_attempts': result.get('all_attempts', []),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ ERROR {elapsed:.1f}s")
        
        return {
            'test_id': test_id,
            'case_id': case_id,
            'agent': 'router',
            'run_num': run_num,
            'source': case['source'],
            'success': False,
            'time': elapsed,
            'error': str(e),
            'error_detail': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }


def test_with_react_single(case: Dict, run_num: int) -> Dict[str, Any]:
    """用ReAct Agent测试单个案例（单次运行）"""
    
    case_id = case['id']
    test_id = f"{case_id}_react_run{run_num}"
    
    print(f"  🔶 {test_id}...", end=" ", flush=True)
    
    start_time = time.time()
    
    try:
        # 准备输入
        buggy_code, error_traceback, project_path = prepare_test_input(case)
        
        # 创建ReAct Agent
        agent = ReActAgent(
            api_key=api_key,
            max_iterations=15,
            temperature=0.1
        )
        
        # 禁用日志输出
        import logging
        logging.getLogger('src.agent').setLevel(logging.WARNING)
        logging.getLogger('src.agent.tools').setLevel(logging.WARNING)
        
        # 执行debug
        result = agent.debug(
            buggy_code=buggy_code,
            error_traceback=error_traceback,
            project_path=project_path,
            max_iterations=15
        )
        
        elapsed = time.time() - start_time
        success = result.get('success', False)
        iterations = result.get('iterations', 0)
        
        print(f"{'✅' if success else '❌'} {elapsed:.1f}s ({iterations} iter)")
        
        # 详细记录
        return {
            'test_id': test_id,
            'case_id': case_id,
            'agent': 'react',
            'run_num': run_num,
            'source': case['source'],
            'success': success,
            'time': elapsed,
            'iterations': iterations,
            'fixed_code': result.get('fixed_code', ''),
            'react_history': result.get('history', []),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ ERROR {elapsed:.1f}s")
        
        return {
            'test_id': test_id,
            'case_id': case_id,
            'agent': 'react',
            'run_num': run_num,
            'source': case['source'],
            'success': False,
            'time': elapsed,
            'error': str(e),
            'error_detail': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }


# ============== 主测试流程 ==============

def run_batch_test():
    """运行批量测试"""
    print("=" * 80)
    print("🥊 Router vs ReAct - Batch Comparison Test")
    print("=" * 80)
    
    # 加载测试案例
    test_cases = load_all_test_cases()
    
    # 加载checkpoint
    checkpoint = load_checkpoint()
    
    print(f"⚙️  Config: {NUM_RUNS} runs × 2 agents = {len(test_cases) * NUM_RUNS * 2} tests")
    print(f"🚀 Parallel: {MAX_WORKERS} workers")
    print(f"⏱️  Estimated: ~{(len(test_cases) * NUM_RUNS * 2 / MAX_WORKERS * 30 / 60):.0f}min\n")
    
    # 预初始化Embedder
    print("🔧 Pre-initializing Embedder...")
    from src.rag.embedder import get_embedder_instance
    try:
        embedder = get_embedder_instance()
        print(f"✅ Embedder ready (dim={embedder.embedding_dim})\n")
    except Exception as e:
        print(f"❌ Embedder failed: {e}")
        return
    
    # 生成所有测试任务
    all_tasks = []
    for case in test_cases:
        for agent_type in ['router', 'react']:
            for run_num in range(1, NUM_RUNS + 1):
                test_id = f"{case['id']}_{agent_type}_run{run_num}"
                
                # 跳过已完成
                if test_id in checkpoint['completed']:
                    continue
                
                all_tasks.append((case, agent_type, run_num))
    
    total_tests = len(test_cases) * NUM_RUNS * 2
    completed_count = len(checkpoint['completed'])
    
    print(f"📊 Progress: {completed_count}/{total_tests} completed")
    print(f"🔄 Remaining: {len(all_tasks)} tasks\n")
    
    if len(all_tasks) == 0:
        print("✅ All tests already completed!")
        generate_report(checkpoint, test_cases)
        return
    
    # 并行执行
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_task = {}
        for case, agent_type, run_num in all_tasks:
            if agent_type == 'router':
                future = executor.submit(test_with_router_single, case, run_num)
            else:
                future = executor.submit(test_with_react_single, case, run_num)
            
            future_to_task[future] = (case['id'], agent_type, run_num)
        
        # 收集结果
        for future in as_completed(future_to_task):
            case_id, agent_type, run_num = future_to_task[future]
            
            try:
                result = future.result()
                
                # 保存结果
                test_id = result['test_id']
                checkpoint['results'][test_id] = result
                checkpoint['completed'].append(test_id)
                
                # 保存checkpoint
                save_checkpoint(checkpoint)
                
                # 打印进度
                completed_count = len(checkpoint['completed'])
                progress = (completed_count / total_tests) * 100
                
                print(f"[{completed_count}/{total_tests}] {progress:.1f}%")
                
            except Exception as e:
                print(f"❌ Task failed: {case_id}_{agent_type}_run{run_num}: {e}")
    
    elapsed = time.time() - start_time
    
    print(f"\n✅ All tests completed in {elapsed/60:.1f}min")
    print("=" * 80)
    
    # 生成报告
    generate_report(checkpoint, test_cases)


# ============== 报告生成 ==============

def generate_report(checkpoint: Dict, test_cases: List[Dict]):
    """生成详细对比报告"""
    print("\n📊 Generating comparison report...")
    
    results = checkpoint['results']
    
    # 按agent分组
    router_results = [r for r in results.values() if r['agent'] == 'router']
    react_results = [r for r in results.values() if r['agent'] == 'react']
    
    # 基础统计
    router_stats = calculate_stats(router_results)
    react_stats = calculate_stats(react_results)
    
    # 按来源统计
    router_by_source = {
        'constructed': [r for r in router_results if r['source'] == 'constructed'],
        'bugsinpy': [r for r in router_results if r['source'] == 'bugsinpy']
    }
    react_by_source = {
        'constructed': [r for r in react_results if r['source'] == 'constructed'],
        'bugsinpy': [r for r in react_results if r['source'] == 'bugsinpy']
    }
    
    # 组装报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'config': {
            'num_runs': NUM_RUNS,
            'total_cases': len(test_cases),
            'total_tests': len(results)
        },
        'overall': {
            'router': router_stats,
            'react': react_stats
        },
        'by_source': {
            'router': {
                'constructed': calculate_stats(router_by_source['constructed']),
                'bugsinpy': calculate_stats(router_by_source['bugsinpy'])
            },
            'react': {
                'constructed': calculate_stats(react_by_source['constructed']),
                'bugsinpy': calculate_stats(react_by_source['bugsinpy'])
            }
        },
        'detailed_results': results
    }
    
    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_file = os.path.join(OUTPUT_DIR, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Report saved: {report_file}")
    
    # 打印摘要
    print_summary(report)


def calculate_stats(results: List[Dict]) -> Dict:
    """计算统计数据"""
    if not results:
        return {}
    
    successes = [r for r in results if r.get('success')]
    times = [r.get('time', 0) for r in results]
    
    return {
        'total_runs': len(results),
        'success_count': len(successes),
        'success_rate': len(successes) / len(results) * 100,
        'avg_time': sum(times) / len(times),
        'min_time': min(times),
        'max_time': max(times)
    }


def print_summary(report: Dict):
    """打印测试摘要"""
    print("\n" + "=" * 80)
    print("📊 COMPARISON SUMMARY")
    print("=" * 80)
    
    router = report['overall']['router']
    react = report['overall']['react']
    
    print(f"\n✅ SUCCESS RATE:")
    print(f"  Router: {router['success_rate']:.1f}% ({router['success_count']}/{router['total_runs']})")
    print(f"  ReAct:  {react['success_rate']:.1f}% ({react['success_count']}/{react['total_runs']})")
    
    print(f"\n⏱️  TIME:")
    print(f"  Router: avg={router['avg_time']:.1f}s, min={router['min_time']:.1f}s, max={router['max_time']:.1f}s")
    print(f"  ReAct:  avg={react['avg_time']:.1f}s, min={react['min_time']:.1f}s, max={react['max_time']:.1f}s")
    
    # 按来源统计
    print(f"\n📋 BY SOURCE:")
    
    router_const = report['by_source']['router']['constructed']
    react_const = report['by_source']['react']['constructed']
    print(f"  Constructed (30 cases × {NUM_RUNS} runs):")
    print(f"    Router: {router_const['success_rate']:.1f}%")
    print(f"    ReAct:  {react_const['success_rate']:.1f}%")
    
    router_real = report['by_source']['router']['bugsinpy']
    react_real = report['by_source']['react']['bugsinpy']
    print(f"  BugsinPy (4 cases × {NUM_RUNS} runs):")
    print(f"    Router: {router_real['success_rate']:.1f}%")
    print(f"    ReAct:  {react_real['success_rate']:.1f}%")
    
    print("=" * 80)


# ============== 主入口 ==============

if __name__ == "__main__":
    try:
        run_batch_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted - progress saved to checkpoint")
        print("    Re-run to continue from where you left off")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        traceback.print_exc()