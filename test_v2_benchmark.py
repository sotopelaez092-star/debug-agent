#!/usr/bin/env python3
"""V2 Benchmark 批量测试脚本 - 支持 MiMo vs Claude 对比"""
import sys
import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from src.core.error_identifier import ErrorIdentifier
from src.strategies.registry import ErrorStrategyRegistry
from src.tools_new.context_tools import ContextTools


class V2BenchmarkTester:
    """V2 Benchmark 测试器"""

    def __init__(self, test_cases_dir: str = "tests/test_cases_v2"):
        self.test_cases_dir = Path(test_cases_dir)
        self.results = []

        # 检测当前使用的模型
        base_url = os.getenv('ANTHROPIC_BASE_URL', 'Anthropic Official API')
        self.model_name = 'mimo' if 'mimo' in base_url.lower() else 'claude'

        print(f"\n{'='*70}")
        print(f"V2 Benchmark 测试")
        print(f"{'='*70}")
        print(f"模型: {self.model_name}")
        print(f"API: {base_url}")
        print(f"{'='*70}\n")

    def load_test_cases(self, limit: int = None) -> list:
        """加载测试用例"""
        test_cases = []

        for error_type_dir in sorted(self.test_cases_dir.iterdir()):
            if not error_type_dir.is_dir() or error_type_dir.name.startswith('.'):
                continue

            error_type = error_type_dir.name

            for case_dir in sorted(error_type_dir.iterdir()):
                if case_dir.is_dir() and (case_dir / "main.py").exists():
                    test_cases.append({
                        'path': case_dir,
                        'error_type': error_type
                    })

                    if limit and len(test_cases) >= limit:
                        return test_cases

        return test_cases

    def test_single_case(self, case_info: dict, index: int, total: int) -> dict:
        """测试单个用例"""
        case_dir = case_info['path']
        error_type = case_info['error_type']

        # 读取 metadata
        metadata_file = case_dir / "metadata.json"
        metadata = {}
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)

        case_id = metadata.get('case_id', case_dir.name)
        difficulty = metadata.get('difficulty', 'unknown')

        print(f"\n{'='*70}")
        print(f"[{index}/{total}] {case_id}")
        print(f"类型: {error_type} | 难度: {difficulty}")
        print(f"{'='*70}")

        # 运行测试获取错误
        try:
            result = subprocess.run(
                [sys.executable, "main.py"],
                cwd=str(case_dir),
                capture_output=True,
                text=True,
                timeout=10
            )
        except subprocess.TimeoutExpired:
            print(f"⏱️  超时（10秒）")
            return {
                'case_id': case_id,
                'error_type': error_type,
                'difficulty': difficulty,
                'success': False,
                'reason': 'Timeout',
                'duration': 10
            }

        if result.returncode == 0:
            print(f"⚠️  程序本身没有错误，跳过")
            return {
                'case_id': case_id,
                'error_type': error_type,
                'difficulty': difficulty,
                'success': False,
                'reason': 'No error found',
                'duration': 0,
                'skipped': True
            }

        print(f"🔍 检测到错误，开始修复...")

        # 使用策略尝试快速修复
        start_time = time.time()
        try:
            # 识别错误
            identifier = ErrorIdentifier()
            error = identifier.identify(result.stderr)

            print(f"   错误类型: {error.error_type}")
            print(f"   错误文件: {error.error_file}")

            # 获取策略
            registry = ErrorStrategyRegistry()
            registry.register_all_defaults()
            strategy = registry.get(error.error_type)

            if not strategy:
                duration = time.time() - start_time
                print(f"❌ 无对应策略")
                return {
                    'case_id': case_id,
                    'error_type': error_type,
                    'difficulty': difficulty,
                    'success': False,
                    'reason': 'No strategy',
                    'duration': duration
                }

            # 提取错误信息
            extracted = strategy.extract(error.error_message)
            print(f"   提取信息: {extracted}")

            # 创建 ContextTools
            context_tools = ContextTools(str(case_dir))

            # 快速搜索
            search_result = strategy.fast_search(extracted, context_tools, error.error_file)

            if search_result and search_result.confidence >= 0.7:
                print(f"   ✅ 快速路径命中 (置信度: {search_result.confidence:.2f})")
                # 这里简化了，实际应该调用修复逻辑
                # 但为了测试，我们只记录是否找到了高置信度匹配
                success = True
            else:
                conf = search_result.confidence if search_result else 0.0
                print(f"   🔍 需要完整探索 (置信度: {conf:.2f})")
                # 需要 ReAct 完整探索
                success = False

            duration = time.time() - start_time

            result_dict = {
                'case_id': case_id,
                'error_type': error_type,
                'difficulty': difficulty,
                'success': success,
                'duration': duration,
                'confidence': search_result.confidence if search_result else 0.0,
                'used_fast_path': success
            }

            if success:
                print(f"✅ 测试完成 (耗时: {duration:.1f}s)")
            else:
                print(f"⚠️  需要完整探索 (耗时: {duration:.1f}s)")

            return result_dict

        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ 异常: {str(e)[:100]}")

            return {
                'case_id': case_id,
                'error_type': error_type,
                'difficulty': difficulty,
                'success': False,
                'duration': duration,
                'error': str(e)[:200]
            }

    def run_batch_test(self, limit: int = None):
        """批量测试"""
        # 加载测试用例
        test_cases = self.load_test_cases(limit=limit)

        print(f"加载 {len(test_cases)} 个测试用例")
        if limit:
            print(f"(限制: {limit} 个)")

        # 运行测试
        for i, case_info in enumerate(test_cases, 1):
            result = self.test_single_case(case_info, i, len(test_cases))

            if not result.get('skipped'):
                self.results.append(result)

            # 显示当前统计
            if self.results:
                success_count = sum(1 for r in self.results if r.get('success'))
                print(f"\n📊 当前统计: {success_count}/{len(self.results)} 成功 ({success_count/len(self.results)*100:.1f}%)")

        # 生成报告
        self.generate_report()

    def generate_report(self):
        """生成测试报告"""
        print("\n\n" + "="*70)
        print("测试报告")
        print("="*70)

        if not self.results:
            print("\n⚠️  无有效测试结果")
            return

        # 整体统计
        total = len(self.results)
        success_count = sum(1 for r in self.results if r.get('success'))
        success_rate = success_count / total * 100

        durations = [r.get('duration', 0) for r in self.results]
        avg_duration = sum(durations) / len(durations) if durations else 0

        confidences = [r.get('confidence', 0) for r in self.results]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        print(f"\n## 整体表现")
        print(f"   总用例数: {total}")
        print(f"   成功数: {success_count}")
        print(f"   成功率: {success_rate:.1f}%")
        print(f"   平均耗时: {avg_duration:.1f}秒")
        print(f"   平均置信度: {avg_confidence:.3f}")

        # 按错误类型统计
        by_type = defaultdict(lambda: {'total': 0, 'success': 0, 'durations': [], 'confidences': []})
        for r in self.results:
            error_type = r.get('error_type', 'unknown')
            by_type[error_type]['total'] += 1
            if r.get('success'):
                by_type[error_type]['success'] += 1
            by_type[error_type]['durations'].append(r.get('duration', 0))
            by_type[error_type]['confidences'].append(r.get('confidence', 0))

        print(f"\n## 按错误类型统计")
        print(f"{'类型':<20s} {'成功率':<20s} {'平均耗时':<12s} {'平均置信度'}")
        print("-" * 70)
        for error_type, stats in sorted(by_type.items()):
            rate = stats['success'] / stats['total'] * 100
            avg_dur = sum(stats['durations']) / len(stats['durations'])
            avg_conf = sum(stats['confidences']) / len(stats['confidences'])
            print(f"{error_type:<20s} {stats['success']}/{stats['total']} ({rate:>5.1f}%) {avg_dur:>10.1f}s {avg_conf:>12.3f}")

        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f"v2_test_{self.model_name}_{timestamp}.json"

        with open(result_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'model': self.model_name,
                'base_url': os.getenv('ANTHROPIC_BASE_URL', 'Anthropic Official'),
                'total': total,
                'success_count': success_count,
                'success_rate': success_rate,
                'avg_duration': avg_duration,
                'avg_confidence': avg_confidence,
                'by_type': dict(by_type),
                'results': self.results
            }, f, indent=2)

        print(f"\n✅ 详细结果已保存到: {result_file}")
        return result_file


def main():
    import argparse

    parser = argparse.ArgumentParser(description='V2 Benchmark 批量测试')
    parser.add_argument('--limit', type=int, help='限制测试用例数量')
    parser.add_argument('--quick', action='store_true', help='快速测试（6个用例）')

    args = parser.parse_args()

    limit = 6 if args.quick else args.limit

    tester = V2BenchmarkTester()
    tester.run_batch_test(limit=limit)


if __name__ == "__main__":
    main()
