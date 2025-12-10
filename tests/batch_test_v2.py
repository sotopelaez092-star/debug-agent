#!/usr/bin/env python3
"""
Router vs ReAct 批量对比测试 V2
改进：
1. 分离存储结构（小summary + 详细结果分开）
2. 失败案例单独保存，包含完整LLM思考
3. 生成Markdown失败摘要
4. 支持 --fresh-start 清除旧数据
"""

import sys
import os
import json
import time
import argparse
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

# 改进的输出结构
OUTPUT_DIR = "data/evaluation/batch_comparison"
SUMMARY_FILE = f"{OUTPUT_DIR}/summary.json"
FAILURES_MD_FILE = f"{OUTPUT_DIR}/failures_summary.md"
DETAILED_DIR = f"{OUTPUT_DIR}/detailed_results"
FAILURES_DIR = f"{OUTPUT_DIR}/failures"
CHECKPOINT_FILE = f"{OUTPUT_DIR}/checkpoint.json"

# API Key
api_key = os.getenv('DEEPSEEK_API_KEY')
if not api_key:
    print("❌ Error: DEEPSEEK_API_KEY not set")
    sys.exit(1)


# ============== 测试集加载（不变）==============

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


# ============== Checkpoint管理（不变）==============

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


# ============== 改进：保存详细结果 ==============

def save_detailed_result(result: Dict):
    """
    保存详细结果到单独文件
    
    结构：
    - detailed_results/{case_id}_{agent}_{run}.json  # 所有结果
    - failures/{case_id}_{agent}_{run}.json         # 只有失败
    """
    os.makedirs(DETAILED_DIR, exist_ok=True)
    os.makedirs(FAILURES_DIR, exist_ok=True)
    
    # 1. 保存到detailed_results
    detailed_file = os.path.join(DETAILED_DIR, f"{result['test_id']}.json")
    with open(detailed_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # 2. 如果失败，额外保存到failures目录
    if not result['success']:
        failure_file = os.path.join(FAILURES_DIR, f"{result['test_id']}.json")
        
        # 添加额外的调试信息
        failure_detail = {
            **result,
            'analysis': analyze_failure(result)  # 自动分析失败原因
        }
        
        with open(failure_file, 'w', encoding='utf-8') as f:
            json.dump(failure_detail, f, indent=2, ensure_ascii=False)


def analyze_failure(result: Dict) -> Dict:
    """
    自动分析失败原因
    
    返回：
    {
        'likely_reason': '...',
        'llm_last_thought': '...',
        'suggestions': [...]
    }
    """
    analysis = {
        'likely_reason': 'Unknown',
        'llm_last_action': None,
        'suggestions': []
    }
    
    agent_type = result['agent']
    
    if agent_type == 'router':
        # Router失败分析
        if 'error' in result:
            analysis['likely_reason'] = f"Exception: {result['error']}"
        elif 'all_attempts' in result:
            attempts = result['all_attempts']
            if attempts:
                last_attempt = attempts[-1]
                if 'execution_result' in last_attempt:
                    exec_result = last_attempt['execution_result']
                    if not exec_result.get('success'):
                        analysis['likely_reason'] = "Docker执行失败"
                        analysis['llm_last_action'] = last_attempt.get('explanation', '')
                else:
                    analysis['likely_reason'] = "LLM生成修复失败"
                    analysis['llm_last_action'] = last_attempt.get('explanation', '')
        
        analysis['suggestions'] = [
            "检查LLM生成的代码是否有语法错误",
            "检查是否超出最大重试次数",
            "查看all_attempts中的每次尝试"
        ]
    
    elif agent_type == 'react':
        # ReAct失败分析
        if 'error' in result:
            analysis['likely_reason'] = f"Exception: {result['error']}"
        elif 'react_history' in result:
            history = result['react_history']
            if history:
                last_step = history[-1]
                analysis['llm_last_thought'] = last_step.get('thought', '')
                analysis['llm_last_action'] = last_step.get('action', '')
                
                # 判断失败原因
                if result.get('iterations', 0) >= 15:
                    analysis['likely_reason'] = "超出最大迭代次数（15次）"
                elif 'execute_code' not in str(history):
                    analysis['likely_reason'] = "LLM未调用execute_code验证"
                else:
                    analysis['likely_reason'] = "LLM决策错误或生成代码有问题"
        
        analysis['suggestions'] = [
            "检查react_history中的思考过程",
            "查看是否有重复的Tool调用",
            "确认是否调用了execute_code验证"
        ]
    
    return analysis


# ============== 单次测试函数（增强版）==============

def test_with_router_single(case: Dict, run_num: int) -> Dict[str, Any]:
    """用Router Agent测试单个案例（单次运行）"""
    
    case_id = case['id']
    test_id = f"{case_id}_router_run{run_num}"
    
    print(f"  🔷 [{case['name']}] Router Run {run_num}...", end=" ", flush=True)
    
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
        detailed_result = {
            'test_id': test_id,
            'case_id': case_id,
            'case_name': case['name'],
            'agent': 'router',
            'run_num': run_num,
            'source': case['source'],
            'error_type': case.get('error_type', 'Unknown'),
            'success': success,
            'time': elapsed,
            'attempts': len(result.get('all_attempts', [])),
            'fixed_code': result.get('fixed_code', ''),
            'all_attempts': result.get('all_attempts', []),  # 完整的重试历史
            'original_error': error_traceback,
            'timestamp': datetime.now().isoformat()
        }
        
        # 保存详细结果
        save_detailed_result(detailed_result)
        
        return detailed_result
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ ERROR {elapsed:.1f}s")
        
        error_result = {
            'test_id': test_id,
            'case_id': case_id,
            'case_name': case['name'],
            'agent': 'router',
            'run_num': run_num,
            'source': case['source'],
            'error_type': case.get('error_type', 'Unknown'),
            'success': False,
            'time': elapsed,
            'error': str(e),
            'error_detail': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }
        
        # 保存详细结果
        save_detailed_result(error_result)
        
        return error_result


def test_with_react_single(case: Dict, run_num: int) -> Dict[str, Any]:
    """用ReAct Agent测试单个案例（单次运行）"""
    
    case_id = case['id']
    test_id = f"{case_id}_react_run{run_num}"
    
    print(f"  🔶 [{case['name']}] ReAct Run {run_num}...", end=" ", flush=True)
    
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
        detailed_result = {
            'test_id': test_id,
            'case_id': case_id,
            'case_name': case['name'],
            'agent': 'react',
            'run_num': run_num,
            'source': case['source'],
            'error_type': case.get('error_type', 'Unknown'),
            'success': success,
            'time': elapsed,
            'iterations': iterations,
            'fixed_code': result.get('fixed_code', ''),
            'react_history': result.get('history', []),  # 完整的思考历史
            'original_error': error_traceback,
            'timestamp': datetime.now().isoformat()
        }
        
        # 保存详细结果
        save_detailed_result(detailed_result)
        
        return detailed_result
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ ERROR {elapsed:.1f}s")
        
        error_result = {
            'test_id': test_id,
            'case_id': case_id,
            'case_name': case['name'],
            'agent': 'react',
            'run_num': run_num,
            'source': case['source'],
            'error_type': case.get('error_type', 'Unknown'),
            'success': False,
            'time': elapsed,
            'error': str(e),
            'error_detail': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }
        
        # 保存详细结果
        save_detailed_result(error_result)
        
        return error_result


# ============== 主测试流程（改进）==============

def run_batch_test(fresh_start: bool = False):
    """运行批量测试"""
    print("=" * 80)
    print("🥊 Router vs ReAct - Batch Comparison Test V2")
    print("=" * 80)
    
    # 清除旧数据
    if fresh_start:
        print("🗑️  Fresh start - removing old data...")
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
        if os.path.exists(DETAILED_DIR):
            import shutil
            shutil.rmtree(DETAILED_DIR)
        if os.path.exists(FAILURES_DIR):
            import shutil
            shutil.rmtree(FAILURES_DIR)
        print("   ✅ Old data cleared\n")
    
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
        generate_summary(checkpoint, test_cases)
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
                
                # 保存结果（只保存简要信息到checkpoint）
                test_id = result['test_id']
                checkpoint['results'][test_id] = {
                    'test_id': test_id,
                    'success': result['success'],
                    'time': result['time'],
                    'agent': result['agent']
                }
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
    
    # 生成摘要
    generate_summary(checkpoint, test_cases)


# ============== 改进：生成紧凑摘要 ==============

def generate_summary(checkpoint: Dict, test_cases: List[Dict]):
    """
    生成紧凑的摘要报告
    
    输出：
    1. summary.json - 只有统计数据（小文件）
    2. failures_summary.md - 失败案例清单（Markdown）
    """
    print("\n📊 Generating summary...")
    
    # 收集所有详细结果
    all_results = []
    for filename in os.listdir(DETAILED_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(DETAILED_DIR, filename), 'r') as f:
                all_results.append(json.load(f))
    
    # 按agent分组
    router_results = [r for r in all_results if r['agent'] == 'router']
    react_results = [r for r in all_results if r['agent'] == 'react']
    
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
    
    # 失败案例
    router_failures = [r for r in router_results if not r['success']]
    react_failures = [r for r in react_results if not r['success']]
    
    # 组装紧凑摘要
    summary = {
        'timestamp': datetime.now().isoformat(),
        'config': {
            'num_runs': NUM_RUNS,
            'total_cases': len(test_cases),
            'total_tests': len(all_results)
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
        'failures': {
            'router': [r['test_id'] for r in router_failures],
            'react': [r['test_id'] for r in react_failures]
        },
        'failure_by_error_type': analyze_failures_by_error_type(all_results)
    }
    
    # 保存紧凑摘要
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Summary saved: {SUMMARY_FILE}")
    
    # 生成Markdown失败报告
    generate_failures_markdown(router_failures, react_failures)
    
    # 打印摘要
    print_summary(summary)


def analyze_failures_by_error_type(results: List[Dict]) -> Dict:
    """按错误类型分析失败案例"""
    failure_by_type = {}
    
    for r in results:
        if not r['success']:
            error_type = r.get('error_type', 'Unknown')
            if error_type not in failure_by_type:
                failure_by_type[error_type] = []
            failure_by_type[error_type].append(r['test_id'])
    
    return failure_by_type


def generate_failures_markdown(router_failures: List[Dict], react_failures: List[Dict]):
    """
    生成Markdown格式的失败案例报告
    
    输出：failures_summary.md
    """
    md_content = f"""# 失败案例分析报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 总体情况

- **Router失败**: {len(router_failures)} 个
- **ReAct失败**: {len(react_failures)} 个
- **ReAct额外失败**: {len(react_failures) - len(router_failures)} 个

---

## 🔷 Router失败案例 ({len(router_failures)}个)

"""
    
    for failure in sorted(router_failures, key=lambda x: x['test_id']):
        md_content += f"""### {failure['test_id']}

- **案例名**: {failure['case_name']}
- **错误类型**: {failure.get('error_type', 'Unknown')}
- **耗时**: {failure['time']:.1f}s
- **尝试次数**: {failure.get('attempts', 0)}
- **失败原因**: {failure.get('analysis', {}).get('likely_reason', '未分析')}

**LLM最后一次尝试**:
```
{failure.get('analysis', {}).get('llm_last_action', '无')}
```

**详细结果**: `detailed_results/{failure['test_id']}.json`

---

"""
    
    md_content += f"""
## 🔶 ReAct失败案例 ({len(react_failures)}个)

"""
    
    for failure in sorted(react_failures, key=lambda x: x['test_id']):
        md_content += f"""### {failure['test_id']}

- **案例名**: {failure['case_name']}
- **错误类型**: {failure.get('error_type', 'Unknown')}
- **耗时**: {failure['time']:.1f}s
- **迭代次数**: {failure.get('iterations', 0)}
- **失败原因**: {failure.get('analysis', {}).get('likely_reason', '未分析')}

**LLM最后的思考**:
```
{failure.get('analysis', {}).get('llm_last_thought', '无')}
```

**LLM最后的行动**:
```
{failure.get('analysis', {}).get('llm_last_action', '无')}
```

**详细结果**: `detailed_results/{failure['test_id']}.json`

---

"""
    
    # 保存
    with open(FAILURES_MD_FILE, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"✅ Failures summary saved: {FAILURES_MD_FILE}")


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


def print_summary(summary: Dict):
    """打印测试摘要"""
    print("\n" + "=" * 80)
    print("📊 COMPARISON SUMMARY")
    print("=" * 80)
    
    router = summary['overall']['router']
    react = summary['overall']['react']
    
    print(f"\n✅ SUCCESS RATE:")
    print(f"  Router: {router['success_rate']:.1f}% ({router['success_count']}/{router['total_runs']})")
    print(f"  ReAct:  {react['success_rate']:.1f}% ({react['success_count']}/{react['total_runs']})")
    
    print(f"\n⏱️  TIME:")
    print(f"  Router: avg={router['avg_time']:.1f}s, min={router['min_time']:.1f}s, max={router['max_time']:.1f}s")
    print(f"  ReAct:  avg={react['avg_time']:.1f}s, min={react['min_time']:.1f}s, max={react['max_time']:.1f}s")
    
    # 失败案例
    print(f"\n❌ FAILURES:")
    print(f"  Router: {len(summary['failures']['router'])} cases")
    for test_id in summary['failures']['router']:
        print(f"    - {test_id}")
    
    print(f"  ReAct:  {len(summary['failures']['react'])} cases")
    for test_id in summary['failures']['react']:
        print(f"    - {test_id}")
    
    print(f"\n📝 详细失败分析请查看: {FAILURES_MD_FILE}")
    print("=" * 80)


# ============== 主入口 ==============

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Router vs ReAct 批量对比测试')
    parser.add_argument('--fresh-start', action='store_true', help='清除旧数据，重新开始')
    args = parser.parse_args()
    
    try:
        run_batch_test(fresh_start=args.fresh_start)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted - progress saved to checkpoint")
        print("    Re-run to continue from where you left off")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        traceback.print_exc()