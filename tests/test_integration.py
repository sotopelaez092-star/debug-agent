"""
集成测试：验证 Debug Agent 完整流程
测试带错误的代码 -> Agent 自动调试 -> 验证修复结果
"""

import asyncio
import sys
import tempfile
import shutil
from pathlib import Path


async def test_simple_import_error():
    """测试简单的 ImportError 修复"""
    print("=" * 60)
    print("集成测试 1: ImportError 修复")
    print("=" * 60)

    # 创建临时测试项目
    temp_dir = Path(tempfile.mkdtemp(prefix="debug_test_"))
    print(f"临时目录: {temp_dir}")

    try:
        # 创建有错误的代码
        buggy_code = """import maths  # 错误：应该是 math

def calculate_area(radius):
    return maths.pi * radius ** 2

if __name__ == "__main__":
    print(f"Area: {calculate_area(5)}")
"""

        # 写入文件
        main_file = temp_dir / "main.py"
        main_file.write_text(buggy_code)
        print(f"\n创建测试文件: {main_file}")
        print("错误代码:")
        print(buggy_code)

        # 运行代码获取错误
        import subprocess
        result = subprocess.run(
            [sys.executable, str(main_file)],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print("❌ 代码应该有错误但成功执行了")
            return False

        error_traceback = result.stderr
        print(f"\n错误信息:\n{error_traceback}")

        # 初始化 Debug Agent
        from src.agent.debug_agent_new import DebugAgent

        print("\n初始化 Debug Agent...")
        agent = DebugAgent(project_path=str(temp_dir))

        # 执行调试
        print("\n开始调试...")
        debug_result = await agent.debug(
            buggy_code=buggy_code,
            error_traceback=error_traceback,
            error_file="main.py",
            max_retries=3
        )

        # 验证结果
        print("\n" + "=" * 60)
        print("调试结果:")
        print("=" * 60)
        print(f"成功: {debug_result.success}")
        print(f"尝试次数: {debug_result.attempts}")
        print(f"说明: {debug_result.explanation}")

        if debug_result.success:
            print("\n修复后的代码:")
            print("-" * 60)
            print(debug_result.fixed_code)
            print("-" * 60)

            # 验证修复后的代码能运行
            print("\n验证修复后的代码...")
            fixed_file = temp_dir / "main_fixed.py"
            fixed_file.write_text(debug_result.fixed_code)

            verify_result = subprocess.run(
                [sys.executable, str(fixed_file)],
                capture_output=True,
                text=True,
                timeout=5
            )

            if verify_result.returncode == 0:
                print("✅ 修复后的代码成功执行！")
                print(f"输出: {verify_result.stdout.strip()}")
                return True
            else:
                print(f"❌ 修复后的代码仍有错误:\n{verify_result.stderr}")
                return False
        else:
            print("❌ 调试失败")
            return False

    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时目录
        print(f"\n清理临时目录: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)


async def test_name_error():
    """测试简单的 NameError 修复"""
    print("\n" + "=" * 60)
    print("集成测试 2: NameError 修复")
    print("=" * 60)

    temp_dir = Path(tempfile.mkdtemp(prefix="debug_test_"))
    print(f"临时目录: {temp_dir}")

    try:
        # 创建有错误的代码
        buggy_code = """def greet(name):
    message = "Hello, " + nam  # 错误：应该是 name
    return message

if __name__ == "__main__":
    print(greet("World"))
"""

        main_file = temp_dir / "main.py"
        main_file.write_text(buggy_code)
        print(f"\n创建测试文件: {main_file}")

        # 运行代码获取错误
        import subprocess
        result = subprocess.run(
            [sys.executable, str(main_file)],
            capture_output=True,
            text=True,
            timeout=5
        )

        error_traceback = result.stderr
        print(f"\n错误信息:\n{error_traceback[:200]}...")

        # 初始化 Debug Agent
        from src.agent.debug_agent_new import DebugAgent

        print("\n初始化 Debug Agent...")
        agent = DebugAgent(project_path=str(temp_dir))

        # 执行调试
        print("\n开始调试...")
        debug_result = await agent.debug(
            buggy_code=buggy_code,
            error_traceback=error_traceback,
            error_file="main.py",
            max_retries=3
        )

        # 验证结果
        print("\n" + "=" * 60)
        print("调试结果:")
        print("=" * 60)
        print(f"成功: {debug_result.success}")
        print(f"尝试次数: {debug_result.attempts}")

        if debug_result.success:
            print("\n✅ 调试成功！")
            print(f"修复说明: {debug_result.explanation[:100]}...")
            return True
        else:
            print("❌ 调试失败")
            return False

    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def main():
    """运行所有集成测试"""
    print("\n" + "=" * 60)
    print("Debug Agent 集成测试")
    print("=" * 60)

    results = []

    # 测试 1: ImportError
    result1 = await test_simple_import_error()
    results.append(("ImportError 修复", result1))

    # 测试 2: NameError
    result2 = await test_name_error()
    results.append(("NameError 修复", result2))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有集成测试通过！系统运行正常。\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败。\n")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
