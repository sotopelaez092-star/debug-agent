"""测试MultiFileFixer"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO)

from src.agent.tools.multi_file_fixer import MultiFileFixer

# 案例23的数据
all_files = {
    "main.py": """from models import User
user = User('Tom')
print(user.age)""",
    
    "models.py": """class User:
    def __init__(self, name):
        self.name = name"""
}

error_file = "main.py"
error_message = "AttributeError: 'User' object has no attribute 'age'"

# 测试
print("=" * 60)
print("测试 MultiFileFixer - 案例23")
print("=" * 60)
print(f"错误: {error_message}")
print(f"文件: {list(all_files.keys())}")
print("=" * 60)

fixer = MultiFileFixer()
result = fixer.fix(
    error_file=error_file,
    error_message=error_message,
    all_files=all_files
)

print(f"\n成功: {result['success']}")
print(f"分析: {result.get('analysis', '')}")
print(f"说明: {result.get('explanation', '')}")

if result['success']:
    print("\n修复后的文件:")
    for filename, content in result['fixed_files'].items():
        print(f"\n--- {filename} ---")
        print(content)