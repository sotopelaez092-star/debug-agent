import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import tempfile
import os
import logging

# 开启详细日志
logging.basicConfig(level=logging.INFO)

from src.agent.react_agent import ReActAgent

# 加载案例23
with open("data/test_cases/week6_test_set.json") as f:
    data = json.load(f)

case = [c for c in data['test_cases'] if c['id'] == 23][0]
print(f"案例: {case['name']}")
print(f"错误: {case['error_message']}")

# 创建临时目录
temp_dir = tempfile.mkdtemp(prefix="debug_case23_")
for file_path, content in case['project_files'].items():
    full_path = os.path.join(temp_dir, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True) if os.path.dirname(full_path) else None
    with open(full_path, 'w') as f:
        f.write(content)

print(f"\n临时目录: {temp_dir}")
print(f"文件: {os.listdir(temp_dir)}")

# 运行Agent
agent = ReActAgent()
result = agent.debug(
    buggy_code=case['project_files'][case['error_file']],
    error_traceback=f"Traceback:\n  File \"{case['error_file']}\", line 1\n{case['error_message']}",
    project_path=temp_dir
)

print(f"\n结果: {'成功' if result['success'] else '失败'}")
print(f"迭代: {result.get('iterations', 0)}")