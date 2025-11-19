"""
测试CodeFixer with Context
"""
import os
import sys
from typing import Optional, Dict, Any
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.agent.tools.code_fixer import CodeFixer


def test_build_prompt_with_context():
    """测试Prompt构建包含上下文"""
    fixer = CodeFixer(api_key="fake-key")
    
    buggy_code = "result = calculate(10, 20)"
    error_message = "NameError: name 'calculate' is not defined"
    
    context = {
        "related_symbols": {
            "calculate": {
                "file": "utils.py",
                "definition": "def calculate(a, b):\n    return a + b",
                "type": "function"
            }
        },
        "import_suggestions": ["from utils import calculate"]
    }
    
    prompt = fixer._build_prompt(buggy_code, error_message, context, None)
    
    # 验证Prompt包含关键信息
    assert "calculate" in prompt
    assert "utils.py" in prompt
    assert "def calculate(a, b)" in prompt
    assert "from utils import calculate" in prompt
    assert "NameError" in prompt
    
    print("✅ Prompt构建测试通过")
    print("\n生成的Prompt:")
    print("=" * 60)
    print(prompt)
    print("=" * 60)


if __name__ == "__main__":
    test_build_prompt_with_context()