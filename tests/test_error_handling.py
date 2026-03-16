"""
测试所有错误处理改进

验证：
1. 所有模块可以正常导入
2. 基本功能正常运行
3. 错误处理按预期工作
"""

import sys
import asyncio
from pathlib import Path

def test_imports():
    """测试所有模块导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)

    try:
        # Phase 1: 工具系统
        from src.models.tool_result import ToolResult, ErrorType
        from src.tools_new.base import BaseTool
        from src.tools_new.registry import ToolRegistry
        from src.tools_new.read_file_tool import ReadFileTool
        from src.tools_new.grep_tool import GrepTool
        print("✅ Phase 1 模块导入成功")

        # Phase 2: LLM 错误处理
        from src.core.llm_error_handler import (
            LLMError, LLMNetworkError, call_llm_with_retry, parse_llm_response_safe
        )
        from src.core.code_fixer import CodeFixer
        print("✅ Phase 2 模块导入成功")

        # Phase 3: 核心模块
        from src.core.pattern_fixer import PatternFixer
        from src.core.loop_detector import LoopDetector, LoopAction
        print("✅ Phase 3 模块导入成功")

        # Phase 4: Agent
        from src.agent.debug_agent import DebugAgent
        print("✅ Phase 4 模块导入成功")

        # Phase 5: Context Tools
        from src.tools_new.context_tools import ContextTools
        print("✅ Phase 5 模块导入成功")

        print("\n✅ 所有模块导入测试通过\n")
        return True
    except Exception as e:
        print(f"\n❌ 导入失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_tool_result():
    """测试 ToolResult 数据类"""
    print("=" * 60)
    print("测试 2: ToolResult 功能")
    print("=" * 60)

    from src.models.tool_result import ToolResult, ErrorType

    try:
        # 成功结果
        success_result = ToolResult.success_result(data={"key": "value"})
        assert success_result.success == True
        assert success_result.data == {"key": "value"}
        print("✅ 成功结果创建正确")

        # 错误结果
        error_result = ToolResult.error_result(
            error="文件不存在",
            error_type=ErrorType.NOT_FOUND
        )
        assert error_result.success == False
        assert error_result.error == "文件不存在"
        assert error_result.error_type == ErrorType.NOT_FOUND
        print("✅ 错误结果创建正确")

        print("\n✅ ToolResult 测试通过\n")
        return True
    except Exception as e:
        print(f"\n❌ ToolResult 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_read_file_tool():
    """测试 ReadFileTool 错误处理"""
    print("=" * 60)
    print("测试 3: ReadFileTool 错误处理")
    print("=" * 60)

    from src.tools_new.read_file_tool import ReadFileTool
    from src.models.tool_result import ErrorType

    try:
        tool = ReadFileTool(".")

        # 测试正常读取
        result = await tool.safe_execute(path="README.md")
        if result.success:
            print("✅ 正常文件读取成功")

        # 测试文件不存在
        result = await tool.safe_execute(path="nonexistent_file_12345.txt")
        assert result.success == False
        assert result.error_type == ErrorType.NOT_FOUND
        print("✅ 文件不存在错误处理正确")

        # 测试参数验证
        result = await tool.safe_execute(path="", start_line=0)
        print(f"   Debug: success={result.success}, error_type={result.error_type}, error={result.error}")
        assert result.success == False
        assert result.error_type == ErrorType.VALIDATION, f"Expected VALIDATION, got {result.error_type}"
        print("✅ 参数验证错误处理正确")

        print("\n✅ ReadFileTool 测试通过\n")
        return True
    except Exception as e:
        print(f"\n❌ ReadFileTool 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_loop_detector():
    """测试 LoopDetector 参数验证"""
    print("=" * 60)
    print("测试 4: LoopDetector 参数验证")
    print("=" * 60)

    from src.core.loop_detector import LoopDetector

    try:
        detector = LoopDetector()

        # 测试正常记录
        detector.record_attempt(
            fixed_code="print('hello')",
            error_type="NameError",
            error_message="name 'x' is not defined",
            layer=1,
            success=False
        )
        assert detector.get_attempt_count() == 1
        print("✅ 正常记录尝试成功")

        # 测试参数验证 - 无效的 layer
        try:
            detector.record_attempt(
                fixed_code="code",
                error_type="Error",
                error_message="msg",
                layer=0,  # 无效
                success=False
            )
            print("❌ 应该抛出 ValueError")
            return False
        except ValueError as e:
            print(f"✅ 参数验证正确: {e}")

        print("\n✅ LoopDetector 测试通过\n")
        return True
    except Exception as e:
        print(f"\n❌ LoopDetector 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_pattern_fixer():
    """测试 PatternFixer 错误处理"""
    print("=" * 60)
    print("测试 5: PatternFixer 错误处理")
    print("=" * 60)

    from src.core.pattern_fixer import PatternFixer

    try:
        fixer = PatternFixer()

        # 测试正常修复
        result = fixer.try_fix(
            code="import maths",
            error_type="ModuleNotFoundError",
            error_message="No module named 'maths'"
        )
        if result:
            print(f"✅ 修复成功: {result[1]}")

        # 测试参数验证
        result = fixer.try_fix(
            code="",  # 空代码
            error_type="Error",
            error_message="msg"
        )
        assert result is None
        print("✅ 空代码参数验证正确")

        print("\n✅ PatternFixer 测试通过\n")
        return True
    except Exception as e:
        print(f"\n❌ PatternFixer 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("错误处理改进 - 综合测试")
    print("=" * 60 + "\n")

    results = []

    # 同步测试
    results.append(("模块导入", test_imports()))
    results.append(("ToolResult", test_tool_result()))
    results.append(("LoopDetector", test_loop_detector()))
    results.append(("PatternFixer", test_pattern_fixer()))

    # 异步测试
    results.append(("ReadFileTool", await test_read_file_tool()))

    # 总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！错误处理改进已成功应用。\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查错误日志。\n")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
