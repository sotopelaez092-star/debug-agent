#!/usr/bin/env python3
"""测试pandas_118案例"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent.debug_agent import DebugAgent
from dotenv import load_dotenv

load_dotenv()

buggy_code = """import numpy as np
from pandas.core.dtypes.missing import notna
from pandas.core.arrays import Categorical
from pandas.core.frame import DataFrame
from pandas.core.indexes.base import Index

def melt(frame, id_vars=None, value_vars=None):
    cols = ['col1', 'col2', 'col3']
    
    if id_vars is not None:
        if not isinstance(id_vars, (list, tuple)):
            id_vars = [id_vars]
        else:
            id_vars = list(id_vars)
            missing = Index(com.flatten(id_vars)).difference(cols)
            if not missing.empty:
                raise KeyError("id_vars not found")
    
    if value_vars is not None:
        value_vars = list(value_vars)
        missing = Index(com.flatten(value_vars)).difference(cols)
        if not missing.empty:
            raise KeyError("value_vars not found")
    
    return frame
"""

error_traceback = "NameError: name 'com' is not defined"

api_key = os.getenv("DEEPSEEK_API_KEY")
agent = DebugAgent(api_key=api_key, project_path=None)

print("🧪 测试 pandas_118...")
start = time.time()
result = agent.debug(buggy_code, error_traceback)
elapsed = time.time() - start

print(f"\n{'✅' if result['success'] else '❌'} 成功: {result['success']}")
print(f"⏱️  耗时: {elapsed:.2f}秒")
print(f"🔄 尝试: {len(result['attempts'])}")

if result['success']:
    # ✅ fixed_code在attempts[0]里
    fixed = result['attempts'][0]['fixed_code']
    has_numpy = 'import numpy' in fixed
    has_pandas = 'import pandas' in fixed or 'from pandas' in fixed
    
    print(f"\n🔍 numpy: {'❌存在' if has_numpy else '✅已移除'}")
    print(f"🔍 pandas: {'❌存在' if has_pandas else '✅已移除'}")
    
    if not has_numpy and not has_pandas:
        print("\n🎉 完美！所有第三方库已移除！")
        print("\n修复说明:")
        print(result['attempts'][0]['explanation'])