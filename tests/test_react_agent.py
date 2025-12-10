"""
ReAct Agent 测试脚本
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.react_agent import ReActAgent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_simple_name_error():
    """测试1: 简单的NameError（单文件）"""
    print("\n" + "=" * 60)
    print("测试1: 简单的NameError（拼写错误）")
    print("=" * 60)
    
    buggy_code = '''
def greet(name):
    print(f"Hello, {nme}")  # 拼写错误: nme -> name

greet("World")
'''
    
    error_traceback = '''
Traceback (most recent call last):
  File "test.py", line 5, in <module>
    greet("World")
  File "test.py", line 2, in greet
    print(f"Hello, {nme}")
NameError: name 'nme' is not defined
'''
    
    # 创建Agent并运行
    agent = ReActAgent()
    result = agent.debug(
        buggy_code=buggy_code,
        error_traceback=error_traceback
    )
    
    # 打印结果
    print("\n" + "-" * 40)
    print("测试结果:")
    print(f"  成功: {result.get('success')}")
    print(f"  迭代次数: {result.get('iterations')}")
    
    if result.get('success'):
        print(f"\n修复后代码:\n{result.get('fixed_code', '')[:500]}")
        print(f"\n说明: {result.get('explanation', '')[:200]}")
    else:
        print(f"\n错误: {result.get('error')}")
    
    # 打印历史（简化版）
    print("\n" + "-" * 40)
    print("ReAct历史:")
    for h in result.get('history', []):
        print(f"\n迭代 {h['iteration']}:")
        print(f"  Action: {h['action'].get('type')} - {h['action'].get('tool', '')}")
        if h.get('observation'):
            print(f"  Observation: {h['observation'][:100]}...")
    
    return result


if __name__ == "__main__":
    print("🚀 开始测试 ReAct Agent")
    print("=" * 60)
    
    result = test_simple_name_error()
    
    print("\n" + "=" * 60)
    print(f"测试完成! 成功: {result.get('success')}")
    print("=" * 60)