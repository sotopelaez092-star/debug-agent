"""
端到端集成测试
测试3个工具的协同工作
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.agent.tools.error_identifier import ErrorIdentifier
from src.agent.tools.rag_searcher import RAGSearcher
from src.agent.tools.code_fixer import CodeFixer


def test_full_debug_flow():
    """
    测试完整的Debug流程
    
    流程：
    1. ErrorIdentifier识别错误
    2. RAGSearcher检索解决方案
    3. CodeFixer生成修复
    """
    print("=" * 60)
    print("🚀 开始端到端测试：完整Debug流程")
    print("=" * 60)
    
    # ========== 测试数据 ==========
    buggy_code = """
def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    return total / count

result = calculate_average([])
print(result)
"""
    
    error_traceback = """
Traceback (most recent call last):
  File "test.py", line 6, in <module>
    result = calculate_average([])
  File "test.py", line 4, in calculate_average
    return total / count
ZeroDivisionError: division by zero
"""
    
    print("\n📝 测试代码:")
    print(buggy_code)
    print("\n❌ 错误信息:")
    print(error_traceback)
    
    # ========== 步骤1: 识别错误 ==========
    print("\n" + "=" * 60)
    print("步骤1: ErrorIdentifier - 识别错误")
    print("=" * 60)
    
    identifier = ErrorIdentifier()
    error_info = identifier.identify(error_traceback)
    
    print(f"\n✅ 错误识别结果:")
    print(f"  错误类型: {error_info['error_type']}")
    print(f"  错误描述: {error_info['error_message']}")
    print(f"  文件: {error_info['file']}")
    print(f"  行号: {error_info['line']}")
    
    # ========== 步骤2: 检索解决方案 ==========
    print("\n" + "=" * 60)
    print("步骤2: RAGSearcher - 检索解决方案")
    print("=" * 60)
    
    searcher = RAGSearcher()
    
    # 构造查询（使用错误类型 + 错误描述）
    search_query = f"{error_info['error_type']}: {error_info['error_message']}"
    
    solutions = searcher.search(search_query, top_k=3)
    
    print(f"\n✅ 检索到 {len(solutions)} 个相关方案:")
    for i, sol in enumerate(solutions, 1):
        print(f"\n  方案{i} (相似度: {sol['similarity']:.3f}):")
        print(f"  {sol['content'][:150]}...")
    
    # ========== 步骤3: 生成修复 ==========
    print("\n" + "=" * 60)
    print("步骤3: CodeFixer - 生成修复")
    print("=" * 60)
    
    fixer = CodeFixer()
    
    fix_result = fixer.fix_code(
        buggy_code=buggy_code,
        error_message=error_traceback,
        solutions=solutions
    )
    
    print(f"\n✅ 修复完成!")
    print(f"\n修复后的代码:")
    print("-" * 60)
    print(fix_result['fixed_code'])
    print("-" * 60)
    
    print(f"\n修复说明:")
    print(fix_result['explanation'])
    
    print(f"\n改动列表:")
    for change in fix_result['changes']:
        print(f"  • {change}")
    
    # ========== 总结 ==========
    print("\n" + "=" * 60)
    print("🎉 端到端测试完成！")
    print("=" * 60)
    print(f"✅ 错误识别: {error_info['error_type']}")
    print(f"✅ 知识检索: {len(solutions)} 个方案")
    print(f"✅ 代码修复: 成功生成")
    print("=" * 60)


if __name__ == "__main__":
    test_full_debug_flow()