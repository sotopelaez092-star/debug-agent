#!/usr/bin/env python3
"""
结果分析工具 - 查看失败案例的LLM思考过程

用法:
    python analyze_results.py --case constructed_12       # 查看特定案例
    python analyze_results.py --failures                   # 查看所有失败
    python analyze_results.py --failures --agent router   # 只看Router失败
    python analyze_results.py --compare constructed_12    # 对比Router vs ReAct
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List

# 路径
DETAILED_DIR = "data/evaluation/batch_comparison/detailed_results"
FAILURES_DIR = "data/evaluation/batch_comparison/failures"
SUMMARY_FILE = "data/evaluation/batch_comparison/summary.json"


def load_result(test_id: str) -> Dict:
    """加载特定测试的详细结果"""
    result_file = os.path.join(DETAILED_DIR, f"{test_id}.json")
    
    if not os.path.exists(result_file):
        print(f"❌ 结果文件不存在: {result_file}")
        return None
    
    with open(result_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def print_router_detail(result: Dict):
    """打印Router的详细思考过程"""
    print("=" * 80)
    print(f"🔷 Router: {result['test_id']}")
    print("=" * 80)
    
    print(f"\n📋 基本信息:")
    print(f"  案例名: {result['case_name']}")
    print(f"  错误类型: {result.get('error_type', 'Unknown')}")
    print(f"  成功: {'✅' if result['success'] else '❌'}")
    print(f"  耗时: {result['time']:.1f}秒")
    print(f"  尝试次数: {result.get('attempts', 0)}")
    
    print(f"\n🐛 原始错误:")
    print(result.get('original_error', '无'))
    
    if 'all_attempts' in result and result['all_attempts']:
        print(f"\n🔄 所有尝试:")
        for i, attempt in enumerate(result['all_attempts'], 1):
            print(f"\n--- 第{i}次尝试 ---")
            print(f"修复说明: {attempt.get('explanation', '无')}")
            print(f"\n生成的代码:")
            print("```python")
            print(attempt.get('fixed_code', '无'))
            print("```")
            
            if 'execution_result' in attempt:
                exec_result = attempt['execution_result']
                print(f"\n执行结果: {'✅ 成功' if exec_result.get('success') else '❌ 失败'}")
                if not exec_result.get('success'):
                    print(f"错误输出: {exec_result.get('stderr', '无')}")
    
    if 'analysis' in result:
        print(f"\n🔍 失败分析:")
        analysis = result['analysis']
        print(f"  可能原因: {analysis.get('likely_reason', '未知')}")
        print(f"\n  建议:")
        for suggestion in analysis.get('suggestions', []):
            print(f"    - {suggestion}")


def print_react_detail(result: Dict):
    """打印ReAct的详细思考过程"""
    print("=" * 80)
    print(f"🔶 ReAct: {result['test_id']}")
    print("=" * 80)
    
    print(f"\n📋 基本信息:")
    print(f"  案例名: {result['case_name']}")
    print(f"  错误类型: {result.get('error_type', 'Unknown')}")
    print(f"  成功: {'✅' if result['success'] else '❌'}")
    print(f"  耗时: {result['time']:.1f}秒")
    print(f"  迭代次数: {result.get('iterations', 0)}")
    
    print(f"\n🐛 原始错误:")
    print(result.get('original_error', '无'))
    
    if 'react_history' in result and result['react_history']:
        print(f"\n🧠 完整思考过程:")
        for i, step in enumerate(result['react_history'], 1):
            print(f"\n{'='*60}")
            print(f"第{i}轮:")
            print(f"{'='*60}")
            
            print(f"\n💭 Thought:")
            print(step.get('thought', '无'))
            
            print(f"\n⚡ Action:")
            print(f"  Tool: {step.get('action', '无')}")
            print(f"  Input: {step.get('action_input', '无')}")
            
            print(f"\n👁️ Observation:")
            obs = step.get('observation', '无')
            if len(str(obs)) > 500:
                print(str(obs)[:500] + "... (截断)")
            else:
                print(obs)
    
    if 'analysis' in result:
        print(f"\n🔍 失败分析:")
        analysis = result['analysis']
        print(f"  可能原因: {analysis.get('likely_reason', '未知')}")
        print(f"  最后的思考: {analysis.get('llm_last_thought', '无')}")
        print(f"  最后的行动: {analysis.get('llm_last_action', '无')}")
        print(f"\n  建议:")
        for suggestion in analysis.get('suggestions', []):
            print(f"    - {suggestion}")


def show_case(case_id: str):
    """显示特定案例的所有运行结果"""
    print(f"\n🔍 查找案例: {case_id}")
    
    # 查找所有相关结果
    all_files = os.listdir(DETAILED_DIR)
    related_files = [f for f in all_files if f.startswith(case_id)]
    
    if not related_files:
        print(f"❌ 未找到案例: {case_id}")
        return
    
    print(f"✅ 找到 {len(related_files)} 个结果\n")
    
    # 按agent和run分组
    router_results = []
    react_results = []
    
    for filename in sorted(related_files):
        test_id = filename.replace('.json', '')
        result = load_result(test_id)
        
        if result:
            if result['agent'] == 'router':
                router_results.append(result)
            else:
                react_results.append(result)
    
    # 显示Router结果
    if router_results:
        print("\n" + "🔷" * 40)
        print("ROUTER RESULTS")
        print("🔷" * 40)
        for result in router_results:
            print(f"\n{result['test_id']}: {'✅ 成功' if result['success'] else '❌ 失败'} ({result['time']:.1f}s)")
    
    # 显示ReAct结果
    if react_results:
        print("\n" + "🔶" * 40)
        print("REACT RESULTS")
        print("🔶" * 40)
        for result in react_results:
            print(f"\n{result['test_id']}: {'✅ 成功' if result['success'] else '❌ 失败'} ({result['time']:.1f}s, {result.get('iterations', 0)} iter)")
    
    # 询问是否查看详细
    print("\n" + "=" * 80)
    choice = input("查看哪个结果的详细信息？(输入完整test_id，或按Enter跳过): ").strip()
    
    if choice:
        result = load_result(choice)
        if result:
            if result['agent'] == 'router':
                print_router_detail(result)
            else:
                print_react_detail(result)


def show_all_failures(agent_filter: str = None):
    """显示所有失败案例"""
    # 加载summary
    if not os.path.exists(SUMMARY_FILE):
        print(f"❌ Summary文件不存在: {SUMMARY_FILE}")
        return
    
    with open(SUMMARY_FILE, 'r') as f:
        summary = json.load(f)
    
    failures = summary['failures']
    
    if agent_filter:
        if agent_filter not in failures:
            print(f"❌ 无效的agent: {agent_filter}")
            return
        
        failure_list = failures[agent_filter]
        print(f"\n📋 {agent_filter.upper()} 失败案例 ({len(failure_list)}个):")
    else:
        failure_list = failures['router'] + failures['react']
        print(f"\n📋 所有失败案例 ({len(failure_list)}个):")
        print(f"  Router: {len(failures['router'])} 个")
        print(f"  ReAct: {len(failures['react'])} 个")
    
    # 列出所有失败
    for i, test_id in enumerate(failure_list, 1):
        result = load_result(test_id)
        if result:
            print(f"\n{i}. {test_id}")
            print(f"   案例: {result['case_name']}")
            print(f"   错误类型: {result.get('error_type', 'Unknown')}")
            print(f"   耗时: {result['time']:.1f}秒")
            if 'analysis' in result:
                print(f"   原因: {result['analysis'].get('likely_reason', '未知')}")
    
    # 询问是否查看详细
    print("\n" + "=" * 80)
    choice = input("查看哪个失败案例的详细信息？(输入编号或test_id，或按Enter跳过): ").strip()
    
    if choice:
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(failure_list):
                test_id = failure_list[idx]
            else:
                print("❌ 无效的编号")
                return
        else:
            test_id = choice
        
        result = load_result(test_id)
        if result:
            if result['agent'] == 'router':
                print_router_detail(result)
            else:
                print_react_detail(result)


def compare_case(case_id: str):
    """对比Router vs ReAct在同一案例上的表现"""
    print(f"\n🆚 对比案例: {case_id}")
    
    # 查找所有相关结果
    all_files = os.listdir(DETAILED_DIR)
    related_files = [f for f in all_files if f.startswith(case_id)]
    
    if not related_files:
        print(f"❌ 未找到案例: {case_id}")
        return
    
    # 加载所有结果
    router_results = []
    react_results = []
    
    for filename in sorted(related_files):
        test_id = filename.replace('.json', '')
        result = load_result(test_id)
        
        if result:
            if result['agent'] == 'router':
                router_results.append(result)
            else:
                react_results.append(result)
    
    # 统计对比
    print("\n" + "=" * 80)
    print("📊 对比统计")
    print("=" * 80)
    
    if router_results:
        router_success = sum(1 for r in router_results if r['success'])
        router_avg_time = sum(r['time'] for r in router_results) / len(router_results)
        router_avg_attempts = sum(r.get('attempts', 0) for r in router_results) / len(router_results)
        
        print(f"\n🔷 Router ({len(router_results)} 次运行):")
        print(f"  成功率: {router_success}/{len(router_results)} ({router_success/len(router_results)*100:.1f}%)")
        print(f"  平均耗时: {router_avg_time:.1f}秒")
        print(f"  平均尝试: {router_avg_attempts:.1f}次")
    
    if react_results:
        react_success = sum(1 for r in react_results if r['success'])
        react_avg_time = sum(r['time'] for r in react_results) / len(react_results)
        react_avg_iter = sum(r.get('iterations', 0) for r in react_results) / len(react_results)
        
        print(f"\n🔶 ReAct ({len(react_results)} 次运行):")
        print(f"  成功率: {react_success}/{len(react_results)} ({react_success/len(react_results)*100:.1f}%)")
        print(f"  平均耗时: {react_avg_time:.1f}秒")
        print(f"  平均迭代: {react_avg_iter:.1f}次")
    
    # 询问是否查看详细
    print("\n" + "=" * 80)
    print("可用操作:")
    print("  1. 查看Router第1次运行详细")
    print("  2. 查看ReAct第1次运行详细")
    print("  3. 对比两者的思考过程（并排显示）")
    print("  0. 退出")
    
    choice = input("\n选择操作: ").strip()
    
    if choice == '1' and router_results:
        print_router_detail(router_results[0])
    elif choice == '2' and react_results:
        print_react_detail(react_results[0])
    elif choice == '3':
        print("\n（并排对比功能待实现）")


def main():
    parser = argparse.ArgumentParser(description='分析测试结果')
    parser.add_argument('--case', type=str, help='查看特定案例（如 constructed_12）')
    parser.add_argument('--failures', action='store_true', help='查看所有失败案例')
    parser.add_argument('--agent', type=str, choices=['router', 'react'], help='过滤特定agent')
    parser.add_argument('--compare', type=str, help='对比Router vs ReAct（指定case_id）')
    
    args = parser.parse_args()
    
    if args.case:
        show_case(args.case)
    elif args.failures:
        show_all_failures(args.agent)
    elif args.compare:
        compare_case(args.compare)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()