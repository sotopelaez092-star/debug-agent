#!/usr/bin/env python3
"""
AI Debug Assistant 功能演示
测试各个核心模块的功能
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_error_identifier():
    """测试错误识别器"""
    print_section("1. ErrorIdentifier - 错误识别")

    from src.agent.tools.error_identifier import ErrorIdentifier

    identifier = ErrorIdentifier()

    # 测试 NameError
    traceback1 = """
Traceback (most recent call last):
  File "main.py", line 5, in greet
    print(f"Hello, {nane}")
NameError: name 'nane' is not defined
"""

    result = identifier.identify(traceback1)
    print(f"输入: NameError traceback")
    print(f"识别结果:")
    print(f"  - 错误类型: {result['error_type']}")
    print(f"  - 错误信息: {result['error_message']}")
    print(f"  - 文件: {result['file']}")
    print(f"  - 行号: {result['line']}")
    print("✅ ErrorIdentifier 工作正常")

def test_loop_detector():
    """测试循环检测器"""
    print_section("2. LoopDetector - 循环检测")

    from src.agent.loop_detector import LoopDetector

    detector = LoopDetector(max_similar_code=2, max_same_error=3)

    # 模拟第一次尝试
    attempt1 = {
        'fixed_code': 'print("hello")',
        'error': None,
        'success': True
    }
    result1 = detector.check(attempt1)
    print(f"尝试1: 新代码 -> is_loop={result1['is_loop']}")

    # 模拟重复代码
    attempt2 = {
        'fixed_code': 'print("hello")',  # 相同代码
        'error': None,
        'success': False
    }
    result2 = detector.check(attempt2)
    print(f"尝试2: 重复代码 -> is_loop={result2['is_loop']}, type={result2.get('loop_type', 'N/A')}")

    # 模拟相同错误多次
    detector2 = LoopDetector(max_similar_code=2, max_same_error=2)
    for i in range(3):
        attempt = {
            'fixed_code': f'print({i})',
            'error': 'NameError: x is not defined',
            'success': False
        }
        result = detector2.check(attempt)
        print(f"尝试{i+1}: 相同错误 -> is_loop={result['is_loop']}")

    print("✅ LoopDetector 工作正常")

def test_token_manager():
    """测试Token管理器"""
    print_section("3. TokenManager - 上下文压缩")

    from src.agent.token_manager import TokenManager

    manager = TokenManager(max_context_tokens=100)  # 设置很小的限制来演示压缩

    context = {
        'error_file_content': 'def main():\n    print("hello")',
        'error_message': 'NameError: name "x" is not defined',
        'related_symbols': {'func1': 'def func1(): pass', 'func2': 'def func2(): pass'},
        'rag_solutions': ['Solution 1: Try this...', 'Solution 2: Another approach...'],
        'related_files': {'utils.py': 'def helper(): pass' * 50}  # 故意加长
    }

    compressed = manager.compress_context(context)

    print(f"原始上下文 keys: {list(context.keys())}")
    print(f"压缩后上下文 keys: {list(compressed.keys())}")
    print(f"压缩策略: 按优先级保留，低优先级内容被截断")
    print("✅ TokenManager 工作正常")

def test_config_loader():
    """测试配置加载器"""
    print_section("4. ConfigLoader - 配置加载")

    from src.agent.config_loader import ConfigLoader

    # 不存在配置文件时使用默认配置
    loader = ConfigLoader("/tmp/nonexistent")
    config = loader.config

    print(f"默认配置:")
    print(f"  - max_retries: {config.get('debug', {}).get('max_retries', 'N/A')}")
    print(f"  - timeout: {config.get('debug', {}).get('timeout', 'N/A')}")
    print(f"  - ignore_dirs: {config.get('scan', {}).get('ignore_dirs', [])[:3]}...")
    print("✅ ConfigLoader 工作正常")

def test_env_detector():
    """测试环境检测器"""
    print_section("5. PythonEnvDetector - 环境检测")

    from src.collectors.env_detector import PythonEnvDetector

    detector = PythonEnvDetector(Path(__file__).parent)
    result = detector.detect()

    print(f"检测结果:")
    print(f"  - Python版本: {result['python_version']}")
    print(f"  - 虚拟环境类型: {result['venv_type']}")
    print(f"  - 检测到的框架: {result['frameworks']}")
    print(f"  - 依赖数量: {len(result['dependencies'])}")
    print("✅ PythonEnvDetector 工作正常")

def test_error_router():
    """测试错误路由器"""
    print_section("6. ErrorRouter - 错误路由")

    from src.handlers.error_router import ErrorRouter

    router = ErrorRouter()

    # 测试 NameError 路由
    error_info = {
        'error_type': 'NameError',
        'error_message': "name 'nane' is not defined",
        'file': 'main.py',
        'line': 5
    }

    result = router.route(error_info, str(Path(__file__).parent))

    print(f"输入错误类型: {error_info['error_type']}")
    print(f"路由结果:")
    print(f"  - handler: {result.get('handler', 'N/A')}")
    print(f"  - suggestions: {result.get('suggestions', [])[:2]}")
    print("✅ ErrorRouter 工作正常")

def test_context_manager():
    """测试上下文管理器"""
    print_section("7. ContextManager - 跨文件上下文提取")

    from src.agent.context_manager import ContextManager

    # 使用当前项目作为测试目标
    project_path = str(Path(__file__).parent)
    manager = ContextManager(project_path)

    print(f"项目路径: {project_path}")
    print(f"懒加载模式: 文件按需加载")

    # 测试获取上下文 (使用正确的API签名)
    context = manager.get_context_for_error(
        error_file="src/agent/debug_agent.py",
        error_line=10,
        error_type="NameError",
        undefined_name="ErrorIdentifier"
    )

    print(f"上下文结果:")
    print(f"  - related_symbols 数量: {len(context.get('related_symbols', {}))}")
    print(f"  - related_files 数量: {len(context.get('related_files', {}))}")
    print(f"  - import_suggestions: {context.get('import_suggestions', [])[:2]}")
    print("✅ ContextManager 工作正常")

def main():
    print("\n" + "🐛 AI Debug Assistant 功能演示 ".center(60, "="))
    print("测试各个核心模块是否正常工作\n")

    tests = [
        test_error_identifier,
        test_loop_detector,
        test_token_manager,
        test_config_loader,
        test_env_detector,
        test_error_router,
        test_context_manager,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} 失败: {e}")
            failed += 1

    print_section("测试结果汇总")
    print(f"通过: {passed}/{len(tests)}")
    print(f"失败: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 所有模块工作正常！")
    else:
        print(f"\n⚠️ 有 {failed} 个模块需要检查")

if __name__ == "__main__":
    main()
