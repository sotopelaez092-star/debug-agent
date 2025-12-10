"""
PerformanceMonitor测试脚本
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent.performance_monitor import PerformanceMonitor


def test_basic_functionality():
    """测试1: 基本功能"""
    print("\n" + "="*60)
    print("测试1: 基本功能")
    print("="*60)
    
    # 创建监控器
    monitor = PerformanceMonitor()
    
    # 记录3条数据（2成功，1失败）
    test_data = [
        {
            "error_type": "NameError",
            "success": True,
            "total_time": 7.5,
            "attempts": 1,
            "total_tokens": 1250,
            "prompt_tokens": 800,
            "completion_tokens": 450,
            "llm_calls": 1
        },
        {
            "error_type": "NameError",
            "success": True,
            "total_time": 6.2,
            "attempts": 1,
            "total_tokens": 1100,
            "prompt_tokens": 700,
            "completion_tokens": 400,
            "llm_calls": 1
        },
        {
            "error_type": "ImportError",
            "success": False,
            "total_time": 8.1,
            "attempts": 3,
            "total_tokens": 1400,
            "prompt_tokens": 900,
            "completion_tokens": 500,
            "llm_calls": 3
        }
    ]
    
    for data in test_data:
        monitor.record_execution(data)
    
    print(f"✅ 成功记录 {len(test_data)} 条数据")
    
    # 生成报告
    report = monitor.generate_report()
    
    # 验证总体统计
    summary = report['summary']
    print(f"\n📊 总体统计:")
    print(f"  - 总执行次数: {summary['total_executions']}")
    print(f"  - 成功: {summary['successful']}")
    print(f"  - 失败: {summary['failed']}")
    print(f"  - 成功率: {summary['success_rate']:.1%}")
    print(f"  - 平均耗时: {summary['avg_time']}秒")
    print(f"  - 总Token数: {summary['total_tokens']}")
    print(f"  - 总成本: ${summary['total_cost']:.6f}")
    print(f"  - 平均尝试次数: {summary['avg_attempts']}")
    
    # 断言验证
    assert summary['total_executions'] == 3, "总执行次数错误"
    assert summary['successful'] == 2, "成功次数错误"
    assert summary['failed'] == 1, "失败次数错误"
    assert abs(summary['success_rate'] - 0.667) < 0.01, "成功率错误"
    
    # 验证按错误类型统计
    by_error = report['by_error_type']
    print(f"\n📈 按错误类型统计:")
    for error_type, stats in by_error.items():
        print(f"  {error_type}:")
        print(f"    - 数量: {stats['count']}")
        print(f"    - 成功率: {stats['success_rate']:.1%}")
        print(f"    - 平均耗时: {stats['avg_time']}秒")
        print(f"    - 平均尝试: {stats['avg_attempts']}")
    
    assert by_error['NameError']['success_rate'] == 1.0, "NameError成功率错误"
    assert by_error['ImportError']['success_rate'] == 0.0, "ImportError成功率错误"
    
    print("\n✅ 测试1通过！")


def test_empty_data():
    """测试2: 空数据"""
    print("\n" + "="*60)
    print("测试2: 空数据")
    print("="*60)
    
    monitor = PerformanceMonitor()
    report = monitor.generate_report()
    
    print(f"空数据报告: {report}")
    
    assert "error" in report, "应该返回错误信息"
    assert report['error'] == "没有执行记录", "错误信息不正确"
    
    print("✅ 测试2通过！")


def test_invalid_data():
    """测试3: 无效数据"""
    print("\n" + "="*60)
    print("测试3: 无效数据")
    print("="*60)
    
    monitor = PerformanceMonitor()
    
    # 测试1: None
    try:
        monitor.record_execution(None)
        assert False, "应该抛出ValueError"
    except ValueError as e:
        print(f"✅ 正确拒绝None: {e}")
    
    # 测试2: 缺少必需字段
    try:
        monitor.record_execution({"error_type": "NameError"})
        assert False, "应该抛出ValueError"
    except ValueError as e:
        print(f"✅ 正确拒绝缺少字段: {e}")
    
    # 测试3: 空字典
    try:
        monitor.record_execution({})
        assert False, "应该抛出ValueError"
    except ValueError as e:
        print(f"✅ 正确拒绝空字典: {e}")
    
    print("\n✅ 测试3通过！")


def test_file_operations():
    """测试4: 文件保存和加载"""
    print("\n" + "="*60)
    print("测试4: 文件保存和加载")
    print("="*60)
    
    # 创建临时测试文件路径
    test_file = "data/test_performance.json"
    
    # 创建监控器并记录数据
    monitor1 = PerformanceMonitor()
    monitor1.record_execution({
        "error_type": "NameError",
        "success": True,
        "total_time": 5.0,
        "attempts": 1
    })
    monitor1.record_execution({
        "error_type": "TypeError",
        "success": False,
        "total_time": 7.0,
        "attempts": 2
    })
    
    print(f"记录了 {len(monitor1.executions)} 条数据")
    
    # 保存到文件
    monitor1.save_to_file(test_file)
    print(f"✅ 保存到: {test_file}")
    
    # 验证文件存在
    assert os.path.exists(test_file), "文件未创建"
    
    # 加载到新监控器
    monitor2 = PerformanceMonitor()
    monitor2.load_from_file(test_file)
    print(f"✅ 从文件加载了 {len(monitor2.executions)} 条数据")
    
    # 验证数据一致
    assert len(monitor2.executions) == 2, "加载的数据量不对"
    assert monitor2.executions[0]['error_type'] == "NameError", "数据内容不对"
    assert monitor2.executions[1]['error_type'] == "TypeError", "数据内容不对"
    
    # 生成报告验证
    report = monitor2.generate_report()
    assert report['summary']['total_executions'] == 2, "报告统计不对"
    
    # 清理测试文件
    os.remove(test_file)
    print(f"✅ 清理测试文件: {test_file}")
    
    print("\n✅ 测试4通过！")


def test_cache_mechanism():
    """测试5: 缓存机制"""
    print("\n" + "="*60)
    print("测试5: 缓存机制")
    print("="*60)
    
    monitor = PerformanceMonitor()
    
    # 记录数据
    monitor.record_execution({
        "error_type": "NameError",
        "success": True,
        "total_time": 5.0,
        "attempts": 1
    })
    
    # 第一次生成报告（计算）
    report1 = monitor.generate_report()
    print("✅ 第一次生成报告（计算）")
    
    # 第二次生成报告（应该用缓存）
    report2 = monitor.generate_report()
    print("✅ 第二次生成报告（应该使用缓存）")
    
    # 验证两次结果相同
    assert report1 == report2, "缓存结果不一致"
    
    # 记录新数据（应该清除缓存）
    monitor.record_execution({
        "error_type": "TypeError",
        "success": False,
        "total_time": 7.0,
        "attempts": 2
    })
    
    # 再次生成报告（应该重新计算）
    report3 = monitor.generate_report()
    print("✅ 记录新数据后重新生成报告")
    
    # 验证结果不同
    assert report3['summary']['total_executions'] == 2, "缓存未正确清除"
    
    print("\n✅ 测试5通过！")


def test_real_scenario():
    """测试6: 真实场景模拟"""
    print("\n" + "="*60)
    print("测试6: 真实场景模拟（模拟Router Agent执行）")
    print("="*60)
    
    monitor = PerformanceMonitor()
    
    # 模拟10次Debug执行
    scenarios = [
        {"error_type": "NameError", "success": True, "time": 7.5, "attempts": 1, "tokens": 1250},
        {"error_type": "NameError", "success": True, "time": 6.2, "attempts": 1, "tokens": 1100},
        {"error_type": "ImportError", "success": True, "time": 8.1, "attempts": 1, "tokens": 1400},
        {"error_type": "AttributeError", "success": True, "time": 7.8, "attempts": 1, "tokens": 1300},
        {"error_type": "TypeError", "success": False, "time": 9.5, "attempts": 3, "tokens": 2100},
        {"error_type": "NameError", "success": True, "time": 6.9, "attempts": 1, "tokens": 1150},
        {"error_type": "ValueError", "success": True, "time": 7.2, "attempts": 1, "tokens": 1200},
        {"error_type": "KeyError", "success": True, "time": 6.5, "attempts": 1, "tokens": 1050},
        {"error_type": "IndexError", "success": False, "time": 10.2, "attempts": 3, "tokens": 2300},
        {"error_type": "NameError", "success": True, "time": 7.1, "attempts": 1, "tokens": 1180},
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        data = {
            "error_type": scenario["error_type"],
            "success": scenario["success"],
            "total_time": scenario["time"],
            "attempts": scenario["attempts"],
            "total_tokens": scenario["tokens"],
            "prompt_tokens": int(scenario["tokens"] * 0.64),  # 约64%是prompt
            "completion_tokens": int(scenario["tokens"] * 0.36),  # 约36%是completion
            "llm_calls": scenario["attempts"]
        }
        monitor.record_execution(data)
        print(f"  [{i}/10] {scenario['error_type']}: {'✅ 成功' if scenario['success'] else '❌ 失败'}")
    
    # 生成最终报告
    report = monitor.generate_report()
    
    print("\n" + "="*60)
    print("📊 最终统计报告")
    print("="*60)
    
    summary = report['summary']
    print(f"\n总体统计:")
    print(f"  - 总执行次数: {summary['total_executions']}")
    print(f"  - 成功: {summary['successful']} ({summary['success_rate']:.1%})")
    print(f"  - 失败: {summary['failed']}")
    print(f"  - 平均耗时: {summary['avg_time']}秒")
    print(f"  - 总Token数: {summary['total_tokens']:,}")
    print(f"  - 总成本: ${summary['total_cost']:.6f}")
    print(f"  - 平均尝试次数: {summary['avg_attempts']}")
    
    print(f"\n按错误类型统计:")
    for error_type, stats in sorted(report['by_error_type'].items()):
        print(f"  {error_type}:")
        print(f"    数量: {stats['count']}, "
              f"成功率: {stats['success_rate']:.0%}, "
              f"平均耗时: {stats['avg_time']}s, "
              f"平均尝试: {stats['avg_attempts']}")
    
    # 保存报告
    output_file = "data/test_report.json"
    monitor.save_to_file(output_file)
    print(f"\n✅ 报告已保存: {output_file}")
    
    print("\n✅ 测试6通过！")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🧪 " + "="*58 + " 🧪")
    print("🧪  PerformanceMonitor 完整测试套件")
    print("🧪 " + "="*58 + " 🧪")
    
    try:
        test_basic_functionality()
        test_empty_data()
        test_invalid_data()
        test_file_operations()
        test_cache_mechanism()
        test_real_scenario()
        
        print("\n" + "🎉 " + "="*58 + " 🎉")
        print("🎉  所有测试通过！")
        print("🎉 " + "="*58 + " 🎉\n")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()