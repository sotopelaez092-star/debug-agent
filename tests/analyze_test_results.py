"""
测试结果分析脚本

功能：
1. 读取测试结果JSON文件
2. 生成统计分析
3. 识别失败模式
4. 生成改进建议
"""

import json
import os
from typing import Dict, List, Any
from collections import defaultdict


class TestResultAnalyzer:
    """测试结果分析器"""
    
    def __init__(self, result_file: str):
        """
        初始化分析器
        
        Args:
            result_file: 测试结果JSON文件路径
        """
        self.result_file = result_file
        self.results: List[Dict[str, Any]] = []
        
        # 加载结果
        self._load_results()
    
    def _load_results(self):
        """加载测试结果"""
        if not os.path.exists(self.result_file):
            raise FileNotFoundError(f"结果文件不存在: {self.result_file}")
        
        with open(self.result_file, 'r', encoding='utf-8') as f:
            self.results = json.load(f)
        
        print(f"已加载 {len(self.results)} 个测试结果")
    
    def analyze_by_difficulty(self) -> Dict[str, Dict]:
        """按难度分析成功率"""
        stats = defaultdict(lambda: {'total': 0, 'success': 0, 'failed': 0})
        
        for result in self.results:
            difficulty = result.get('difficulty', 'unknown')
            stats[difficulty]['total'] += 1
            
            if result['success']:
                stats[difficulty]['success'] += 1
            else:
                stats[difficulty]['failed'] += 1
        
        # 计算成功率
        for difficulty, data in stats.items():
            if data['total'] > 0:
                data['success_rate'] = round(data['success'] / data['total'] * 100, 2)
            else:
                data['success_rate'] = 0
        
        return dict(stats)
    
    def analyze_by_error_type(self) -> Dict[str, Dict]:
        """按错误类型分析"""
        stats = defaultdict(lambda: {'total': 0, 'success': 0, 'failed': 0})
        
        for result in self.results:
            # 从test_name中提取错误类型
            test_name = result.get('test_name', '')
            if ' - ' in test_name:
                error_type = test_name.split(' - ')[0]
            else:
                error_type = 'Unknown'
            
            stats[error_type]['total'] += 1
            
            if result['success']:
                stats[error_type]['success'] += 1
            else:
                stats[error_type]['failed'] += 1
        
        # 计算成功率
        for error_type, data in stats.items():
            if data['total'] > 0:
                data['success_rate'] = round(data['success'] / data['total'] * 100, 2)
            else:
                data['success_rate'] = 0
        
        return dict(stats)
    
    def analyze_time_stats(self) -> Dict[str, float]:
        """分析时间统计"""
        times = [r.get('elapsed_time', 0) for r in self.results]
        
        if not times:
            return {}
        
        return {
            'min': round(min(times), 2),
            'max': round(max(times), 2),
            'avg': round(sum(times) / len(times), 2),
            'total': round(sum(times), 2)
        }
    
    def analyze_retry_stats(self) -> Dict[str, Any]:
        """分析重试统计"""
        attempts_list = [r.get('attempts', 0) for r in self.results if r.get('attempts', 0) > 0]
        
        if not attempts_list:
            return {}
        
        # 按尝试次数分布
        distribution = defaultdict(int)
        for attempts in attempts_list:
            distribution[attempts] += 1
        
        # 首次成功率
        first_try_success = sum(1 for r in self.results if r['success'] and r.get('attempts', 0) == 1)
        total_success = sum(1 for r in self.results if r['success'])
        first_try_rate = (first_try_success / total_success * 100) if total_success > 0 else 0
        
        return {
            'avg_attempts': round(sum(attempts_list) / len(attempts_list), 2),
            'max_attempts': max(attempts_list),
            'distribution': dict(distribution),
            'first_try_success_rate': round(first_try_rate, 2)
        }
    
    def get_failed_cases(self) -> List[Dict[str, Any]]:
        """获取所有失败案例"""
        return [r for r in self.results if not r['success']]
    
    def print_full_analysis(self):
        """打印完整分析报告"""
        print("=" * 70)
        print("测试结果详细分析")
        print("=" * 70)
        
        # 总体统计
        total = len(self.results)
        success = sum(1 for r in self.results if r['success'])
        failed = total - success
        success_rate = (success / total * 100) if total > 0 else 0
        
        print(f"\n📊 总体统计:")
        print(f"  总案例数: {total}")
        print(f"  成功: {success} ({success_rate:.1f}%)")
        print(f"  失败: {failed} ({100 - success_rate:.1f}%)")
        
        # 按难度分析
        print(f"\n📈 按难度分析:")
        difficulty_stats = self.analyze_by_difficulty()
        for difficulty in ['easy', 'medium', 'hard']:
            if difficulty in difficulty_stats:
                stats = difficulty_stats[difficulty]
                print(f"  {difficulty.upper()}:")
                print(f"    成功率: {stats['success_rate']}%")
                print(f"    成功/总数: {stats['success']}/{stats['total']}")
        
        # 按错误类型分析
        print(f"\n🔍 按错误类型分析:")
        error_stats = self.analyze_by_error_type()
        for error_type, stats in sorted(error_stats.items(), key=lambda x: x[1]['success_rate']):
            print(f"  {error_type}:")
            print(f"    成功率: {stats['success_rate']}%")
            print(f"    成功/总数: {stats['success']}/{stats['total']}")
        
        # 时间统计
        print(f"\n⏱️  时间统计:")
        time_stats = self.analyze_time_stats()
        if time_stats:
            print(f"  平均耗时: {time_stats['avg']}s")
            print(f"  最短耗时: {time_stats['min']}s")
            print(f"  最长耗时: {time_stats['max']}s")
            print(f"  总耗时: {time_stats['total']}s")
        
        # 重试统计
        print(f"\n🔄 重试统计:")
        retry_stats = self.analyze_retry_stats()
        if retry_stats:
            print(f"  平均尝试次数: {retry_stats['avg_attempts']}")
            print(f"  最大尝试次数: {retry_stats['max_attempts']}")
            print(f"  首次成功率: {retry_stats['first_try_success_rate']}%")
            print(f"  尝试次数分布:")
            for attempts, count in sorted(retry_stats['distribution'].items()):
                print(f"    {attempts}次: {count}个案例")
        
        # 失败案例分析
        failed_cases = self.get_failed_cases()
        if failed_cases:
            print(f"\n❌ 失败案例详情:")
            for case in failed_cases:
                print(f"\n  {case['test_id']} - {case['test_name']}")
                print(f"  难度: {case['difficulty']}")
                print(f"  尝试次数: {case.get('attempts', 0)}")
                
                # 显示失败原因
                if 'error' in case:
                    print(f"  异常: {case['error']}")
                elif 'execution_result' in case:
                    exec_result = case['execution_result']
                    if 'stderr' in exec_result:
                        print(f"  执行错误: {exec_result['stderr'][:100]}...")
        
        # 改进建议
        print(f"\n💡 改进建议:")
        self._print_improvement_suggestions(difficulty_stats, error_stats, failed_cases)
        
        print("=" * 70)
    
    def _print_improvement_suggestions(
        self, 
        difficulty_stats: Dict, 
        error_stats: Dict,
        failed_cases: List
    ):
        """打印改进建议"""
        suggestions = []
        
        # 基于难度的建议
        if 'easy' in difficulty_stats and difficulty_stats['easy']['success_rate'] < 80:
            suggestions.append("简单案例成功率不足80%，需要优化基础错误处理")
        
        if 'medium' in difficulty_stats and difficulty_stats['medium']['success_rate'] < 60:
            suggestions.append("中等案例成功率不足60%，需要改进边界条件处理")
        
        if 'hard' in difficulty_stats and difficulty_stats['hard']['success_rate'] < 40:
            suggestions.append("困难案例成功率较低，考虑添加更多上下文信息")
        
        # 基于错误类型的建议
        for error_type, stats in error_stats.items():
            if stats['success_rate'] < 50:
                suggestions.append(f"{error_type} 成功率偏低，需要针对性优化Prompt或RAG检索")
        
        # 基于失败案例的建议
        if len(failed_cases) > 0:
            # 检查是否有多次尝试都失败的
            max_attempts_failed = [c for c in failed_cases if c.get('attempts', 0) >= 3]
            if max_attempts_failed:
                suggestions.append("有案例尝试3次仍失败，考虑增加最大重试次数或改进重试策略")
        
        # 打印建议
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
        else:
            print("  系统表现良好，暂无改进建议")
    
    def export_summary(self, output_file: str = "test_summary.txt"):
        """导出摘要到文本文件"""
        output_dir = os.path.dirname(self.result_file)
        output_path = os.path.join(output_dir, output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # 重定向打印输出到文件
            import sys
            original_stdout = sys.stdout
            sys.stdout = f
            
            self.print_full_analysis()
            
            sys.stdout = original_stdout
        
        print(f"\n分析报告已导出到: {output_path}")


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python analyze_test_results.py <result_file.json>")
        print("\n或者使用最新的结果文件:")
        
        # 查找最新的结果文件
        result_dir = "tests/results"
        if os.path.exists(result_dir):
            result_files = [f for f in os.listdir(result_dir) if f.endswith('.json')]
            if result_files:
                latest_file = sorted(result_files)[-1]
                latest_path = os.path.join(result_dir, latest_file)
                print(f"使用: {latest_path}")
                
                analyzer = TestResultAnalyzer(latest_path)
                analyzer.print_full_analysis()
                analyzer.export_summary()
            else:
                print("没有找到结果文件")
        else:
            print(f"结果目录不存在: {result_dir}")
        
        sys.exit(1)
    
    result_file = sys.argv[1]
    
    # 创建分析器
    analyzer = TestResultAnalyzer(result_file)
    
    # 打印完整分析
    analyzer.print_full_analysis()
    
    # 导出摘要
    analyzer.export_summary()


if __name__ == "__main__":
    main()