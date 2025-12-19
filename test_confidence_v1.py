#!/usr/bin/env python3
"""V1 简单用例置信度阈值测试"""
import sys
import os
import json
import subprocess
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from src.core.error_identifier import ErrorIdentifier
from src.strategies.registry import ErrorStrategyRegistry
from src.tools_new.context_tools import ContextTools


class V1ConfidenceThresholdTester:
    """V1 置信度阈值测试器"""

    def __init__(self, test_cases_dir: str = "tests/test_cases_v1"):
        self.test_cases_dir = Path(test_cases_dir)
        self.error_identifier = ErrorIdentifier()
        self.results = []

    def load_test_cases(self) -> List[Path]:
        """加载所有 V1 测试用例"""
        test_cases = []

        for case_dir in self.test_cases_dir.iterdir():
            if case_dir.is_dir() and not case_dir.name.startswith('.'):
                main_file = case_dir / "main.py"
                if main_file.exists():
                    test_cases.append(case_dir)

        return sorted(test_cases)

    def run_test_case(self, case_dir: Path) -> Optional[Dict]:
        """运行单个测试用例"""
        main_file = case_dir / "main.py"

        # 读取元数据
        metadata_file = case_dir / "metadata.json"
        metadata = {}
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)

        # 运行测试获取错误
        try:
            result = subprocess.run(
                [sys.executable, "main.py"],  # 使用相对路径
                cwd=str(case_dir),
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                # 识别错误
                error = self.error_identifier.identify(result.stderr)

                return {
                    'case_id': metadata.get('case_id', case_dir.name),
                    'case_dir': str(case_dir),
                    'error_type': error.error_type,
                    'error': error,
                    'traceback': result.stderr,
                    'metadata': metadata
                }
        except Exception as e:
            print(f"⚠️  Error running {case_dir.name}: {e}")

        return None

    def test_strategy_confidence(
        self,
        test_case: Dict,
        threshold: float
    ) -> Dict:
        """测试单个用例在指定阈值下的表现"""

        # 创建策略注册表
        registry = ErrorStrategyRegistry()
        registry.register_all_defaults(confidence_threshold=threshold)

        # 获取对应的策略
        error_type = test_case['error_type']
        strategy = registry.get(error_type)
        if not strategy:
            return {
                'used_fast_path': False,
                'confidence': 0.0,
                'reason': 'No strategy found'
            }

        # 提取错误信息
        error = test_case['error']
        extracted = strategy.extract(error.error_message)

        # 创建 ContextTools
        case_dir = Path(test_case['case_dir'])
        try:
            context_tools = ContextTools(str(case_dir))

            # 执行快速搜索
            search_result = strategy.fast_search(
                extracted,
                context_tools,
                error.error_file
            )

            if search_result and search_result.confidence >= threshold:
                return {
                    'used_fast_path': True,
                    'confidence': search_result.confidence,
                    'found': search_result.symbol or search_result.location,
                    'reason': 'Fast path - confidence above threshold'
                }
            else:
                return {
                    'used_fast_path': False,
                    'confidence': search_result.confidence if search_result else 0.0,
                    'reason': f'Confidence {search_result.confidence if search_result else 0.0:.2f} below threshold {threshold}',
                    'search_result': search_result
                }
        except Exception as e:
            import traceback
            return {
                'used_fast_path': False,
                'confidence': 0.0,
                'reason': f'Error: {str(e)}',
                'traceback': traceback.format_exc()
            }

    def test_threshold(self, threshold: float, test_cases: List[Path]) -> Dict:
        """测试指定阈值下的整体表现"""
        print(f"\n{'='*70}")
        print(f"测试阈值: {threshold}")
        print(f"{'='*70}")

        results = []

        for case_dir in test_cases:
            # 运行测试用例
            test_case = self.run_test_case(case_dir)
            if not test_case:
                continue

            # 测试策略置信度
            result = self.test_strategy_confidence(test_case, threshold)

            result['case_id'] = test_case['case_id']
            result['error_type'] = test_case['error_type']
            result['edit_distance'] = test_case['metadata'].get('edit_distance', 0)
            result['expected_similarity'] = test_case['metadata'].get('expected_similarity', 0)
            results.append(result)

            # 显示进度
            status = "✅ 快速" if result['used_fast_path'] else "🔍 探索"
            conf = result['confidence']
            edit_dist = result['edit_distance']
            reason = result.get('reason', '')
            print(f"  {status} [{edit_dist}] {test_case['case_id']:45s} 置信度: {conf:.3f}")
            if conf == 0.0 and 'traceback' in result:
                print(f"      ERROR: {result['reason']}")
                print(f"      {result['traceback'][:200]}")

        # 统计结果
        return self.calculate_statistics(threshold, results)

    def calculate_statistics(self, threshold: float, results: List[Dict]) -> Dict:
        """计算统计数据"""
        stats = {
            'threshold': threshold,
            'results': results,
            'overall': {}
        }

        total_cases = len(results)
        total_fast_path = sum(1 for r in results if r['used_fast_path'])
        confidences = [r['confidence'] for r in results]

        # 按编辑距离分组统计
        by_edit_distance = defaultdict(lambda: {'total': 0, 'fast_path': 0, 'confidences': []})
        for r in results:
            ed = r['edit_distance']
            by_edit_distance[ed]['total'] += 1
            if r['used_fast_path']:
                by_edit_distance[ed]['fast_path'] += 1
            by_edit_distance[ed]['confidences'].append(r['confidence'])

        stats['overall'] = {
            'total': total_cases,
            'fast_path_count': total_fast_path,
            'fast_path_rate': total_fast_path / total_cases if total_cases else 0,
            'avg_confidence': sum(confidences) / len(confidences) if confidences else 0
        }

        stats['by_edit_distance'] = {}
        for ed, data in by_edit_distance.items():
            stats['by_edit_distance'][ed] = {
                'total': data['total'],
                'fast_path_count': data['fast_path'],
                'fast_path_rate': data['fast_path'] / data['total'] if data['total'] else 0,
                'avg_confidence': sum(data['confidences']) / len(data['confidences']) if data['confidences'] else 0
            }

        return stats

    def run_all_tests(self, thresholds: List[float]) -> List[Dict]:
        """运行所有阈值的测试"""
        print("\n" + "="*70)
        print("V1 置信度阈值测试")
        print("="*70)

        # 加载测试用例
        test_cases = self.load_test_cases()

        print(f"\n加载 V1 测试用例: {len(test_cases)} 个")

        # 对每个阈值进行测试
        all_results = []
        for threshold in thresholds:
            result = self.test_threshold(threshold, test_cases)
            all_results.append(result)
            self.results.append(result)

        return all_results

    def generate_report(self, results: List[Dict]) -> str:
        """生成测试报告"""
        report = []
        report.append("\n" + "="*80)
        report.append("V1 置信度阈值测试报告")
        report.append("="*80)

        # 整体对比
        report.append("\n## 不同阈值的整体表现")
        report.append("\n| 阈值 | 快速路径命中率 | 平均置信度 | 总用例数 |")
        report.append("|------|---------------|-----------|---------|")

        for result in results:
            threshold = result['threshold']
            overall = result['overall']
            report.append(
                f"| {threshold:.2f} | "
                f"{overall['fast_path_rate']*100:.1f}% | "
                f"{overall['avg_confidence']:.3f} | "
                f"{overall['total']} |"
            )

        # 按编辑距离分析
        report.append("\n## 不同编辑距离的阈值效果")

        # 收集所有编辑距离
        all_edit_distances = set()
        for result in results:
            all_edit_distances.update(result.get('by_edit_distance', {}).keys())

        for edit_dist in sorted(all_edit_distances):
            report.append(f"\n### 编辑距离 = {edit_dist}")
            report.append("\n| 阈值 | 快速路径命中率 | 平均置信度 | 用例数 |")
            report.append("|------|---------------|-----------|--------|")

            for result in results:
                if edit_dist in result.get('by_edit_distance', {}):
                    stats = result['by_edit_distance'][edit_dist]
                    report.append(
                        f"| {result['threshold']:.2f} | "
                        f"{stats['fast_path_rate']*100:.1f}% | "
                        f"{stats['avg_confidence']:.3f} | "
                        f"{stats['total']} |"
                    )

        # 详细用例结果
        report.append("\n## 详细用例结果")
        report.append("\n| 用例 | 编辑距离 | 阈值 0.6 | 阈值 0.7 | 阈值 0.75 | 阈值 0.8 |")
        report.append("|------|---------|---------|---------|----------|---------|")

        # 收集每个用例在不同阈值下的置信度
        case_results = defaultdict(dict)
        for result in results:
            threshold = result['threshold']
            for case_result in result.get('results', []):
                case_id = case_result['case_id']
                case_results[case_id]['edit_distance'] = case_result['edit_distance']
                case_results[case_id][threshold] = case_result['confidence']

        for case_id in sorted(case_results.keys()):
            data = case_results[case_id]
            edit_dist = data.get('edit_distance', 0)
            report.append(
                f"| {case_id[:40]} | {edit_dist} | "
                f"{data.get(0.60, 0):.3f} | "
                f"{data.get(0.70, 0):.3f} | "
                f"{data.get(0.75, 0):.3f} | "
                f"{data.get(0.80, 0):.3f} |"
            )

        # 建议
        report.append("\n## 建议")

        best_threshold = max(results, key=lambda r: r['overall']['fast_path_rate'])
        report.append(f"\n**最优阈值**: {best_threshold['threshold']:.2f}")
        report.append(f"  - 快速路径命中率: {best_threshold['overall']['fast_path_rate']*100:.1f}%")
        report.append(f"  - 平均置信度: {best_threshold['overall']['avg_confidence']:.3f}")

        return "\n".join(report)


def main():
    """主函数"""
    thresholds = [0.60, 0.65, 0.70, 0.75, 0.80]

    tester = V1ConfidenceThresholdTester()
    results = tester.run_all_tests(thresholds)

    # 生成报告
    report = tester.generate_report(results)
    print(report)

    # 保存结果
    with open("confidence_test_v1_results.json", 'w') as f:
        json.dump(tester.results, f, indent=2, default=str)
    print("\n✅ 结果已保存到: confidence_test_v1_results.json")

    # 保存报告
    with open("confidence_test_v1_report.md", 'w') as f:
        f.write(report)
    print("✅ 报告已保存到: confidence_test_v1_report.md")


if __name__ == "__main__":
    main()
