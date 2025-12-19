#!/usr/bin/env python3
"""测试 MiMo 真实修复能力 - 测试完自动还原"""
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


class RealFixTester:
    """真实修复测试器 - 测试完自动还原"""

    def __init__(self, test_cases_dir: str = "tests/test_cases_v2"):
        self.test_cases_dir = Path(test_cases_dir)
        self.results = []
        self.backup_dir = Path("/tmp/v2_backup")

        # 检测模型
        base_url = os.getenv('ANTHROPIC_BASE_URL', 'Anthropic Official API')
        self.model_name = 'mimo' if 'mimo' in base_url.lower() else 'claude'

        print(f"\n{'='*70}")
        print(f"MiMo 真实修复能力测试")
        print(f"{'='*70}")
        print(f"模型: {self.model_name}")
        print(f"API: {base_url}")
        print(f"测试后自动还原: 是")
        print(f"{'='*70}\n")

    def backup_case(self, case_dir: Path):
        """备份测试用例"""
        backup_path = self.backup_dir / case_dir.relative_to(self.test_cases_dir)
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        # 复制整个目录
        if backup_path.exists():
            shutil.rmtree(backup_path)
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
            print(f"   ✅ 已还原: {case_dir.name}")

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
                'stderr': 'Timeout'
            }

    def call_claude_code_fix(self, case_dir: Path, error_info: str) -> dict:
        """调用 Claude Code 进行修复（通过 CLI）"""
        # 创建修复提示
        prompt = f"""这个目录包含一个有错误的 Python 项目。

错误信息:
{error_info[:500]}

请帮我：
1. 分析错误原因
2. 修复错误（直接修改文件）
3. 验证修复成功

项目目录: {case_dir}
请开始修复。
"""

        # 保存 prompt 到临时文件
        prompt_file = case_dir / ".fix_prompt.txt"
        prompt_file.write_text(prompt)

        print(f"   📝 修复提示已生成")
        print(f"   ⚠️  需要手动运行 Claude Code 进行修复")
        print(f"      cd {case_dir}")
        print(f"      claude < .fix_prompt.txt")
        print()

        return {
            'success': False,
            'reason': 'Manual intervention required'
        }

    def simple_pattern_fix(self, case_dir: Path, error_type: str, error_msg: str) -> dict:
        """简单模式修复（基于规则）"""
        import re
        from src.core.pattern_fixer import PatternFixer

        try:
            # 读取错误文件
            if 'File' in error_msg:
                match = re.search(r'File "([^"]+)"', error_msg)
                if match:
                    error_file_path = match.group(1)
                    if os.path.exists(error_file_path):
                        with open(error_file_path) as f:
                            content = f.read()

                        # 使用 PatternFixer
                        fixer = PatternFixer()
                        fixed_content = fixer.fix(content, error_msg)

                        if fixed_content != content:
                            with open(error_file_path, 'w') as f:
                                f.write(fixed_content)
                            return {
                                'success': True,
                                'method': 'pattern_fixer',
                                'file': error_file_path
                            }

            return {
                'success': False,
                'reason': 'Pattern fixer could not fix'
            }
        except Exception as e:
            return {
                'success': False,
                'reason': f'Error: {str(e)}'
            }

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

        # 1. 备份
        print(f"📦 备份测试用例...")
        backup_path = self.backup_case(case_dir)

        # 2. 运行获取错误
        print(f"🔍 运行测试用例...")
        initial_result = self.run_case(case_dir)

        if initial_result['returncode'] == 0:
            print(f"⚠️  程序没有错误，跳过")
            self.restore_case(case_dir, backup_path)
            return {
                'case_id': case_id,
                'error_type': error_type,
                'difficulty': difficulty,
                'success': False,
                'reason': 'No error',
                'duration': 0,
                'skipped': True
            }

        print(f"❌ 检测到错误")
        print(f"   错误信息: {initial_result['stderr'][:200]}...")

        # 3. 尝试修复
        print(f"🔧 尝试自动修复...")
        start_time = time.time()

        fix_result = self.simple_pattern_fix(
            case_dir,
            error_type,
            initial_result['stderr']
        )

        duration = time.time() - start_time

        # 4. 验证修复
        if fix_result.get('success'):
            print(f"   ✅ 修复完成，验证中...")
            verify_result = self.run_case(case_dir)

            if verify_result['returncode'] == 0:
                print(f"   ✅ 修复成功! (耗时: {duration:.1f}s)")
                success = True
            else:
                print(f"   ❌ 修复失败，程序仍有错误")
                print(f"      {verify_result['stderr'][:200]}...")
                success = False
        else:
            print(f"   ⚠️  无法自动修复: {fix_result.get('reason', 'unknown')}")
            success = False

        # 5. 还原
        print(f"♻️  还原测试用例...")
        self.restore_case(case_dir, backup_path)

        result = {
            'case_id': case_id,
            'error_type': error_type,
            'difficulty': difficulty,
            'success': success,
            'duration': duration,
            'initial_error': initial_result['stderr'][:500],
            'fix_method': fix_result.get('method', 'none')
        }

        return result

    def run_batch_test(self, limit: int = None):
        """批量测试"""
        # 创建备份目录
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 加载测试用例
        test_cases = self.load_test_cases(limit=limit)

        print(f"加载 {len(test_cases)} 个测试用例")
        if limit:
            print(f"(限制: {limit} 个)")
        print()

        # 运行测试
        for i, case_info in enumerate(test_cases, 1):
            result = self.test_single_case(case_info, i, len(test_cases))

            if not result.get('skipped'):
                self.results.append(result)

            # 显示统计
            if self.results:
                success_count = sum(1 for r in self.results if r.get('success'))
                print(f"\n📊 当前统计: {success_count}/{len(self.results)} 成功 ({success_count/len(self.results)*100:.1f}%)")

        # 生成报告
        self.generate_report()

        # 清理备份
        print(f"\n🧹 清理备份...")
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)

    def generate_report(self):
        """生成报告"""
        print("\n\n" + "="*70)
        print("测试报告")
        print("="*70)

        if not self.results:
            print("\n⚠️  无有效测试结果")
            return

        # 统计
        total = len(self.results)
        success_count = sum(1 for r in self.results if r.get('success'))
        success_rate = success_count / total * 100

        durations = [r.get('duration', 0) for r in self.results]
        avg_duration = sum(durations) / len(durations) if durations else 0

        print(f"\n## 整体表现")
        print(f"   总用例数: {total}")
        print(f"   成功数: {success_count}")
        print(f"   成功率: {success_rate:.1f}%")
        print(f"   平均耗时: {avg_duration:.1f}秒")

        # 按类型统计
        by_type = defaultdict(lambda: {'total': 0, 'success': 0})
        for r in self.results:
            error_type = r.get('error_type', 'unknown')
            by_type[error_type]['total'] += 1
            if r.get('success'):
                by_type[error_type]['success'] += 1

        print(f"\n## 按错误类型统计")
        print(f"{'类型':<20s} {'成功率'}")
        print("-" * 40)
        for error_type, stats in sorted(by_type.items()):
            rate = stats['success'] / stats['total'] * 100
            print(f"{error_type:<20s} {stats['success']}/{stats['total']} ({rate:.1f}%)")

        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f"mimo_real_fix_results_{timestamp}.json"

        with open(result_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'model': self.model_name,
                'base_url': os.getenv('ANTHROPIC_BASE_URL', 'Anthropic Official'),
                'total': total,
                'success_count': success_count,
                'success_rate': success_rate,
                'avg_duration': avg_duration,
                'results': self.results
            }, f, indent=2)

        print(f"\n✅ 详细结果已保存到: {result_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='MiMo 真实修复能力测试')
    parser.add_argument('--limit', type=int, help='限制测试用例数量')
    parser.add_argument('--quick', action='store_true', help='快速测试（6个用例）')

    args = parser.parse_args()

    limit = 6 if args.quick else args.limit

    print("\n⚠️  注意: 此脚本使用简单的 Pattern Fixer 进行修复")
    print("   如需测试完整的 LLM 修复能力，建议手动使用 Claude Code")
    print()

    tester = RealFixTester()
    tester.run_batch_test(limit=limit)


if __name__ == "__main__":
    main()
