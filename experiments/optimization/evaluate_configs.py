"""
评估不同配置的效果
- baseline: temp=0.3, max_iter=10
- lower_temp: temp=0.1, max_iter=10
- more_iters: temp=0.3, max_iter=15
- optimized: temp=0.1, max_iter=15
"""
import json
import sys
from pathlib import Path
import tempfile
import os
import time
from typing import Dict, List
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agent.react_agent import ReActAgent

# 配置
CONFIGS = [
    {
        'name': 'baseline',
        'temperature': 0.3,
        'max_iterations': 10,
        'description': '原始配置'
    },
    {
        'name': 'lower_temp',
        'temperature': 0.1,
        'max_iterations': 10,
        'description': '只降低temperature'
    },
    {
        'name': 'more_iters',
        'temperature': 0.3,
        'max_iterations': 15,
        'description': '只增加max_iterations'
    },
    {
        'name': 'optimized',
        'temperature': 0.1,
        'max_iterations': 15,
        'description': '完全优化'
    }
]

NUM_RUNS = 3  # 每个case运行3次

def load_test_cases():
    """加载测试案例"""
    test_file = project_root / 'data/test_cases/week6_test_set.json'
    with open(test_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['test_cases']

def run_single_test(case: Dict, config: Dict) -> Dict:
    """
    运行单个测试
    
    Returns:
        {
            'case_id': int,
            'success': bool,
            'iterations': int,
            'time': float,
            'error': str (if failed)
        }
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # 写入项目文件
            for filename, content in case['project_files'].items():
                filepath = os.path.join(tmpdir, filename)
                with open(filepath, 'w') as f:
                    f.write(content)
            
            # 创建agent（使用指定配置）
            agent = ReActAgent(
                temperature=config['temperature'],
                max_iterations=config['max_iterations']
            )
            
            # 运行测试
            start_time = time.time()
            result = agent.debug(
                buggy_code=case['project_files'][case['error_file']],
                error_traceback=f"Traceback:\n  File \"{case['error_file']}\"\n{case['error_message']}",
                project_path=tmpdir
            )
            elapsed = time.time() - start_time
            
            return {
                'case_id': case['id'],
                'case_name': case['name'],
                'success': result['success'],
                'iterations': result['iterations'],
                'time': round(elapsed, 2),
                'error': result.get('error', '')
            }
    
    except Exception as e:
        return {
            'case_id': case['id'],
            'case_name': case['name'],
            'success': False,
            'iterations': 0,
            'time': 0,
            'error': str(e)
        }

def evaluate_config(config: Dict, test_cases: List[Dict]) -> List[Dict]:
    """评估一个配置"""
    print(f"\n{'='*70}")
    print(f"配置: {config['name']} - {config['description']}")
    print(f"  temperature: {config['temperature']}")
    print(f"  max_iterations: {config['max_iterations']}")
    print('='*70)
    
    all_results = []
    
    # 运行多轮
    for run in range(1, NUM_RUNS + 1):
        print(f"\n--- 第 {run}/{NUM_RUNS} 轮 ---")
        
        for i, case in enumerate(test_cases, 1):
            case_name_short = case['name'][:40]
            print(f"[{i:2d}/30] Case {case['id']:2d}: {case_name_short}...", end=' ', flush=True)
            
            result = run_single_test(case, config)
            result['run'] = run
            result['config'] = config['name']
            result['timestamp'] = datetime.now().isoformat()
            
            all_results.append(result)
            
            # 显示结果
            status = "✅" if result['success'] else "❌"
            print(f"{status} ({result['iterations']:2d}次, {result['time']:5.1f}s)")
        
        # 本轮统计
        run_results = [r for r in all_results if r['run'] == run]
        success_count = sum(1 for r in run_results if r['success'])
        avg_time = sum(r['time'] for r in run_results) / len(run_results)
        avg_iters = sum(r['iterations'] for r in run_results if r['success']) / max(success_count, 1)
        
        print(f"\n本轮统计:")
        print(f"  成功率: {success_count}/30 = {success_count/30*100:.1f}%")
        print(f"  平均时间: {avg_time:.1f}秒")
        print(f"  平均迭代: {avg_iters:.1f}次")
    
    return all_results

def analyze_results(all_results: List[Dict]) -> Dict:
    """分析结果"""
    analysis = {}
    
    # 按config分组
    by_config = {}
    for result in all_results:
        config_name = result['config']
        if config_name not in by_config:
            by_config[config_name] = []
        by_config[config_name].append(result)
    
    # 分析每个config
    for config_name, results in by_config.items():
        # 按case_id分组
        by_case = {}
        for r in results:
            case_id = r['case_id']
            if case_id not in by_case:
                by_case[case_id] = []
            by_case[case_id].append(r)
        
        # 计算每个case的统计
        case_stats = {}
        for case_id, case_results in by_case.items():
            success_count = sum(1 for r in case_results if r['success'])
            total_runs = len(case_results)
            
            case_stats[case_id] = {
                'success_rate': success_count / total_runs,
                'case_name': case_results[0]['case_name'],
                'avg_iterations': sum(r['iterations'] for r in case_results if r['success']) / max(success_count, 1),
                'avg_time': sum(r['time'] for r in case_results) / total_runs
            }
        
        # 整体统计
        total_success = sum(1 for r in results if r['success'])
        total_tests = len(results)
        
        success_results = [r for r in results if r['success']]
        avg_iterations = sum(r['iterations'] for r in success_results) / len(success_results) if success_results else 0
        avg_time = sum(r['time'] for r in results) / len(results)
        
        # 找出不稳定的case（成功率在0-100%之间）
        unstable_cases = [
            {'id': cid, 'name': stats['case_name'], 'rate': stats['success_rate']}
            for cid, stats in case_stats.items()
            if 0 < stats['success_rate'] < 1.0
        ]
        
        analysis[config_name] = {
            'total_success': total_success,
            'total_tests': total_tests,
            'success_rate': total_success / total_tests,
            'avg_iterations': avg_iterations,
            'avg_time': avg_time,
            'case_stats': case_stats,
            'unstable_cases': unstable_cases
        }
    
    return analysis

def generate_report(configs: List[Dict], analysis: Dict, output_file: Path):
    """生成Markdown报告"""
    lines = []
    
    lines.append("# ReAct Agent 配置优化评估报告")
    lines.append("")
    lines.append(f"**评估时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**测试案例数**: 30")
    lines.append(f"**每案例运行次数**: {NUM_RUNS}")
    lines.append(f"**总测试次数**: {30 * NUM_RUNS * len(configs)}")
    lines.append("")
    
    # 配置说明
    lines.append("## 评估配置")
    lines.append("")
    lines.append("| 配置名称 | Temperature | Max Iterations | 说明 |")
    lines.append("|---------|------------|----------------|------|")
    for cfg in configs:
        lines.append(f"| {cfg['name']} | {cfg['temperature']} | {cfg['max_iterations']} | {cfg['description']} |")
    lines.append("")
    
    # 整体对比
    lines.append("## 整体对比")
    lines.append("")
    lines.append("| 配置 | 成功率 | 平均迭代次数 | 平均时间(s) | 不稳定案例数 |")
    lines.append("|------|--------|-------------|------------|------------|")
    
    for cfg in configs:
        data = analysis[cfg['name']]
        lines.append(
            f"| **{cfg['name']}** | "
            f"**{data['success_rate']*100:.1f}%** ({data['total_success']}/{data['total_tests']}) | "
            f"{data['avg_iterations']:.1f} | "
            f"{data['avg_time']:.1f} | "
            f"{len(data['unstable_cases'])} |"
        )
    lines.append("")
    
    # 优化效果
    baseline = analysis['baseline']
    optimized = analysis['optimized']
    
    lines.append("## 优化效果")
    lines.append("")
    lines.append("### baseline → optimized")
    lines.append("")
    lines.append(f"- **成功率**: {baseline['success_rate']*100:.1f}% → {optimized['success_rate']*100:.1f}% "
                 f"(变化: {(optimized['success_rate'] - baseline['success_rate'])*100:+.1f}%)")
    lines.append(f"- **平均迭代**: {baseline['avg_iterations']:.1f} → {optimized['avg_iterations']:.1f} "
                 f"(变化: {optimized['avg_iterations'] - baseline['avg_iterations']:+.1f})")
    lines.append(f"- **平均时间**: {baseline['avg_time']:.1f}s → {optimized['avg_time']:.1f}s "
                 f"(变化: {optimized['avg_time'] - baseline['avg_time']:+.1f}s)")
    lines.append(f"- **不稳定案例**: {len(baseline['unstable_cases'])} → {len(optimized['unstable_cases'])} "
                 f"(变化: {len(optimized['unstable_cases']) - len(baseline['unstable_cases']):+d})")
    lines.append("")
    
    # 不稳定案例分析
    lines.append("## 不稳定案例分析")
    lines.append("")
    
    for cfg in configs:
        data = analysis[cfg['name']]
        if data['unstable_cases']:
            lines.append(f"### {cfg['name']}")
            lines.append("")
            for case in data['unstable_cases']:
                lines.append(f"- **Case {case['id']}**: {case['name']} - 成功率 {case['rate']*100:.0f}%")
            lines.append("")
        else:
            lines.append(f"### {cfg['name']}")
            lines.append("")
            lines.append("✅ 无不稳定案例（所有案例要么100%成功要么100%失败）")
            lines.append("")
    
    # 写入文件
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\n✅ 报告已保存: {output_file}")
    
    # 打印摘要到控制台
    print("\n" + "="*70)
    print("评估摘要")
    print("="*70)
    print('\n'.join(lines[6:30]))  # 打印配置和对比表格

def main():
    print("="*70)
    print("ReAct Agent 配置优化评估")
    print("="*70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试配置数: {len(CONFIGS)}")
    print(f"测试案例数: 30")
    print(f"每案例运行: {NUM_RUNS}次")
    print(f"预计总测试: {30 * NUM_RUNS * len(CONFIGS)}次")
    print()
    
    # 加载测试案例
    test_cases = load_test_cases()
    print(f"✅ 加载了 {len(test_cases)} 个测试案例")
    
    # 评估每个配置
    all_results = []
    for config in CONFIGS:
        results = evaluate_config(config, test_cases)
        all_results.extend(results)
        
        # 保存中间结果（防止中途中断）
        interim_file = project_root / 'experiments/optimization/interim_results.json'
        interim_file.parent.mkdir(parents=True, exist_ok=True)
        with open(interim_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # 分析结果
    print("\n" + "="*70)
    print("分析结果...")
    print("="*70)
    analysis = analyze_results(all_results)
    
    # 生成报告
    report_file = project_root / 'experiments/optimization/config_optimization_report.md'
    generate_report(CONFIGS, analysis, report_file)
    
    # 保存完整数据
    data_file = project_root / 'experiments/optimization/config_optimization_data.json'
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump({
            'configs': CONFIGS,
            'results': all_results,
            'analysis': {k: {**v, 'case_stats': {}} for k, v in analysis.items()}  # 简化case_stats
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 数据已保存: {data_file}")
    print()
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

if __name__ == '__main__':
    main()