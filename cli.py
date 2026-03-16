#!/usr/bin/env python3
"""
Debug Agent CLI - AI 驱动的 Python 自动调试工具

用法:
  # 自动运行文件，捕获错误并修复
  python cli.py run <project_path> <file>

  # 手动提供错误信息
  python cli.py fix <project_path> <file> --error "NameError: name 'foo' is not defined"

  # 交互式 demo（使用内置测试用例）
  python cli.py demo
"""

import asyncio
import argparse
import subprocess
import sys
import os
from pathlib import Path

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).parent))


def run_and_capture(project_path: str, file_path: str) -> tuple[bool, str, str]:
    """运行 Python 文件并捕获输出"""
    full_path = Path(project_path) / file_path
    result = subprocess.run(
        [sys.executable, str(full_path)],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=project_path,
    )
    return result.returncode == 0, result.stdout, result.stderr


async def do_debug(project_path: str, file_path: str, error_traceback: str, auto_apply: bool = False):
    """执行调试流程"""
    from src.agent.debug_agent_new import DebugAgent

    full_path = Path(project_path) / file_path
    buggy_code = full_path.read_text()

    print(f"\n{'='*60}")
    print(f"  Debug Agent - AI 自动调试")
    print(f"{'='*60}")
    print(f"  项目: {project_path}")
    print(f"  文件: {file_path}")
    print(f"  错误: {error_traceback[:100]}...")
    print(f"{'='*60}\n")

    agent = DebugAgent(project_path=project_path)

    print("[1/3] 分析错误中...")
    result = await agent.debug(
        buggy_code=buggy_code,
        error_traceback=error_traceback,
        error_file=file_path,
        max_retries=3,
    )

    print(f"\n{'='*60}")
    if result.success:
        print("  修复成功!")
        print(f"  尝试次数: {result.attempts}")
        print(f"  说明: {result.explanation}")
        print(f"\n  --- 修复后的代码 ---")
        print(result.fixed_code)

        if auto_apply:
            full_path.write_text(result.fixed_code)
            print(f"\n  已写入 {file_path}")
        else:
            try:
                answer = input(f"\n是否将修复写入 {file_path}? [y/N] ").strip().lower()
                if answer == "y":
                    full_path.write_text(result.fixed_code)
                    print(f"  已写入 {file_path}")
            except EOFError:
                pass
    else:
        print("  修复失败")
        print(f"  说明: {result.explanation}")
    print(f"{'='*60}\n")

    return result


async def cmd_run(args):
    """run 子命令：自动运行文件，捕获错误并修复"""
    project_path = str(Path(args.project_path).resolve())
    file_path = args.file

    print(f"运行 {file_path} ...")
    success, stdout, stderr = run_and_capture(project_path, file_path)

    if success:
        print(f"  程序运行成功，无错误。")
        if stdout:
            print(f"  输出: {stdout.strip()}")
        return

    print(f"  捕获到错误:\n{stderr.strip()}\n")
    await do_debug(project_path, file_path, stderr, auto_apply=args.yes)


async def cmd_fix(args):
    """fix 子命令：手动提供错误信息进行修复"""
    project_path = str(Path(args.project_path).resolve())
    file_path = args.file
    error = args.error
    await do_debug(project_path, file_path, error, auto_apply=args.yes)


async def cmd_demo(args):
    """demo 子命令：使用内置测试用例演示"""
    import json
    import tempfile
    import shutil

    demo_cases = [
        {
            "name": "NameError - 拼写错误",
            "code": '''def calculate_sum(numbers):
    """计算数字列表的和"""
    return sum(numbers)

def main():
    data = [1, 2, 3, 4, 5]
    # Bug: calculate_summ 多了一个 m
    result = calculate_summ(data)
    print(f"Sum: {result}")

if __name__ == "__main__":
    main()
''',
            "error": "Traceback (most recent call last):\n  File \"main.py\", line 12, in <module>\n    main()\n  File \"main.py\", line 8, in main\n    result = calculate_summ(data)\nNameError: name 'calculate_summ' is not defined",
        },
        {
            "name": "ImportError - 模块名拼写错误",
            "code": '''import maths

def area(radius):
    return maths.pi * radius ** 2

print(area(5))
''',
            "error": "Traceback (most recent call last):\n  File \"main.py\", line 1, in <module>\n    import maths\nModuleNotFoundError: No module named 'maths'",
        },
        {
            "name": "TypeError - 参数错误",
            "code": '''def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

# Bug: 传了太多参数
result = greet("Alice", "Hi", "World")
print(result)
''',
            "error": 'Traceback (most recent call last):\n  File "main.py", line 5, in <module>\n    result = greet("Alice", "Hi", "World")\nTypeError: greet() takes from 1 to 2 positional arguments but 3 were given',
        },
    ]

    print(f"\n{'='*60}")
    print(f"  Debug Agent Demo")
    print(f"  共 {len(demo_cases)} 个测试用例")
    print(f"{'='*60}\n")

    for i, case in enumerate(demo_cases, 1):
        print(f"\n--- Demo {i}/{len(demo_cases)}: {case['name']} ---")
        print(f"错误代码:")
        for line in case["code"].strip().split("\n"):
            print(f"  {line}")
        print(f"\n错误信息:")
        print(f"  {case['error'].split(chr(10))[-1]}")

        # 创建临时项目目录
        tmpdir = tempfile.mkdtemp(prefix="debug_agent_demo_")
        main_file = Path(tmpdir) / "main.py"
        main_file.write_text(case["code"])

        try:
            result = await do_debug(tmpdir, "main.py", case["error"])
        except Exception as e:
            print(f"  错误: {e}")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

        if i < len(demo_cases):
            input("\n按 Enter 继续下一个 demo...")


def main():
    parser = argparse.ArgumentParser(
        description="Debug Agent - AI 驱动的 Python 自动调试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cli.py run ./my_project main.py     # 运行并自动修复
  python cli.py fix ./my_project main.py --error "NameError: ..."
  python cli.py demo                          # 交互式演示
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # run 子命令
    run_parser = subparsers.add_parser("run", help="运行文件并自动修复错误")
    run_parser.add_argument("project_path", help="项目根目录")
    run_parser.add_argument("file", help="要运行的 Python 文件（相对于项目根目录）")
    run_parser.add_argument("-y", "--yes", action="store_true", help="自动应用修复，不询问")

    # fix 子命令
    fix_parser = subparsers.add_parser("fix", help="手动提供错误信息进行修复")
    fix_parser.add_argument("project_path", help="项目根目录")
    fix_parser.add_argument("file", help="有 bug 的文件（相对于项目根目录）")
    fix_parser.add_argument("--error", required=True, help="错误 traceback")
    fix_parser.add_argument("-y", "--yes", action="store_true", help="自动应用修复，不询问")

    # demo 子命令
    subparsers.add_parser("demo", help="运行内置演示用例")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "run":
        asyncio.run(cmd_run(args))
    elif args.command == "fix":
        asyncio.run(cmd_fix(args))
    elif args.command == "demo":
        asyncio.run(cmd_demo(args))


if __name__ == "__main__":
    main()
