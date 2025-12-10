"""
ReAct Agent 跨文件测试 - 案例16
"""

import sys
import os
import json
import shutil
import tempfile
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.react_agent import ReActAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_case_16():
    """案例16: NameError - 跨文件函数未import"""
    print("\n" + "=" * 60)
    print("案例16: NameError - 跨文件函数未import")
    print("=" * 60)
    
    # 1. 创建临时项目目录
    temp_dir = tempfile.mkdtemp(prefix="test_case_16_")
    print(f"临时目录: {temp_dir}")
    
    try:
        # 2. 创建项目文件
        # main.py
        main_code = "result = calculate(10, 20)\nprint(f'Result: {result}')"
        with open(os.path.join(temp_dir, "main.py"), "w") as f:
            f.write(main_code)
        
        # utils.py
        utils_code = "def calculate(a, b):\n    return a + b"
        with open(os.path.join(temp_dir, "utils.py"), "w") as f:
            f.write(utils_code)
        
        print(f"\n项目文件:")
        print(f"  main.py: {main_code}")
        print(f"  utils.py: {utils_code}")
        
        # 3. 错误信息
        error_traceback = """
Traceback (most recent call last):
  File "main.py", line 1, in <module>
    result = calculate(10, 20)
NameError: name 'calculate' is not defined
"""
        
        # 4. 运行ReAct Agent
        agent = ReActAgent()
        result = agent.debug(
            buggy_code=main_code,
            error_traceback=error_traceback,
            project_path=temp_dir
        )
        
        # 5. 打印结果
        print("\n" + "-" * 40)
        print("测试结果:")
        print(f"  成功: {result.get('success')}")
        print(f"  迭代次数: {result.get('iterations')}")
        
        if result.get('success'):
            print(f"\n修复后代码:\n{result.get('fixed_code', '')}")
            print(f"\n说明: {result.get('explanation', '')[:200]}")
        else:
            print(f"\n错误: {result.get('error')}")
        
        # 6. 打印ReAct历史
        print("\n" + "-" * 40)
        print("ReAct历史:")
        for h in result.get('history', []):
            action = h['action']
            tool = action.get('tool', action.get('type', ''))
            print(f"  迭代{h['iteration']}: {tool}")
        
        return result
        
    finally:
        # 7. 清理临时目录
        shutil.rmtree(temp_dir)
        print(f"\n临时目录已清理")


if __name__ == "__main__":
    print("🚀 测试ReAct Agent - 案例16（跨文件）")
    result = test_case_16()
    print("\n" + "=" * 60)
    print(f"测试完成! 成功: {result.get('success')}")
    print("=" * 60)