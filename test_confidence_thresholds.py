#!/usr/bin/env python3
"""
置信度阈值测试脚本

测试目标:
1. 验证不同阈值 (0.6, 0.65, 0.7, 0.75, 0.8) 的效果
2. 对比不同错误类型是否需要不同阈值
3. 找出最优阈值配置

测试指标:
- 快速路径命中率: 使用快速路径修复的比例
- 成功率: 修复成功的比例
- LLM调用次数: 平均每个用例的LLM调用次数
- 平均耗时: 每个用例的平均处理时间
"""

import sys
import os
import json
import time
import subprocess
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional
import asyncio

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core.error_identifier import ErrorIdentifier
from src.strategies.registry import ErrorStrategyRegistry
from src.tools_new.context_tools import ContextTools


class ConfidenceThresholdTester:
    """置信度阈值测试器"""

    def __init__(self, test_cases_dir: str = "tests/test_cases_v2"):
        self.test_cases_dir = Path(test_cases_dir)
        self.error_identifier = ErrorIdentifier()
        self.results = []

    def load_test_cases(self) -> Dict[str, List[Path]]:
        """加载所有测试用例，按错误类型分类"""
        test_cases = defaultdict(list)

        for error_type_dir in self.test_cases_dir.iterdir():
            if not error_type_dir.is_dir() or error_type_dir.name.startswith('.'):
                continue

            error_type = error_type_dir.name

            for case_dir in error_type_dir.iterdir():
                if case_dir.is_dir() and case_dir.name.startswith('case_'):
                    main_file = case_dir / "main.py"
                    if main_file.exists():
                        test_cases[error_type].append(case_dir)

        return test_cases

    def run_test_case(self, case_dir: Path) -> Optional[Dict]:
        """运行单个测试用例，获取错误信息"""
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
                [sys.executable, str(main_file)],
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
                    'error_type': metadata.get('error_type', error.error_type),
                    'difficulty': metadata.get('difficulty', 'unknown'),
                    'error': error,
                    'traceback': result.stderr,
                    'metadata': metadata
                }
        except Exception as e:
            print(f"⚠️  Error running {case_dir.name}: {e}")

        return None

    def test_strategy_confidence(
        self,
        error_type: str,
        test_case: Dict,
        threshold: float
    ) -> Dict:
        """测试单个用例在指定阈值下的表现"""

        # 创建策略注册表
        registry = ErrorStrategyRegistry()
        registry.register_all_defaults(confidence_threshold=threshold)

        # 获取对应的策略
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

        # 创建 ContextTools（需要项目路径）
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
                    'reason': f'Confidence {search_result.confidence if search_result else 0.0:.2f} below threshold {threshold}'
                }
        except Exception as e:
            return {
                'used_fast_path': False,
                'confidence': 0.0,
                'reason': f'Error: {str(e)[:100]}'
            }

    def test_threshold(self, threshold: float, test_cases: Dict[str, List[Path]]) -> Dict:
        """测试指定阈值下的整体表现"""
        print(f"\n{'='*60}")
        print(f"测试阈值: {threshold}")
        print(f"{'='*60}")

        results_by_type = defaultdict(list)

        for error_type, cases in test_cases.items():
            print(f"\n{error_type}: {len(cases)} 个用例")

            for case_dir in cases:
                # 运行测试用例
                test_case = self.run_test_case(case_dir)
                if not test_case:
                    continue

                # 测试策略置信度
                result = self.test_strategy_confidence(
                    error_type,
                    test_case,
                    threshold
                )

                result['case_id'] = test_case['case_id']
                result['difficulty'] = test_case['difficulty']
                results_by_type[error_type].append(result)

                # 显示进度
                status = "✅ 快速" if result['used_fast_path'] else "🔍 调查"
                conf = result['confidence']
                print(f"  {status} {test_case['case_id'][:40]:40s} 置信度: {conf:.3f}")

        # 统计结果
        return self.calculate_statistics(threshold, results_by_type)

    def calculate_statistics(self, threshold: float, results_by_type: Dict) -> Dict:
        """计算统计数据"""
        stats = {
            'threshold': threshold,
            'by_type': {},
            'overall': {}
        }

        total_cases = 0
        total_fast_path = 0
        all_confidences = []

        for error_type, results in results_by_type.items():
            fast_path_count = sum(1 for r in results if r['used_fast_path'])
            confidences = [r['confidence'] for r in results]

            stats['by_type'][error_type] = {
                'total': len(results),
                'fast_path_count': fast_path_count,
                'fast_path_rate': fast_path_count / len(results) if results else 0,
                'avg_confidence': sum(confidences) / len(confidences) if confidences else 0,
                'max_confidence': max(confidences) if confidences else 0,
                'min_confidence': min(confidences) if confidences else 0
            }

            total_cases += len(results)
            total_fast_path += fast_path_count
            all_confidences.extend(confidences)

        stats['overall'] = {
            'total': total_cases,
            'fast_path_count': total_fast_path,
            'fast_path_rate': total_fast_path / total_cases if total_cases else 0,
            'avg_confidence': sum(all_confidences) / len(all_confidences) if all_confidences else 0
        }

        return stats

    def run_all_tests(self, thresholds: List[float]) -> List[Dict]:
        """运行所有阈值的测试"""
        print("\n" + "="*60)
        print("置信度阈值测试")
        print("="*60)

        # 加载测试用例
        test_cases = self.load_test_cases()

        print(f"\n加载测试用例:")
        total = 0
        for error_type, cases in test_cases.items():
            print(f"  {error_type:20s} {len(cases)} 个")
            total += len(cases)
        print(f"  {'总计':20s} {total} 个")

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
        report.append("置信度阈值测试报告")
        report.append("="*80)

        # 1. 整体对比
        report.append("\n## 1. 不同阈值的整体表现")
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

        # 2. 按错误类型对比
        report.append("\n## 2. 不同错误类型的阈值需求")

        # 获取所有错误类型
        error_types = set()
        for result in results:
            error_types.update(result['by_type'].keys())

        for error_type in sorted(error_types):
            report.append(f"\n### {error_type}")
            report.append("\n| 阈值 | 快速路径命中率 | 平均置信度 | 用例数 |")
            report.append("|------|---------------|-----------|--------|")

            for result in results:
                if error_type in result['by_type']:
                    stats = result['by_type'][error_type]
                    report.append(
                        f"| {result['threshold']:.2f} | "
                        f"{stats['fast_path_rate']*100:.1f}% | "
                        f"{stats['avg_confidence']:.3f} | "
                        f"{stats['total']} |"
                    )

        # 3. 建议
        report.append("\n## 3. 建议的阈值配置")
        report.append("\n基于测试结果的建议:")

        # 找出最优阈值
        best_overall = max(results, key=lambda r: r['overall']['fast_path_rate'])
        report.append(f"\n**整体最优阈值**: {best_overall['threshold']:.2f}")
        report.append(f"  - 快速路径命中率: {best_overall['overall']['fast_path_rate']*100:.1f}%")
        report.append(f"  - 平均置信度: {best_overall['overall']['avg_confidence']:.3f}")

        # 按错误类型推荐
        report.append("\n**按错误类型推荐**:")
        for error_type in sorted(error_types):
            type_results = [
                (r['threshold'], r['by_type'][error_type]['fast_path_rate'])
                for r in results if error_type in r['by_type']
            ]
            best_threshold, best_rate = max(type_results, key=lambda x: x[1])
            report.append(f"  - {error_type:20s} {best_threshold:.2f} (命中率 {best_rate*100:.1f}%)")

        return "\n".join(report)

    def save_results(self, filename: str = "confidence_test_results.json"):
        """保存测试结果"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✅ 结果已保存到: {filename}")


def main():
    """主函数"""
    # 测试的阈值列表
    thresholds = [0.60, 0.65, 0.70, 0.75, 0.80]

    # 创建测试器
    tester = ConfidenceThresholdTester()

    # 运行测试
    results = tester.run_all_tests(thresholds)

    # 生成报告
    report = tester.generate_report(results)
    print(report)

    # 保存结果
    tester.save_results()

    # 同时保存报告
    with open("confidence_test_report.md", 'w') as f:
        f.write(report)
    print("✅ 报告已保存到: confidence_test_report.md")


if __name__ == "__main__":
    main()
