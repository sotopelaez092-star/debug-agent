# tests/test_case_30.py
import sys
sys.path.insert(0, '/Users/FiaShi/Desktop/projects/debug-agent')

from src.agent.react_agent import ReActAgent
import tempfile
import os

# 案例30数据
case = {
    "main.py": """from utils import process
data = None
result = process(data)
print(result.upper())""",
    "utils.py": """def process(data):
    if data is None:
        return None
    return data * 2""",
    "traceback": """Traceback:
  File "main.py", line 4
AttributeError: 'NoneType' object has no attribute 'upper'"""
}

# 创建临时项目
with tempfile.TemporaryDirectory() as tmpdir:
    for filename, content in case.items():
        if filename != "traceback":
            filepath = os.path.join(tmpdir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
    
    agent = ReActAgent()
    result = agent.debug(
        buggy_code=case["main.py"],
        error_traceback=case["traceback"],
        project_path=tmpdir
    )
    
    print(f"成功: {result['success']}")
    print(f"迭代: {result['iterations']}")
