#!/usr/bin/env python3
"""MiMo 自动化批量测试 - 真实修复 + 自动还原"""
import sys
import os
import json
import time
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from src.core.error_identifier import ErrorIdentifier
from src.agent.debug_agent import DebugAgent


class MiMoAutoTester:
    """MiMo 自动化测试器"""

    def __init__(self, test_cases_dir: str = "tests/test_cases_v2"):
        self.test_cases_dir = Path(test_cases_dir)
        self.backup_dir = Path("/tmp/v2_test_backup")
        self.results = []

        # 检测模型
        base_url = os.getenv('ANTHROPIC_BASE_URL', 'Anthropic Official API')
        self.model_name = 'mimo' if 'mimo' in base_url.lower() else 'claude'

        print(f"\n{'='*70}")
        print(f"V2 Benchmark 自动化测试")
        print(f"{'='*70}")
        print(f"模型: {self.model_name}")
        print(f"API: {base_url}")
        print(f"自动备份还原: 是")
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
                    metadata_file = case_dir / "metadata.json"
                    metadata = {}
                    if metadata_file.exists():
                        with open(metadata_file) as f:
                            metadata = json.load(f)

                    test_cases.append({
                        'path': case_dir,
                        'error_type': error_type,
                        'case_id': metadata.get('case_id', case_dir.name),
                        'difficulty': metadata.get('difficulty', 'unknown')
                    })

                    if limit and len(test_cases) >= limit:
                        return test_cases

        return test_cases

    def backup_case(self, case_dir: Path) -> Path:
        """备份测试用例"""
        backup_path = self.backup_dir / case_dir.relative_to(self.test_cases_dir.parent)

        # 删除旧备份
        if backup_path.exists():
            shutil.rmtree(backup_path)

        # 复制整个目录
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(case_dir, backup_path)

        return backup_path

    def restore_case(self, case_dir: Path, backup_path: Path):
        """还原测试用例"""
        if backup_path.exists():
            # 删除修改后的目录
            if case_dir.exists():
                shutil.rmtree(case_dir)
            # 从备份还原
            shutil.copytree(backup_path, case_dir)

    def run_case(self, case_dir: Path) -> dict:
        """运行测试用例"""
        try:
            result = subprocess.run(
                [sys.executable, "main.py"],
                cwd=str(case_dir),
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': 'Timeout after 10s'
            }
        except Exception as e:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }

    def test_single_case(self, case_info: dict, index: int, total: int) -> dict:
        """测试单个用例"""
        case_dir = case_info['path']
        case_id = case_info['case_id']
        error_type = case_info['error_type']
        difficulty = case_info['difficulty']

        print(f"\n{'='*70}")
        print(f"[{index}/{total}] {case_id}")
        print(f"类型: {error_type} | 难度: {difficulty}")
        print(f"{'='*70}")

        # 1. 备份
        print(f"📦 备份中...")
        backup_path = self.backup_case(case_dir)

        try:
            # 2. 运行获取初始错误
            print(f"🔍 运行测试...")
            initial_result = self.run_case(case_dir)

            if initial_result['returncode'] == 0:
                print(f"⚠️  程序没有错误，跳过")
                self.restore_case(case_dir, backup_path)
                return {
                    'case_id': case_id,
                    'error_type': error_type,
                    'difficulty': difficulty,
                    'success': False,
                    'skipped': True,
                    'reason': 'No initial error',
                    'duration': 0
                }

            print(f"❌ 检测到错误:")
            error_preview = initial_result['stderr'].split('\n')[-3:]
            for line in error_preview:
                if line.strip():
                    print(f"   {line}")

            # 3. 使用 Debug Agent 修复
            print(f"🔧 启动 Debug Agent 修复...")
            start_time = time.time()

            try:
                # 识别错误文件
                from src.core.error_identifier import ErrorIdentifier
                identifier = ErrorIdentifier()
                error = identifier.identify(initial_result['stderr'])

                # 读取出错文件的代码
                error_file_path = case_dir / Path(error.error_file).name if error.error_file else case_dir / "main.py"
                if error_file_path.exists():
                    buggy_code = error_file_path.read_text()
                else:
                    buggy_code = ""

                # 创建 agent
                agent = DebugAgent(
                    project_path=str(case_dir)
                )

                # 运行调试（异步）
                import asyncio
                fix_result = asyncio.run(agent.debug(
                    buggy_code=buggy_code,
                    error_traceback=initial_result['stderr'],
                    error_file=str(error.error_file) if error.error_file else ""
                ))
                duration = time.time() - start_time

                print(f"   修复耗时: {duration:.1f}s")

            except Exception as e:
                duration = time.time() - start_time
                print(f"   ❌ Debug Agent 异常: {str(e)[:100]}")

                self.restore_case(case_dir, backup_path)
                return {
                    'case_id': case_id,
                    'error_type': error_type,
                    'difficulty': difficulty,
                    'success': False,
                    'duration': duration,
                    'error': str(e)[:300]
                }

            # 4. 验证修复
            print(f"✅ 验证修复结果...")
            verify_result = self.run_case(case_dir)

            if verify_result['returncode'] == 0:
                print(f"   ✅ 修复成功!")
                success = True
            else:
                print(f"   ❌ 修复失败，仍有错误:")
                error_preview = verify_result['stderr'].split('\n')[-2:]
                for line in error_preview:
                    if line.strip():
                        print(f"      {line}")
                success = False

            result = {
                'case_id': case_id,
                'error_type': error_type,
                'difficulty': difficulty,
                'success': success,
                'duration': duration,
                'initial_error': initial_result['stderr'][-500:],
                'final_error': verify_result['stderr'][-500:] if not success else None
            }

        finally:
            # 5. 无论成功失败，都还原
            print(f"♻️  还原测试用例...")
            self.restore_case(case_dir, backup_path)

        return result

    def run_batch_test(self, limit: int = None):
        """批量测试"""
        # 创建备份目录
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 加载测试用例
        test_cases = self.load_test_cases(limit=limit)

        print(f"加载 {len(test_cases)} 个测试用例")
        if limit:
            print(f"(限制: 前 {limit} 个)")
        print()

        # 运行测试
        for i, case_info in enumerate(test_cases, 1):
            result = self.test_single_case(case_info, i, len(test_cases))

            if not result.get('skipped'):
                self.results.append(result)

            # 显示统计
            if self.results:
                success_count = sum(1 for r in self.results if r.get('success'))
                avg_duration = sum(r.get('duration', 0) for r in self.results) / len(self.results)
                print(f"\n📊 当前统计: {success_count}/{len(self.results)} 成功 " +
                      f"({success_count/len(self.results)*100:.1f}%) | " +
                      f"平均耗时: {avg_duration:.1f}s")

        # 生成报告
        self.generate_report()

        # 清理备份
        print(f"\n🧹 清理备份目录...")
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        print(f"   ✅ 清理完成")

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
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)

        print(f"\n## 整体表现")
        print(f"   总用例数: {total}")
        print(f"   成功数: {success_count}")
        print(f"   成功率: {success_rate:.1f}%")
        print(f"   平均耗时: {avg_duration:.1f}s")
        print(f"   最快: {min_duration:.1f}s | 最慢: {max_duration:.1f}s")

        # 按错误类型统计
        by_type = defaultdict(lambda: {'total': 0, 'success': 0, 'durations': []})
        for r in self.results:
            error_type = r.get('error_type', 'unknown')
            by_type[error_type]['total'] += 1
            if r.get('success'):
                by_type[error_type]['success'] += 1
            by_type[error_type]['durations'].append(r.get('duration', 0))

        print(f"\n## 按错误类型统计")
        print(f"{'类型':<20s} {'成功率':<20s} {'平均耗时'}")
        print("-" * 60)
        for error_type, stats in sorted(by_type.items()):
            rate = stats['success'] / stats['total'] * 100
            avg_dur = sum(stats['durations']) / len(stats['durations'])
            print(f"{error_type:<20s} {stats['success']}/{stats['total']} ({rate:>5.1f}%) {avg_dur:>10.1f}s")

        # 按难度统计
        by_difficulty = defaultdict(lambda: {'total': 0, 'success': 0})
        for r in self.results:
            difficulty = r.get('difficulty', 'unknown')
            by_difficulty[difficulty]['total'] += 1
            if r.get('success'):
                by_difficulty[difficulty]['success'] += 1

        print(f"\n## 按难度统计")
        print(f"{'难度':<20s} {'成功率'}")
        print("-" * 40)
        for difficulty, stats in sorted(by_difficulty.items()):
            rate = stats['success'] / stats['total'] * 100
            print(f"{difficulty:<20s} {stats['success']}/{stats['total']} ({rate:.1f}%)")

        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f"{self.model_name}_v2_results_{timestamp}.json"

        with open(result_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'model': self.model_name,
                'base_url': os.getenv('ANTHROPIC_BASE_URL', 'Anthropic Official'),
                'total': total,
                'success_count': success_count,
                'success_rate': success_rate,
                'avg_duration': avg_duration,
                'min_duration': min_duration,
                'max_duration': max_duration,
                'by_type': dict(by_type),
                'by_difficulty': dict(by_difficulty),
                'results': self.results
            }, f, indent=2)

        print(f"\n✅ 详细结果已保存到: {result_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='MiMo V2 自动化批量测试')
    parser.add_argument('--limit', type=int, help='限制测试用例数量')
    parser.add_argument('--quick', action='store_true', help='快速测试（6个用例）')
    parser.add_argument('--all', action='store_true', help='测试全部30个用例')

    args = parser.parse_args()

    if args.all:
        limit = None
    elif args.quick:
        limit = 6
    else:
        limit = args.limit

    tester = MiMoAutoTester()
    tester.run_batch_test(limit=limit)


if __name__ == "__main__":
    main()
