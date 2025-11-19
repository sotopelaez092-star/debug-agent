"""
单文件测试运行脚本

功能：
1. 加载所有测试案例
2. 逐个调用DebugAgent进行测试
3. 记录每个案例的结果（成功/失败、耗时、尝试次数）
4. 保存结果到JSON文件
5. 生成统计报告
"""

import sys
import os
import json
import time
from typing import Dict, Any, List
from datetime import datetime
import logging

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.single_file_test_cases import TEST_CASES, get_test_cases_by_difficulty
from src.agent.debug_agent import DebugAgent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SingleFileTestRunner:
    """单文件测试运行器"""
    
    def __init__(self, output_dir: str = "tests/results"):
        """
        初始化测试运行器
        
        Args:
            output_dir: 结果输出目录
        """
        self.output_dir = output_dir
        self.agent = DebugAgent()
        self.results: List[Dict[str, Any]] = []
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
    
    def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个测试案例
        
        Args:
            test_case: 测试案例字典
            
        Returns:
            测试结果字典
        """
        test_id = test_case['id']
        test_name = test_case['name']
        difficulty = test_case['difficulty']
        
        logger.info(f"开始测试 {test_id} - {test_name} ({difficulty})")
        
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 调用DebugAgent
            result = self.agent.debug(
                buggy_code=test_case['buggy_code'],
                error_traceback=test_case['error_traceback'],
                max_retries=2
            )
            
            # 记录结束时间
            elapsed_time = time.time() - start_time
            
            # 构建测试结果
            test_result = {
                'test_id': test_id,
                'test_name': test_name,
                'difficulty': difficulty,
                'success': result['success'],
                'elapsed_time': round(elapsed_time, 2),
                'attempts': len(result.get('all_attempts', [])),
                'original_error': result.get('original_error', {}),
                'final_code': result.get('fixed_code', ''),
                'explanation': result.get('explanation', ''),
                'execution_result': result.get('execution_result', {}),
                'all_attempts': result.get('all_attempts', []),
                'timestamp': datetime.now().isoformat()
            }
            
            # 记录结果
            if result['success']:
                logger.info(f"✅ {test_id} 成功 ({elapsed_time:.2f}s, {test_result['attempts']}次尝试)")
            else:
                logger.warning(f"❌ {test_id} 失败 ({elapsed_time:.2f}s, {test_result['attempts']}次尝试)")
            
            return test_result
            
        except Exception as e:
            logger.error(f"❌ {test_id} 执行异常: {e}", exc_info=True)
            
            return {
                'test_id': test_id,
                'test_name': test_name,
                'difficulty': difficulty,
                'success': False,
                'error': str(e),
                'elapsed_time': 0,
                'attempts': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def run_all_tests(
        self, 
        filter_difficulty: str = None,
        filter_ids: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        运行所有测试案例
        
        Args:
            filter_difficulty: 可选，只运行指定难度的测试 ('easy', 'medium', 'hard')
            filter_ids: 可选，只运行指定ID的测试
            
        Returns:
            所有测试结果列表
        """
        # 筛选测试案例
        if filter_difficulty:
            test_cases = get_test_cases_by_difficulty(filter_difficulty)
            logger.info(f"只运行 {filter_difficulty} 级别的测试")
        elif filter_ids:
            test_cases = [tc for tc in TEST_CASES if tc['id'] in filter_ids]
            logger.info(f"只运行指定的测试: {filter_ids}")
        else:
            test_cases = TEST_CASES
            logger.info(f"运行全部 {len(test_cases)} 个测试案例")
        
        print("=" * 60)
        print("开始单文件测试")
        print("=" * 60)
        
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] {test_case['id']} - {test_case['name']}")
            print("-" * 60)
            
            result = self.run_single_test(test_case)
            results.append(result)
            
            # 简短显示结果
            if result['success']:
                print(f"✅ 成功 ({result['elapsed_time']}s, {result['attempts']}次尝试)")
            else:
                print(f"❌ 失败 ({result['elapsed_time']}s, {result['attempts']}次尝试)")
        
        self.results = results
        return results
    
    def save_results(self, filename: str = None):
        """
        保存测试结果到JSON文件
        
        Args:
            filename: 可选，自定义文件名
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"single_file_test_results_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"结果已保存到: {filepath}")
        return filepath
    
    def print_summary(self):
        """打印测试摘要"""
        if not self.results:
            print("没有测试结果")
            return
        
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        
        # 总体统计
        total = len(self.results)
        success = sum(1 for r in self.results if r['success'])
        failed = total - success
        success_rate = (success / total * 100) if total > 0 else 0
        
        print(f"\n总案例数: {total}")
        print(f"成功: {success} ({success_rate:.1f}%)")
        print(f"失败: {failed} ({100 - success_rate:.1f}%)")
        
        # 平均统计
        total_time = sum(r.get('elapsed_time', 0) for r in self.results)
        avg_time = total_time / total if total > 0 else 0
        
        attempts_list = [r.get('attempts', 0) for r in self.results if r.get('attempts', 0) > 0]
        avg_attempts = sum(attempts_list) / len(attempts_list) if attempts_list else 0
        
        print(f"\n平均耗时: {avg_time:.2f}s")
        print(f"平均尝试次数: {avg_attempts:.2f}")
        print(f"总耗时: {total_time:.2f}s")
        
        # 按难度统计
        print("\n按难度统计:")
        for difficulty in ['easy', 'medium', 'hard']:
            difficulty_results = [r for r in self.results if r.get('difficulty') == difficulty]
            if difficulty_results:
                d_success = sum(1 for r in difficulty_results if r['success'])
                d_total = len(difficulty_results)
                d_rate = (d_success / d_total * 100) if d_total > 0 else 0
                print(f"  {difficulty.upper()}: {d_success}/{d_total} ({d_rate:.1f}%)")
        
        # 失败案例
        failed_cases = [r for r in self.results if not r['success']]
        if failed_cases:
            print("\n失败案例:")
            for case in failed_cases:
                print(f"  - {case['test_id']}: {case['test_name']}")
                if 'error' in case:
                    print(f"    错误: {case['error']}")
        
        print("=" * 60)
    
    def print_detailed_results(self):
        """打印详细结果"""
        print("\n" + "=" * 60)
        print("详细测试结果")
        print("=" * 60)
        
        for result in self.results:
            print(f"\n{result['test_id']} - {result['test_name']}")
            print("-" * 60)
            print(f"难度: {result['difficulty']}")
            print(f"结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
            print(f"耗时: {result.get('elapsed_time', 0):.2f}s")
            print(f"尝试次数: {result.get('attempts', 0)}")
            
            if result['success']:
                print(f"\n修复说明:")
                print(result.get('explanation', 'N/A'))
            else:
                if 'error' in result:
                    print(f"\n错误信息:")
                    print(result['error'])


def main():
    """主函数"""
    # 创建测试运行器
    runner = SingleFileTestRunner()
    
    # 运行所有测试
    # 如果只想测试某个难度，可以传入 filter_difficulty='easy'
    # 如果只想测试某些ID，可以传入 filter_ids=['TC001', 'TC002']
    results = runner.run_all_tests()
    
    # 保存结果
    filepath = runner.save_results()
    
    # 打印摘要
    runner.print_summary()
    
    # 可选：打印详细结果
    # runner.print_detailed_results()
    
    print(f"\n完整结果已保存到: {filepath}")
    
    # 返回成功率（用于CI/CD）
    total = len(results)
    success = sum(1 for r in results if r['success'])
    success_rate = (success / total * 100) if total > 0 else 0
    
    print(f"\n最终成功率: {success_rate:.1f}%")
    
    # 如果成功率低于50%，退出码为1（失败）
    if success_rate < 50:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()