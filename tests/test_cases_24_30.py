"""测试案例24-30"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import tempfile
import os
import time
import shutil
import logging

logging.basicConfig(level=logging.INFO)

from src.agent.react_agent import ReActAgent

# 加载测试案例
with open("data/test_cases/week6_test_set.json") as f:
    data = json.load(f)

# 筛选案例24-30
cases = [c for c in data['test_cases'] if 24 <= c['id'] <= 30]
print(f"测试案例: {[c['id'] for c in cases]}")
print("=" * 60)

agent = ReActAgent()
results = []

for case in cases:
    print(f"\n[案例{case['id']}] {case['name']}")
    print(f"错误: {case['error_message']}")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix=f"test_case_{case['id']}_")
    
    try:
        # 创建项目文件
        for file_path, content in case['project_files'].items():
            full_path = os.path.join(temp_dir, file_path)
            dir_name = os.path.dirname(full_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
        
        # 运行Agent
        start_time = time.time()
        result = agent.debug(
            buggy_code=case['project_files'][case['error_file']],
            error_traceback=f"Traceback:\n  File \"{case['error_file']}\", line 1\n{case['error_message']}",
            project_path=temp_dir if len(case['project_files']) > 1 else None
        )
        elapsed = time.time() - start_time
        
        status = "✅" if result['success'] else "❌"
        print(f"{status} 迭代: {result.get('iterations', 0)}, 耗时: {elapsed:.1f}s")
        
        results.append({
            'id': case['id'],
            'name': case['name'],
            'success': result['success'],
            'iterations': result.get('iterations', 0),
            'time': round(elapsed, 1)
        })
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# 打印汇总
print("\n" + "=" * 60)
print("汇总")
print("=" * 60)
success = sum(1 for r in results if r['success'])
print(f"成功: {success}/{len(results)}")
for r in results:
    status = "✅" if r['success'] else "❌"
    print(f"  {status} 案例{r['id']}: {r['name']} ({r['iterations']}次, {r['time']}s)")