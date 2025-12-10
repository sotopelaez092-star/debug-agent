"""
测试PerformanceMonitor集成到DebugAgent
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent.debug_agent import DebugAgent
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_single_debug_with_monitor():
    """测试1: 单次Debug + 性能监控"""
    print("\n" + "="*60)
    print("测试1: 单次Debug + 性能监控")
    print("="*60)
    
    # 准备测试数据
    buggy_code = """
def greet(name):
    print(f"Hello, {nme}")  # 拼写错误

greet("Tom")
"""
    
    error_traceback = """
Traceback (most recent call last):
  File "test.py", line 4, in <module>
    greet("Tom")
  File "test.py", line 2, in greet
    print(f"Hello, {nme}")
NameError: name 'nme' is not defined
"""
    
    # 创建Agent（需要API Key）
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 错误：未找到DEEPSEEK_API_KEY环境变量")
        return
    
    agent = DebugAgent(api_key=api_key)
    
    # 执行Debug
    print("\n开始Debug...")
    result = agent.debug(
        buggy_code=buggy_code,
        error_traceback=error_traceback,
        max_retries=2
    )
    
    print("\n" + "="*60)
    print("Debug结果")
    print("="*60)
    print(f"成功: {result['success']}")
    print(f"尝试次数: {result['total_attempts']}")
    
    if result['success']:
        print(f"\n✅ 修复成功！")
        print(f"修复后的代码:\n{result['final_code']}")
    else:
        print(f"\n❌ 修复失败")
    
    # 检查监控数据
    print("\n" + "="*60)
    print("性能监控数据")
    print("="*60)
    
    # 验证monitor有数据
    assert len(agent.monitor.executions) == 1, "应该有1条记录"
    
    execution = agent.monitor.executions[0]
    print(f"\n记录的数据:")
    print(f"  错误类型: {execution['error_type']}")
    print(f"  成功: {execution['success']}")
    print(f"  尝试次数: {execution['attempts']}")
    print(f"  总耗时: {execution['total_time']:.2f}秒")
    print(f"  总Token数: {execution.get('total_tokens', 0)}")
    print(f"  估算成本: ${execution.get('total_tokens', 0) * 0.14 / 1_000_000:.6f}")
    
    # 验证各阶段时间
    if 'stage_times' in execution:
        print(f"\n  各阶段耗时:")
        for stage, time_spent in execution['stage_times'].items():
            print(f"    - {stage}: {time_spent:.2f}秒")
    
    # 生成报告
    print("\n" + "="*60)
    print("统计报告")
    print("="*60)
    
    report = agent.monitor.generate_report()
    summary = report['summary']
    
    print(f"\n总体统计:")
    print(f"  总执行次数: {summary['total_executions']}")
    print(f"  成功率: {summary['success_rate']:.1%}")
    print(f"  平均耗时: {summary['avg_time']}秒")
    print(f"  总Token数: {summary['total_tokens']}")
    print(f"  总成本: ${summary['total_cost']:.6f}")
    print(f"  平均尝试次数: {summary['avg_attempts']}")
    
    # 保存数据
    output_file = "data/monitor_test.json"
    agent.monitor.save_to_file(output_file)
    print(f"\n✅ 监控数据已保存: {output_file}")
    
    print("\n✅ 测试1通过！")


def test_multiple_debug_with_monitor():
    """测试2: 多次Debug + 统计报告"""
    print("\n" + "="*60)
    print("测试2: 多次Debug + 统计报告")
    print("="*60)
    
    # 准备3个测试案例
    test_cases = [
        {
            "name": "NameError - 拼写错误",
            "code": "def greet(name): print(f'Hello, {nme}')\ngreet('Tom')",
            "traceback": "NameError: name 'nme' is not defined"
        },
        {
            "name": "TypeError - 类型错误",
            "code": "result = '5' + 3",
            "traceback": "TypeError: can only concatenate str (not 'int') to str"
        },
        {
            "name": "ZeroDivisionError - 除零",
            "code": "def avg(nums): return sum(nums)/len(nums)\navg([])",
            "traceback": "ZeroDivisionError: division by zero"
        }
    ]
    
    # 创建Agent
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 错误：未找到DEEPSEEK_API_KEY环境变量")
        return
    
    agent = DebugAgent(api_key=api_key)
    
    # 依次执行
    for i, case in enumerate(test_cases, 1):
        print(f"\n[{i}/3] {case['name']}")
        
        try:
            result = agent.debug(
                buggy_code=case['code'],
                error_traceback=case['traceback'],
                max_retries=2
            )
            
            status = "✅ 成功" if result['success'] else "❌ 失败"
            print(f"  结果: {status}, 尝试: {result['total_attempts']}次")
            
        except Exception as e:
            print(f"  ❌ 执行出错: {e}")
    
    # 生成完整报告
    print("\n" + "="*60)
    print("完整统计报告")
    print("="*60)
    
    report = agent.monitor.generate_report()
    summary = report['summary']
    
    print(f"\n总体统计:")
    print(f"  总执行次数: {summary['total_executions']}")
    print(f"  成功: {summary['successful']}")
    print(f"  失败: {summary['failed']}")
    print(f"  成功率: {summary['success_rate']:.1%}")
    print(f"  平均耗时: {summary['avg_time']}秒")
    print(f"  总Token数: {summary['total_tokens']:,}")
    print(f"  总成本: ${summary['total_cost']:.6f}")
    
    print(f"\n按错误类型统计:")
    for error_type, stats in report['by_error_type'].items():
        print(f"  {error_type}:")
        print(f"    数量: {stats['count']}, "
              f"成功率: {stats['success_rate']:.0%}, "
              f"平均耗时: {stats['avg_time']}s")
    
    # 保存数据
    output_file = "data/monitor_multiple_test.json"
    agent.monitor.save_to_file(output_file)
    print(f"\n✅ 监控数据已保存: {output_file}")
    
    print("\n✅ 测试2通过！")


if __name__ == "__main__":
    print("\n" + "🧪 " + "="*58 + " 🧪")
    print("🧪  PerformanceMonitor集成测试")
    print("🧪 " + "="*58 + " 🧪")
    
    try:
        # 测试1: 单次Debug
        test_single_debug_with_monitor()
        
        # 测试2: 多次Debug
        test_multiple_debug_with_monitor()
        
        print("\n" + "🎉 " + "="*58 + " 🎉")
        print("🎉  所有集成测试通过！")
        print("🎉 " + "="*58 + " 🎉\n")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()